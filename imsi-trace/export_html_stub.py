"""HTML docs export stub for Confluence-like publishing."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    lines = ["<html><body><h1>ntn-roaming-lab docs export</h1><ul>"]
    for p in sorted((ROOT / "docs").rglob("*.md")):
        rel = p.relative_to(ROOT)
        lines.append(f"<li>{rel.as_posix()}</li>")
    lines.append("</ul></body></html>")
    (dest / "index.html").write_text("\n".join(lines), encoding="utf-8")
