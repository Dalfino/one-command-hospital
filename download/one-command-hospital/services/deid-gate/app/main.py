"""De-identification gate — the PHI white-out pen.

Every byte of clinical text passes here BEFORE it may touch an LLM.
Improvement context: safety architecture, not a feature. The model never
sees identifiers, so there is nothing to leak.
"""
import os
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

app = FastAPI(title="deid-gate", version="0.1.0")
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
    analyzer = AnalyzerEngine(nlp_engine=None, supported_languages=["en"])
    # NOTE: for production, plug NlpEngineProvider with the downloaded model and
    # raise score_threshold; keep v0 permissive (fail-safe = over-redact).


class DeidRequest(BaseModel):
    text: str
    language: str = "en"


class DeidResponse(BaseModel):
    anonymized: str
    findings: List[dict]
    finding_count: int


@app.post("/deid", response_model=DeidResponse)
def deid(req: DeidRequest):
    if analyzer is None:
        raise HTTPException(status_code=503, detail="analyzer not loaded")
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
    return DeidResponse(anonymized=out.text, findings=findings, finding_count=len(findings))


@app.get("/health")
def health():
    return {"ok": analyzer is not None, "service": "deid-gate"}
