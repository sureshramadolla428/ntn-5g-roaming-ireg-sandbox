# Ubuntu 22.04 bootstrap

## 1. Copy lab

```bash
# From Windows share / scp / usb
mkdir -p ~/ntn-roaming-lab
# copy contents of ntn-roaming-lab → ~/ntn-roaming-lab
cd ~/ntn-roaming-lab
```

## 2. Copy references (read-only)

```bash
mkdir -p ~/reference
cp -a "/path/to/URRANSIM_Open5gs" ~/reference/
cp -a "/path/to/5g-ntn-emulation-lab" ~/reference/5g-ntn-emulation-lab
cp -a "/path/to/3GPP_RAG_SA_LAB" ~/reference/   # optional RAG
chmod -R a-w ~/reference
```

Do **not** delete OneDrive originals. Quarantine only under `~/quarantine` after user approval — see `docs/quarantine-plan.md`.

## 3. Packages

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 python3-venv python3-pip \
  iproute2 iptables lksctp-tools jq tcpdump make git
sudo modprobe sctp
echo sctp | sudo tee /etc/modules-load.d/sctp.conf
lsmod | grep sctp   # PASS: sctp listed
```

## 4. OAI clone (canonical)

```bash
git clone https://gitlab.eurecom.fr/oai/openairinterface5g.git ~/openairinterface5g
cd ~/openairinterface5g
git checkout 38dc378   # tag 2026.w16 family per CONFIG_CHANGES.md
# build per OAI docs: ./build_oai -w SIMU --ninja --nrUE --gNB
# overlay configs from ~/ntn-roaming-lab/ran/oai/configs/
```

## 5. Python venv

```bash
cd ~/ntn-roaming-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 6. Sync from Windows + live stacks (VM)

Windows copies often have CRLF. Reference trees are `chmod a-w`. Do this in order:

```bash
# Mount share if needed
sudo mkdir -p /mnt/hgfs
sudo vmhgfs-fuse .host:/ /mnt/hgfs -o allow_other

cd ~/ntn-roaming-lab
source .venv/bin/activate

rsync -av --exclude '.venv' --exclude '__pycache__' --exclude '.git' \
  /mnt/hgfs/MVNOs_and_MNOs/ntn-roaming-lab/ ~/ntn-roaming-lab/

# Python fixer works even if .sh files still have CRLF
python3 scripts/fix_crlf.py
chmod +x scripts/*.sh

# One-shot: quarantine + docker up + verify + provision
# Add --aggressive to move ~/reference/3GPP_RAG_SA_LAB into ~/quarantine
bash scripts/vm-bringup.sh --aggressive
```

If `docker info` fails after adding your user to the docker group, **do not** paste `newgrp docker` followed by more commands — `newgrp` opens a subshell and **swallows the rest of the paste** (old containers without dual-home stay running). Use a single `sg docker -c '...'` with **bash** inside — `sg` runs `/bin/sh` (dash), which has no `source` and will fail with `source: not found` if you put bare `source .venv/...` in the `-c` string:

```bash
sg docker -c 'cd ~/ntn-roaming-lab && bash scripts/ubuntu-sg-bootstrap.sh'
# or inline (bash -lc wraps source):
sg docker -c "bash -lc 'cd ~/ntn-roaming-lab && source .venv/bin/activate && make bootstrap-docker && make provision-subscribers && make verify-live'"
```

Or logout/login after `sudo usermod -aG docker $USER`, then run `make bootstrap-docker` normally.

## 7. First tests

```bash
make test-fast
make signoff-check
# Live: NTN_LIVE_NET=1 pytest -k LAB-IREG-000
```

## DEFERRED-TO-UBUNTU checklist

- [ ] Sync from Windows (`rsync` or `bash scripts/sync-from-share.sh`) then `python3 scripts/fix_crlf.py`
- [ ] Live stacks Up (`bash scripts/vm-bringup.sh --aggressive`)
- [ ] Subscriber Mongo provision (included in vm-bringup; re-run `make provision-subscribers` if needed)
- [ ] SCTP AMF attach (LAB-IREG-001/002) + pcap
- [ ] freeDiameter DRA relay (build `ipx/freediameter` image; peer HSS)
- [ ] OAI NTN LEO attach + MEASURED ping RTT (LAB-IREG-024/025)
- [ ] iptables LAB-IREG-000 live (`NTN_LIVE_NET=1`)
- [ ] multi-point pcaps under `pcaps/LAB-IREG-*/<ts>/`
- [ ] Osmocom STP/HLR/MSC cfg syntax vs installed packages

See **[`docs/phase-status-and-next-steps.md`](phase-status-and-next-steps.md)** for full narrative.

## Next VM block (copy-paste after Windows sync)

AMF/UPF need the SCTP kernel module. After OneDrive/rsync of these lab fixes:

```bash
# 1) SCTP (persist across reboot)
sudo modprobe sctp
echo sctp | sudo tee /etc/modules-load.d/sctp.conf
lsmod | grep sctp

# 2) Sync this Windows tree, strip CRLF
sudo mkdir -p /mnt/hgfs
sudo vmhgfs-fuse .host:/ /mnt/hgfs -o allow_other || true
bash ~/ntn-roaming-lab/scripts/sync-from-share.sh
# (or rsync manually — sync-from-share also runs fix_crlf + chmod)

# 3) ONE line — sg + bash (not newgrp; not bare source in sg -c). Force-recreates dual-home IPX + provision + verify
sg docker -c 'cd ~/ntn-roaming-lab && bash scripts/ubuntu-sg-bootstrap.sh'

# 4) Confirm dual-home IPs (expect ntn-ipx-net=10.10.3.20/.21/.22/.23/.24 and .30/.31/.32)
docker inspect -f '{{.Name}} {{range $k,$v := .NetworkSettings.Networks}}{{$k}}={{$v.IPAddress}} {{end}}' \
  home-nrf home-ausf home-udm home-udr home-scp visited-nrf visited-amf visited-scp

# 5) Live attach
cd ~/ntn-roaming-lab && source .venv/bin/activate
export UERANSIM_BIN=~/UERANSIM/build
bash scripts/live-first-attach.sh
```

Live attach is still pending until `docker ps` shows home-nrf, home-udm, visited-amf, visited-smf, ipx-dra **Up** **and** the inspect above shows the IPX addresses.

