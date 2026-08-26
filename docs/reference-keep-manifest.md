# Reference keep manifest — NTN roaming lab

What this project **actually uses**. Everything else is optional for quarantine (not deletion).

## REQUIRED (do not remove)

| Path | Why | Already copied into lab? |
|------|-----|------------------------|
| **`ntn-roaming-lab/`** | Writable lab repo — all phases live here | N/A (this IS the project) |
| **`URRANSIM_Open5gs/`** | Open5GS + UERANSIM compose/YAML, PLMN/subscriber patterns | Yes — `home-network/`, `visited-network/`, `ran/ueransim/` |
| **`5g-ntn-emulation-lab - Cursor/oai-config/`** | NTN LEO/GEO confs, `CONFIG_CHANGES.md`, OAI pin `38dc378` | Yes — `ran/oai/configs/` |
| **`5g-ntn-emulation-lab - Cursor/monitoring/`** | Prometheus/Grafana templates (Phase 11) | Partial — adapt as needed |

## NOT needed in reference (lab replaces or clones fresh)

| Item | Lab alternative |
|------|-----------------|
| Full **Open5GS source tree** | Docker image `ghcr.io/herlesupreeth/docker_open5gs:master` |
| Full **UERANSIM source tree** in reference | Build once on Ubuntu; configs in `ntn-roaming-lab/ran/ueransim/` |
| **OAI source** in Windows/OneDrive | Fresh clone on Ubuntu: `openairinterface5g` @ **`38dc378` / `2026.w16`** |
| Nested duplicate copies | Use sibling paths only |

## OPTIONAL quarantine (large — your choice)

| Path | Approx size | Risk if removed |
|------|-------------|-----------------|
| **`3GPP_RAG_SA_LAB/`** (entire folder) | ~17 GB | Lose RAG/failtest portfolio; **lab does not require it** |
| `5g-ntn-emulation-lab - Cursor/oai-config/evidence/` | portion of ~3 GB | Lose archived pcaps/logs; configs remain |
| Nested `3GPP_RAG_SA_LAB/**/5g-ntn-emulation-lab*` | duplicate | None if sibling NTN lab kept |
| Nested `3GPP_RAG_SA_LAB/**/URRANSIM*` / `github-ueransim*` | duplicate | None if sibling kept |
| `**/__pycache__`, `.venv`, `node_modules` | small–medium | Regenerable |

## Minimal reference layout (recommended on Ubuntu)

After cleanup, `~/reference/` can be:

```
~/reference/
  URRANSIM_Open5gs/
  5g-ntn-emulation-lab/          # renamed from "5g-ntn-emulation-lab - Cursor"
```

Optional: keep slim `3GPP_RAG_SA_LAB/3GPP_Spec_Test/` only if you still use RAG — otherwise quarantine whole folder.

## Open5GS / UERANSIM / OAI copies you mentioned

| Component | Keep in reference? | Use in lab |
|-----------|-------------------|------------|
| Open5GS configs (compose/YAML) | **Yes** — `URRANSIM_Open5gs` | Copied + adapted in `ntn-roaming-lab` |
| Open5GS git source | **No** (unless you patch core) | Docker image |
| UERANSIM configs | **Yes** — in lab `ran/ueransim/` | Live attach on VM |
| UERANSIM build tree | On Ubuntu VM only, not OneDrive | `UERANSIM_BIN` for scripts |
| NTN configs | **Yes** — `oai-config/` | `ran/oai/` |
| OAI git + build | Ubuntu `~/openairinterface5g` @ pin | Tier-2 NTN tests |

**Do not delete originals on OneDrive until Ubuntu lab is live and verified.**
