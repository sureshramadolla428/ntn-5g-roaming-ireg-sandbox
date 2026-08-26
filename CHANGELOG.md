# Changelog

## tc05-pfcp-capture-checklist ? N4 evidence for next LBO run

- Added `docs/runbooks/tc-05-full-capture-checklist.md` (ordered steps; N4 on
  `ntn-visited-net` SMF `10.10.2.12` ? UPF `10.10.2.13` UDP/8805).
- Linked from TC-05 `014834` LBO evidence + DEMO-SNAPS; **W9** PFCP snap marked
  pending until next capture with `tshark -Y pfcp` count > 0.
- Local/private scripts: `live-first-attach.sh` + `capture-ireg-tc.sh` multi-point
  fallback now include N4 hosts (public tree gitignores `scripts/**`).

## rename-ireg-sandbox - public rename + branding scrub

- GitHub public slug: `ntn-5g-roaming-ireg-sandbox` (display: NTN 5G Roaming IREG Sandbox).
- Private companion: `ntn-5g-roaming-ireg-sandbox-scripts`.
- User-facing docs: IREG practice / IREG sandbox framing; honesty caveat (B1, no SEPP, not GSMA operator sign-off).
- Removed local IDE/agent tooling and handoff prompt dumps from the published tree; gitignore excludes them.

## fix-tc05-lbo-default ? ROAMING_MODE=LBO + UPF pool sync

- Root cause of UE **10.45.0.3** on TC-05: compose defaulted `ROAMING_MODE=HR` so
  `smf_init.sh` assigned HR pool while `visited-upf` still used `.env` **10.46**
  (`session.subnet` / `gateway`) ? ping to neither GW worked.
- Default `ROAMING_MODE=LBO` on visited-smf **and** visited-upf; `upf_init.sh`
  selects the same HR/LBO pools as SMF.
- `run-tc-05-golden.sh` recreates SMF+UPF with LBO before attach; `run-tc-15-hr.sh`
  recreates both with HR for **10.45**.
- Docs: DEF-0016, ireg-tc-execution ?5, TC-05-spec, variants/README honesty.

## junk-path-home-false-positive ? allow host /home/... PCAP_DIR

- Refresh/sync junk filter no longer matches host path segment `/home/` before
  `pcaps/TC-*`; only components *after* `TC-*` (e.g. `pcaps/TC-05/home/...`) are
  refused. Python `_is_junk_capture_path` already scoped after `TC-*`; tests +
  `scripts/test-refuse-junk-pcap.sh` cover the false-positive.
- `--stop` / `POST /clear` still do not delete pcap files (metrics only).

## flow-dashboard-clear-on-stop ? POST /clear + default --stop zeros

- `POST /clear` (and `POST /reload {"clear": true}`) zeros all flow gauges; health
  ready with `observed=0`, `pcap_dir=null`, parser=`cleared`.
- `scripts/clear-flow-dashboard.sh` ? curl wrapper for zeroing Grafana now.
- `capture-ireg-tc.sh --stop` clears by default; `KEEP_FLOW_METRICS=1` keeps last
  ladder (and refreshes when `REFRESH_FLOW_DASHBOARD` ? 0).
- `refresh-flow-dashboard.sh` auto-clears when no capture dir is found.
- Tests: `test_clear_endpoint_zeros_observed_and_gauges`.

## grafana-v11-panel-fix ? unmistakable title + always-emit KPIs + sync script

- Dashboards **`(v11 panel-fix)`** (v10 claimed but Ubuntu UI still stuck on pre-v10).
- Header: **Active capture (from exporter tc_id)** ? never hardcode TC-06.
- Domain panels: prefer `count(step_total{domain=})` then domain gauge; `noValue` is `?`.
- Procedure success rates **always emitted** after reload (0 when no attempt/accept).
- Coverage gauges use `phase_coverage_ratio` / `coverage_ratio` only; pending text
  `PENDING ? run refresh-flow-dashboard`.
- New `scripts/grafana-sync-live.sh` one-shot: regenerate ? recreate exporter on latest
  TC timestamp ? POST reload ? DELETE+import uid `ntn-roaming-overview` ? health/metrics.
