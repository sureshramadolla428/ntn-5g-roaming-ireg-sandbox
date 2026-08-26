# Grafana 5G roaming flow dashboard

Post-capture visualization for TC-05 (and TC-15 HR attempts). **Live attach parsing is DEFERRED-TO-UBUNTU**; Windows runs offline pytest + fixture ladder only.

**Related:** [`docs/call-flows/5g-sa-roaming-reference.md`](../call-flows/5g-sa-roaming-reference.md) · [`scripts/refresh-flow-dashboard.sh`](../../scripts/refresh-flow-dashboard.sh) · [`scripts/clear-flow-dashboard.sh`](../../scripts/clear-flow-dashboard.sh)

---

## Dashboard URLs

| Dashboard | UID | URL |
|-----------|-----|-----|
| **00 — Roaming Overview** | `ntn-roaming-overview` | http://127.0.0.1:3000/d/ntn-roaming-overview |
| **02 — 5G Roaming Flow** | `ntn-5g-roaming-flow` | http://127.0.0.1:3000/d/ntn-5g-roaming-flow |

Regenerate JSON after catalog changes:

```bash
python dashboard/grafana/gen_dashboards.py
```

---

## Color palette

| Role | Hex | Usage |
|------|-----|-------|
| HOME / HPLMN | `#2E7D32` | Home NF headers, reg phase row |
| VISITED / VPLMN | `#1565C0` | Visited NF headers, PDU phase row |
| IPX | `#EF6C00` | IPX SBI relay banner |
| RAN | `#6A1B9A` | NAS/NGAP / UE-gNB |
| Auth phase | `#FF9800` | Authentication row accent |
| observed | `#43A047` | Step seen in pcap/fixture |
| partial_expected | `#FBC02D` | Expected PARTIAL/N/A (LBO vs HR) |
| missing | `#E53935` | Expected MEASURED but absent |

Thresholds on stat/gauge panels: **green=observed · yellow=partial_expected · red=missing**.

---

## Honesty (dashboard banner)

| Label | Meaning |
|-------|---------|
| **B1 same-PLMN** | UE/gNB camp **001/01** — not production VPLMN **999/70** |
| **No SEPP/N32** | Dual-home SBI on ipx-net; `ipx-sbi-proxy` is a stand-in |
| **LBO vs HR** | TC-05 **MEASURED** visited PDU (10.46.x); HR steps pdu-4…pdu-10 **PARTIAL** until TC-15 **10.45.x** |
| **Colors** | VPLMN `#1565C0`, HPLMN `#2E7D32`, IPX `#EF6C00`, RAN `#6A1B9A` |

---

## Panel guide — 00 Overview

- **Domain stat row** — HOME / VISITED / IPX / RAN observed-step counts (color backgrounds). **RAN may stay 0** until `ran-net.pcap` NAS/NGAP is parsed — not a KPI failure.
- **Flow Completeness Debug View** — observed / partial / missing / expected denominator / catalog total (28). Denominator for TC-05 coverage is **23** (excludes 5 HR-only N/A pdu steps). Exporter logs `expected_denominator=23` on `/reload`.
- **Coverage gauges** — `roaming_flow_phase_coverage_ratio{phase}` = observed ÷ TC-expected per phase; overall `roaming_flow_coverage_ratio{tc_id}`. Shows **PENDING — not wired** when no scrape yet (not 0%).
- **3GPP procedure success rates** — MEASURED ladder gauges from
  `roaming_procedure_success_rate{procedure=registration|auth|pdu}`
  (binary step presence; not multi-trial GSMA KPIs).
- **Harness KPIs** — C8 pass rate, passed/executed totals from `harness/reports/*.json`.

---

## Panel guide — 02 Roaming Flow

