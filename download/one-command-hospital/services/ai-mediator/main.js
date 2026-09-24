/**
 * AI Mediator — the reusable plug between a hospital and any AI.
 *
 * Improvement #4: ONE contract every future model can ride on:
 *   clinical event / question → deid-gate → AI service → verifier
 *   → FHIR resource writeback (with provenance) → surfaced in the EHR.
 *
 * v0.2: Medplum Bot JWT auth (client_credentials + JWT assertion) and the
 * /signoff endpoint that closes the human_action audit loop.
 * v0.3 hardening:
 *   - the QUESTION itself is de-identified too (was: only note context — a
 *     clinician typing "Mr Smith's warfarin plan" would have leaked a name);
 *   - tamper-evident hash-chained audit trail (audit.js) + /audit/verify;
 *   - per-IP rate limiting, body-size cap, security headers, /metrics;
 *   - refusals and ungrounded answers exposed for alerting.
 */
import express from "express";
import { randomUUID } from "node:crypto";
import { authMode, fhirHeaders } from "./medplum-auth.js";
import { audit, verifyChain, auditPath } from "./audit.js";
import { enqueue as reviewEnqueue, listOpen as reviewListOpen, counts as reviewCounts,
         resolve as reviewResolve, isDecision, feedbackPath } from "./review.js";
import { logEvent, newRequestId, questionHash } from "./logging.js";
import {
  REQUESTS, DURATION, REFUSALS, UNGROUNDED,
  SIGNOFFS, AUDIT_EVENTS, AUDIT_VERIFY_FAILURES, AUDIT_RECORDS,
  REVIEW_OPEN, REVIEW_RESOLVED, renderMetrics,
} from "./metrics.js";

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "1mb" }));

const DEID_URL = process.env.DEID_URL || "http://deid-gate:8000/deid";
const RAG_URL = process.env.RAG_URL || "http://guideline-rag:8000/answer";
const VERIFY_URL = process.env.VERIFY_URL || "http://verifier:8000/verify";
const MEDPLUM_FHIR_URL = process.env.MEDPLUM_FHIR_URL || "http://medplum:8080/fhir";

// ── rate limiting: per-IP token bucket (RATE_LIMIT_RPS / RATE_LIMIT_BURST) ──
const RATE_RPS = parseFloat(process.env.RATE_LIMIT_RPS || "10");
const RATE_BURST = parseFloat(process.env.RATE_LIMIT_BURST || "20");
// A HUNG upstream is worse than a dead one: without a deadline, a stalled
// verifier/deid/RAG hangs the clinician's request forever. Fail closed within
// UPSTREAM_TIMEOUT_MS instead (regression-tested by the fail-closed tier).
const UPSTREAM_TIMEOUT_MS = parseInt(process.env.UPSTREAM_TIMEOUT_MS || "10000", 10);
const buckets = new Map();

function rateLimit(req, res, next) {
  const key = req.ip || "anon";
  const now = Date.now() / 1000;
  const [tokens, last] = buckets.get(key) || [RATE_BURST, now];
  const nextTokens = Math.min(RATE_BURST, tokens + (now - last) * RATE_RPS);
  if (nextTokens < 1) {
    buckets.set(key, [nextTokens, now]);
    REQUESTS.inc({ route: req.path, code: "429" });
    return res.status(429).json({ error: "rate limit exceeded" });
  }
  buckets.set(key, [nextTokens - 1, now]);
  next();
}

function securityHeaders(_req, res, next) {
  res.set({
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
  });
  next();
}

function metricsTrail(route) {
  const start = process.hrtime.bigint();
  return (req, res) => {
    const ms = Number(process.hrtime.bigint() - start) / 1e6;
    REQUESTS.inc({ route, code: String(res.statusCode) });
    DURATION.observe({ route }, ms);
  };
}

/** Trace middleware: one X-Request-ID per clinical question. The mediator
 *  mints the ROOT id and every downstream hop (deid, rag, verifier, FHIR)
 *  receives it as a header — one request, one greppable trace across services. */
app.use((req, res, next) => {
  req.id = req.headers["x-request-id"] || newRequestId();
  res.setHeader("X-Request-ID", req.id);
  next();
});

