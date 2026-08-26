"""
MOCK: Diameter SGd SMSC stand-in with Alert-SC / PSM retry simulation.
Production equivalent: SMSC/SMSF over SGd (TS 29.338) + Alert-SC (TS 29.338 §5.3).
Divergences: minimal framing; HTTP sidecar for lab harness; no full ASN.1 / NAS SMS.
"""
from __future__ import annotations

import json
import socket
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

HOST, PORT = "0.0.0.0", 3868
HTTP_PORT = 8081

# UNVERIFIED — lab retry cap for teaching only
ALERT_SC_MAX_RETRIES_UNVERIFIED = 3


@dataclass
class PsmState:
    """In-memory PSM stand-in for one subscriber."""

    imsi: str
    psm_active: bool = True
    pending_mt: list[bytes] = field(default_factory=list)
    alert_sc_sent: int = 0
    delivered: int = 0


_psm: dict[str, PsmState] = {}
_lock = threading.Lock()


def _state(imsi: str) -> PsmState:
    with _lock:
        if imsi not in _psm:
            _sm = PsmState(imsi=imsi)
            _psm[imsi] = _sm
            return _sm
        return _psm[imsi]


def handle_diameter(conn: socket.socket) -> None:
    """Minimal SGd socket handler — MOCK-SGD-ACK or Alert-SC path."""
    try:
        data = conn.recv(4096)
        if not data:
            return
        payload = data.decode("utf-8", errors="replace")
        if "ALERT-SC" in payload.upper() or payload.startswith("ALERT"):
            imsi = "001010000000001"
            st = _state(imsi)
            st.alert_sc_sent += 1
            if st.pending_mt and not st.psm_active:
                for msg in st.pending_mt:
                    conn.sendall(b"MOCK-MT-DELIVER:" + msg[:64])
                st.delivered += len(st.pending_mt)
                st.pending_mt.clear()
            else:
                conn.sendall(b"MOCK-ALERT-SC-ACK")
        else:
            conn.sendall(b"MOCK-SGD-ACK")
    finally:
        conn.close()


class _Handler(BaseHTTPRequestHandler):
    """HTTP API for harness / TC-09."""

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, code: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(
                200,
                {
                    "status": "ok",
                    "mock": "sgd-smsc",
                    "alert_sc": True,
                    "psm_simulation": True,
                },
            )
            return
        if self.path == "/stats":
            with _lock:
                summary = {
                    imsi: {
                        "psm_active": s.psm_active,
                        "pending": len(s.pending_mt),
                        "alert_sc_sent": s.alert_sc_sent,
                        "delivered": s.delivered,
                    }
                    for imsi, s in _psm.items()
                }
            self._json(200, {"subscribers": summary})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body.decode() or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"})
            return

        if self.path == "/psm":
            imsi = str(data.get("imsi", "001010000000001"))
            st = _state(imsi)
            st.psm_active = bool(data.get("active", True))
            self._json(200, {"imsi": imsi, "psm_active": st.psm_active})
            return

        if self.path == "/mt-buffer":
            imsi = str(data.get("imsi", "001010000000001"))
            payload = bytes.fromhex(str(data.get("payload_hex", "48656c6c6f")))
            st = _state(imsi)
            if st.psm_active:
                st.pending_mt.append(payload)
                self._json(202, {"stored": True, "reason": "psm-active-buffer"})
            else:
                self._json(200, {"stored": False, "reason": "would-deliver-live"})
            return

        if self.path == "/alert-sc":
            imsi = str(data.get("imsi", "001010000000001"))
            st = _state(imsi)
            retries = 0
            delivered = 0
            while st.pending_mt and retries < ALERT_SC_MAX_RETRIES_UNVERIFIED:
                retries += 1
                st.alert_sc_sent += 1
                if not st.psm_active:
                    delivered = len(st.pending_mt)
                    st.delivered += delivered
                    st.pending_mt.clear()
                    break
            self._json(
                200,
                {
                    "alert_sc_attempts": retries,
                    "delivered": delivered,
                    "still_buffered": len(st.pending_mt),
                },
            )
            return

        self._json(404, {"error": "unknown path"})


def serve_http() -> None:
    server = HTTPServer((HOST, HTTP_PORT), _Handler)
    print(f"SGd mock HTTP on {HOST}:{HTTP_PORT}")
    server.serve_forever()


def main() -> None:
    try:
        import pycrate  # noqa: F401

        print("pycrate available — structured encode path still MOCK")
    except ImportError:
        print("pycrate not installed — using minimal framing mock")

    threading.Thread(target=serve_http, daemon=True).start()
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"SGd mock Diameter listen on {HOST}:{PORT}")
    while True:
        c, _ = s.accept()
        threading.Thread(target=handle_diameter, args=(c,), daemon=True).start()


if __name__ == "__main__":
    main()
