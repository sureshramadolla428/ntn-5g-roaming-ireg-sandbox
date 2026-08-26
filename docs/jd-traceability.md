# JD traceability (lab ↔ role requirements)

| Req | Summary | Phases | Artifacts |
|-----|---------|--------|-----------|
| R1 | Multi-PLMN roaming topology Home/Visited/IPX | 0,1,2 | `home-network/`, `visited-network/`, `ipx/` |
| R2 | E2E roaming: reg, auth, SMS, NIDD | 1,2,5,6,9 | `harness/testcases/LAB-IREG-*` |
| R3 | NTN direct-to-device timing/channel emulation | 3,14 | `ran/oai/`, netem B4 profiles |
| R4 | IR.21 / partner profile exchange | 7 | `ir21/` |
| R5 | Diameter/SS7 fault domain isolation | 2,4,9,13 | `fault_domain.py`, multi-point capture |
| R6 | Automated IREG-style suite + CI | 9,10 | pytest + `ci/` |
| R7 | Portfolio metrics | 11 | `dashboard/`, C8/C9/D3/D4 |
| R8 | Cross-functional billing/signalling | 8,11,12 | billing mock + docs |
| R9 | IMSI trace / defect workflow | 13 | `imsi-trace/`, Jira CSV |
