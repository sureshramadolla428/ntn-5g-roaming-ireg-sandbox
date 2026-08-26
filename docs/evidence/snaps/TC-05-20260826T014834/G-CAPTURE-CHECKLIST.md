# Grafana panel capture checklist — same run `20260826T014834`

After Ubuntu refresh pointed at **this** capture only:

```bash
PCAP_DIR=~/ntn-roaming-lab/pcaps/LAB-IREG-001/20260826T014834 \
  bash scripts/refresh-flow-dashboard.sh TC-05
curl -s http://127.0.0.1:8010/health | jq '{pcap_dir, domains, observed, coverage}'
# REQUIRE: .domains.ran > 0 and pcap_dir ends with 20260826T014834
```

Save PNGs into this folder (one each, no duplicates):

| File | Dashboard | Panel |
|------|-----------|-------|
| `G1-overview-domains.png` | ntn-roaming-overview | HOME/VISITED/IPX/RAN tiles |
| `G2-overview-success-rates.png` | ntn-roaming-overview | Procedure success rates |
| `G3-overview-coverage.png` | ntn-roaming-overview | Observed/expected coverage |
| `G4-overview-completeness.png` | ntn-roaming-overview | Flow completeness debug |
| `G5-flow-ladder.png` | ntn-5g-roaming-flow | Call-flow ladder |
| `G6-flow-phases.png` | ntn-5g-roaming-flow | AUTH/REG/PDU phases |
| `G7-flow-steps.png` | ntn-5g-roaming-flow | Signalling steps table |

Until PNGs exist, cite `G-health-offline.json` for domain/RAN numbers (same PCAP_DIR).
