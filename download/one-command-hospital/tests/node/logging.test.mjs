/**
 * Node tier — logging.js structured-log contract.
 *
 * Pins the PHI rule: raw narrative fields are redacted with a length marker,
 * shape matches the Python hardening.py JSON logs, trace ids mint uniquely,
 * and questionHash is the only sanctioned question→log correlation.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { mock } from "node:test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const modUrl = new URL("../../services/ai-mediator/logging.js", import.meta.url);
const { logEvent, newRequestId, questionHash } = await import(fileURLToPath(modUrl));

function captureLog(fn) {
  const calls = [];
  const m = mock.method(console, "log", (...args) => calls.push(args.join(" ")));
  try { fn(); } finally { m.mock.restore(); }
  assert.ok(calls.length >= 1, "expected a log line");
  return JSON.parse(calls[calls.length - 1]);
}

test("log line has the shared JSON shape (ts/level/service/event/request_id)", () => {
  const rec = captureLog(() => logEvent("ai-mediator", "answer", { refusal: false }, { requestId: "rid9" }));
  assert.equal(rec.service, "ai-mediator");
  assert.equal(rec.event, "answer");
  assert.equal(rec.request_id, "rid9");
  assert.equal(rec.level, "info");
  assert.equal(rec.refusal, false);
  assert.ok(rec.ts);
});

test("raw question text never reaches the log", () => {
  const rec = captureLog(() =>
    logEvent("ai-mediator", "answer", { question: "Robert Smith warfarin dose", question_sha: "abc123" }));
  assert.equal(rec.question, "<redacted len=26>");
  assert.equal(rec.question_sha, "abc123");
  assert.ok(!JSON.stringify(rec).includes("Robert Smith"));
});

test("redaction is case-insensitive and covers context/note/payload", () => {
  const rec = captureLog(() =>
    logEvent("ai-mediator", "x", { ContextText: "private note", note: "hi", Payload: "data" }));
  assert.equal(rec.ContextText, "<redacted len=12>");
  assert.equal(rec.note, "<redacted len=2>");
  assert.equal(rec.Payload, "<redacted len=4>");
});

test("error level is honoured", () => {
  const rec = captureLog(() =>
    logEvent("ai-mediator", "boom", {}, { level: "error" }));
  assert.equal(rec.level, "error");
});

test("newRequestId: 16 hex chars, unique across calls", () => {
  const a = newRequestId();
  const b = newRequestId();
  assert.match(a, /^[0-9a-f]{16}$/);
  assert.notEqual(a, b);
});

test("questionHash: 12 hex chars, deterministic, different per input", () => {
  const h1 = questionHash("same");
  assert.match(h1, /^[0-9a-f]{12}$/);
  assert.equal(h1, questionHash("same"));
  assert.notEqual(h1, questionHash("other"));
});
