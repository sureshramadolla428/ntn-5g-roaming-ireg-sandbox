"""IR.21/RAEX-shaped lab profile parser/generator."""
from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any

import yaml

IMSI_RE = re.compile(r"^0010100000000(0[1-9]|1[0-9]|20)$")
TADIG_LAB = {"LABHM", "LABVS"}


def load_yaml_profile(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_profile(profile: dict[str, Any], network_plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tadig = profile.get("tadig")
    if tadig not in TADIG_LAB:
        errors.append(f"tadig {tadig} not in lab placeholders LABHM/LABVS (V19)")
    mcc, mnc = str(profile.get("mcc")), str(profile.get("mnc"))
    if mcc not in {"001", "999"}:
        errors.append(f"unexpected MCC {mcc}")
    ip = profile.get("amfNgApIp")
    if ip:
        addr = ipaddress.ip_address(ip)
        nets = [ipaddress.ip_network(n["subnet"]) for n in network_plan["networks"].values()]
        if not any(addr in n for n in nets):
            errors.append(f"IP {ip} not in network-plan subnets")
    return errors


def validate_imsi(imsi: str) -> bool:
    return bool(IMSI_RE.match(imsi))
