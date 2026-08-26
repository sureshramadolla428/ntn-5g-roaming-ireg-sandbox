# Status: done vs pending (post scaffold-gap-close-1)

Honest status after the Windows gap-close pass. No live attach or MEASURED pcaps claimed.

## Done (scaffold / offline)

| Area | Status |
|------|--------|
| `MASTER_PROMPT.md` | Present (~117 KB) |
| `.cursor/rules/` accuracy, file-safety, execution | Present |
| Phase 0 network-plan + check-network | Present |
| Phase 1 home Open5GS NF YAMLs (001-01) + compose mounts | Present |
| Phase 1 visited configs (999-70) | Present |
| Phase 2 freeDiameter templates + Dockerfile + SBI proxy + fault API | Present (DRA runtime = Ubuntu) |
| Phase 4 Osmocom minimal cfg templates (UNVERIFIED syntax) | Present |
| Phase 9 offline unit / mocked LAB-IREG cases | Expanded |
| PLMN BCD C1, Diameter registry, fault_domain, IR.21, billing, SCEF | Unit-tested |
| `pcaps/README.md` + placeholder dirs | No fake binaries |
| Makefile: signoff-check, flake-check, test-ntn, report | Present |
| Docs: CHANGELOG, defect-log, this status | Updated |

## DEFERRED-TO-UBUNTU (true live / MEASURED)

| Item | Reason |
|------|--------|
| LAB-IREG-001 / 002 registration | Live UE attach |
| LAB-IREG-006 / 007 PDU | Live N4/N3 session |
| LAB-IREG-017 / 018 SMS | Live SGd/MAP |
| LAB-IREG-024 / 025 NTN | OAI + netem MEASURED RTT |
| LAB-IREG-000 live probe | iptables/docker namespace |
| freeDiameterd peer bring-up | Needs Linux image build + SCTP |
| Osmocom STP/HLR/MSC runtime | Config syntax unverified vs package |
| Subscriber Mongo provision + attach | Script ready; runtime Ubuntu |
| Real pcaps under `pcaps/LAB-IREG-*` | Produced on Ubuntu only |
| MEASURED KPI numbers in reports | Require pcaps/logs |

## First Ubuntu commands

```bash
cd ~/ntn-roaming-lab
# follow docs/runbooks/ubuntu-bootstrap.md
make check-network
make up-home
```
