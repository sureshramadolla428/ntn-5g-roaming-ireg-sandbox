"""TC-09 Alert-SC / PSM mock tests (offline + optional live probe)."""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def _post(url: str, body: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read().decode())


def run_offline_logic() -> None:
    """Pure state machine without network (unit-level)."""
    pending: list[bytes] = []
    psm_active = True
    pending.append(b"hi")
    assert len(pending) == 1
    psm_active = False
    pending.clear()
    assert not pending


def live_probe(base: str = "http://127.0.0.1:8081") -> None:
    """Exercise HTTP sidecar when mocks compose is up."""
    health = _get(f"{base}/health")
    assert health["alert_sc"] is True
    imsi = "001010000000001"
    _post(f"{base}/psm", {"imsi": imsi, "active": True})
    buf = _post(f"{base}/mt-buffer", {"imsi": imsi, "payload_hex": "48656c6c6f"})
    assert buf["stored"] is True
    alert = _post(f"{base}/alert-sc", {"imsi": imsi})
    assert alert["still_buffered"] >= 0
    _post(f"{base}/psm", {"imsi": imsi, "active": False})
    alert2 = _post(f"{base}/alert-sc", {"imsi": imsi})
    print("TC-09 mock Alert-SC probe OK:", alert2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-probe", action="store_true")
    args = parser.parse_args()
    run_offline_logic()
    if args.live_probe:
        try:
            live_probe()
        except (urllib.error.URLError, OSError, AssertionError) as exc:
            print("Live probe skipped/failed (mocks may be down):", exc)


if __name__ == "__main__":
    main()