- **Live sequence diagram** — open call-flow ladder in a new tab; legend explains step status (green/yellow/red) and message roles (red=request, green=success, orange=intermediate/policy). Message-role colors are **UNVERIFIED** until live NAS parsing on Ubuntu.
- **Phase rows** — Auth / Reg / PDU with observed · partial · missing stat panels.
- **Coverage gauges** — total + per-phase observed %.
- **Bar chart** — stacked steps by procedure and result.
- **State timeline** — `roaming_flow_step_total` per step/result.
- **Ladder table** — color-coded Result column.
- **Per-step stat grid** — one panel per catalog step (`auth-1` … `pdu-12`).
- **Call-flow HTML iframe** — `http://127.0.0.1:8010/static/roaming-callflow.html?api=http://127.0.0.1:8010/ladder/latest` (auto-refreshes from `/ladder/latest`; static served via FastAPI `StaticFiles` mount).
- **Topology nodeGraph** — static VPLMN/HPLMN nodes + observed-step highlight.

---

## Bring up monitoring stack (Ubuntu or Windows Docker)

```bash
cd ~/ntn-roaming-lab   # or synced copy
make create-networks   # once — creates ntn-monitoring-net
cd dashboard
docker compose up -d
```

| Service | URL | Role |
|---------|-----|------|
| Grafana | http://127.0.0.1:3000 | Dashboards 00 + 02 |
| Prometheus | http://127.0.0.1:9090 | Scrapes flow-exporter |
| flow-exporter | http://127.0.0.1:8010 | `/metrics`, `/ladder/latest`, `/static/roaming-callflow.html`, `POST /reload`, `POST /clear` |
| Streamlit | http://127.0.0.1:8501 | IREG gate (separate) |

Default Grafana login: `admin` / `admin` (change on first login).

---

## TC-05 capture → refresh ladder

```bash
# 1) Golden attach with capture (Ubuntu)
bash scripts/run-tc-05-golden.sh --with-capture
# ... attach completes ...
bash scripts/capture-ireg-tc.sh TC-05 --stop
# default: clears flow-exporter gauges → Grafana zeros
# keep last MEASURED ladder: KEEP_FLOW_METRICS=1 bash scripts/capture-ireg-tc.sh TC-05 --stop

# 2) Open dashboards (hard refresh Ctrl+Shift+R)
# http://127.0.0.1:3000/d/ntn-roaming-overview   — title (v11 panel-fix)
# http://127.0.0.1:3000/d/ntn-5g-roaming-flow
```

Capture layout: `pcaps/TC-05/<YYYYMMDDTHHMMSS>/{ran,visited,home,ipx}-net.pcap`

Optional env / scripts:

```bash
# Zero dashboard now (without stopping capture):
bash scripts/clear-flow-dashboard.sh
# or: curl -X POST http://127.0.0.1:8010/clear

# Re-show last capture after clear / stop:
export PCAP_DIR=~/ntn-roaming-lab/pcaps/TC-05/20250824T153000
export FLOW_EXPORTER_URL=http://127.0.0.1:8010
bash scripts/refresh-flow-dashboard.sh
# Keep ladder on --stop: KEEP_FLOW_METRICS=1
```

---

## Parser backends

1. **tshark** (preferred on Ubuntu host / container with `apt install tshark`)
2. **pyshark** (optional; still needs tshark)
3. **fixture** — `dashboard/exporters/fixtures/tc05_minimal_ladder.json` when no pcaps/parser (Windows offline tests)

Container mounts `../pcaps`, `../harness/reports`, and `grafana/public-assets` read-only.

---

## API quick reference

```bash
curl -s http://127.0.0.1:8010/health
curl -s http://127.0.0.1:8010/ladder/latest | jq '.steps[:3]'
curl -s http://127.0.0.1:8010/static/roaming-callflow.html?embed=1 | head
curl -X POST http://127.0.0.1:8010/reload
curl -X POST http://127.0.0.1:8010/clear
curl -s http://127.0.0.1:8010/metrics | grep -E 'roaming_flow|roaming_procedure|harness_'
```

Prometheus metrics:

