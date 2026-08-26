# TC-11 demo snaps — user-plane (same LBO attach as TC-05 `014834`)

**Run id for W/G alignment:** `TC-05-20260826T014834` (user-plane proven on same attach)  
**Dedicated TC-11 capture stamp:** none on this Windows tree — **do not invent**.

## Sync status: PARTIAL (inherits TC-05 LBO attach)

| Item | Status |
|------|--------|
| UE / GW | MEASURED on TC-05 `014834`: TUN **10.46.0.3**, ping **10.46.0.1** 3/3 |
| W* dedicated TC-11 | Not separate — cite TC-05 W8 + UE log TUN up |
| G* | Same PCAP_DIR as TC-05 after refresh; no separate GUI pack |
| DN 8.8.8.8 | **NOT claimed** (no NAT) |

**Honesty:** B1 001/01; no SEPP; LBO not HR.  
**Snap folder:** reuse [`../TC-05-20260826T014834/`](../TC-05-20260826T014834/) — do not duplicate PNGs.  
Fresh TC-11 with `--with-capture` on Ubuntu → new `TC-11-<ts>/` pack only if a new timestamp is produced.
