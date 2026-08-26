# Cleanup log (safe cleanup performed 2026-08-21)

## Parent `MVNOs and MNOs`

Top-level contents MEASURED:
- `3GPP_RAG_SA_LAB` — **PRESERVED** (reference; deletion forbidden)
- `5g-ntn-emulation-lab - Cursor` — **PRESERVED** (reference; deletion forbidden)
- `URRANSIM_Open5gs` — **PRESERVED** (reference; deletion forbidden)
- `ntn-roaming-lab` — lab deliverable

**Deleted at parent level:** none (no unrelated loose files/folders present).

## Inside `ntn-roaming-lab`

Deleted accidental temp/generator artifacts:- `_gen_p01.py`
- `_gen_p0.py`
- `_gen_p1.py`
- `_gen_p23.py`
- `_gen_p48.py`
- `_gen_p9.py`
- `_gen_rest.py`
- `_fix_tests.py`
- `_master_prompt_extract.txt`

Also removed `__pycache__` / `.pytest_cache` if present.
Kept: all phase deliverables, `.venv` is gitignored (not deleted so local unit tests remain usable).
