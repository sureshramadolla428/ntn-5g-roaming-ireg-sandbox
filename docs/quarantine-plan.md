# Quarantine plan (recommendations only — nothing moved on Windows)

Per Phase -1 / 3A.4: **never delete** user reference trees. On Ubuntu after copying to `~/reference/`:

## Recommended REBUILDABLE candidates (user decides)

| Relative path under reference | Why REBUILDABLE | Approx reclaim |
|------------------------------|-----------------|----------------|
| `**/__pycache__/`, `.venv/`, `node_modules/` | regenerable | small–medium |
| Nested duplicate trees under `3GPP_RAG_SA_LAB/` that mirror siblings | duplicate of KEEP-CORE siblings | large (GBs) — **EXPENSIVE-REBUILD / UNCLEAR until user confirms** |
| Large evidence PCAPs if already archived elsewhere | regenerable from re-run | varies |

## EXPENSIVE-REBUILD (leave in place)

- Any future `openairinterface5g` `ran_build/` / `cmake_targets/`
- Docker image layers for OAI CN5G / Open5GS

## Procedure on Ubuntu (after user approval)

1. `chmod -R a-w ~/reference`
2. Move only approved REBUILDABLE items to `~/quarantine/` preserving relative paths
3. Run `~/quarantine/RESTORE.sh` to reverse

Sample RESTORE content: `scripts/ubuntu/RESTORE.sh.sample`
