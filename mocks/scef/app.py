"""
MOCK: SCEF T8 NIDD API stand-in.
Production equivalent: SCEF/NEF T8 NIDD (TS 29.122) + MT buffering (TS 23.682 PSM).
Divergences: lab paths are placeholders; store-and-forward is in-memory only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="SCEF T8 NIDD Mock", version="0.2.0")

# UNVERIFIED path shape pending TS 29.122 OpenAPI check (V11)
T8_NIDD_PATH = "/t8-nidd/v1/unverified/scs-as-sessions"  # UNVERIFIED
BUFFER_PATH = "/t8-nidd/v1/unverified/mt-buffer"  # UNVERIFIED — TC-13
# UNVERIFIED 128-octet teaching boundary (V12) — not claimed as 3GPP normative
NIDD_MAX_PAYLOAD_UNVERIFIED = 128


@dataclass
class NiddBufferEntry:
    """In-memory MT NIDD buffer entry (PSM stand-in)."""

    payload: bytes
    psm_active: bool = True
    delivered: bool = False


_store: dict[str, bytes] = {}
_buffer: dict[str, NiddBufferEntry] = {}


class NiddPayload(BaseModel):
    ue_id: str
    payload_hex: str = Field(..., description="hex-encoded NIDD payload")


class BufferPayload(NiddPayload):
    psm_active: bool = True


class PsmState(BaseModel):
    psm_active: bool = True


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "paths_verified": False,
        "v11": "UNVERIFIED",
        "v12": "UNVERIFIED",
        "mt_buffer": True,
    }


@app.post(T8_NIDD_PATH)
def create_session(body: NiddPayload) -> dict[str, Any]:
    raw = bytes.fromhex(body.payload_hex)
    if len(raw) > NIDD_MAX_PAYLOAD_UNVERIFIED:
        raise HTTPException(status_code=413, detail="payload exceeds UNVERIFIED lab size boundary")
    _store[body.ue_id] = raw
    return {"status": "accepted", "stored": True, "store_and_forward": "in-memory-stub"}


@app.get(T8_NIDD_PATH + "/{ue_id}")
def get_session(ue_id: str) -> dict[str, Any]:
    if ue_id not in _store:
        raise HTTPException(status_code=404, detail="no stored payload")
    return {"ue_id": ue_id, "payload_hex": _store[ue_id].hex()}


@app.post(BUFFER_PATH)
def buffer_mt_nidd(body: BufferPayload) -> dict[str, Any]:
    """TC-13: buffer MT NIDD while PSM active; deliver when PSM clears."""
    raw = bytes.fromhex(body.payload_hex)
    if len(raw) > NIDD_MAX_PAYLOAD_UNVERIFIED:
        raise HTTPException(status_code=413, detail="payload exceeds UNVERIFIED lab size boundary")
    entry = NiddBufferEntry(payload=raw, psm_active=body.psm_active)
    _buffer[body.ue_id] = entry
    if body.psm_active:
        return {"status": "buffered", "ue_id": body.ue_id, "reason": "psm-active"}
    entry.delivered = True
    return {"status": "delivered", "ue_id": body.ue_id, "payload_hex": raw.hex()}


@app.post(BUFFER_PATH + "/{ue_id}/psm")
def set_psm(ue_id: str, body: PsmState) -> dict[str, Any]:
    if ue_id not in _buffer:
        raise HTTPException(status_code=404, detail="no buffer for ue")
    _buffer[ue_id].psm_active = body.psm_active
    if not body.psm_active and not _buffer[ue_id].delivered:
        _buffer[ue_id].delivered = True
        return {
            "status": "delivered-on-wake",
            "payload_hex": _buffer[ue_id].payload.hex(),
        }
    return {"status": "updated", "psm_active": body.psm_active}


@app.get(BUFFER_PATH + "/{ue_id}")
def get_buffer(ue_id: str) -> dict[str, Any]:
    if ue_id not in _buffer:
        raise HTTPException(status_code=404, detail="no buffer for ue")
    e = _buffer[ue_id]
    return {
        "ue_id": ue_id,
        "psm_active": e.psm_active,
        "delivered": e.delivered,
        "payload_hex": e.payload.hex(),
    }


@app.get(BUFFER_PATH)
def buffer_stats() -> dict[str, Any]:
    return {
        "count": len(_buffer),
        "pending": sum(1 for e in _buffer.values() if e.psm_active and not e.delivered),
    }
