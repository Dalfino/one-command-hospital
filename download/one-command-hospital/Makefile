.PHONY: help up up-gpu down logs patients conformance eval clean

help:
	@echo "One-Command Hospital"
	@echo "  make up          start core stack (EHR, spine, bus, AI services)"
	@echo "  make up-gpu      core stack + vLLM serving BioMistral-7B"
	@echo "  make patients    generate synthetic population into ./data/synthea"
	@echo "  make conformance start HAPI FHIR (conformance checks)"
	@echo "  make eval        run eval harness -> eval/report.md"
	@echo "  make down        stop everything"

up:
	docker compose up -d --build

up-gpu:
	docker compose --profile gpu up -d --build

down:
	docker compose --profile gpu --profile conformance --profile patients down

logs:
	docker compose logs -f --tail=100

patients:
	docker compose --profile patients run --rm --build synthea

conformance:
	docker compose --profile conformance up -d

eval:
	cd eval && python3 run_eval.py
