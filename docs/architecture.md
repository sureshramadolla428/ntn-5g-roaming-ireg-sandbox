# Architecture — Home / IPX / Visited

Three domains on one Ubuntu host via Docker bridges (`network-plan.yaml`).

- **HOME (001-01, TADIG LABHM placeholder):** subscriber DB, AUSF/UDM/UDR/PCF/HSS.
- **VISITED (999-70, TADIG LABVS placeholder):** AMF/SMF/UPF serving NTN/terrestrial RAN.
- **IPX:** freeDiameter DRA/DEA + **SBI proxy stand-in** (not SEPP; V14) + fault-injection API.

Roaming modes: HR (`smf-hr.yaml`) and LBO (`smf-lbo.yaml`). Runtime verification DEFERRED-TO-UBUNTU.

See also: `docs/network-plan.md`, `docs/call-flows/`.
