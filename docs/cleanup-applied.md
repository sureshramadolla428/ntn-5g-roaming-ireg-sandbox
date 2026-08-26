# Cleanup applied — NTN roaming lab

## Policy

Per master prompt **3A.4**: reference trees are not **permanently deleted** by automation.
We **quarantine** (move to `~/quarantine/` with `RESTORE.sh`) or remove only **REBUILDABLE** caches.

## What the project requires (KEEP)

See **[`reference-keep-manifest.md`](reference-keep-manifest.md)**.

Minimum:
- `ntn-roaming-lab/` (writable lab)
- `URRANSIM_Open5gs/` (Open5GS/UERANSIM configs)
- `5g-ntn-emulation-lab - Cursor/oai-config/` + `monitoring/` (NTN + observability)

## Safe to quarantine (low risk)

| Target | Command |
|--------|---------|
| `__pycache__`, `.venv`, `node_modules` under reference | `bash scripts/quarantine-project-cruft.sh` |
| `ntn-roaming-lab/files.zip`, `files/` | same script |

## Optional large reclaim (~17 GB)

| Target | Command |
|--------|---------|
| Entire `3GPP_RAG_SA_LAB/` | `bash scripts/quarantine-project-cruft.sh --aggressive` |

**Lab does not depend on 3GPP_RAG_SA_LAB** — only on the two sibling folders above. Quarantine only after you confirm you do not need RAG/failtest portfolio on this machine.

## Ubuntu VM (after copy to ~/reference)

```bash
cd ~/ntn-roaming-lab
chmod +x scripts/*.sh
export PARENT=$HOME
export REFERENCE_ROOT=$HOME/reference
export QUARANTINE=$HOME/quarantine
bash scripts/quarantine-project-cruft.sh          # safe
# bash scripts/quarantine-project-cruft.sh --aggressive   # optional ~17GB
```

## Windows OneDrive

Prefer running quarantine **on Ubuntu** after sync. OneDrive moves of 17 GB are slow and can conflict.

If you must reclaim Windows disk: move `3GPP_RAG_SA_LAB` to an external drive manually — do not delete until Ubuntu lab is verified live.

## Open5GS / UERANSIM / OAI copies

| Copy type | Action |
|-----------|--------|
| Config packs (URRANSIM, oai-config) | **KEEP** |
| Full git/build trees | Not needed in reference; use Docker (Open5GS), build on VM (UERANSIM/OAI) |
| OAI on Ubuntu | Clone @ `38dc378` — do not rely on an unverified local OAI folder |
