# Verification register
Seeded from master prompt Appendix E. Update status only with citations.

| ID | Item | Status | Where to verify | Lab handling |
|----|------|--------|-----------------|-------------|
| V1 | Experimental-Result-Code 5004 vs 5420 naming | UNVERIFIED | TS 29.272 | diameter_codes.py flags UNVERIFIED |
| V2 | Full S6a/S6d Experimental-Result-Code list | UNVERIFIED | TS 29.272 | subset only |
| V3 | TS 29.338 55xx SGd codes | UNVERIFIED | TS 29.338 | mock stubs |
| V4 | T3517 default 5GS | UNVERIFIED | TS 24.501 | not hardcoded as fact |
| V5 | Full NAS timer table EPS/5GS | UNVERIFIED | TS 24.301/24.501 | KPI margins deferred |
| V6 | cellSpecificKoffset-r17 range + SCS | PARTIAL | TS 38.331 + OAI conf MEASURED | value 40 in LEO conf — range UNVERIFIED |
| V7 | ta-Common / Drift units | PARTIAL | TS 38.331 | values copied from OAI conf; units cite UNVERIFIED |
| V8 | kmac in installed OAI | UNVERIFIED | OAI source @ 38dc378 | DEFERRED-TO-UBUNTU grep |
| V9 | TS 38.821 delay table exact | UNVERIFIED | TS 38.821 | B3 computed REFERENCE |
| V10 | TS 38.821 Doppler values | UNVERIFIED | TS 38.821 | not claimed as MEASURED |
| V11 | TS 29.122 T8 NIDD paths | UNVERIFIED | TS 29.122 | mock paths labelled |
| V12 | NIDD max payload size | UNVERIFIED | TS 29.122/29.128 | 128 octet boundary labelled UNVERIFIED |
| V13 | TS 24.008 GPRS Timer 2/3 | UNVERIFIED | TS 24.008 | not used as hard assert |
| V14 | Open5GS SEPP/N32 present? | VERIFIED-ABSENT | reference compose MEASURED | SBI proxy stand-in; attach uses ipx-net dual-home |
| V21 | Open5GS AUSF discovery across PLMN without SEPP (IP NRF URIs on ipx-net) | UNVERIFIED | Ubuntu AMF/AUSF logs | dual-home stand-in; not N32 |
| V22 | Open5GS AMF cause #7 = HTTP 404 path (`gmm_cause_from_sbi`) | VERIFIED-SOURCE | open5gs `src/amf/nas-path.c` | distinct from access_control #11 |
| V23 | UERANSIM UE `mcc`/`mnc` = HPLMN for SUCI; no equivalent/preferred PLMN config key | VERIFIED-SOURCE | wiki Configuration + `src/ue/nas/mm/identity.cpp` generateSuci | B1 same-PLMN gNB; B2 MOCK IMSI last resort |
| V15 | Open5GS Prometheus endpoint | UNVERIFIED | Open5GS source | metrics server in yaml — scrape DEFERRED |
| V16 | OAI NTN param names @ branch | PARTIAL | evidence conf MEASURED | full source DEFERRED-TO-UBUNTU |
| V17 | Hosted CI SCTP support | UNVERIFIED-LIKELY-NO | runner docs | self-hosted / Ubuntu only |
| V18 | Python Diameter library | UNVERIFIED | PyPI | minimal framing + optional pycrate |
| V19 | TADIG structural rules | LAB-PLACEHOLDER | GSMA | LABHM/LABVS labelled placeholders |
| V20 | TAP3/RAP structure | UNVERIFIED | GSMA TD.57 | JSON educational model only |
| V24 | Open5GS ODB / operator_determined_barring bit → roaming barred | UNVERIFIED | Open5GS + TS 23.008 | TC-06 stub; use AMF access_control #11 stand-in; do not assert Diameter 5004 (V1) |
| V25 | Live HR (vSMF/hSMF/N9) on installed Open5GS image | PARTIAL | Ubuntu N16/N9 pcaps | **LBO MEASURED** on TC-05 `20260826T014834` (UE **10.46.0.3**, GW ping **10.46.0.1**). Historical `20260826T010742` UE **10.45.0.3** was misconfig (not full HR) and is SUPERSEDED. Do **not** claim full HR until N16/N9+hUPF MEASURED |
| V26 | Wireshark `ngap.procedureCode == 15` = Initial Context Setup | UNVERIFIED | Wireshark dissector + TS 38.413 | TC-05 optional step; do not hard-assert without primary-source check |
| V27 | Wireshark `pfcp.msg_type == 50/51` = Session Modification Request/Response | UNVERIFIED | Wireshark PFCP dissector + TS 29.244 | TC-05 `pdu-9` filter refine; generic `pfcp` filter acceptable for MEASURED |
