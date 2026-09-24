"""Unit tier — the hardening kit.

Covers the security primitives every service ships: token-bucket rate
limiting, metric render correctness, request tracing and the body cap —
the exact code that sits in front of every clinical request.
"""
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import hardening
from hardening import _RateLimiter, Counter, Gauge, Histogram, install


# ── token bucket ──────────────────────────────────────────────────────────

def test_rate_limiter_allows_burst_then_rejects():
    rl = _RateLimiter(rate=1, burst=2)
    assert rl.allow("ip1") is True
    assert rl.allow("ip1") is True
    assert rl.allow("ip1") is False          # burst exhausted


def test_rate_limiter_refills_over_time():
    rl = _RateLimiter(rate=50, burst=1)      # 50 tokens/sec → 20ms per token
    assert rl.allow("ip9") is True
    assert rl.allow("ip9") is False
    time.sleep(0.03)                         # ≈1.5 tokens accrued
    assert rl.allow("ip9") is True


def test_rate_limiter_is_per_key():
    rl = _RateLimiter(rate=1, burst=1)
    assert rl.allow("a") is True
    assert rl.allow("b") is True             # other IPs unaffected
    assert rl.allow("a") is False


# ── metric render correctness ─────────────────────────────────────────────

def test_counter_renders_sorted_labels_and_totals():
    c = Counter("test_counter_total", "help text")
    c.inc({"route": "/b", "code": "200"})
    c.inc({"route": "/b", "code": "200"})
    c.inc({"route": "/a", "code": "500"})
    lines = c.render()
    assert lines[0] == "# HELP test_counter_total help text"
    assert lines[1] == "# TYPE test_counter_total counter"
    assert 'test_counter_total{code="200",route="/b"} 2.0' in lines
    assert 'test_counter_total{code="500",route="/a"} 1.0' in lines


def test_histogram_buckets_are_cumulative_with_inf_and_sum():
    h = Histogram("test_hist_ms", "help", buckets=[10, 100])
    h.observe({"route": "/x"}, 5)     # ≤10, ≤100
    h.observe({"route": "/x"}, 50)    # ≤100 only
    h.observe({"route": "/x"}, 500)   # neither → only +Inf
    lines = h.render()
    joined = "\n".join(lines)
    assert 'test_hist_ms_bucket{route="/x",le="10"} 1' in joined
    assert 'test_hist_ms_bucket{route="/x",le="100"} 2' in joined
    assert 'test_hist_ms_bucket{route="/x",le="+Inf"} 3' in joined
    assert 'test_hist_ms_count{route="/x"} 3' in joined
    assert 'test_hist_ms_sum{route="/x"} 555' in joined


def test_gauge_renders_latest_value():
    g = Gauge("test_gauge", "help")
    g.set({"route": "/x"}, 0.123)
    assert 'test_gauge{route="/x"} 0.123' in g.render()


# ── middleware: tracing, headers, body cap, rate limit ────────────────────

@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(hardening, "RATE_RPS", 1000)   # effectively unlimited
    monkeypatch.setattr(hardening, "RATE_BURST", 1000)
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"ok": True}

    install(app, "test-svc")
    return TestClient(app)


def test_request_id_is_generated_and_echoed(client):
    r = client.get("/health")
    assert r.status_code == 200
    rid = r.headers["X-Request-ID"]
    assert 8 <= len(rid) <= 32


def test_request_id_is_propagated_from_caller(client):
    r = client.get("/health", headers={"X-Request-ID": "trace-abc-123"})
    assert r.headers["X-Request-ID"] == "trace-abc-123"


def test_security_headers_on_every_response(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Cache-Control"] == "no-store"


def test_body_cap_returns_413(client, monkeypatch):
    monkeypatch.setattr(hardening, "BODY_LIMIT", 10)
    r = client.post("/health", content=b"x" * 64,
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_rate_limit_returns_429(monkeypatch):
    monkeypatch.setattr(hardening, "RATE_RPS", 0.001)
    monkeypatch.setattr(hardening, "RATE_BURST", 1)
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"ok": True}

    install(app, "test-svc-rate")
    c = TestClient(app)
    assert c.get("/health").status_code == 200
    assert c.get("/health").status_code == 429