- Refresh/reload refuse junk `mnt`/`home`/`hgfs` PCAP paths; health prints `pcap_dir`.
- Prometheus flow-exporter scrape interval 5s (instant gauge queries).

## grafana-v10-live-tc-sync ? domain PromQL + auto-refresh exact PCAP_DIR

- Domain panels: `roaming_flow_domain_observed_total` **or** `count(step_total{domain=?})`;
  `noValue` is `?` (not `0`) so missing scrape ? zero. Step gauge gains `domain` label.
- `capture-ireg-tc.sh --stop` refreshes by default with the **exact** `PCAP_DIR` from
  state; skip with `REFRESH_FLOW_DASHBOARD=0`.
- Procedure KPIs: ready when attempt **or** accept known (accept-only ? 100%);
  `/health` exposes `pcap_dir`, `tc_id`, `observed`, `coverage`, `domains`, rates.
- Dashboards **`(v10 live-tc-sync)`**; header says active-TC denominator (not hardcoded TC-06).

## grafana-v9-capture-sync ? reload clears gauges + sync to latest TC capture

- Exporter fully clears all capture gauges on `/reload` (no zeroed ghost series);
  publishes `roaming_flow_domain_observed_total`, `roaming_procedure_kpi_ready`;
  `resolve_latest_capture` ignores `mnt`/`home` junk trees under `pcaps/TC-*/`.
- Refresh script maps host?`/pcaps/...`, recreates exporter with `PCAP_DIR`, curls
  health/coverage/procedure rates after reload.
- Dashboards regenerated as **`(v9 capture-sync)`**; success panels use
  `100 * roaming_procedure_success_rate` with noValue `PENDING ? reload capture`.

## grafana-v8-success-rates ? ladder-derived procedure KPIs

- Flow exporter publishes `roaming_procedure_success_rate` / `_attempts_total` / `_successes_total`
  from catalog step presence (reg-7/auth-1, auth-8|9/auth-3|6, pdu-11/pdu-1).
- Grafana 00/02: replaced orange UNVERIFIED placeholders with MEASURED ladder gauges;
  titles marked `(v8 success-rates)`.
- `dashboard/kpi-traceability.md`: procedure rates ? LAB MEASURED (ladder); honesty note.
- Tests: procedure KPI oracles + dashboard PromQL in `test_pcap_flow_exporter.py` /
  `test_gen_dashboards.py`.

## demo-populate-stats ? offline C8 KPIs + fixture flow metrics

