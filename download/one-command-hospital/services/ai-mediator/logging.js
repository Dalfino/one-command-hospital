/**
 * logging.js — structured JSON logging + trace ids for ai-mediator (zero deps).
 *
 * Mirrors the per-service hardening.py (services/<svc>/app/) so Python and Node
 * logs land in the same shape: { ts, level, service, event, request_id, ...fields }.
 *
 * PHI policy: the mediator handles the raw clinical question, so this module
 * enforces the no-narrative rule — known raw-text field names are redacted to
 * a length marker, and questionHash() is the ONLY sanctioned way to correlate
 * a log line with a question (short SHA prefix, irreversible in practice).
 */
import { createHash, randomUUID } from "node:crypto";

const RAW_TEXT_FIELDS = new Set([
  "question", "text", "answer", "note", "context", "contexttext",
  "context_text", "prompt", "payload", "narrative",
]);

function redact(fields = {}) {
  const out = {};
  for (const [k, v] of Object.entries(fields)) {
    out[k] = RAW_TEXT_FIELDS.has(k.toLowerCase())
      ? `<redacted len=${String(v).length}>`
      : v;
  }
  return out;
}

export function logEvent(service, event, fields = {}, opts = {}) {
  const rec = {
    ts: new Date().toISOString(),
    level: opts.level || "info",
    service,
    event,
    request_id: opts.requestId ?? null,
    ...redact(fields),
  };
  console.log(JSON.stringify(rec));
}

export const newRequestId = () => randomUUID().replace(/-/g, "").slice(0, 16);

export function questionHash(q) {
  return createHash("sha256").update(String(q)).digest("hex").slice(0, 12);
}
