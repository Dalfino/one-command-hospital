import React, { useEffect, useState } from "react";
import fhir from "fhirclient";

const MEDIATOR = import.meta.env.VITE_MEDIATOR_URL || "http://localhost:8103";

export default function App() {
  const [ctx, setCtx] = useState(null); // {patientId, patientName}
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    fhir.oauth2
      .ready()
      .then(async (client) => {
        let patientName = "patient context";
        try {
          const p = await client.patient.read();
          patientName =
            [p.name?.[0]?.given?.join(" "), p.name?.[0]?.family].filter(Boolean).join(" ") ||
            `Patient/${p.id}`;
        } catch {
          /* context without patient read scope — keep generic label */
        }
        setCtx({ patientId: client.patient.id ?? null, patientName });
      })
      .catch(() => setCtx({ patientId: null, patientName: "no SMART context (standalone mode)" }));
  }, []);

  async function ask(e) {
    e.preventDefault();
    if (!question.trim()) return;
    setBusy(true);
    setErr(null);
    setResult(null);
    try {
      const r = await fetch(`${MEDIATOR}/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          patientId: ctx?.patientId,
          userId: "clinician",
        }),
      });
      if (!r.ok) throw new Error(`mediator ${r.status}`);
      setResult(await r.json());
    } catch (e2) {
      setErr(String(e2.message || e2));
    } finally {
      setBusy(false);
    }
  }

  async function signOff(action) {
    if (!result?.communication?.id) return;
    setBusy(true);
    try {
      await fetch(`${MEDIATOR}/signoff`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          communicationId: result.communication.id,
          action, // "signed_off" | "escalated"
          by: ctx?.patientName || "clinician",
        }),
      });
      setResult({ ...result, signed: action });
    } finally {
      setBusy(false);
    }
  }

  const ans = result?.communication?.payload?.[0]?.contentString
    ? JSON.parse(result.communication.payload[0].contentString)
    : null;

  return (
    <div className="wrap">
      <header className="head">
        <span className="pulse" aria-hidden="true" />
        <div>
          <h1>Guideline Copilot</h1>
          <p className="ctx">{ctx ? ctx.patientName : "connecting to EHR…"}</p>
        </div>
      </header>

      <form onSubmit={ask} className="ask">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about a hospital protocol… e.g. 'Does a mechanical mitral valve need bridging?'"
          aria-label="Protocol question"
        />
        <button disabled={busy || !question.trim()} type="submit">
          {busy ? "…" : "Ask"}
        </button>
      </form>

      {err && <div className="banner err">pipeline error: {err}</div>}

      {ans && (
        <section className={`card ${ans.refusal ? "refusal" : ""}`}>
          {ans.refusal ? (
            <>
              <div className="banner warn">NOT COVERED — no guideline section supports this</div>
              <p className="muted">{ans.refusal_reason || "Ask the library or escalate to a senior."}</p>
            </>
          ) : (
            <>
              <pre className="answer">{ans.answer}</pre>
              <div className="chips">
                {ans.citations?.map((c) => (
                  <span key={c.corpus_id + c.section} className="chip" title={c.title}>
                    {c.corpus_id} §{c.section} · {c.edition}
                  </span>
                ))}
                <span className={`chip ${ans.grounding ? "ok" : "warn"}`}>
                  {ans.grounding ? "grounded" : "needs review"}
                </span>
              </div>
            </>
          )}
          <footer className="foot">
            <span className="muted">
              advisory only · model {ans.model} · {ans.latency_ms} ms
            </span>
            {!result.signed && !ans.refusal && (
              <span className="actions">
                <button className="ghost" disabled={busy} onClick={() => signOff("escalated")}>
                  Escalate
                </button>
                <button disabled={busy} onClick={() => signOff("signed_off")}>
                  Sign
                </button>
              </span>
            )}
            {result.signed && <b className="chip ok">{result.signed.replace("_", " ")}</b>}
          </footer>
        </section>
      )}

      <p className="disclaimer">
        Answers come only from the hospital's own guidelines, with citations and editions.
        This assistant never diagnoses and never prescribes.
      </p>
    </div>
  );
}
