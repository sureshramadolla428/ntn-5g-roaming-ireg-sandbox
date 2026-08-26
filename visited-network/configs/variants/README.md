# HR / LBO SMF subnet variants
#
# MOCK policy note: Open5GS roaming HR/LBO must be verified on the installed image.
# Production equivalent: home-routed vs local-breakout PDU per TS 23.501 / 23.502.
#
# Wiring honesty (updated 2026-08-26):
# - Runtime configs use placeholders in smf.yaml / upf.yaml:
#     smf.session: [{ subnet, gateway, dnn }]
#     upf.session: [{ subnet, gateway, dnn }]
#   (keys from lab copies under visited-network/configs/{smf,upf}/ — not invented.)
# - smf_init.sh + upf_init.sh read ROAMING_MODE (HR|LBO) and set UE_IPV4_INTERNET*
#   before sed. Both NFs must share the same mode or UE IP vs ogstun GW diverge.
# - Default compose + .env: ROAMING_MODE=LBO → 10.46 pool (TC-05 golden).
# - TC-15: ROAMING_MODE=HR → 10.45 on visited-smf AND visited-upf (lab stand-in).
# - smf-hr.yaml / smf-lbo.yaml below use alternate `smf.subnet.addr` shape for
#   reference only — init does NOT merge these files; pool comes from env sed.
# - Full HR user plane (N9/home UPF) still PARTIAL — see TC-15 runbook.
#
# See docs/ireg-tc-matrix.md TC-15 and docs/runbooks/ireg-tc-execution.md §5.
