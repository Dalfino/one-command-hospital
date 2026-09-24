.PHONY: help up up-gpu down logs patients conformance eval eval-full observe doctor audit-verify \
	test-unit test-node test-integration test-integration-native stack-prod stack-stop edge-up edge-down backup restore loadtest clean

help:
	@echo "One-Command Hospital"
	@echo "  make doctor       preflight check (docker, env, ports, disk, GPU, secrets)"
	@echo "  make up           start core stack (EHR, spine, bus, AI services)"
	@echo "  make up-gpu       core stack + vLLM serving BioMistral-7B"
	@echo "  make observe      + Prometheus (:8106) and Grafana (:8107) dashboards"
	@echo "  make edge-up      + TLS terminator (:8443) — widget / api / emr routes"
	@echo "  make patients     generate synthetic population into ./data/synthea"
	@echo "  make conformance  start HAPI FHIR (conformance checks)"
	@echo "  make eval         run seed eval (fast) -> eval/report.md"
	@echo "  make eval-full    run 208-question eval -> eval/report_full.md"
	@echo "  make audit-verify walk the hash-chained audit log via ai-mediator"
	@echo "  make test-unit    pytest unit tier (fast, no docker) — security & logic"
	@echo "  make test-node    node tests — audit chain, log redaction, metrics"
	@echo "  make test-integration         boot docker test stack + golden path / fail-closed / PHI"
	@echo "  make test-integration-native  same suite, no docker (bare-process stack)"
	@echo "  make loadtest                 locust load test vs mediator (SLO evidence)"
	@echo "  make backup       verified backup (repo + audit ledger, sha256 manifest)"
	@echo "  make restore      verified restore drill (FILE=backups/<name>.tar.gz)"
	@echo "  make down         stop everything"

up:
	docker compose up -d --build

up-gpu:
	docker compose --profile gpu up -d --build

observe:
	docker compose --profile gpu --profile observe up -d --build

edge-up:
	docker compose --profile edge up -d --build

edge-down:
	docker compose --profile edge rm -sf edge

down:
	docker compose --profile gpu --profile conformance --profile patients --profile observe --profile edge down

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

test-unit:
	python3 -m pip install -q -r tests/requirements.txt
	python3 -m pytest tests/unit -q

test-node:
	node --test tests/node/*.test.mjs

test-integration:
	docker compose -f tests/integration/docker-compose.test.yml up -d --build
	python3 -m pip install -q -r tests/requirements.txt
	python3 -m pytest tests/integration -m integration -q; \
	status=$$?; docker compose -f tests/integration/docker-compose.test.yml down -v; \
	exit $$status

# No-docker path (sandboxes, dev laptops, air-gapped hosts): boots the four
# services as bare processes with the same env the test containers get, runs
# the SAME integration tier, then stops them. Evidence is equivalent by design.
test-integration-native:
	bash tools/native_stack.sh up-test
	python3 -m pip install -q -r tests/requirements.txt
	python3 -m pytest tests/integration -m integration -q; \
	status=$$?; bash tools/native_stack.sh down; \
	exit $$status

# Bare-process prod-shape stack (ports 8100-8103) — what loadtest targets when
# docker is unavailable. `make stack-stop` tears it down.
stack-prod:
	bash tools/native_stack.sh up-prod

stack-stop:
	bash tools/native_stack.sh down

loadtest:
	@if command -v locust >/dev/null 2>&1; then \
		locust -f tools/loadtest/locustfile.py --headless \
			-u $(or $(LOCUST_USERS),20) -r 2 -t $(or $(LOCUST_RUN_TIME),2m) \
			--host $(or $(LOCUST_HOST),http://localhost:8103); \
	else \
		echo "locust not found — falling back to docker image"; \
		docker run --rm --network host -v $(PWD)/tools/loadtest:/mnt/locust \
			locustio/locust -f /mnt/locust/locustfile.py --headless \
			-u $(or $(LOCUST_USERS),20) -r 2 -t $(or $(LOCUST_RUN_TIME),2m); \
	fi

backup:
	bash tools/backup.sh

restore:
	bash tools/restore.sh $(FILE)

clean:
	docker compose --profile gpu --profile conformance --profile patients --profile observe --profile edge down -v
