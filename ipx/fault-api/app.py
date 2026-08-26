"""Fault-injection API for IPX DRA/SBI path."""
from __future__ import annotations

from enum import Enum
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="IPX Fault Injection API", version="0.1.0")


class FaultType(str, Enum):
    none = "none"
    drop_request = "drop_request"
    delay_ms = "delay_ms"
    rewrite_realm = "rewrite_realm"
    rewrite_visited_plmn = "rewrite_visited_plmn"
    answer_realm_not_served = "answer_realm_not_served"
    blackhole = "blackhole"


class FaultConfig(BaseModel):
    fault: FaultType = FaultType.none
    delay_ms: int = 0
    note: str = ""


_state = FaultConfig()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/fault")
def get_fault() -> FaultConfig:
    return _state


@app.put("/fault")
def set_fault(cfg: FaultConfig) -> FaultConfig:
    global _state
    _state = cfg
    return _state


@app.post("/fault/reset")
def reset() -> FaultConfig:
    global _state
    _state = FaultConfig()
    return _state