- `roaming_flow_step_total{phase,step,procedure,result,domain}`
- `roaming_flow_step_timestamp{phase,step}`
- `roaming_flow_coverage_ratio` — observed / TC-expected steps (23 for TC-05; 0–1)
- `roaming_flow_phase_coverage_ratio{phase}` — observed / TC-expected per phase
- `roaming_flow_domain_observed_total{domain,tc_id}` — observed steps per ran/visited/home/ipx
- `roaming_procedure_success_rate{procedure,tc_id}` — binary ladder completion (0–1); omitted only if neither attempt nor accept observed
- `roaming_procedure_kpi_ready{procedure,tc_id}` — 1 when rate published
- `roaming_procedure_attempts_total{procedure,tc_id}` / `roaming_procedure_successes_total{procedure,tc_id}` — Gauge 0|1
- `harness_pass_rate`, `harness_reports_passed_total`, `harness_reports_executed_total`, `harness_reports_files_total`

`result`: `observed` | `missing` | `partial_expected`

---

## Offline tests (Windows)

```powershell
cd C:\Users\sures\OneDrive\Desktop\MVNOs_and_MNOs\ntn-roaming-lab
.\.venv\Scripts\python.exe -m pytest harness/testcases/test_pcap_flow_exporter.py -q
make check-network
```

---

## What is live vs post-capture vs fixture

| Capability | Status |
|------------|--------|
| Docker stack (Grafana/Prometheus/exporter) | **Live** on any host with Docker |
| Real pcap parse → ladder | **Post-capture refresh** (Ubuntu + tshark) |
| Fixture ladder / pytest | **Windows offline PASS** |
| Harness C8 on overview | **Live** when JSON files exist in `harness/reports/`; else shows **0** |
| Call-flow HTML iframe | **Live** when flow-exporter running; data from fixture or pcap parse |
| Real-time NF metrics from Open5GS | **Not wired** (V15 UNVERIFIED) |

---

## Troubleshooting

- **You are on the OLD 00-overview dashboard if you see:**
  - Auth or PDU phase coverage stuck at **33.3%** (3/9 or 4/12 — wrong catalog denominators)
  - Two coverage gauges (**0%** from `or vector(0)` plus ~35.7%)
  - No row titled **Flow Completeness Debug View**
  - Panel title **Observed / catalog coverage** (replaced by **Observed / expected coverage**)
  - Fix: follow **`docs/runbooks/grafana-stale-dashboard.md`** (DELETE-by-UID import).
    Titles must show **`(v11 panel-fix)`** — if not, sync failed.
- **Empty dashboard stats:** run `refresh-flow-dashboard.sh` after capture; confirm Prometheus target `flow-exporter:8010` is UP.
- **Stale stats after --stop:** default `--stop` now clears to zeros (`POST /clear`). To keep last ladder: `KEEP_FLOW_METRICS=1`. Manual zero: `bash scripts/clear-flow-dashboard.sh` or `curl -X POST http://127.0.0.1:8010/clear`.
- **All steps `missing`:** pcaps empty or tshark missing in container — install tshark in image or run exporter on Ubuntu host with `PCAP_DIR` set.
- **HR steps show partial_expected on TC-05:** expected — LBO golden path skips hSMF/hUPF.
- **Call-flow iframe blank:** open `http://127.0.0.1:8010/static/roaming-callflow.html?api=http://127.0.0.1:8010/ladder/latest` directly; confirm `/ladder/latest` returns JSON and static is mounted (`PUBLIC_ASSETS` volume in docker-compose).
- **Signalling table duplicate rows:** caused by stale Prometheus series when step `result` changed across reloads. Exporter now uses a Gauge and zeros old labels; table query filters `roaming_flow_step_total > 0`. After upgrade, `POST /reload` once or restart flow-exporter.
- **Harness KPIs zero:** drop JSON reports into `harness/reports/` and `POST /reload` on flow-exporter.


## Demo populate stats (Windows + Ubuntu)

Safest path to non-zero Grafana harness (C8) and flow metrics without claiming live attach MEASURED numbers on Windows.

### Windows (offline reports + fixture ladder)

