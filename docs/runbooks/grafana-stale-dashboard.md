# Grafana stale / live-TC-sync dashboard (v11 panel-fix)

If Grafana still shows **TC-06 expected denominator**, domain counters stuck at **0**,
or blank 3GPP success rates, the live UI did not import the current repo JSON.

**Symptom:** Ubuntu Grafana still shows old 00/02 dashboards after Windows→VM sync,
or Overview sticks to a previous TC capture (HOME/VISITED/IPX/RAN all 0 while Flow
steps observed > 0; Auth 33.3%; success rates No data) after a new pcap run.

**One-shot fix on Ubuntu:**

```bash
cd ~/ntn-roaming-lab   # or your lab checkout
sg docker -c 'bash scripts/grafana-sync-live.sh TC-05'
```

**Proof of success:** dashboard titles include **`(v11 panel-fix)`**.
If the title does not say `(v11 panel-fix)`, sync failed.

Import always DELETE+overwrite uid **`ntn-roaming-overview`** (no duplicate stale overview).

Also check `/health` → `pcap_dir` is a real `…/TC-05/YYYYMMDDTHHMMSS` (never `mnt`/`home`).

## Root causes

1. Domain panels used `noValue: "0"` / PromQL that hid step counts behind a zero gauge.
2. Procedure success rate omitted when attempt/accept both missing → Grafana **No data**.
3. Grafana DB kept a prior dashboard revision — import must **DELETE by UID** then POST.
4. Refresh picked junk nested trees (`pcaps/TC-05/mnt`, `…/home/…`) instead of timestamp dirs.

## After every TC (default)

```bash
bash scripts/capture-ireg-tc.sh TC-05 --stop
# default: clears Grafana flow gauges to zero (POST /clear)
# keep last MEASURED ladder: KEEP_FLOW_METRICS=1 bash scripts/capture-ireg-tc.sh TC-05 --stop
# re-show pcaps later: bash scripts/refresh-flow-dashboard.sh TC-05
# zero now without --stop: bash scripts/clear-flow-dashboard.sh
```

## Verify title in UI

1. Hard refresh: **Ctrl+Shift+R**
2. Open http://127.0.0.1:3000/d/ntn-roaming-overview — title must be
   **`00 — Roaming Overview (v11 panel-fix)`**
3. Open http://127.0.0.1:3000/d/ntn-5g-roaming-flow — title must be
   **`02 — 5G Roaming Flow (v11 panel-fix)`**
4. Overview domain row HOME/VISITED/IPX/RAN must match `/health` → `domains`
   (not all 0 when `observed` > 0).
5. Row **3GPP procedure success rates** must show % (or **PENDING — run refresh-flow-dashboard**)
   — **not** blank No data after reload.
6. `/health` prints `pcap_dir`, `tc_id`, `observed`, `coverage` — sync/refresh scripts
   echo these loudly.

Still stuck? Re-run `bash scripts/grafana-sync-live.sh TC-05` then hard-refresh again.