app.use(securityHeaders);
app.use(rateLimit);

async function postJson(url, body, requestId = null) {
  const r = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(requestId ? { "X-Request-ID": requestId } : {}),
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
  });
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}

app.get("/health", (_req, res) =>
  res.json({ ok: true, service: "ai-mediator", auth: authMode() })
);

app.get("/metrics", (_req, res) => {
  res.type("text/plain; version=0.0.4; charset=utf-8").send(renderMetrics());
});

/** GET /audit/verify — walk the hash chain; alerts fire on ok:false. */
app.get("/audit/verify", async (_req, res) => {
  const result = verifyChain();
  AUDIT_RECORDS.set({ route: "/audit/verify" }, result.records);
  if (!result.ok) AUDIT_VERIFY_FAILURES.inc({ route: "/audit/verify" });
  res.json({ ...result, file: auditPath() });
});

app.post("/process", async (req, res) => {
  const trail = metricsTrail("/process");
  res.on("finish", () => trail(req, res));
  const started = Date.now();
  const { question, contextText = "", patientId = null, userId = "unknown" } = req.body || {};
  if (!question) return res.status(400).json({ error: "question required" });

  try {
    // 1. De-ID the QUESTION itself — a typed narrative can carry identifiers.
    const deidQ = await postJson(DEID_URL, { text: question }, req.id);
    const scrubbedQuestion = deidQ.anonymized;

    // 2. De-ID any note context BEFORE it may reach the LLM path.
    let scrubbedContext = "";
    let deidMeta = { question_findings: deidQ.finding_count };
    if (contextText) {
      const deid = await postJson(DEID_URL, { text: contextText }, req.id);
      scrubbedContext = deid.anonymized;
      deidMeta.context_findings = deid.finding_count;
    }

    // 3. Ask the guideline RAG service (citations forced inside).
    const rag = await postJson(RAG_URL, { question: scrubbedQuestion }, req.id);
    if (rag.refusal) REFUSALS.inc({ route: "/process", reason: rag.refusal_reason || "unspecified" });

    // 4. Verify grounding (Phase 1: medspaCy ConText replaces heuristics).
    let verification;
    if (rag.refusal) {
      verification = { grounded: true, notes: ["verifier skipped (refusal)"] };
    } else if (!(rag.citations || []).length) {
      // HARD RULE (regression-guarded by tests/integration): an answer with
      // zero citations is ungrounded by definition. It must be flagged for
      // human review — never passed to the EHR as if it were verified.
      verification = { grounded: false, notes: ["answer carried no citations — flagged for review"] };
      UNGROUNDED.inc({ route: "/process", note: "no citations" });
    } else {
      try {
        verification = await postJson(VERIFY_URL, {
          answer: rag.answer,
          sources: rag.citations.map((c) => ({
            corpus_id: c.corpus_id,
            section: c.section,
            text: c.text || c.title,  // quoted section text grounds the answer; title is the last resort
          })),
        }, req.id);
        if (!verification.grounded) UNGROUNDED.inc({ route: "/process" });
      } catch {
        // verifier down → fail CLOSED: flag for review, never silently pass
        verification = { grounded: false, notes: ["verifier unreachable"] };
        UNGROUNDED.inc({ route: "/process", note: "verifier unreachable" });
      }
    }

    // 5. Write back as a FHIR Communication with full provenance.
    const communication = {
      resourceType: "Communication",
      id: randomUUID(),
      status: "completed",
      category: [
        {
          coding: [
            { system: "http://one-command-hospital.local/ai", code: "guideline-answer" },
          ],
        },
      ],
      subject: patientId ? { reference: `Patient/${patientId}` } : undefined,
      sender: { display: "Guideline Copilot (advisory)" },
      sent: new Date().toISOString(),
      payload: [
        {
          contentString: JSON.stringify(
            {
              question: scrubbedQuestion, // scrubbed — raw question never persisted
              scrubbed_context: scrubbedContext || undefined,
              deid: deidMeta,
              answer: rag.answer,
              refusal: rag.refusal,
              citations: rag.citations, // corpus id + edition + section
              grounding: verification.grounded,
              verifier_notes: verification.notes,
              model: rag.model,
              latency_ms: rag.latency_ms,
              auth_mode: authMode(),
              human_action: "pending_review", // closed by clinician sign-off
              requested_by: userId,
            },
            null,
            2
          ),
        },
      ],
    };

    let fhir = { written: false };
    try {
      const r = await fetch(`${MEDPLUM_FHIR_URL}/Communication`, {
        signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
        method: "POST",
        headers: {
          ...(await fhirHeaders()),
          "X-Request-ID": req.id,
        },
        body: JSON.stringify(communication),
      });
      if (authMode() === "unauthenticated-v0") fhir.warning = "sandbox: unauthenticated writeback";
      fhir = { ...fhir, written: r.ok, status: r.status };
    } catch {
      /* Medplum down → still return the answer to the clinician */
    }

    // 6. Audit AFTER the outcome is known; detail carries no raw narrative.
    const record = audit(userId, "answer", {
      communication_id: communication.id,
      patient_ref: patientId ? `Patient/${patientId}` : null,
      refusal: rag.refusal,
      grounded: verification.grounded,
      citations: (rag.citations || []).map((c) => `${c.corpus_id}§${c.section}@${c.edition}`),
      deid_findings: deidMeta,
      fhir_written: fhir.written,
      total_latency_ms: Date.now() - started,
    });
    AUDIT_EVENTS.inc({ route: "/process", action: "answer" });

    // 6b. Ungrounded answers land in the clinician review queue (M22) —
    // "pending_review" becomes a worklist item, not just a JSON flag.
    if (!verification.grounded) {
      const item = reviewEnqueue({
        qid: record.seq,               // audit seq doubles as the queue id
        audit_seq: record.seq,
        communication_id: communication.id,
        question_sha: questionHash(scrubbedQuestion),
        reason: (verification.notes || []).join("; ") || "ungrounded answer",
      });
      if (item) REVIEW_OPEN.set({ route: "review" }, reviewCounts().open);
    }

    logEvent("ai-mediator", "answer", {
      question_sha: questionHash(scrubbedQuestion),
      question_chars: question.length,
      refusal: rag.refusal,
      grounded: verification.grounded,
      citations: (rag.citations || []).length,
      fhir_written: fhir.written,
      audit_seq: record.seq,
      total_latency_ms: Date.now() - started,
    }, { requestId: req.id });

    res.json({ communication, fhir, audit_seq: record.seq, total_latency_ms: Date.now() - started });
  } catch (e) {
    audit(userId, "answer_error", { error: String(e.message) });
    AUDIT_EVENTS.inc({ route: "/process", action: "answer_error" });
    logEvent("ai-mediator", "answer_error", { error: String(e.message) },
             { level: "error", requestId: req.id });
    res.status(502).json({ error: String(e.message), stage: "pipeline" });
  }
});

