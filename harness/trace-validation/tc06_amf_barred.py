"""TC-06 helper: temporarily remove HOME PLMN from visited AMF access_control.

MOCK divergence from Diameter 5004 (V1 UNVERIFIED). Expect 5GMM cause #11
when HOME is removed from allow-list (Open5GS amf.yaml.in semantics).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def remove_home_plmn(amf_path: Path, home_mcc: str = "001", home_mnc: str = "01") -> None:
    """Remove the access_control stanza matching HOME_MCC/HOME_MNC placeholders."""
    text = amf_path.read_text(encoding="utf-8")
    # After init sed, placeholders become digits — match rendered home PLMN block.
    pattern = re.compile(
        rf"(\s+- plmn_id:\s*\n\s+mcc: \"{re.escape(home_mcc)}\"\s*\n\s+mnc: \"{re.escape(home_mnc)}\"\s*\n)",
        re.MULTILINE,
    )
    new_text, n = pattern.subn("", text)
    if n == 0:
        # Fallback: placeholder form before container start
        pattern2 = re.compile(
            r"\s+- plmn_id:\s*\n\s+mcc: \"HOME_MCC\"\s*\n\s+mnc: \"HOME_MNC\"\s*\n",
            re.MULTILINE,
        )
        new_text, n = pattern2.subn("", text)
    if n == 0:
        print(f"WARN: no HOME PLMN access_control block removed from {amf_path}", file=sys.stderr)
    amf_path.write_text(new_text, encoding="utf-8")
    print(f"Removed {n} HOME access_control block(s) from {amf_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remove-home-plmn", type=Path, required=True)
    parser.add_argument("--home-mcc", default="001")
    parser.add_argument("--home-mnc", default="01")
    args = parser.parse_args(argv)
    remove_home_plmn(args.remove_home_plmn, args.home_mcc, args.home_mnc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
