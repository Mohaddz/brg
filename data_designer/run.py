"""Run a data designer command from the organized workspace."""
import argparse
import runpy
import sys
from _paths import ROOT


def main():
    commands = {p.stem: p for folder in ("pipeline", "catalogs", "tools")
                for p in (ROOT / folder).glob("*.py") if not p.name.startswith("_") and p.stem not in {"openrouter", "common", "recipe", "diversity_catalog", "expanded_catalog", "expanded_catalog_v2"}}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=sorted(commands))
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    sys.argv = [str(commands[args.command]), *args.arguments]
    runpy.run_path(str(commands[args.command]), run_name="__main__")


if __name__ == "__main__":
    main()