- Added `scripts/write_offline_harness_reports.py` (pytest ? harness/reports/*.json for flow-exporter C8 gauges; OFFLINE/MOCK label).
- Added `scripts/demo-populate-stats.sh` (safest TC/report refresh path for demos).
- `dashboard/docker-compose.yml`: `GRAFANA_HOST_PORT` / `PROMETHEUS_HOST_PORT` overrides for host port conflicts.
- Runbook: `docs/runbooks/grafana-5g-flow.md` demo populate section (Windows fixture vs Ubuntu TC-05 MEASURED).

## grafana-5g-flow ? dashboard fix (reg stats, topology, log fallback)

- Reg stat panels use `or vector(0)` ? no more empty "No data" when reg steps are missing.
- Replaced broken `nodeGraph` with colorful static SVG topology + call-flow iframe on `127.0.0.1:8010`.
- Added `flow_exporter_parser_info` metric and parser/coverage stat panels.
- Pcap parse: HTTP/2 `header.value` fallback, log grep supplement from `docker-logs/*.log`, multi-bridge reg paths.
- `POST /reload` accepts JSON `pcap_dir`; refresh script sends capture path.

## grafana-5g-flow ? pcap ladder exporter + roaming dashboard (Phase C)

- Added `dashboard/exporters/pcap_flow_exporter.py`: offline pcap ? Prometheus `roaming_flow_step_*` + `/ladder` JSON (:8010); tshark/pyshark/fixture backends.
- Added `dashboard/exporters/flow_catalog.py` mapped from `docs/call-flows/5g-sa-roaming-reference.md` with B1 / no SEPP / LBO vs HR honesty labels.
- Grafana: `dashboard/grafana/dashboards/02-5g-roaming-flow.json` (VPLMN `#1565C0`, HPLMN `#2E7D32`); provisioning provider; Prometheus scrape job for flow-exporter.
- `dashboard/docker-compose.yml`: `flow-exporter` @ 10.10.7.14; `network-plan.yaml` host entry + port 8010.
- `scripts/refresh-flow-dashboard.sh` ? post TC-05 capture reload hook (DEFERRED-TO-UBUNTU live).
- Tests: `harness/testcases/test_pcap_flow_exporter.py` (offline fixture on Windows).
- Runbook: `docs/runbooks/grafana-5g-flow.md`.

## call-flows ? 5G SA roaming reference evidence map
- Added `docs/call-flows/5g-sa-roaming-reference.md`: four slide flows ? pcap filters, log greps, TC-05/TC-15 honesty (B1, LBO vs HR, no SEPP).

## ireg-tc-harness-expansion ? per-TC runners + mock depth

- Added `scripts/run-ireg-tc.sh` dispatcher and runners for TC-03/04/06/11/15/16/07/09/10/12/13/20/21/01-deferred.
- `live-first-attach.sh`: `ATTACH_MODE` tc03/tc16, `UE_YAML` override, `EXPECT_FAILURE` for negatives.
- `visited-network/configs/smf/smf_init.sh`: consumes `ROAMING_MODE` (HR/LBO pool selection ? DEF-0016 partial fix).
- SGd mock: Alert-SC/PSM HTTP sidecar (:8081); SCEF: MT NIDD buffer API (TC-13); MAP SRI-SM stub @ 10.10.6.12.
- Helpers: `sqn_resync.py`, `tc06_amf_barred.py`; docs: `lte-epc-deferred-path.md`; matrix statuses updated.

## ireg-tc-suite-ready ? interview TC-01?25 matrix + capture
- Added `docs/ireg-tc-matrix.md` mapping user TC-01?25 ? LAB-IREG/scripts with READY-LIVE / PARTIAL / MOCK-ONLY / DEFERRED / BLOCKED (no invented AVPs).
- Added `scripts/capture-ireg-tc.sh`, `scripts/run-tc-05-golden.sh`, `docs/runbooks/ireg-tc-execution.md`.
- Negative stubs: wrong-key UE (TC-03), unknown DNN UE (TC-16), TC-06 barred marker (5004 stays V1 UNVERIFIED).
- Documented MEASURED B1 + LBO 10.46 vs unwired `ROAMING_MODE`/HR variants; SEPP absent; no NAT; UERANSIM VPLMN camp limit.
- `make up-ss7`, `make capture-ireg TC=TC-05`; phase-status START HERE points at matrix + golden path.

## verify-live-home-plmn ? accept placeholders or rendered HOME MCC/MNC
- `make verify-live` falsely FAILed visited AMF HOME PLMN check: `grep -A6 plmn_support` never reached the second (HOME) PLMN block.
- Checker now reads `HOME_MCC`/`HOME_MNC` from `visited-network/.env` and accepts `HOME_MCC` **or** rendered values (e.g. `001`) in `access_control`/`guami`/`tai`/`plmn_support` (+ `relative_capacity: 255`); still FAILs if a section is missing.
- Runbook: UE TUN `Permission denied` after Registration Accept needs `sudo`/`CAP_NET_ADMIN` for user-plane ping.

## ueransim-suci-hplmn-b1 ? SUCI 999/70 404 root cause + Option B dual-track
- MEASURED: AMF `suci-0-999-70-?-0000000001` ? AUSF/UDM 404 ? Registration reject **#7** while Mongo has `001010000000001`.
- Root cause: UERANSIM wiki `mcc`/`mnc` = **HPLMN** (must match SUPI); `generateSuci()` uses `config->hplmn`, not SUPI digits. Setting 999/70 "for camping" mis-encodes SUCI. No equivalent/preferred PLMN YAML keys (Option A unsupported without patches).
- **B1 (default):** UE `mcc`/`mnc` **001/01**; `gnb-home-plmn-auth.yaml` broadcast 001/01; visited AMF `tai`/`plmn_support` add HOME for NG Setup. Expected SUCI `suci-0-001-01-0000-0-0-0000000001`. Single-PLMN auth proof ? not true VPLMN camp.
- **B2 (last resort MOCK):** `lab-subscribers-mock-vplmn-imsi.ndjson` (`999700000000001`) ? not auto-provisioned.
- `live-first-attach.sh` default `ATTACH_MODE=b1-home-plmn`; runbook + `verify-live` assert UE HPLMN consistency.

## fivegs-services-not-allowed ? cause #7 vs access_control
- MEASURED Ubuntu reject: `FIVEG_SERVICES_NOT_ALLOWED` ? UE `5U3-ROAMING-NOT-ALLOWED` (5GMM cause **#7**).
- Open5GS maps HTTP **404** (AUSF `Cannot find SUCI` / nudm errors) to cause #7; missing `access_control` home PLMN is cause **#11** (not #7).
- Visited AMF: keep `access_control` 999-70+001-01; add HOME `guami`, `relative_capacity: 255` (keys from `amf.yaml.in` / docker_open5gs roaming).
- Home PCF dual-homed on ipx-net `10.10.3.25`, single NRF = `VISITED_NRF_IPX` (AM policy after UDM).
- Subscriber: confirm ARD=32 is Open5GS default (not NR deny); add `operator_determined_barring: 0`.
- Runbook `live-first-attach.md` documents cause #7 vs #11 vs #65; Ubuntu collect paste uses `sg docker`.

## verify-live-mawk-fix ? portable NRF URI counter
- `make verify-live` aborted under Ubuntu default `mawk` with `runaway regular expression` on `[[:space:]]` / nested classes in `scripts/verify-live-stack.sh`.
- Replaced awk NRF-client URI counter with portable `python3` regex; Makefile unchanged (`bash scripts/verify-live-stack.sh`).

## single-nrf-client ? Open5GS MEASURED dual-NRF crash fix
- Root cause: listing two `sbi.client.nrf` URIs crashes Open5GS (`Only one NRF client can be set`, `lib/sbi/context.c`).
- Visited AMF/SCP: single NRF = visited `NRF_IP` (`10.10.2.10`).
- Home AUSF/UDM/UDR/PCF: single NRF = `VISITED_NRF_IPX` (`10.10.3.30`) so visited AMF can discover them; home SCP/SMF stay on home NRF.
- Home UDR dual-homed on ipx-net `10.10.3.24` (reach visited NRF). Dual-home **interfaces** kept; dual NRF **clients** removed.
- `verify-live` fails on multi-NRF YAML, restarting containers, and the crash log signature.
- No static AMF `ausf:` client key in Open5GS 2.8 `context.c` (only `nrf`/`scp`/`delegated`) ? not used.

## sg-dash-source-fix ? bash inside `sg docker -c`
- MEASURED: `sg docker -c '? source .venv?'` fails under dash (`source: not found`); bootstrap never ran; containers stayed without `ntn-ipx-net`.
- All hints now use `bash scripts/ubuntu-sg-bootstrap.sh` or `sg docker -c "bash -lc '? source ?'"` ? never bare `source` in the `sg -c` string.

## sg-docker-bootstrap ? dual-home verify + newgrp-safe paste
- Visited AMF now binds SBI on **AMF_IPX** `10.10.3.31` (plus visited-net); `.env` + longest-token sed include `AMF_IPX` before `AMF_IP`.
- `make verify-live` checks ipx-net IPs for home-nrf/ausf/udm/scp and visited-nrf/amf/scp, plus AMF `HOME_MCC` access_control template.
- Added `scripts/ubuntu-sg-bootstrap.sh` and `make sg-bootstrap-hint` ? use `sg docker -c '...'` so `newgrp` cannot swallow bootstrap after sync.
- Runbooks: `ubuntu-bootstrap.md`, `live-first-attach.md`, phase-status ?B updated.

## dual-home-ipx-complete ? placeholder sed + AUSF/UDM/SCP binds
- `*_init.sh` now substitutes **longest tokens first** (`NRF_IPX`/`HOME_MCC` before `NRF_IP`/`MCC`). Short-first sed would have turned `NRF_IPX` into `10.10.1.10X` and `HOME_MCC` into `HOME_999`.
- Home AUSF/UDM listen on home-net **and** ipx-net; home SCP dual-homed at `10.10.3.23`; visited SCP also binds `10.10.3.32`.
- UERANSIM `gnb.yaml` aligned to reference `open5gs-gnb.yaml` schema (cells + `cellAccessType`) with lab IPs. UE stays home IMSI `001010000000001` / serving 999-70; OPc remains lab `?823C` (not reference `?83CA`).

## payload-not-forwarded-sbi ? visited AMF ? home AUSF via ipx-net
- Root cause (config): visited NRF has no AUSF; home AUSF not reachable from visited-net (iptables DROP); FastAPI `/n32-standin` is not Open5GS SBI.
- Lab stand-in (not SEPP): dual-home home NRF/AUSF/UDM + visited AMF/SCP on `ntn-ipx-net`; AMF `access_control` for 001-01 (Open5GS `amf.yaml.in` / docker_open5gs roaming).
- Runbook: `docs/runbooks/live-first-attach.md` ? PAYLOAD_NOT_FORWARDED meaning + Ubuntu log collect.

## docker-bootstrap-fix ? Ubuntu network bring-up
- Removed `external: true` from domain compose files; networks created by `scripts/create_docker_networks.sh`.
- Added `make create-networks`, `make bootstrap-docker`, `make up-lab`.
- Fixed visited Open5GS mounts to per-NF paths; added `visited-network/configs/{nrf,scp,amf,smf,upf}/`.
- `enforce-ipx-routing.sh` applies iptables DOCKER-USER DROP rules.

## scaffold-gap-close-1 ? Windows audit gap close
- Saved lab specification document (v2 full text)
- Added local workspace accuracy / file-safety / execution rules
- Phase 1: home Open5GS NF YAMLs (nrf/scp/ausf/udm/udr/pcf/hss/smf/upf) PLMN **001-01**, per-NF mounts, HSS+HR SMF/UPF in compose; IMSI 001010000000001?020 unchanged; visited remains **999-70**
- Phase 2: freeDiameter Dockerfile + entrypoint (replaces `sleep infinity`); SBI proxy remain stand-in (not SEPP)
- Phase 4: Osmocom STP/HLR/MSC minimal cfg templates (UNVERIFIED vs package)
- Phase 9: converted many DEFERRED cases to offline unit/mocked asserts; live attach stays DEFERRED-TO-UBUNTU
- Added PLMN BCD (C1) + Diameter registry unit tests
- `pcaps/README.md` ? no fake binaries; Ubuntu capture layout
- Makefile: `signoff-check`, `flake-check`, `test-ntn`, `report`
- Docs: `status-done-vs-pending.md`, defect-log, this changelog

## phase-00 ? Network plan
- network-plan.yaml, docker/networks.yml, check-network, LAB-IREG-000 skeleton, network-plan.md

## phase-01 ? Dual Open5GS
- home-network / visited-network compose + configs PLMN 001-01 / 999-70, subscribers, HR/LBO variants

## phase-02 ? IPX
- freeDiameter templates, SBI proxy stand-in (NOT SEPP), fault API, fault_domain, diameter_codes

## phase-03 ? OAI/NTN
- Copied NTN confs, 3GPP?OAI map, corrected B4 netem, staged start

## phase-04 ? SS7/MAP stubs
- Osmocom compose stubs, MAP call-flow, E.212?E.214 lab map

## phase-05 ? SGd SMSC mock
- Minimal Diameter framing mock (+ pycrate note)

## phase-06 ? SCEF T8 NIDD mock
- FastAPI paths UNVERIFIED; size boundary; concat/emergency docs

## phase-07 ? IR.21 lab profiles
- YAML/XML/XSD lab-authored; validators

## phase-08 ? Billing educational CDR
- JSON reconcile + RAP-style rejects; NOT TAP3

## phase-09 ? Harness
- Stack abstraction; 25+ LAB-IREG cases; multi-point capture design

## phase-10 ? CI
- GitHub Actions + Jenkinsfile; V17 SCTP note

## phase-11 ? Dashboard
- Streamlit + Prometheus/Grafana; metric citations C8/C9/D3/D4

## phase-12 ? Docs package
- test-strategy, architecture, call-flows, demo-script, defect-log, limitations, README

## phase-13 ? IMSI trace
- correlate, Jira CSV, HTML export stub, defect-coverage

## phase-14 ? NTN suite
- ntn-test-rationale + NTN pytest markers

## phase--1 ? Inventory
- reference-inventory, quarantine-plan, verification-register, jd-traceability
