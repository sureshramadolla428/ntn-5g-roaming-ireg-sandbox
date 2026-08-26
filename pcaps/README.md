# PCAPs — capture layout (no invented binaries)

This lab does **not** ship fabricated `.pcap` / `.pcapng` files.

## When captures are produced

Real captures are generated on **Ubuntu 22.04** after the stack is up:

```bash
# Example multi-point capture (see docs/call-flows/multi-point-capture.md)
sudo tcpdump -i <visited-edge-if> -w pcaps/LAB-IREG-001/$(date +%Y%m%dT%H%M%S)/visited-edge.pcap
sudo tcpdump -i <ipx-if>          -w pcaps/LAB-IREG-001/$(date +%Y%m%dT%H%M%S)/ipx.pcap
sudo tcpdump -i <home-edge-if>    -w pcaps/LAB-IREG-001/$(date +%Y%m%dT%H%M%S)/home-edge.pcap
```

Windows scaffolding cannot produce SCTP/NGAP/Diameter MEASURED results. Any report
number from a pcap must be labelled **MEASURED** only after these files exist.

## Directory layout

```
pcaps/
  README.md                          # this file
  TC-XX/                             # interview suite (preferred)
    <timestamp>/
      ran-net.pcap | visited-net.pcap | home-net.pcap | ipx-net.pcap
      docker-logs/
      NOTES.md
  LAB-IREG-XXX/                      # legacy harness ids (live-first-attach.sh)
    <timestamp>/
      multi-point.pcap | nr-ue.log | …
```

Interview capture helper: `bash scripts/capture-ireg-tc.sh TC-05` (see `docs/runbooks/ireg-tc-execution.md`).

Placeholder directories under `LAB-IREG-000/` exist for layout only — they contain no packet data.

## Policy

- Do not commit empty dummy binary pcaps.
- Controlled-failure captures belong alongside success captures for the same LAB-IREG id.
- Link pcaps from the phase runbook and IMSI-trace export when available.
