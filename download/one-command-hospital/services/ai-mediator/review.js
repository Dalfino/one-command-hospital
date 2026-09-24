/**
 * review.js — clinician review queue + feedback ledger (M22, zero dependencies).
 *
 * Every answer the verifier flags `grounded:false` (pending_review) lands in
 * a durable worklist instead of vanishing into the audit log. Clinicians
 * resolve items with a decision and an optional correction; corrections are
 * kept in feedback.jsonl so the steward can promote them into the eval set
 * (tools/feedback_to_eval.py) — the human-feedback loop made real.
 *
 * Storage: same AUDIT_DIR as audit.js. review_queue.jsonl is the queue
 * (status open|resolved), feedback.jsonl is append-only evidence. Neither
 * carries raw narratives: items hold question_sha + audit_seq references
 * only; corrections are written verbatim because the offline eval-seeding
 * tool needs the text — treat feedback.jsonl as PHI-classified (header note).
 */
import { appendFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import path from "node:path";

const AUDIT_DIR = process.env.AUDIT_DIR || "/app/audit";
const QUEUE_FILE = path.join(AUDIT_DIR, "review_queue.jsonl");
const FEEDBACK_FILE = path.join(AUDIT_DIR, "feedback.jsonl");

const DECISIONS = ["accurate_enough", "inaccurate", "unsafe", "not_needed"];

let items = [];          // in-memory mirror; index by qid
let loaded = false;

function init() {
  if (loaded) return;
  mkdirSync(AUDIT_DIR, { recursive: true });
  items = [];
  if (existsSync(QUEUE_FILE)) {
    const byQid = new Map();
    for (const line of readFileSync(QUEUE_FILE, "utf8").split("\n").filter(Boolean)) {
      try {
        const rec = JSON.parse(line);
        // The file is an append-log: enqueue AND resolve both append. Last
        // record per qid wins — a resolved item must not resurrect as open.
        byQid.set(rec.qid, rec);
      } catch { /* torn line: queue is advisory */ }
    }
    items = [...byQid.values()];
  }
  loaded = true;
}

export function enqueue({ qid, audit_seq, communication_id, question_sha, reason }) {
  init();
  if (!qid || items.some((i) => i.qid === qid)) return null; // idempotent
  const item = {
    qid,
    audit_seq: audit_seq ?? null,
    communication_id: communication_id ?? null,
    question_sha: question_sha ?? null,
    reason: reason ?? "ungrounded answer",
    status: "open",
    created_at: new Date().toISOString(),
    resolved_at: null,
    resolution: null,
  };
  items.push(item);
  appendFileSync(QUEUE_FILE, JSON.stringify(item) + "\n");
  return item;
}

export function listOpen() {
  init();
  return items.filter((i) => i.status === "open");
}

export function counts() {
  init();
  return {
    open: items.filter((i) => i.status === "open").length,
    resolved: items.filter((i) => i.status === "resolved").length,
    total: items.length,
  };
}

export function isDecision(d) {
  return DECISIONS.includes(d);
}

/** Resolve an item; append a feedback record when a decision is substantive
 * (not_needed is tracked in the queue only). Returns {item, feedback}. */
export function resolve({ qid, decision, correction = "", by = "clinician" }) {
  init();
  const item = items.find((i) => i.qid === qid && i.status === "open");
  if (!item) return null;
  item.status = "resolved";
  item.resolved_at = new Date().toISOString();
  item.resolution = { decision, by };
  appendFileSync(QUEUE_FILE, JSON.stringify(item) + "\n");

  let feedback = null;
  if (decision !== "not_needed") {
    feedback = {
      ts: item.resolved_at,
      qid,
      decision,
      by,
      correction: String(correction || ""),
      // NOTE: correction may quote clinical text — feedback.jsonl is
      // PHI-classified and lives with the audit ledger (same volume, off-box
      // shipping applies). Keep it out of any public artifact.
    };
    appendFileSync(FEEDBACK_FILE, JSON.stringify(feedback) + "\n");
  }
  return { item, feedback };
}

export function feedbackPath() {
  return FEEDBACK_FILE;
}
