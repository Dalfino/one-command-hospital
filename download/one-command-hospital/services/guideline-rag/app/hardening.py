"""Security & observability hardening kit — container-local, zero dependencies.

Duplicated BY DESIGN into each FastAPI service's build context (services/*/app/)
instead of a shared package, so every Docker build stays self-contained.

`install(app, service)` wires, in this order:
  1. /metrics endpoint        — Prometheus text exposition (no third-party client)
  2. request metrics          — http_requests_total{service,route,code}
                                http_request_duration_ms histogram{service,route}
  3. X-Request-ID tracing     — generate-or-propagate; contextvar + response header
  4. body-size cap            — 413 over BODY_LIMIT_BYTES (default 1 MB)
  5. per-IP token bucket      — 429 over RATE_LIMIT_RPS / RATE_LIMIT_BURST
  6. security headers         — nosniff / DENY / no-store on every response
  7. structured access log    — one JSON line per request to stdout

Logging policy (HIPAA / audit hygiene): NEVER log raw clinical text. Pass
`question_sha=` / `text_len=` style fields instead — json_log() redacts the
known raw-text field names as a second line of defense.

Extra collectors (refusals, findings, gauges) are registered via `extra=`.
"""
import hashlib
import json as _json
import os
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
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

# ── Structured logging + request tracing ─────────────────────────────────
# request_id lives in a contextvar so any layer can stamp its log lines with
# the same trace id the middleware assigned (mediator generates the root id;
# downstream services propagate it via the X-Request-ID header).
_request_id: ContextVar = ContextVar("request_id", default=None)

# Field names whose values must never hit the logs raw. json_log redacts them
# with a length marker so debugging still shows shape, never content.
_RAW_TEXT_FIELDS = {"question", "text", "answer", "note", "context", "contexttext",
                    "context_text", "prompt", "payload", "narrative"}


def request_id_of() -> str | None:
    """Current request's trace id (set by the hardening middleware)."""
    return _request_id.get()


def text_sha(s: str) -> str:
    """Short SHA prefix for logging text without logging text."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def _redact(fields: dict) -> dict:
    out = {}
    for k, v in fields.items():
        if k.lower() in _RAW_TEXT_FIELDS:
            out[k] = f"<redacted len={len(str(v))}>"
        else:
            out[k] = v
    return out


def json_log(service: str, event: str, level: str = "info",
             request_id: str | None = None, **fields) -> None:
    """One JSON line to stdout: {ts, level, service, event, request_id, ...}.
    Ships with any container log driver; keep it parseable, keep it PHI-free."""
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "level": level,
        "service": service,
        "event": event,
        "request_id": request_id if request_id is not None else _request_id.get(),
        **_redact(fields),
    }
    print(_json.dumps(rec, ensure_ascii=False), flush=True)


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
    """Attach metrics, tracing, rate limiting, body cap, security headers, logs."""
    limiter = _RateLimiter(RATE_RPS, RATE_BURST)
    for c in (extra or []):
        _register(c)

    class HardeningMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            # X-Request-ID: propagate the caller's trace id or mint one. The
            # mediator generates the root id for a clinical question; every
            # downstream hop reuses it so one request = one greppable trace.
            rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
            _request_id.set(rid)

            def _stamp(resp):
                resp.headers["X-Request-ID"] = rid
                return resp

            if request.url.path == "/metrics":
                lines = []
                for collector in REGISTRY:
                    lines += collector.render()
                return _stamp(Response("\n".join(lines) + "\n",
                                       media_type="text/plain; version=0.0.4; charset=utf-8"))
            cl = request.headers.get("content-length", "")
            if cl.isdigit() and int(cl) > BODY_LIMIT:
                REQUESTS.inc({"service": service, "route": request.url.path, "code": "413"})
                return _stamp(JSONResponse({"error": "payload too large"}, status_code=413))
            ip = request.client.host if request.client else "anon"
            if not limiter.allow(ip):
                REQUESTS.inc({"service": service, "route": request.url.path, "code": "429"})
                return _stamp(JSONResponse({"error": "rate limit exceeded"}, status_code=429))
            start = time.perf_counter()
            response = await call_next(request)
            ms = (time.perf_counter() - start) * 1000
            REQUESTS.inc({"service": service, "route": request.url.path,
                          "code": str(response.status_code)})
            DURATION.observe({"service": service, "route": request.url.path}, ms)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Cache-Control"] = "no-store"
            json_log(service, "http_request", request_id=rid,
                     method=request.method, path=request.url.path,
                     status=response.status_code, ms=round(ms, 1))
            return _stamp(response)

    app.add_middleware(HardeningMiddleware)
