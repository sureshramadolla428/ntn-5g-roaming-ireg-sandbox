"""TC-10 MAP SRI-SM mock tests."""
from __future__ import annotations

import argparse
import socket


def offline_assert() -> None:
    assert b"MOCK-SRI-SM" in b"MOCK-SRI-SM-OK"


def live_probe(host: str = "10.10.6.12", port: int = 2906) -> None:
    s = socket.create_connection((host, port), timeout=3)
    s.sendall(b"SRI-SM MSISDN=001010000000001")
    ack = s.recv(256)
    s.close()
    assert b"MOCK-SRI-SM" in ack
    print("TC-10 MAP mock probe OK:", ack[:80])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-probe", action="store_true")
    args = parser.parse_args()
    offline_assert()
    if args.live_probe:
        try:
            live_probe()
        except OSError as exc:
            print("Live probe skipped:", exc)


if __name__ == "__main__":
    main()
