# Home Open5GS NF configs — PLMN 001-01

`ghcr.io/herlesupreeth/docker_open5gs` entrypoint (`open5gs_init.sh`) runs:

`/mnt/<nf>/${COMPONENT_NAME}_init.sh`

Each directory must contain both `<nf>.yaml` and `<nf>_init.sh` (plus `webui/webui_init.sh`).
Placeholders (`NRF_IP`, `MCC`, …) are substituted from `home-network/.env`.

| Dir | Role | IP (network-plan) |
|-----|------|-------------------|
| nrf/ | NRF | 10.10.1.10 (+ IPX 10.10.3.20) |
| ausf/ | AUSF | 10.10.1.11 (+ IPX 10.10.3.21; NRF client = visited via IPX) |
| udm/ | UDM | 10.10.1.12 (+ IPX 10.10.3.22; NRF client = visited via IPX) |
| udr/ | UDR | 10.10.1.13 (+ IPX 10.10.3.24; NRF client = visited via IPX) |
| hss/ | HSS (Diameter S6a; uses image freeDiameter conf) | 10.10.1.14 |
| pcf/ | PCF | 10.10.1.15 |
| scp/ | SCP | 10.10.1.21 (+ IPX 10.10.3.23) |
| smf/ | Home-routed SMF | 10.10.1.23 |
| upf/ | Home-routed UPF | 10.10.1.24 |
| webui/ | WebUI init only | 10.10.1.22 |

Subscribers: `../subscribers/provision.json` IMSI `001010000000001`–`020`.
Visited PLMN remains **999-70**.

**Ubuntu:** `chmod +x configs/*/*_init.sh` (Windows shares drop +x). After `make up-home`, provision Mongo via `scripts/provision_subscribers.py`.
