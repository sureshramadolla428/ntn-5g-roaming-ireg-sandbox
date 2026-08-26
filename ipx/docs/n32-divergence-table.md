# N32 divergence table (lab SBI proxy vs production SEPP)

| Capability | Production SEPP/N32 | This lab | Impact |
|------------|---------------------|----------|--------|
| N32-c capability negotiation | Yes (TS 29.573) | **Not modelled** | No handshake assertions |
| PRINS / message protection | Yes | **Not modelled** | No confidentiality tests |
| IPX provider modification tracking | Yes | **Not modelled** | Cannot detect mid-path tamper as SEPP would |
| HTTP/2 SBI relay | Yes | Lab attach path: **ipx-net dual-home** + home AUSF/UDM/UDR register to **visited NRF** (single NRF client; Open5GS HTTP/2). FastAPI proxy is HTTP/1 debug only | Reachability stand-in, not N32 |
| Diameter S6a via DRA | Via IPX DRA | freeDiameter template | Primary inter-PLMN auth path in lab |
| Naming | SEPP | **SBI proxy stand-in** | Must never be called SEPP |

V14: Open5GS SEPP absent in reference — VERIFIED-ABSENT.
