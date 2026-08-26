# NTN test rationale

Why NTN cases exist in an IREG-style gate:

- Direct-to-device changes timing (TA, Koffset) and path delay; registration/PDU timers must be validated under GEO/LEO RTT (B3/B4 REFERENCE).
- Emergency messaging for D2D is SMS/NIDD-first (not IMS) in this lab.
- Beam/country mapping is lab GeoJSON only — never a real constellation claim.

Fallback: UERANSIM+netem when OAI NTN unavailable — labelled as channel emulation, **not** OAI NTN PHY.
