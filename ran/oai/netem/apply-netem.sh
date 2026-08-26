#!/usr/bin/env bash
# Apply corrected B4 profiles. DEFERRED-TO-UBUNTU (requires tc).
set -euo pipefail
IFACE=${1:?iface}
PROFILE=${2:?profile}
case "$PROFILE" in
  terrestrial) tc qdisc del dev "$IFACE" root 2>/dev/null || true ;;
  leo-600) tc qdisc replace dev "$IFACE" root netem delay 13ms 4ms distribution normal ;;
  leo-1200) tc qdisc replace dev "$IFACE" root netem delay 21ms 5ms distribution normal ;;
  geo) tc qdisc replace dev "$IFACE" root netem delay 271ms 10ms distribution normal ;;
  *) echo "unknown profile"; exit 1 ;;
esac
tc qdisc show dev "$IFACE"
echo "Record MEASURED RTT with: ping -c 5 <peer>"
