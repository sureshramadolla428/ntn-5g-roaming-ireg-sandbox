#!/bin/bash
# Lab init for herlesupreeth/docker_open5gs (BSD-2-Clause, adapted).
# Image entrypoint: /mnt/<nf>/${COMPONENT_NAME}_init.sh  WORKDIR=/open5gs
set -eo pipefail
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-/open5gs/install/lib/$(uname -m)-linux-gnu}"
mkdir -p /open5gs/install/var/log/open5gs

sleep 5
cp /mnt/hss/hss.yaml /open5gs/install/etc/open5gs/hss.yaml
for tok in HSS_IP MONGO_IP MAX_NUM_UE; do
  eval "val=\${$tok-}"
  [ -n "$val" ] && sed -i "s|$tok|$val|g" /open5gs/install/etc/open5gs/hss.yaml
done
# Keep image-packaged freeDiameter hss.conf (do not overlay /etc/freeDiameter).
cd /open5gs/install/bin
exec ./open5gs-hssd "$@"
