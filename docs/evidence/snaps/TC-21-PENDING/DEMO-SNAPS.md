# TC-21 demo snaps — NTN netem

**Sync status: NOT SYNCED (REFERENCE netem; OAI DEFERRED)**

Runner: `scripts/run-tc-21-ntn-netem.sh` — applies netem profile (REFERENCE delays).  
Offline pytest may PASS without live attach. Do not claim MEASURED NTN RTT from netem alone.

After Ubuntu run with capture: create `TC-21-<ts>/` with W* (optional attach) + G* only if exporter pointed at **that** ts. Label RTT MEASURED vs PROFILE REFERENCE separately.

**Honesty:** netem ≠ OAI NTN PHY; B1 if attach used.
