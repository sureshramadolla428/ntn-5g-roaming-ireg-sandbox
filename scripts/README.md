# Scripts (private)

Operational bring-up, IREG TC runners, capture helpers, and Grafana sync scripts for **ntn-5g-roaming-ireg-sandbox** are **not published** in this public repository.

They live in the private companion:

→ **https://github.com/sureshramadolla428/ntn-5g-roaming-ireg-sandbox-scripts**

Local lab clones keep a full `scripts/` tree on disk (gitignored). Key JD helpers expected locally / in the private repo:

- `run-jd-five-tcs.sh` — TC-05 → TC-11 → TC-04 → TC-07 → TC-21 with LBO / PFCP / `domains.ran` gates
- `run-tc-05-golden.sh`, `run-tc-11-userplane.sh`, `run-tc-04-sqn-resync.sh`, `run-tc-07-mock-sgd.sh`, `run-tc-21-ntn-netem.sh`
- `capture-ireg-tc.sh`, `refresh-flow-dashboard.sh` (`chmod a+rX` + exporter reload)

Available to reviewers **on request**. Do not commit `.env`, real operator keys, or production credentials into either repo.
