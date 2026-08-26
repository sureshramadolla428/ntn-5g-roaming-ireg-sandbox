# Runbook — Home + Visited bring-up

## Preconditions (Ubuntu)

- `modprobe sctp && echo sctp | tee /etc/modules-load.d/sctp.conf && lsmod | grep sctp`
- `make check-network` PASS
- Docker networks created: `bash scripts/create_docker_networks.sh` (domain compose uses `external: true`)

## Steps

```bash
# Preferred one-shot after sync + CRLF fix:
bash scripts/vm-bringup.sh --aggressive

# Or stepwise:
bash scripts/create_docker_networks.sh
make up-home
make up-visited
make up-ipx
sudo bash scripts/enforce-ipx-routing.sh
make provision-subscribers
```

## PASS criteria

- `docker ps` shows home-* and visited-* healthy
- Visited AMF listening SCTP 38412 on 10.10.2.11
- LAB-IREG-000 live probe fails for direct path
- UERANSIM UE home IMSI registers via visited gNB (LAB-IREG-001) — DEFERRED-TO-UBUNTU

## Verify commands

```bash
docker logs visited-amf 2>&1 | grep -i guami
docker exec visited-amf ss -Sln | grep 38412 || true
```