/**
 * POST /signoff — closes the audit loop.
 * Body: { communicationId, action: "signed_off"|"escalated", by }
 * Reads the Communication from Medplum, updates human_action, writes it back.
 */
app.post("/signoff", async (req, res) => {
  const trail = metricsTrail("/signoff");
  res.on("finish", () => trail(req, res));
  const { communicationId, action, by = "clinician" } = req.body || {};
  if (!communicationId || !["signed_off", "escalated"].includes(action)) {
    return res.status(400).json({ error: "communicationId and valid action required" });
  }
  try {
    const getUrl = `${MEDPLUM_FHIR_URL}/Communication/${communicationId}`;
    const g = await fetch(getUrl, { headers: await fhirHeaders({ Accept: "application/fhir+json" }), signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS) });
    if (!g.ok) return res.status(404).json({ error: `Communication ${communicationId} not found` });
    const resource = await g.json();

    const payload = JSON.parse(resource.payload?.[0]?.contentString || "{}");
    payload.human_action = action;
    payload.actioned_by = by;
    payload.actioned_at = new Date().toISOString();
    resource.payload[0].contentString = JSON.stringify(payload, null, 2);

    const p = await fetch(getUrl, {
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
      method: "PUT",
      headers: await fhirHeaders(),
      body: JSON.stringify(resource),
    });

    audit(by, action, { communication_id: communicationId, fhir_status: p.status });
    SIGNOFFS.inc({ route: "/signoff", action });
    AUDIT_EVENTS.inc({ route: "/signoff", action });
    res.json({ ok: p.ok, status: p.status, human_action: action });
  } catch (e) {
    audit(by, "signoff_error", { communication_id: communicationId, error: String(e.message) });
    res.status(502).json({ error: String(e.message) });
  }
});

