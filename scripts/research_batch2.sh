#!/bin/bash
# Deep research batch 2: compliance, deployment, integration, risk
mkdir -p /home/z/my-project/research
cd /home/z/my-project/research

z-ai function -n web_search -a '{"query": "HIPAA compliance LLM hospital deployment PHI on-premise business associate agreement", "num": 8}' -o hipaa.json
z-ai function -n web_search -a '{"query": "EU AI Act medical device AI high-risk classification requirements hospitals 2026", "num": 8}' -o euaiact.json
z-ai function -n web_search -a '{"query": "FDA AI-enabled medical device software guidance predetermined change control plan 2025", "num": 8}' -o fda.json
z-ai function -n web_search -a '{"query": "on-premise LLM inference hospital GPU sizing vLLM Ollama A100 L40S deployment architecture", "num": 8}' -o deployment.json
z-ai function -n web_search -a '{"query": "HL7 FHIR SMART on FHIR LLM integration EHR ambient clinical intelligence workflow", "num": 8}' -o fhir.json
z-ai function -n web_search -a '{"query": "LLM hallucination mitigation healthcare clinical safety guardrails retrieval grounded generation", "num": 8}' -o hallucination.json
z-ai function -n web_search -a '{"query": "clinical text de-identification HIPAA safe harbor Philter MIST tools comparison", "num": 8}' -o deid.json
z-ai function -n web_search -a '{"query": "ambient AI scribe hospital ROI documentation burden burnout reduction evidence 2025", "num": 8}' -o roi.json
z-ai function -n web_search -a '{"query": "open source medical LLM vs commercial Epic Nuance DAX comparison hospital procurement", "num": 8}' -o commercial.json

echo "BATCH2 DONE"
ls -la /home/z/my-project/research/
