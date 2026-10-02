"""Stable workspace paths and imports for directly executed command scripts."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
CONFIGS = ROOT / "configs"
REFERENCES = ROOT / "references"
for folder in ("pipeline", "catalogs", "tools"):
    location = str(ROOT / folder)
    if location not in sys.path:
        sys.path.append(location)
