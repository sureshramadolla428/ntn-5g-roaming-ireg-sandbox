# TC-07 demo snaps — mock SGd

**Sync status: NOT SYNCED for live NAS SMS (MOCK-ONLY)**

Runner: `scripts/run-tc-07-mock-sgd.sh` — HTTP health + Diameter poke to mock.  
Label every artifact **MOCK**. No Wireshark NGAP ladder expected.

When capturing mocks-net: `pcaps/TC-07/<ts>/` + optional Wireshark of Diameter to `10.10.6.11:3868` as **W-MOCK-1** only — do not mix with TC-05 W*.

**Honesty:** Not live MT-SMS over NAS; mock SGd only.
