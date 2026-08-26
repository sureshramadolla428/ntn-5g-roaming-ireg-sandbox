# LTE EPC deferred path (TC-01 / TC-02)

**Status:** DEFERRED-TO-UBUNTU — not built in this phase.

## Present today

| Component | IP | Notes |
|-----------|-----|--------|
| home-hss | 10.10.1.14:3868 | Diameter; S6a target when MME exists |
| ipx-dra | 10.10.3.10 | Diameter routing between PLMNs |
| LAB-IREG-003/005 | offline | RFC 6733 success code 2001 only — not live attach |

## Missing for TC-01/02

| Component | Planned IP (`network-plan.yaml`) | Blocker |
|-----------|----------------------------------|---------|
| visited-mme | 10.10.2.14 (SCTP 36412) | No `visited-network/configs/mme/` compose service |
| visited-sgwc | 10.10.2.15 | Not in docker-compose |
| visited-sgwu | 10.10.2.16 | Not in docker-compose |
| LTE UE / srsRAN | — | Lab RAN is 5G UERANSIM only |

## Next steps (Ubuntu, when prioritised)

1. Copy Open5GS MME/SGW configs from reference (`URRANSIM_Open5gs`) with provenance header.
2. Add services to `visited-network/docker-compose.yml` (or overlay `docker-compose.lte-epc.yml`).
3. Wire S6a: visited-mme → ipx-dra → home-hss.
4. `bash scripts/capture-ireg-tc.sh TC-01` + LTE attach recipe.

## Runnable offline today

```bash
bash scripts/run-tc-01-lte-deferred.sh
# or: pytest -k 'LAB-IREG-003 or LAB-IREG-005'
```

Do **not** claim TC-01/02 MEASURED until live S6a pcap exists.
