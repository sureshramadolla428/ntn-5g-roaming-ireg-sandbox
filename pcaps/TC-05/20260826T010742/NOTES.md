# TC-05 capture 20260826T010742

- Host: sureshramadolla-virtual-machine
- Started: 2026-08-26T01:08:05-05:00
- Matrix: docs/ireg-tc-matrix.md
- Execution: docs/runbooks/ireg-tc-execution.md

## Architecture labels (fill after run)

- [x] B1 same-PLMN camp (001/01) — not true VPLMN 999/70
- [x] SEPP/N32: ABSENT — dual-home / SBI proxy stand-in (V14)
- [x] User plane: **HR 10.45** (UE `10.45.0.3`) — **not** LBO 10.46; caused by then-default `ROAMING_MODE=HR` + UPF still on 10.46 (ping fail). Fixed in lab configs 2026-08-26 — re-run TC-05 for LBO MEASURED
- [x] Result: **PARTIAL**
- [ ] MEASURED evidence files listed below (pcaps pending Windows rsync)

## Stop capture

```bash
bash scripts/capture-ireg-tc.sh TC-05 --stop
```
