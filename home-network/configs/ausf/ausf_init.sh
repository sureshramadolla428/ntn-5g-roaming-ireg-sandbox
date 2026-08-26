#!/bin/bash
# Lab init for herlesupreeth/docker_open5gs (BSD-2-Clause, adapted).
# Image entrypoint: /mnt/<nf>/${COMPONENT_NAME}_init.sh  WORKDIR=/open5gs
set -eo pipefail
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-/open5gs/install/lib/$(uname -m)-linux-gnu}"
mkdir -p /open5gs/install/var/log/open5gs

cp /mnt/ausf/ausf.yaml /open5gs/install/etc/open5gs/ausf.yaml
for tok in UE_IPV4_INTERNET_GW UPF_INTERNET_APN_IF_NAME UE_IPV4_INTERNET UPF_ADVERTISE_IP VISITED_NRF_IPX HOME_NRF_IPX NETWORK_NAME MAX_NUM_UE AUSF_IPX UDM_IPX UDR_IPX SCP_IPX NRF_IPX HOME_MCC HOME_MNC MONGO_IP WEBUI_IP SMF_DNS1 SMF_DNS2 NRF_IP SCP_IP AUSF_IP UDM_IP UDR_IP PCF_IP HSS_IP SMF_IP UPF_IP AMF_IPX AMF_IP NGAP_IP MCC MNC TAC; do
  eval "val=\${$tok-}"
  [ -n "$val" ] && sed -i "s|$tok|$val|g" /open5gs/install/etc/open5gs/ausf.yaml
done
cd /open5gs/install/bin
exec ./open5gs-ausfd "$@"
