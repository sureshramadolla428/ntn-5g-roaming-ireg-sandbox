# Defect log

| ID | Summary | Domain | Status | Guarding test |
|----|---------|--------|--------|---------------|
| DEF-0001 | Direct home↔visited path possible without iptables | IPX/topo | open (live Ubuntu) | LAB-IREG-000 |
| DEF-0002 | Home Open5GS NF YAML configs missing (compose only) | HOME | **closed** scaffold-gap-close-1 | LAB-IREG-000 config assert |
| DEF-0003 | IPX DRA container was `sleep infinity` | IPX | **closed** (runtime Ubuntu) | LAB-IREG-008 |
| DEF-0004 | Osmocom cfg files were comment stubs | SS7 | **closed** (syntax UNVERIFIED) | Phase 4 templates |
| DEF-0005 | Most LAB-IREG cases skip-only with no offline assert | Harness | **closed** partial | offline tier1 suite |
| DEF-0006 | Fake/missing pcap policy unclear | Evidence | **closed** (README, no binaries) | pcaps/README.md |
| DEF-0007 | Experimental Diameter codes must not be VERIFIED oracles | Auth | open (documented) | test_diameter_codes / require_verified |
| DEF-0008 | Open5GS SEPP absent — risk of misnaming SBI proxy | SBI | mitigated | LAB-IREG-010 + n32 table |
| DEF-0009 | docker_open5gs NFs exited immediately: missing `/mnt/<nf>/<nf>_init.sh` (image entrypoint) | HOME/VISITED | **closed** (lab mounts+init) | live `docker ps` / diagnose-exited.sh |
| DEF-0010 | ipx-dra bind-mounted tree over `/etc/freeDiameter` (ro) so template→dra.conf copy failed | IPX | **closed** (image COPY templates) | ipx-dra Up |
| DEF-0011 | Visited AMF cannot discover/reach home AUSF (PAYLOAD_NOT_FORWARDED after NG Setup) | SBI/roaming | mitigated (home AUSF/UDM/UDR register to visited NRF via IPX; SEPP still absent) | LAB-IREG-001 Ubuntu traces |
| DEF-0012 | Dual `sbi.client.nrf` URIs → Open5GS restart loop (`Only one NRF client can be set`) | SBI/config | **closed** (single-NRF-client redesign) | verify-live single-nrf + log signature |
| DEF-0013 | Registration reject `FIVEG_SERVICES_NOT_ALLOWED` / UE `5U3-ROAMING-NOT-ALLOWED` after NG Setup + dual-home | SBI/roaming | **closed** (root cause = wrong SUCI HPLMN from UE mcc/mnc 999/70) | LAB-IREG-001 — expect `suci-0-001-01-…` after B1 |
| DEF-0014 | UERANSIM cannot dual-PLMN: HPLMN SUCI + VPLMN 999/70 camp without patches | RAN/UE | open (documented; B1 same-PLMN auth; B2 MOCK IMSI last resort) | wiki Configuration + `identity.cpp` generateSuci |
| DEF-0015 | UPF/DN: no NAT — UE can ping session GW but not public DNS (e.g. 8.8.8.8) | VISITED/UPF | open (MEASURED gap; TC-11 PARTIAL) | TC-11 / B1 TUN ping |
| DEF-0016 | `ROAMING_MODE` pool select; full HR N9/home-UPF still unproven. **2026-08-26:** compose default was HR → UE **10.45** while UPF ogstun stayed **10.46** (ping fail). Fixed: default **LBO**, wire `upf_init.sh`, recreate both NFs | SMF/UPF | partial fix (pool sync 2026-08-26; N9 still open) | TC-05 LBO / TC-15 HR |
| DEF-0017 | No visited MME/SGW compose — LTE S6a TCs (TC-01/02/…) cannot run E2E | VISITED/EPC | open (DEFERRED; HSS-only) | TC-01 matrix row |
