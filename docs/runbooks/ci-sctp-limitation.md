# V17 — Hosted CI SCTP limitation

GitHub-hosted runners generally **do not** provide a workable SCTP path for Open5GS AMF (NGAP SCTP 38412).

**Lab policy:** `ci/github/workflows/ci.yml` runs pure-Python / plan checks only. Full stack tests run on Ubuntu lab host or self-hosted runners with `modprobe sctp`.
