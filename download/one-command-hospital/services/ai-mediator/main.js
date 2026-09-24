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
import {
  REQUESTS, DURATION, REFUSALS, UNGROUNDED,
  SIGNOFFS, AUDIT_EVENTS, AUDIT_VERIFY_FAILURES, AUDIT_RECORDS, renderMetrics,
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

app.use(securityHeaders);
app.use(rateLimit);

async function postJson(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
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
    const deidQ = await postJson(DEID_URL, { text: question });
    const scrubbedQuestion = deidQ.anonymized;

    // 2. De-ID any note context BEFORE it may reach the LLM path.
    let scrubbedContext = "";
    let deidMeta = { question_findings: deidQ.finding_count };
    if (contextText) {
      const deid = await postJson(DEID_URL, { text: contextText });
      scrubbedContext = deid.anonymized;
      deidMeta.context_findings = deid.finding_count;
    }

    // 3. Ask the guideline RAG service (citations forced inside).
    const rag = await postJson(RAG_URL, { question: scrubbedQuestion });
    if (rag.refusal) REFUSALS.inc({ route: "/process", reason: rag.refusal_reason || "unspecified" });

    // 4. Verify grounding (Phase 1: medspaCy ConText replaces heuristics).
    let verification = { grounded: true, notes: ["verifier skipped (refusal path)"] };
    if (!rag.refusal && rag.citations?.length) {
      try {
        verification = await postJson(VERIFY_URL, {
          answer: rag.answer,
          sources: rag.citations.map((c) => ({
            corpus_id: c.corpus_id,
            section: c.section,
            text: c.title,
          })),
        });
        if (!verification.grounded) UNGROUNDED.inc({ route: "/process" });
      } catch {
        // verifier down → mark for review, never silently pass
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
        method: "POST",
        headers: await fhirHeaders(),
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

    res.json({ communication, fhir, audit_seq: record.seq, total_latency_ms: Date.now() - started });
  } catch (e) {
    audit(userId, "answer_error", { error: String(e.message) });
    AUDIT_EVENTS.inc({ route: "/process", action: "answer_error" });
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
    const g = await fetch(getUrl, { headers: await fhirHeaders({ Accept: "application/fhir+json" }) });
    if (!g.ok) return res.status(404).json({ error: `Communication ${communicationId} not found` });
    const resource = await g.json();

    const payload = JSON.parse(resource.payload?.[0]?.contentString || "{}");
    payload.human_action = action;
    payload.actioned_by = by;
    payload.actioned_at = new Date().toISOString();
    resource.payload[0].contentString = JSON.stringify(payload, null, 2);

    const p = await fetch(getUrl, {
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

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`ai-mediator on :${port} (auth: ${authMode()})`));
