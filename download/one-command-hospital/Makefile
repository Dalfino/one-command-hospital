.PHONY: help up up-gpu down logs patients conformance eval eval-full observe doctor audit-verify clean

help:
	@echo "One-Command Hospital"
	@echo "  make doctor       preflight check (docker, env, ports, disk, GPU, secrets)"
	@echo "  make up           start core stack (EHR, spine, bus, AI services)"
	@echo "  make up-gpu       core stack + vLLM serving BioMistral-7B"
	@echo "  make observe      + Prometheus (:8106) and Grafana (:8107) dashboards"
	@echo "  make patients     generate synthetic population into ./data/synthea"
	@echo "  make conformance  start HAPI FHIR (conformance checks)"
	@echo "  make eval         run seed eval (fast) -> eval/report.md"
	@echo "  make eval-full    run 208-question eval -> eval/report_full.md"
	@echo "  make audit-verify walk the hash-chained audit log via ai-mediator"
	@echo "  make down         stop everything"

up:
	docker compose up -d --build

up-gpu:
	docker compose --profile gpu up -d --build

observe:
	docker compose --profile gpu --profile observe up -d --build

down:
	docker compose --profile gpu --profile conformance --profile patients --profile observe down

logs:
	docker compose logs -f --tail=100

patients:
	docker compose --profile patients run --rm --build synthea

conformance:
	docker compose --profile conformance up -d

eval:
	cd eval && python3 run_eval.py qa_seed.yaml

eval-full:
	cd eval && python3 run_eval.py qa_full.yaml

doctor:
	bash tools/doctor.sh

audit-verify:
	@curl -sf http://localhost:8103/audit/verify | python3 -m json.tool \
		|| echo "ai-mediator unreachable — is the stack up? (make up)"
