/**
 * metrics.js — zero-dependency Prometheus text-format metrics for ai-mediator.
 *
 * Mirrors services/hardening.py: http_requests_total{route,code},
 * http_request_duration_ms histogram{route}, plus mediator-specific counters
 * (refusals, sign-offs, audit chain state). Prometheus scrapes /metrics.
 */

const BUCKETS_MS = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000];

// Prometheus text format escapes backslash, double-quote and newline inside
// label values — without this, a crafted route string could inject fake
// series into the exposition.
function escapeLabelValue(v) {
  return String(v).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n");
}

function labelsKey(labels) {
  return Object.entries(labels).sort(([a], [b]) => (a < b ? -1 : 1))
    .map(([k, v]) => `${k}="${escapeLabelValue(v)}"`).join(",");
}

export class Counter {
  constructor(name, help) {
    this.name = name;
    this.help = help;
    this.values = new Map();
  }
  inc(labels, amount = 1) {
    const key = labelsKey(labels);
    this.values.set(key, (this.values.get(key) || 0) + amount);
  }
  render() {
    const out = [`# HELP ${this.name} ${this.help}`, `# TYPE ${this.name} counter`];
    for (const [key, val] of [...this.values.entries()].sort()) {
      out.push(`${this.name}{${key}} ${val}`);
    }
    return out;
  }
}

export class Histogram {
  constructor(name, help) {
    this.name = name;
    this.help = help;
    this.counts = new Map(); // key -> cumulative-per-bucket array
    this.sums = new Map();
    this.totals = new Map();
  }
  observe(labels, ms) {
    const key = labelsKey(labels);
    if (!this.counts.has(key)) this.counts.set(key, new Array(BUCKETS_MS.length).fill(0));
    const arr = this.counts.get(key);
    for (let i = 0; i < BUCKETS_MS.length; i++) {
      if (ms <= BUCKETS_MS[i]) arr[i] += 1; // cumulative by construction
    }
    this.sums.set(key, (this.sums.get(key) || 0) + ms);
    this.totals.set(key, (this.totals.get(key) || 0) + 1);
  }
  render() {
    const out = [`# HELP ${this.name} ${this.help}`, `# TYPE ${this.name} histogram`];
    for (const [key, arr] of [...this.counts.entries()].sort()) {
      const base = key ? `${key},` : "";
      for (let i = 0; i < BUCKETS_MS.length; i++) {
        out.push(`${this.name}_bucket{${base}le="${BUCKETS_MS[i]}"} ${arr[i]}`);
      }
      out.push(`${this.name}_bucket{${base}le="+Inf"} ${this.totals.get(key) || 0}`);
      out.push(`${this.name}_sum{${key}} ${(this.sums.get(key) || 0).toFixed(3)}`);
      out.push(`${this.name}_count{${key}} ${this.totals.get(key) || 0}`);
    }
    return out;
  }
}

export class Gauge {
  constructor(name, help) {
    this.name = name;
    this.help = help;
    this.values = new Map();
  }
  set(labels, value) {
    this.values.set(labelsKey(labels), value);
  }
  render() {
    const out = [`# HELP ${this.name} ${this.help}`, `# TYPE ${this.name} gauge`];
    for (const [key, val] of [...this.values.entries()].sort()) {
      out.push(`${this.name}{${key}} ${val}`);
    }
    return out;
  }
}

export const REQUESTS = new Counter("http_requests_total", "HTTP requests processed.");
export const DURATION = new Histogram("http_request_duration_ms", "Request latency in ms.");
export const REFUSALS = new Counter("mediator_refusals_total", "Refusals observed from RAG, by reason.");
export const UNGROUNDED = new Counter("mediator_ungrounded_total", "Answers that failed verification.");
export const SIGNOFFS = new Counter("mediator_signoffs_total", "Human sign-offs/escalations recorded, by action.");
export const AUDIT_EVENTS = new Counter("audit_events_total", "Audit events appended, by action.");
export const AUDIT_VERIFY_FAILURES = new Counter("audit_verify_failures_total", "Chain verification failures.");
export const AUDIT_RECORDS = new Gauge("audit_records_last", "Record count at the last chain verification.");
export const REVIEW_OPEN = new Gauge("review_queue_open", "Open items in the clinician review queue.");
export const REVIEW_RESOLVED = new Counter("review_resolutions_total", "Clinician review resolutions, by decision.");

export function renderMetrics() {
  const collectors = [REQUESTS, DURATION, REFUSALS, UNGROUNDED, SIGNOFFS, AUDIT_EVENTS, AUDIT_VERIFY_FAILURES, AUDIT_RECORDS, REVIEW_OPEN, REVIEW_RESOLVED];
  const lines = [];
  for (const c of collectors) lines.push(...c.render());
  return lines.join("\n") + "\n";
}
