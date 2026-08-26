# Test strategy

Tiers: Tier-1 UERANSIM fast gate; Tier-2 OAI NTN RFSIM; mocks for SMS/NIDD/billing.

Interview suite (TC-01…TC-25): see `docs/ireg-tc-matrix.md` and `docs/runbooks/ireg-tc-execution.md`.
Capture: `scripts/capture-ireg-tc.sh`. Golden live path: TC-05 (B1) → TC-11 (GW ping).

Mandatory: LAB-IREG-000 topology guard; auth/reg/PDU; IPX fault matrix; flake job (D4.4).

Evidence: multi-point pcaps + logs; MEASURED RTT when netem applied.

UNVERIFIED items: see `verification-register.md` — must not drive silent pass.
