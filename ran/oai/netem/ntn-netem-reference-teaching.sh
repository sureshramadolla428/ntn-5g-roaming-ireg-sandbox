# PROVENANCE: 5g-ntn-emulation-lab/emulation/ntn-netem.sh
# WARNING: teaching values (leo 25ms) differ from corrected B4 (leo-600=13ms).
# Prefer apply-netem.sh / profiles-b4.yaml for this lab.
#!/usr/bin/env bash
# ntn-netem.sh - apply / clear NTN (satellite) link conditions with tc netem.
#
# Emulates the satellite hop by shaping an interface on the path between the
# gNB (UERANSIM) and the Open5GS core (or the UE's data interface). This does
# NOT implement the NTN air interface - it reproduces the LINK EFFECTS
# (propagation delay, jitter, loss, bandwidth) so you can study how a 5G SA core
# and apps behave under LEO/MEO/GEO latency.
#
# Usage:
#   sudo ./ntn-netem.sh <iface> <terrestrial|leo|meo|geo>   # apply a profile
#   sudo ./ntn-netem.sh <iface> clear                       # remove shaping
#   sudo ./ntn-netem.sh <iface> show                        # show current qdisc
#
# NOTE ON NUMBERS: values below are ILLUSTRATIVE, representative teaching figures
# (one-way delay ~ RTT/2). Real values vary by constellation, altitude, elevation
# angle and payload type - verify against a primary source before quoting them.
# netem 'delay' here is ONE-WAY on this interface; the round-trip is ~2x if the
# reverse path is shaped too, so apply on both ends (or on the bottleneck) for a
# full RTT.

set -euo pipefail
IFACE="${1:-}"; PROFILE="${2:-}"
[ -z "$IFACE" ] || [ -z "$PROFILE" ] && { grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

apply() { # oneway_ms jitter_ms loss_% rate_mbit
  tc qdisc del dev "$IFACE" root 2>/dev/null || true
  tc qdisc add dev "$IFACE" root netem delay "${1}ms" "${2}ms" distribution normal \
     loss "${3}%" rate "${4}mbit"
  echo "applied '$PROFILE' on $IFACE: one-way ${1}ms (+/-${2}ms), loss ${3}%, rate ${4}Mbit"
  echo "  (approx RTT if reverse path also shaped: ~$(( ${1} * 2 )) ms)"
}

case "$PROFILE" in
  terrestrial) apply 10  2  0.1 50 ;;   # ~20 ms RTT
  leo)         apply 25  8  0.8 30 ;;   # ~50 ms RTT, higher jitter/loss
  meo)         apply 70  12 1.0 20 ;;   # ~140 ms RTT
  geo)         apply 270 20 1.5 12 ;;   # ~540 ms RTT (GEO)
  clear)       tc qdisc del dev "$IFACE" root 2>/dev/null || true; echo "cleared shaping on $IFACE" ;;
  show)        tc qdisc show dev "$IFACE" ;;
  *)           echo "unknown profile '$PROFILE' (use terrestrial|leo|meo|geo|clear|show)"; exit 1 ;;
esac
