#!/usr/bin/env bash
# Staged OAI NTN start — DEFERRED-TO-UBUNTU
# Requires: ~/openairinterface5g @ 38dc378 / 2026.w16
set -euo pipefail
OAI_ROOT=${OAI_ROOT:-$HOME/openairinterface5g}
CONF_GNB=${CONF_GNB:-$PWD/ran/oai/configs/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf}
CONF_UE=${CONF_UE:-$PWD/ran/oai/configs/nrue.uicc.ntn-leo.conf}
echo "[1/4] visited core up?"
echo "[2/4] start gNB rfsim"
echo "  sudo \$OAI_ROOT/ran_build/build/nr-softmodem -O \$CONF_GNB --rfsim"
echo "[3/4] start UE"
echo "  sudo \$OAI_ROOT/ran_build/build/nr-uesoftmodem -O \$CONF_UE --rfsim ..."
echo "[4/4] ping + capture"
echo "PASS: oaitun_ue1 up; ping DN; NGSetup+Registration in logs"
