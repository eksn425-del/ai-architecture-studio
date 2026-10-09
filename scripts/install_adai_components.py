"""Opt-in ADAI ZIP installer and SketchUp 2018–2026 discovery.

Examples:
  python scripts/install_adai_components.py --list
  python scripts/install_adai_components.py --install skill mcp
  python scripts/install_adai_components.py --detect-sketchup
Installing does NOT switch the active K Studio SketchUp connector.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from app.adai_components import (COMPONENTS, TARGET_SU_YEARS,
                                 detect_sketchup_installations, install_component)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Print pinned upstream packages")
    parser.add_argument("--install", nargs="+", choices=sorted(COMPONENTS),
                        help="Download and verify packages into .local/adai")
    parser.add_argument("--detect-sketchup", action="store_true",
                        help="Detect Windows SketchUp executables; not a pass")
    args = parser.parse_args()
    if not (args.list or args.install or args.detect_sketchup):
        parser.print_help()
        return
    if args.list:
        print(json.dumps({"target_versions": list(TARGET_SU_YEARS),
                          "packages": COMPONENTS}, indent=2))
    if args.install:
        for name in dict.fromkeys(args.install):
            print(json.dumps(install_component(REPO_ROOT, name), ensure_ascii=False))
    if args.detect_sketchup:
        print(json.dumps(detect_sketchup_installations(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
