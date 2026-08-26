#!/bin/bash
set -eo pipefail
sleep 5
cd /open5gs/webui
exec npm run dev "$@"
