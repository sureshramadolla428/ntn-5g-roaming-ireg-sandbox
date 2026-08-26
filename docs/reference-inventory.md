# Reference inventory (Phase -1)

**MEASURED** on Windows OneDrive workspace `MVNOs and MNOs` on 2026-08-21.
Nested duplicates under `3GPP_RAG_SA_LAB` are listed but **not** preferred as copy sources.

## Top-level folders

| path | apparent project | version/commit | size (approx) | last modified | build arts | git root | dirty | runnable as-is | phases | verdict |
|------|------------------|----------------|---------------|---------------|------------|----------|-------|----------------|--------|---------|
| `3GPP_RAG_SA_LAB/` | Aggregator / RAG + nested copies of NTN & Open5GS labs | mixed / nested | ~17 GB | MEASURED present | y (nested) | unknown (nested) | unknown | partial (docs/evidence) | KEEP-REFERENCE for RAG only; prefer siblings for copy | KEEP-REFERENCE |
| `5g-ntn-emulation-lab/` | NTN emulation lab (OAI configs, monitoring, netem) | OAI configs cite `2026.w16` / `38dc378` | ~3.4 GB | MEASURED | y (evidence pcaps/logs) | unknown | unknown | configs/docs yes; full OAI needs Ubuntu clone | 3, 11, 14 | KEEP-CORE |
| `URRANSIM_Open5gs/` | Open5GS + UERANSIM private-5g pack | Open5GS via herlesupreeth images; PLMN 999/70 | ~15 MB | MEASURED | n (compose stubs) | unknown | unknown | compose reusable after IP/PLMN adapt | 1, 9 | KEEP-CORE |

## OAI trees discovered

| location | NTN params in configs? | usable configs? | commit/branch evidence | notes |
|----------|------------------------|-----------------|------------------------|-------|
| Windows workspace | **No OAI source tree** (`openairinterface5g` / `cmake_targets` absent) | N/A | N/A | MEASURED |
| `5g-ntn-emulation-lab/oai-config/` | Yes — NTN LEO confs with `ntn_Config_r17`, SIB19 fields | Yes (configs + evidence) | Documented pin `38dc378` / tag `2026.w16` in `CONFIG_CHANGES.md` | Configs only |
| Nested under `3GPP_RAG_SA_LAB/.../oai-config/` | Duplicate of sibling | Yes | Same docs | Skip as copy source |
| Nested under `URRANSIM_Open5gs/5g-ntn-emulation-lab/` | Partial docs | Partial | Docs only | Prefer sibling NTN lab |
| Ubuntu VM `~/openairinterface5g` (historical) | Yes (per docs) | Yes when built | `38dc378` / `2026.w16` | SSH not used this session |

## Canonical OAI choice (best-evidence; user override 2026-08-21)

**Canonical for Ubuntu:** fresh clone of `openairinterface5g` at commit **`38dc378`** / tag **`2026.w16`**.

**Config source to copy into lab:** `5g-ntn-emulation-lab\oai-config\` (sibling), especially evidence LEO confs and `CONFIG_CHANGES.md`.

**Rationale:** No OAI source on Windows; documented verified LEO run uses that pin; sibling `oai-config` has NTN keys (`cellSpecificKoffset_r17`, `ta-Common-r17`, positions/velocities) MEASURED in evidence confs. Do **not** merge trees.

## Open5GS / UERANSIM

- Source: `URRANSIM_Open5gs/private-5g/` — compose + `configs/open5gs/{amf,smf,upf}.yaml` + `ue.yaml` / `gnb.yaml`.
- Existing PLMN **999/70** → adapt copies: HOME **001-01**, VISITED **999-70**.
- Lab SIM K/OPc from reference UE yaml (lab keys only).

## SEPP / N32

- Open5GS SEPP **absent** in reference compose (MEASURED). Phase 2 uses **SBI proxy stand-in** + divergence table; **not** named SEPP.

## Monitoring

- Prometheus/Grafana under `5g-ntn-emulation-lab/monitoring/` — KEEP-CORE for Phase 11 adaptation.

## Quarantine

No files moved on Windows. See `docs/quarantine-plan.md` and sample `RESTORE.sh` for Ubuntu later.