Not MEASURED live attach — OFFLINE/MOCK fixture / pytest feed only.

```powershell
cd C:\Users\sures\OneDrive\Desktop\MVNOs_and_MNOs\ntn-roaming-lab
.\.venv\Scripts\python.exe scripts\write_offline_harness_reports.py
bash scripts/create_docker_networks.sh
cd dashboard
# If ATG or another stack already owns :3000 / :9090:
#   $env:GRAFANA_HOST_PORT=3001; $env:PROMETHEUS_HOST_PORT=9091
docker compose up -d --build
curl -sf -X POST http://127.0.0.1:8010/reload
curl -sf http://127.0.0.1:8010/metrics | findstr /R "harness_ roaming_flow_"
```

Or one-shot (Git Bash / WSL):

```bash
bash scripts/demo-populate-stats.sh
# reports only:
bash scripts/demo-populate-stats.sh --offline-only
```

Port conflict note: set `GRAFANA_HOST_PORT=3001` and `PROMETHEUS_HOST_PORT=9091` when another service (e.g. ATG) binds host 3000/9090. Flow-exporter stays on `8010`; Streamlit on `8501`.

### Ubuntu (live TC-05 + mocks + refresh + import + verify)

```bash
# 0) Sync + dashboard stack
rsync -av --exclude '.venv' --exclude '__pycache__' --exclude '.git' \
  /mnt/hgfs/MVNOs_and_MNOs/ntn-roaming-lab/ ~/ntn-roaming-lab/
cd ~/ntn-roaming-lab
python3 scripts/fix_crlf.py
bash scripts/create_docker_networks.sh
cd dashboard && docker compose up -d --build && cd ..

# 1) Offline C8 reports (nonzero harness_* even before attach)
python3 scripts/write_offline_harness_reports.py
# or: bash scripts/demo-populate-stats.sh --skip-compose

# 2) TC-05 golden attach + capture (READY-LIVE; MEASURED only after this)
export UERANSIM_BIN=~/UERANSIM/build ATTACH_MODE=b1-home-plmn KEEP_UE=1
bash scripts/run-tc-05-golden.sh --with-capture
# ... attach completes ...
bash scripts/capture-ireg-tc.sh TC-05 --stop
bash scripts/refresh-flow-dashboard.sh TC-05

# 3) 2–3 MOCK-RUNNABLE TCs that populate evidence (optional capture)
make up-mocks
bash scripts/run-ireg-tc.sh TC-07
bash scripts/run-ireg-tc.sh TC-12
bash scripts/run-ireg-tc.sh TC-20
# optional: TC-09 / TC-13 / TC-10 via run-ireg-tc.sh

# 4) Grafana one-shot sync (titles must show (v11 panel-fix)) + verify
bash scripts/grafana-sync-live.sh TC-05
# or stepwise:
python3 dashboard/grafana/gen_dashboards.py
bash scripts/grafana-import-dashboards.sh
bash scripts/grafana-verify-dashboard.sh

# 5) Confirm metrics
curl -sf http://127.0.0.1:8010/health
curl -sf -X POST http://127.0.0.1:8010/reload
curl -sf http://127.0.0.1:8010/metrics | grep -E 'roaming_flow_|harness_'
# Open: http://127.0.0.1:3000/d/ntn-roaming-overview
#       http://127.0.0.1:3000/d/ntn-5g-roaming-flow
```

### Expected nonzero metrics

After offline reports (and/or TC-05 refresh) plus exporter reload, expect nonzero:

- `harness_reports_files_total`
- `harness_reports_passed_total`
- `harness_reports_executed_total`
- `harness_pass_rate`
- `roaming_flow_step_total` (fixture or pcap ladder)
- `roaming_flow_coverage_ratio`
- `roaming_flow_phase_coverage_ratio`

Dashboard panel titles should show **(v11 panel-fix)**. On Windows without pcaps, ladder/coverage values are fixture/OFFLINE - label them accordingly; do not present as MEASURED live attach.