# Cleanup candidates (user may delete later — NOT deleted by agent)

Per Phase -1d / 3A.4 the three reference trees are **left in place**. Optional reclaim on Ubuntu after copy:

| Path | Why candidate | Approx size | Risk |
|------|---------------|-------------|------|
| `3GPP_RAG_SA_LAB/` nested duplicates of NTN/Open5GS siblings | Duplicate of KEEP-CORE siblings | large share of ~17 GB | HIGH — confirm before quarantine |
| `5g-ntn-emulation-lab - Cursor/oai-config/evidence/` large pcaps/logs | Evidence archive; regenerable by re-run | portion of ~3.4 GB | MEDIUM — keep portfolio proof |
| `**/__pycache__`, `.venv`, `node_modules` under references | REBUILDABLE | small–medium | LOW |
| Nested `URRANSIM_Open5gs/5g-ntn-emulation-lab/` docs copy | Prefer sibling NTN lab | small | LOW |

**Do not delete** Open5GS/UERANSIM configs or `oai-config` NTN confs used by the portable lab.

Parent folder had **no** unrelated loose PDFs/notes outside the four project folders.
