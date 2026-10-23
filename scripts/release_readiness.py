"""Offline release boundary report. Exit 2 means paid public launch is blocked."""
import argparse
import json

from app.runtime_safety import release_readiness


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Print machine-readable capabilities, without credentials or environment dumps.')
    args = parser.parse_args()
    report = release_readiness()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print('K Studio: local single-user candidate. Paid public release: BLOCKED.')
        for name, state in report['cloud_capabilities'].items():
            print(f'- {name}: {state}')
        print('See docs/RELEASE_PREPARATION_CN_2026-10-19.md for deployment and acceptance steps.')
    return 0 if report['paid_multi_user_release_ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