/** GET /review/queue — the open clinician-review worklist (M22). */
app.get("/review/queue", (_req, res) => {
  res.json({ open: reviewListOpen(), counts: reviewCounts(), feedback_file: feedbackPath() });
});

/** POST /review/queue/resolve — clinician verdict + optional correction.
 * Body: {qid, decision: accurate_enough|inaccurate|unsafe|not_needed, correction?, by?} */
app.post("/review/queue/resolve", (req, res) => {
  const { qid, decision, correction, by = "clinician" } = req.body || {};
  if (!qid || !isDecision(decision)) {
    return res.status(400).json({ error: "qid and valid decision required",
                                  decisions: ["accurate_enough", "inaccurate", "unsafe", "not_needed"] });
  }
  const result = reviewResolve({ qid, decision, correction, by });
  if (!result) return res.status(404).json({ error: `open item ${qid} not found` });
  audit(by, "review_resolution", { qid, decision, correction_chars: String(correction || "").length });
  REVIEW_RESOLVED.inc({ route: "/review/queue/resolve", decision });
  REVIEW_OPEN.set({ route: "review" }, reviewCounts().open);
  res.json({ ok: true, qid, decision, feedback_recorded: decision !== "not_needed" });
});

/** GET /review — minimal zero-dependency worklist UI (sandbox-grade).
 * Production swaps this for the portal app behind SSO (see STATE.md blockers). */
app.get("/review", (_req, res) => {
  res.set("Content-Security-Policy",
          "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'");
  res.type("html").send(`<!doctype html><html><head><meta charset="utf-8">
<title>Guideline Copilot — Review Queue</title>
<style>body{font-family:system-ui;margin:2rem;max-width:56rem}h1{font-size:1.3rem}
.item{border:1px solid #ddd;border-radius:8px;padding:1rem;margin:.8rem 0}
.meta{color:#666;font-size:.85rem}textarea{width:100%;min-height:3rem;margin:.4rem 0}
button{margin-right:.4rem;padding:.3rem .7rem;cursor:pointer}
.ok{color:#0a7d33}.bad{color:#b3261e}</style></head><body>
<h1>Review queue — answers flagged for human verification</h1>
<div id="q">loading…</div>
<script>
const DECISIONS=["accurate_enough","inaccurate","unsafe","not_needed"];
function esc(s){const d=document.createElement("div");d.textContent=String(s==null?"":s);return d.innerHTML;}
async function load(){
  const r=await fetch('/review/queue');const d=await r.json();
  const el=document.getElementById('q');
  if(d.open.length===0){el.innerHTML='<p class="ok">Queue empty — nothing awaiting review.</p>';return;}
  el.innerHTML=d.open.map(function(i){
    return '<div class="item"><b>#'+esc(i.qid)+'</b> <span class="meta">'+esc(i.reason)+'</span>'
      +'<div class="meta">audit_seq='+esc(i.audit_seq)+' sha='+esc(i.question_sha)+' at '+esc(i.created_at)+'</div>'
      +'<textarea id="c'+esc(i.qid)+'" placeholder="correction (optional; becomes eval-set candidate)"></textarea><br>'
      +DECISIONS.map(function(dec){return '<button onclick="resolve('+esc(i.qid)+',\\''+dec+'\\')">'+dec+'</button>';}).join("")
      +'</div>';
  }).join("");
}
async function resolve(qid,decision){
  const ta=document.getElementById('c'+qid);
  const correction=ta?ta.value:"";
  const r=await fetch('/review/queue/resolve',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({qid:qid,decision:decision,correction:correction,by:'sandbox-clinician'})});
  if(r.ok){load();}else{alert('resolve failed: '+(await r.text()));}
}
load();setInterval(load,15000);
</script></body></html>`);
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`ai-mediator on :${port} (auth: ${authMode()})`));
