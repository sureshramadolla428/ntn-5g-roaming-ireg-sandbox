"""
MOCK: MAP SRI-SM (SendRoutingInfoForSM) TCP stub.
Production equivalent: SS7 MAP SRI-SM (TS 29.002).
Divergences: ASCII framing only; not real TCAP/BER; GT routing UNVERIFIED.
"""
from __future__ import annotations

import socket
import threading

HOST, PORT = "0.0.0.0", 2906

# UNVERIFIED — lab teaching response; not BER-encoded MAP
SRI_SM_OK = b"MOCK-SRI-SM-OK|msisdn=001010000000001|msc=10.10.5.12"
SRI_SM_ABSENT = b"MOCK-SRI-SM-ABSENT-SUBSCRIBER"


def handle(conn: socket.socket) -> None:
    try:
        data = conn.recv(4096)
        if not data:
            return
        text = data.decode("utf-8", errors="replace").upper()
        if "SRI" in text or "ROUTING" in text:
            if "UNKNOWN" in text or "999999" in text:
                conn.sendall(SRI_SM_ABSENT)
            else:
                conn.sendall(SRI_SM_OK)
        else:
            conn.sendall(b"MOCK-MAP-HELLO")
    finally:
        conn.close()


def main() -> None:
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"MAP SRI-SM mock on {HOST}:{PORT}")
    while True:
        c, addr = s.accept()
        print(f"MAP mock connection from {addr}")
        threading.Thread(target=handle, args=(c,), daemon=True).start()


if __name__ == "__main__":
    main()
