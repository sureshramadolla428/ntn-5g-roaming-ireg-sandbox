# 3GPP NTN → OAI config key map

**MEASURED** keys grepped/read from lab-copied `gnb.sa.band254...ntn-leo.conf` (evidence).
OAI source tree not present on Windows — full V16 verification DEFERRED-TO-UBUNTU against `38dc378`.

| 3GPP concept (REFERENCE) | OAI conf key (MEASURED in evidence conf) | Notes |
|--------------------------|------------------------------------------|-------|
| SIB19 NTN-Config | `ntn_Config_r17` block / `cu_sibs = [2]; du_sibs = [19]` | Presence MEASURED |
| cellSpecificKoffset | `cellSpecificKoffset_r17` | MEASURED value 40 in LEO conf; range V6 UNVERIFIED |
| ta-Common | `ta-Common-r17` | MEASURED 4627000; units V7 UNVERIFIED |
| ta-CommonDrift | `ta-CommonDrift-r17` | MEASURED -230000 |
| Ephemeris position | `positionX/Y/Z-r17` | MEASURED |
| Ephemeris velocity | `velocityVX/Y/VZ-r17` | MEASURED |
| UlSyncValidityDuration | `ntn-UlSyncValidityDuration-r17` | MEASURED = 5 |
| kmac | — | V8 UNVERIFIED — grep OAI source on Ubuntu |

## Fallback if NTN params missing in build

Use **UERANSIM + corrected B4 netem** on N2/N3 path. Document as:

> Channel emulation via tc/netem (B4). **Not** OAI NTN PHY/SIB19.

Do not silently label UERANSIM+netem as OAI NTN.
