/**
 * Unit tier — M22 review queue: enqueue → list → resolve → feedback ledger,
 * with persistence across "restarts" (fresh store instance, same dir).
 * Runs against a temp AUDIT_DIR so the real audit ledger is never touched.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, existsSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const dir = mkdtempSync(path.join(tmpdir(), "och-review-"));
process.env.AUDIT_DIR = dir;

// Import AFTER env so the store binds the temp dir.
const review = await import("../../services/ai-mediator/review.js");

test("enqueue is idempotent and persists", () => {
  const a = review.enqueue({ qid: 1, audit_seq: 1, communication_id: "comm-1",
                             question_sha: "abc", reason: "no citations" });
  assert.equal(a.qid, 1);
  assert.equal(review.enqueue({ qid: 1 }), null); // duplicate ignored
  assert.ok(existsSync(path.join(dir, "review_queue.jsonl")));
});

test("listOpen + counts reflect state", () => {
  review.enqueue({ qid: 2, audit_seq: 2, reason: "verifier unreachable" });
  assert.equal(review.listOpen().length, 2);
  assert.deepEqual(review.counts(), { open: 2, resolved: 0, total: 2 });
});

test("resolve writes feedback for substantive decisions only", () => {
  const r1 = review.resolve({ qid: 1, decision: "inaccurate",
                              correction: "Correct section is [ANTICOAG-BRIDGE §3]", by: "dr-1" });
  assert.equal(r1.item.status, "resolved");
  assert.ok(r1.feedback && r1.feedback.correction.includes("ANTICOAG-BRIDGE"));

  const r2 = review.resolve({ qid: 2, decision: "not_needed" });
  assert.equal(r2.feedback, null); // not_needed: queue-only, no feedback row

  assert.equal(review.resolve({ qid: 99, decision: "inaccurate" }), null); // unknown
  assert.equal(review.counts().open, 0);

  const fb = readFileSync(path.join(dir, "feedback.jsonl"), "utf8").trim().split("\n");
  assert.equal(fb.length, 1); // exactly one feedback record
  assert.deepEqual(JSON.parse(fb[0]).decision, "inaccurate");
});

test("decision validation", () => {
  assert.ok(review.isDecision("accurate_enough"));
  assert.ok(!review.isDecision("sure_whatever"));
});

test("persistence across restart (fresh module instance, same dir)", async () => {
  // Node treats a query-string specifier as a distinct module → simulates a
  // process restart against the same AUDIT_DIR.
  const revived = await import("../../services/ai-mediator/review.js?restart=1");
  // First restart read: qid1 resolved, qid2 resolved (append-log compaction,
  // last record per qid wins — a resolved item never resurrects as open).
  assert.deepEqual(revived.counts(), { open: 0, resolved: 2, total: 2 });
  // A new arrival after restart goes to the worklist normally.
  revived.enqueue({ qid: 3, audit_seq: 3, reason: "post-restart item" });
  assert.deepEqual(revived.counts(), { open: 1, resolved: 2, total: 3 });
  assert.equal(revived.listOpen()[0].qid, 3);
});
