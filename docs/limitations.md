# Limitations (above-the-fold credibility)

**This lab does not prove production roaming readiness.** It is a software-only **IREG practice sandbox** (B1 same-PLMN, no SEPP) — not a formal GSMA IREG operator sign-off.

## Hard limits

- RFSIM does not model RF, fading, or Doppler; netem models delay/jitter/loss only.
- No real SIM/USIM security; lab K/OPc only.
- No real IPX provider, SLA, or partner MNO behaviour.
- No Open5GS SEPP — N32 replaced by labelled SBI proxy stand-in (V14).
- Stock UERANSIM: no HPLMN SUCI + VPLMN 999/70 camp (DEF-0014); B1 same-PLMN camp only.
- Live UE pool target for TC-05 = visited **10.46** (LBO). Default `ROAMING_MODE=LBO` on visited-smf+upf (2026-08-26). Full HR path (N9/hUPF) still unproven (DEF-0016 partial).
- No UPF NAT to public Internet (DEF-0015) — GW ping ≠ DN ping.
- Full LTE EPC (MME/SGW) not composed — S6a TCs DEFERRED (DEF-0017).
- Interview matrix: `docs/ireg-tc-matrix.md` (do not claim all 25 LIVE).
- IR.21 XML/XSD are **lab-authored**, not GSMA schema.
- Billing CDR JSON is educational — **not** TAP3 BER / TD.57 conformance (V20).
- T8 NIDD paths marked UNVERIFIED until TS 29.122 check (V11/V12).
- Hosted CI runners typically lack SCTP (V17) — full stack tests are DEFERRED-TO-UBUNTU / self-hosted.
- Windows build host cannot fully run Open5GS/OAI/SCTP Docker the same way as Ubuntu — runtime verification DEFERRED-TO-UBUNTU.

## MEASURED vs REFERENCE

- **MEASURED:** values observed in this workspace or produced by lab tools on Ubuntu.
- **REFERENCE:** computed/teaching values (e.g. Appendix B3 delays) — not field measurements.
