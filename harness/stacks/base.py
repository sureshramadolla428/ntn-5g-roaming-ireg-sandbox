"""Stack abstraction for UERANSIM vs OAI backends."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AttachResult:
    success: bool
    imsi: str
    backend: str
    detail: str = ""
    measured_rtt_ms: Optional[float] = None


class RanStack(ABC):
    name: str

    @abstractmethod
    def attach(self, imsi: str) -> AttachResult:
        ...

    @abstractmethod
    def detach(self, imsi: str) -> None:
        ...


class UeransimStack(RanStack):
    name = "ueransim"

    def attach(self, imsi: str) -> AttachResult:
        # Live attach DEFERRED-TO-UBUNTU
        return AttachResult(False, imsi, self.name, detail="DEFERRED-TO-UBUNTU")

    def detach(self, imsi: str) -> None:
        return None


class OaiStack(RanStack):
    name = "oai"

    def attach(self, imsi: str) -> AttachResult:
        return AttachResult(False, imsi, self.name, detail="DEFERRED-TO-UBUNTU")

    def detach(self, imsi: str) -> None:
        return None


def get_stack(backend: str = "ueransim") -> RanStack:
    if backend == "oai":
        return OaiStack()
    return UeransimStack()
