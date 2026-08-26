# ---------------------------------------------------------------------------
# PROVENANCE: copied from 5g-ntn-emulation-lab/oai-config/...
# Adaptation date: 2026-08-21 | Lab: ntn-roaming-lab
# Canonical OAI source on Ubuntu: openairinterface5g @ 38dc378 / 2026.w16
# ---------------------------------------------------------------------------
# OAI LEO config changes (reproducible record)

The live OAI build, config files, and logs live on the Ubuntu VM under `~/openairinterface5g`
(they are NOT in this folder). This file records the exact edits applied so the verified LEO run
can be reproduced from scratch, plus how to pull the real artifacts off the VM for evidence.

## Base
- OAI tag **2026.w16** (commit `38dc378224`), built with `./build_oai -w SIMU --ninja --nrUE --gNB`.
- NTN GEO patch applied: `ntn-geo.patch` (from ngkore/OAI-5G-NR-NTN).
- Core: OAI CN5G (docker-compose), PLMN 001/01.

## Edit 1 — LEO gNB conf
File: `ci-scripts/conf_files/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf`
Stock LEO conf targeted a different core (PLMN 208/99, net 192.168.71.x). Re-pointed to CN5G:

```
# PLMN:  mcc = 208; mnc = 99;   ->  mcc = 001; mnc = 01;
# amf_ip_address ipv4:  192.168.71.132  ->  192.168.70.132
# GNB_IPV4_ADDRESS_FOR_NG_AMF / NGU:  192.168.71.140/26  ->  192.168.70.129/26
```
Applied with:
```bash
G=~/openairinterface5g/ci-scripts/conf_files/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf
sed -i 's/mcc = 208; mnc = 99;/mcc = 001; mnc = 01;/' "$G"
sed -i 's#192.168.71.132#192.168.70.132#' "$G"
sed -i 's#192.168.71.140/26#192.168.70.129/26#g' "$G"
```

## Edit 2 — LEO UE conf
File: `ci-scripts/conf_files/nrue.uicc.ntn-leo.conf`
Key/OPc already matched the CN5G test SIM; only the IMSI belonged to the wrong PLMN:
```
# imsi = "208990100001100"  ->  "001010000000001"
```
Applied with:
```bash
U=~/openairinterface5g/ci-scripts/conf_files/nrue.uicc.ntn-leo.conf
sed -i 's/208990100001100/001010000000001/' "$U"
```

## Run
```bash
# gNB
sudo ./ran_build/build/nr-softmodem -O ../ci-scripts/conf_files/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf --rfsim
# UE
sudo ./ran_build/build/nr-uesoftmodem -O ../ci-scripts/conf_files/nrue.uicc.ntn-leo.conf \
  --band 254 -C 2488400000 --CO -873500000 -r 25 --numerology 0 --ssb 60 \
  --rfsim --rfsimulator.[0].prop_delay 20 --rfsimulator.[0].options chanmod \
  --time-sync-I 0.1 --ntn-initial-time-drift -46 --initial-fo 57340 --cont-fo-comp 2
# data test
ping -I oaitun_ue1 192.168.70.135
```

## Pull the real evidence off the VM (recommended)
On the VM, capture logs and copy the actual edited configs into a folder you can move here:
```bash
mkdir -p ~/leo-evidence
# re-run capturing logs:
#   ... nr-softmodem ...   2>&1 | tee ~/leo-evidence/gnb.log
#   ... nr-uesoftmodem ... 2>&1 | tee ~/leo-evidence/ue.log
#   ping -I oaitun_ue1 -c 20 192.168.70.135 | tee ~/leo-evidence/ping.txt
cp ~/openairinterface5g/ci-scripts/conf_files/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf ~/leo-evidence/
cp ~/openairinterface5g/ci-scripts/conf_files/nrue.uicc.ntn-leo.conf ~/leo-evidence/
```
Then copy `~/leo-evidence/` into this `oai-config/` folder (via shared folder, scp, or the VMware
shared clipboard) so the project contains the real logs + configs, not just this record.
Also drop the ping screenshot into `../docs/`.
