"""De-identification gate — the PHI white-out pen (v0.2).

Every byte of clinical text passes here BEFORE it may touch an LLM.
Improvement context: safety architecture, not a feature. The model never
sees identifiers, so there is nothing to leak.

v0.2 hardening: /metrics with entity findings counter, per-IP rate limit,
body-size cap, security headers. Fail-safe posture unchanged: over-redact
rather than under-redact.
"""
import os
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .hardening import Counter, Histogram, install, json_log, request_id_of, text_sha

app = FastAPI(title="deid-gate", version="0.2.0")

FINDINGS = Counter("deid_findings_total", "Entities redacted, by type.")
TEXT_LEN = Histogram("deid_text_len_chars", "Scrubbed text length in chars.",
                     buckets=[100, 500, 1000, 2500, 5000, 10000, 25000, 50000])
install(app, "deid-gate", extra=[FINDINGS, TEXT_LEN])

analyzer: AnalyzerEngine | None = None
anonymizer = AnonymizerEngine()

# Entities that cover HIPAA Safe Harbor-adjacent identifiers Presidio knows.
ENTITY_TYPES = [
    "PERSON", "LOCATION", "PHONE_NUMBER", "EMAIL_ADDRESS", "URL",
    "IP_ADDRESS", "DATE_TIME", "US_SSN", "MEDICAL_LICENSE",
    "US_DRIVER_LICENSE", "CREDIT_CARD", "IBAN_CODE",
]


@app.on_event("startup")
def load():
    global analyzer
    model = os.environ.get("SPACY_MODEL", "en_core_web_sm")
    # Explicit engine: Presidio's built-in default hardcodes en_core_web_lg
    # (400MB) and would silently attempt a model download on every cold boot.
    # SPACY_MODEL (default sm, what the Dockerfile ships) keeps boots offline
    # and fast; set SPACY_MODEL=en_core_web_lg for production recall.
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": model}],
    })
    analyzer = AnalyzerEngine(nlp_engine=provider.create_engine(),
                              supported_languages=["en"])
    # Fail-safe fallbacks for identifiers Presidio's default recognizers miss:
    # 7-digit local US phone formats (clinical callback numbers) and MRN-like
    # digit runs. Over-redact rather than under-redact is the stated posture.
    from presidio_analyzer import Pattern, PatternRecognizer
    analyzer.registry.add_recognizer(PatternRecognizer(
        supported_entity="PHONE_NUMBER", name="us_local_phone_fallback",
        patterns=[Pattern(name="us_local_phone",
                          regex=r"\b\d{3}[-.\s]\d{4}\b", score=0.7)]))
    analyzer.registry.add_recognizer(PatternRecognizer(
        supported_entity="MEDICAL_LICENSE", name="digit_run_id_fallback",
        patterns=[Pattern(name="digit_run_id",
                          regex=r"\b\d{6,}\b", score=0.5)]))


class DeidRequest(BaseModel):
    text: str
    language: str = "en"


class DeidResponse(BaseModel):
    anonymized: str
    findings: List[dict]
    finding_count: int


MAX_TEXT_CHARS = int(os.environ.get("MAX_TEXT_CHARS", "50000"))


@app.post("/deid", response_model=DeidResponse)
def deid(req: DeidRequest):
    if analyzer is None:
        raise HTTPException(status_code=503, detail="analyzer not loaded")
    if len(req.text) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=413,
                            detail=f"text exceeds {MAX_TEXT_CHARS} chars")
    results = analyzer.analyze(
        text=req.text, language=req.language,
        entities=ENTITY_TYPES, score_threshold=0.35,
    )
    operators = {t: OperatorConfig("replace", {"new_text": f"<{t}>"}) for t in ENTITY_TYPES}
    out = anonymizer.anonymize(text=req.text, analyzer_results=results, operators=operators)
    findings = [
        {"entity": r.entity_type, "start": r.start, "end": r.end,
         "score": round(r.score, 3)}
        for r in results
    ]
    FINDINGS.inc({"route": "/deid"}, len(findings))
    TEXT_LEN.observe({"route": "/deid"}, len(req.text))
    # Log the SHA of the input, never the input itself.
    json_log("deid-gate", "deid", request_id=request_id_of(),
             text_sha=text_sha(req.text), findings=len(findings),
             chars=len(req.text))
    return DeidResponse(anonymized=out.text, findings=findings, finding_count=len(findings))


@app.get("/health")
def health():
    return {"ok": analyzer is not None, "service": "deid-gate",
            "max_text_chars": MAX_TEXT_CHARS}
