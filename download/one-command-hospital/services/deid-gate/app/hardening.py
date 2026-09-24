"""Security & observability hardening kit — container-local, zero dependencies.

Duplicated BY DESIGN into each FastAPI service's build context (services/*/app/)
instead of a shared package, so every Docker build stays self-contained.

`install(app, service)` wires, in this order:
  1. /metrics endpoint        — Prometheus text exposition (no third-party client)
  2. request metrics          — http_requests_total{service,route,code}
                                http_request_duration_ms histogram{service,route}
  3. body-size cap            — 413 over BODY_LIMIT_BYTES (default 1 MB)
  4. per-IP token bucket      — 429 over RATE_LIMIT_RPS / RATE_LIMIT_BURST
  5. security headers         — nosniff / DENY / no-store on every response

Extra collectors (refusals, findings, gauges) are registered via `extra=`.
"""
import os
import time
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

DEFAULT_BUCKETS_MS = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

def _labels(labels: dict) -> tuple:
    return tuple(sorted(labels.items()))


def _fmt(key: tuple) -> str:
    return ",".join(f'{k}="{v}"' for k, v in key)


class Counter:
    def __init__(self, name: str, help_text: str):
        self.name, self.help_text = name, help_text
        self._values: dict = {}
        self._lock = Lock()

    def inc(self, labels: dict, amount: float = 1.0):
        key = _labels(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + amount

    def render(self):
        out = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} counter"]
        for key, val in sorted(self._values.items()):
            out.append(f"{self.name}{{{_fmt(key)}}} {val}")
        return out


class Gauge:
    def __init__(self, name: str, help_text: str):
        self.name, self.help_text = name, help_text
        self._values: dict = {}
        self._lock = Lock()

    def set(self, labels: dict, value: float):
        with self._lock:
            self._values[_labels(labels)] = float(value)

    def render(self):
        out = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} gauge"]
        for key, val in sorted(self._values.items()):
            out.append(f"{self.name}{{{_fmt(key)}}} {val}")
        return out


class Histogram:
    def __init__(self, name: str, help_text: str, buckets=None):
        self.name, self.help_text = name, help_text
        self._buckets = buckets or DEFAULT_BUCKETS_MS
        self._counts: dict = {}   # key -> [cumulative per bucket]
        self._sums: dict = {}
        self._totals: dict = {}
        self._lock = Lock()

    def observe(self, labels: dict, value: float):
        key = _labels(labels)
        with self._lock:
            if key not in self._counts:
                self._counts[key] = [0] * len(self._buckets)
            for i, bound in enumerate(self._buckets):
                if value <= bound:
                    self._counts[key][i] += 1   # cumulative by construction
            self._sums[key] = self._sums.get(key, 0.0) + value
            self._totals[key] = self._totals.get(key, 0) + 1

    def render(self):
        out = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} histogram"]
        for key, counts in sorted(self._counts.items()):
            lbl = _fmt(key)
            base = lbl + "," if lbl else ""
            for i, bound in enumerate(self._buckets):
                out.append(f'{self.name}_bucket{{{base}le="{bound}"}} {counts[i]}')
            out.append(f'{self.name}_bucket{{{base}le="+Inf"}} {self._totals.get(key, 0)}')
            out.append(f'{self.name}_sum{{{lbl}}} {round(self._sums.get(key, 0.0), 3)}')
            out.append(f'{self.name}_count{{{lbl}}} {self._totals.get(key, 0)}')
        return out


REGISTRY = []


def _register(collector):
    REGISTRY.append(collector)
    return collector


REQUESTS = _register(Counter("http_requests_total", "HTTP requests processed."))
DURATION = _register(Histogram("http_request_duration_ms", "Request latency in ms."))

RATE_RPS = float(os.environ.get("RATE_LIMIT_RPS", "10"))
RATE_BURST = float(os.environ.get("RATE_LIMIT_BURST", "20"))
BODY_LIMIT = int(os.environ.get("BODY_LIMIT_BYTES", "1000000"))


class _RateLimiter:
    def __init__(self, rate: float, burst: float):
        self.rate, self.burst = rate, burst
        self._buckets: dict = {}
        self._lock = Lock()

    def allow(self, key) -> bool:
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(key, (self.burst, now))
            tokens = min(self.burst, tokens + (now - last) * self.rate)
            if tokens < 1.0:
                self._buckets[key] = (tokens, now)
                return False
            self._buckets[key] = (tokens - 1.0, now)
            return True


def install(app, service: str, extra=None):
    """Attach metrics endpoint, rate limiting, body cap and security headers."""
    limiter = _RateLimiter(RATE_RPS, RATE_BURST)
    for c in (extra or []):
        _register(c)

    class HardeningMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.path == "/metrics":
                lines = []
                for collector in REGISTRY:
                    lines += collector.render()
                return Response("\n".join(lines) + "\n",
                                media_type="text/plain; version=0.0.4; charset=utf-8")
            cl = request.headers.get("content-length", "")
            if cl.isdigit() and int(cl) > BODY_LIMIT:
                REQUESTS.inc({"service": service, "route": request.url.path, "code": "413"})
                return JSONResponse({"error": "payload too large"}, status_code=413)
            ip = request.client.host if request.client else "anon"
            if not limiter.allow(ip):
                REQUESTS.inc({"service": service, "route": request.url.path, "code": "429"})
                return JSONResponse({"error": "rate limit exceeded"}, status_code=429)
            start = time.perf_counter()
            response = await call_next(request)
            ms = (time.perf_counter() - start) * 1000
            REQUESTS.inc({"service": service, "route": request.url.path,
                          "code": str(response.status_code)})
            DURATION.observe({"service": service, "route": request.url.path}, ms)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Cache-Control"] = "no-store"
            return response

    app.add_middleware(HardeningMiddleware)
