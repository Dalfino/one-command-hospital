/**
 * Node tier — metrics.js exposition contract.
 *
 * Prometheus scrapes this; a malformed line breaks monitoring silently.
 * Pins render correctness for counters/histograms/gauges and the label-value
 * escaping that stops a crafted route string from injecting fake series.
 */
import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";

const modUrl = new URL("../../services/ai-mediator/metrics.js", import.meta.url);
const m = await import(fileURLToPath(modUrl));

test("counter renders sorted labelled series", () => {
  const c = new m.Counter("test_c_total", "help text");
  c.inc({ route: "/b", code: "200" });
  c.inc({ route: "/b", code: "200" });
  const lines = c.render();
  assert.equal(lines[0], "# HELP test_c_total help text");
  assert.equal(lines[1], "# TYPE test_c_total counter");
  assert.ok(lines.includes('test_c_total{code="200",route="/b"} 2'));
});

test("histogram buckets cumulative +Inf equals count", () => {
  const h = new m.Histogram("test_h_ms", "help", );
  h.observe({ route: "/x" }, 7);
  h.observe({ route: "/x" }, 30);
  h.observe({ route: "/x" }, 99999);
  const joined = h.render().join("\n");
  assert.ok(joined.includes('test_h_ms_bucket{route="/x",le="10"} 1'));
  assert.ok(joined.includes('test_h_ms_bucket{route="/x",le="100"} 2'));
  assert.ok(joined.includes('test_h_ms_bucket{route="/x",le="+Inf"} 3'));
  assert.ok(joined.includes('test_h_ms_count{route="/x"} 3'));
});

test("label values are escaped — no series injection", () => {
  c_inc_injection();
  const out = m.renderMetrics();
  // the crafted route must appear escaped, and must not create a fake label
  assert.ok(out.includes('route="a\\", b=\\"c"'));
  assert.ok(!out.includes('route="a", b="c"'));
});

function c_inc_injection() {
  m.REQUESTS.inc({ route: 'a", b="c', code: "200" });
}

test("renderMetrics exposes the mediator governance collectors", () => {
  const out = m.renderMetrics();
  for (const name of [
    "http_requests_total", "http_request_duration_ms", "mediator_refusals_total",
    "mediator_ungrounded_total", "mediator_signoffs_total", "audit_events_total",
    "audit_verify_failures_total", "audit_records_last",
  ]) {
    assert.ok(out.includes(`# TYPE ${name} `), `missing collector: ${name}`);
  }
});
