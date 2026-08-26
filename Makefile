# ntn-roaming-lab Makefile
SHELL := /bin/bash
PY ?= python3
export PYTHONPATH := $(CURDIR)

.PHONY: help check-network verify-reference verify-reference-generate \
	create-networks bootstrap-docker up-lab verify-live provision-subscribers \
	sync-from-share vm-bringup quarantine quarantine-aggressive \
	test-unit test-fast test-tier1 test-ntn \
	up-home up-visited up-ipx up-mocks up-ss7 down \
	capture-ireg defect-coverage bootstrap-hint sg-bootstrap-hint \
	signoff-check flake-check report

help:
	@echo "Targets: vm-restart vm-bringup bootstrap-docker verify-live provision-subscribers"
	@echo "         quarantine quarantine-aggressive sync-from-share"
	@echo "         create-networks down check-network test-fast signoff-check"
	@echo "Ubuntu docker group: make sg-bootstrap-hint"

verify-live:
	bash scripts/verify-live-stack.sh

provision-subscribers:
	bash scripts/provision_subscribers.sh

sync-from-share:
	bash scripts/sync-from-share.sh

quarantine:
	python3 scripts/fix_crlf.py
	bash scripts/quarantine-project-cruft.sh

quarantine-aggressive:
	python3 scripts/fix_crlf.py
	bash scripts/quarantine-project-cruft.sh --aggressive

vm-bringup:
	bash scripts/vm-bringup.sh

vm-restart:
	bash scripts/vm-restart-stacks.sh

create-networks:
	bash scripts/create_docker_networks.sh

bootstrap-docker: create-networks
	bash scripts/bootstrap-docker.sh

up-lab: bootstrap-docker
	@echo "Lab stacks up — run: docker ps"

check-network:
	$(PY) scripts/check_network.py

verify-reference:
	$(PY) scripts/verify_reference.py check

verify-reference-generate:
	$(PY) scripts/verify_reference.py generate

test-unit:
	$(PY) -m pytest -q harness/metrics harness/trace-validation ir21 mocks -m "not live and not deferred" --tb=short

test-fast: check-network test-unit
	$(PY) -m pytest -q harness/testcases -m "tier1 and not live" --tb=short

test-tier1:
	$(PY) -m pytest -q harness/testcases -m tier1 --tb=short

test-ntn:
	$(PY) -m pytest -q harness/testcases -m "tier2 or lab_ireg('LAB-IREG-024') or lab_ireg('LAB-IREG-025')" --tb=short

signoff-check: check-network test-fast
	@echo "=== Signoff checklist (scaffold) ==="
	@test -f MASTER_PROMPT.md && echo "PASS: MASTER_PROMPT.md"
	@test -d .cursor/rules && echo "PASS: .cursor/rules"
	@test -f home-network/configs/nrf/nrf.yaml && test -f home-network/configs/nrf/nrf_init.sh && echo "PASS: home NF configs+init"
	@test -f visited-network/configs/amf/amf.yaml && test -f visited-network/configs/amf/amf_init.sh && echo "PASS: visited AMF config+init"
	@test -f ipx/freediameter/Dockerfile && echo "PASS: DRA Dockerfile"
	@test -f ss7-map/configs/osmo-stp.cfg && echo "PASS: Osmocom templates"
	@test -f pcaps/README.md && echo "PASS: pcaps README"
	@echo "signoff-check: OK (live attach still DEFERRED-TO-UBUNTU)"

flake-check:
	$(PY) -m pytest -q harness/testcases -m flaky_candidate --count=5 --tb=line 2>/dev/null \
		|| $(PY) -m pytest -q harness/testcases -m "flaky_candidate and not live" --tb=short

report:
	@mkdir -p reports
	$(PY) -m pytest harness/testcases harness/metrics harness/trace-validation ir21 mocks \
		-m "not live" --tb=no -q \
		--junitxml=reports/junit.xml \
		|| true
	@echo "JUnit: reports/junit.xml"
	@$(PY) imsi-trace/defect_coverage.py || true

up-home: create-networks
	find home-network/configs -name '*_init.sh' -exec chmod +x {} \;
	mkdir -p home-network/logs && chmod 777 home-network/logs || true
	docker compose -f home-network/docker-compose.yml up -d

up-visited: create-networks
	find visited-network/configs -name '*_init.sh' -exec chmod +x {} \;
	mkdir -p visited-network/logs && chmod 777 visited-network/logs || true
	docker compose -f visited-network/docker-compose.yml up -d

up-ipx: create-networks
	docker compose -f ipx/docker-compose.yml up -d --build

up-mocks: create-networks
	docker compose -f mocks/docker-compose.yml up -d --build

up-ss7: create-networks
	docker compose -f ss7-map/docker-compose.yml up -d
	@echo "NOTE: Osmocom cfg syntax UNVERIFIED vs package — MOCK/DEFERRED for live MAP"

# TC=TC-05 make capture-ireg
capture-ireg:
	@test -n "$(TC)" || (echo "Usage: make capture-ireg TC=TC-05"; exit 1)
	bash scripts/capture-ireg-tc.sh $(TC)

# IREG=TC-03 make run-ireg-tc
run-ireg-tc:
	@test -n "$(IREG)" || (echo "Usage: make run-ireg-tc IREG=TC-03 [CAPTURE=1]"; exit 1)
	@if [ "$(CAPTURE)" = "1" ]; then bash scripts/run-ireg-tc.sh $(IREG) --with-capture; else bash scripts/run-ireg-tc.sh $(IREG); fi

# Domain compose files declare networks as external:true.
# Do not merge docker/networks.yml (subnet documentation only).
down:
	docker compose -f home-network/docker-compose.yml down || true
	docker compose -f visited-network/docker-compose.yml down || true
	docker compose -f ipx/docker-compose.yml down || true
	docker compose -f mocks/docker-compose.yml down || true
	docker compose -f ss7-map/docker-compose.yml down || true
	docker compose -f dashboard/docker-compose.yml down || true

defect-coverage:
	$(PY) imsi-trace/defect_coverage.py

bootstrap-hint:
	@echo "See docs/runbooks/ubuntu-bootstrap.md"

# Print Ubuntu paste that cannot be swallowed by newgrp (use sg docker -c + bash).
# NOTE: sg -c runs under /bin/sh (dash); never put bare `source` in the -c string.
sg-bootstrap-hint:
	@echo "=== Ubuntu: sync then ONE sg+bash line (do not use newgrp; do not bare-source in sg -c) ==="
	@echo "cd ~/ntn-roaming-lab && python3 scripts/fix_crlf.py && chmod +x scripts/*.sh"
	@echo "sg docker -c 'cd ~/ntn-roaming-lab && bash scripts/ubuntu-sg-bootstrap.sh'"
	@echo "# inline equivalent (bash -lc required because sg uses dash):"
	@echo "sg docker -c \"bash -lc 'cd ~/ntn-roaming-lab && source .venv/bin/activate && make bootstrap-docker && make provision-subscribers && make verify-live'\""
