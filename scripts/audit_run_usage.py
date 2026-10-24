"""Offline usage projection. Does not contact a provider or mutate a ledger."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.run_usage_audit import read_audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args()
    print(json.dumps(read_audit(args.trace, args.ledger), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
