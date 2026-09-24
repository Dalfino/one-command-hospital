/**
 * Node tier — audit.js hash-chain contract.
 *
 * The tamper-evident audit trail is the governance backbone (M8). These tests
 * pin the properties it MUST have: genesis chaining, ordered sequences,
 * tamper detection with the first bad seq, torn-line detection, middle-record
 * deletion, and honest reporting on an empty ledger. Zero deps — node:test.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, appendFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

// audit.js reads AUDIT_DIR at import time — set it BEFORE the dynamic import.
const dir = mkdtempSync(path.join(tmpdir(), "och-audit-test-"));
process.env.AUDIT_DIR = dir;

const auditUrl = new URL("../../services/ai-mediator/audit.js", import.meta.url);
const { audit, verifyChain, auditPath } = await import(fileURLToPath(auditUrl));

const GENESIS = "0".repeat(64);
const file = () => auditPath();
let pristine = "";

test("empty ledger verifies honestly as ok with zero records", () => {
  const r = verifyChain();
  assert.equal(r.ok, true);
  assert.equal(r.records, 0);
  assert.equal(r.first_bad_seq, null);
});

test("appended records chain: genesis prev_hash, ordered seqs, ok verify", () => {
  const r1 = audit("clinician-1", "answer", { communication_id: "c1" });
  const r2 = audit("clinician-2", "signed_off", { communication_id: "c1" });
  const r3 = audit("clinician-1", "answer", { communication_id: "c2" });

  assert.equal(r1.seq, 1);
  assert.equal(r1.prev_hash, GENESIS);
  assert.equal(r2.seq, 2);
  assert.equal(r2.prev_hash, r1.hash, "each record commits to its predecessor");
  assert.equal(r3.seq, 3);

  const v = verifyChain();
  assert.equal(v.ok, true);
  assert.equal(v.records, 3);

  pristine = readFileSync(file(), "utf8");   // snapshot the clean 3-record ledger
});

const restore = () => writeFileSync(file(), pristine);

test("editing a past record breaks the chain at that seq", () => {
  restore();
  const lines = readFileSync(file(), "utf8").split("\n").filter(Boolean);
  const rec = JSON.parse(lines[1]);                 // seq 2
  rec.detail.communication_id = "TAMPERED";         // silent rewrite
  lines[1] = JSON.stringify(rec);
  writeFileSync(file(), lines.join("\n") + "\n");

  const v = verifyChain();
  assert.equal(v.ok, false);
  assert.equal(v.first_bad_seq, 2, "must report the FIRST bad sequence");
});

test("torn/corrupt line is flagged, not swallowed", () => {
  restore();
  appendFileSync(file(), "{corrupt\n");
  const v = verifyChain();
  assert.equal(v.ok, false);
  assert.equal(v.reason, "unparseable line");
});

test("deletion of a middle record is caught", () => {
  restore();
  const lines = readFileSync(file(), "utf8").split("\n").filter(Boolean);
  assert.equal(lines.length, 3);
  writeFileSync(file(), [lines[0], lines[2]].join("\n") + "\n");  // drop seq 2
  const v = verifyChain();
  assert.equal(v.ok, false, "a gap in the chain must fail verification");
});

test("restored ledger verifies again (chain survives clean reads)", () => {
  restore();
  const v = verifyChain();
  assert.equal(v.ok, true);
  assert.equal(v.records, 3);
});

test("auditPath points at audit.jsonl inside AUDIT_DIR", () => {
  assert.ok(auditPath().endsWith(path.join("audit.jsonl")));
  assert.ok(auditPath().startsWith(dir));
});

test.after(() => {
  rmSync(dir, { recursive: true, force: true });
});
