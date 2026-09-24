/**
 * audit.js — tamper-evident append-only audit trail (zero dependencies).
 *
 * Improvement #4's governance backbone: every AI-mediated clinical event and
 * every human sign-off is appended as a hash-chained JSONL record. Each record
 * commits to its predecessor's hash, so any silent edit or deletion breaks the
 * chain and /audit/verify reports the first bad sequence number.
 *
 * Storage: AUDIT_DIR (default /app/audit) — mount a durable volume; ship
 * off-box. This file is the system of record for "who asked what, what did we
 * answer, what did the clinician do about it".
 */
import { createHash } from "node:crypto";
import { appendFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import path from "node:path";

const AUDIT_DIR = process.env.AUDIT_DIR || "/app/audit";
const AUDIT_FILE = path.join(AUDIT_DIR, "audit.jsonl");
const GENESIS = "0".repeat(64);

let seq = 0;
let lastHash = GENESIS;
let initialized = false;

function sha256(s) {
  return createHash("sha256").update(s).digest("hex");
}

function init() {
  if (initialized) return;
  mkdirSync(AUDIT_DIR, { recursive: true });
  if (existsSync(AUDIT_FILE)) {
    const lines = readFileSync(AUDIT_FILE, "utf8").split("\n").filter(Boolean);
    for (const line of lines) {
      try {
        const rec = JSON.parse(line);
        if (typeof rec.seq === "number" && rec.seq > seq) {
          seq = rec.seq;
          lastHash = rec.hash || lastHash;
        }
      } catch {
        /* a torn final line after a crash: verify() will flag it */
      }
    }
  }
  initialized = true;
}

/**
 * Append one event. Returns the full record including its hash.
 * `detail` must already be free of raw identifiers (the mediator routes
 * questions through deid-gate first; sign-offs carry ids, not narratives).
 */
export function audit(actor, action, detail = {}) {
  init();
  const record = {
    seq: seq + 1,
    ts: new Date().toISOString(),
    actor,
    action,
    detail,
    prev_hash: lastHash,
  };
  const canonical = JSON.stringify({
    seq: record.seq, ts: record.ts, actor: record.actor,
    action: record.action, detail: record.detail, prev_hash: record.prev_hash,
  });
  record.hash = sha256(canonical);
  appendFileSync(AUDIT_FILE, JSON.stringify(record) + "\n");
  seq = record.seq;
  lastHash = record.hash;
  return record;
}

/**
 * Walk the whole chain and confirm every record commits to its predecessor.
 * Returns { ok, records, first_bad_seq } — ok:false means tampering or a torn
 * write; the governance runbook treats that as a SEV-2 incident.
 */
export function verifyChain() {
  init();
  if (!existsSync(AUDIT_FILE)) return { ok: true, records: 0, first_bad_seq: null };
  const lines = readFileSync(AUDIT_FILE, "utf8").split("\n").filter(Boolean);
  let expectPrev = GENESIS;
  let expectedSeq = 1;
  for (const [i, line] of lines.entries()) {
    let rec;
    try {
      rec = JSON.parse(line);
    } catch {
      return { ok: false, records: i, first_bad_seq: expectedSeq, reason: "unparseable line" };
    }
    const canonical = JSON.stringify({
      seq: rec.seq, ts: rec.ts, actor: rec.actor,
      action: rec.action, detail: rec.detail, prev_hash: rec.prev_hash,
    });
    if (rec.seq !== expectedSeq || rec.prev_hash !== expectPrev || rec.hash !== sha256(canonical)) {
      return { ok: false, records: i, first_bad_seq: rec.seq, reason: "chain mismatch" };
    }
    expectPrev = rec.hash;
    expectedSeq += 1;
  }
  return { ok: true, records: lines.length, first_bad_seq: null };
}

export function auditPath() {
  return AUDIT_FILE;
}
