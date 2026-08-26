# 10-minute demo script

1. `make check-network` → PASS
2. Show mermaid in `docs/network-plan.md`
3. Run Tier-1 unit subset: `make test-fast`
4. Inject IPX fault: `curl -X PUT localhost:8080/fault -d '{"fault":"drop_request"}'`
5. Show `fault_domain()` INDETERMINATE vs IPX with incomplete vs complete evidence
6. Open Streamlit dashboard (C8/D4 tooltips)
7. State limitations from README / limitations.md
