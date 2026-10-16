"""Report declared-precision geometry consistency alongside raw strict verdict."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.native_stable_geometry import CONTRACT, compare_stable_geometry
from scripts.audit_native_delivery_stages import audit_stages


def audit_stable_stages(before: dict, bound: dict, download: dict) -> dict:
    try:
        stages = [before, bound, download]
        comparisons = [{'transition': name, **compare_stable_geometry(stages[a], stages[b])}
                       for a, b, name in [(0, 1, 'before_save_to_bound_reopen'),
                                          (1, 2, 'bound_reopen_to_download_reopen'),
                                          (0, 2, 'before_save_to_download_reopen')]]
        return {'status': 'PASS_WITH_DECLARED_PRECISION' if all(c['status'] == 'PASS' for c in comparisons) else 'FAIL',
                'contract': CONTRACT, 'transitions': comparisons,
                'raw_strict_three_stage': audit_stages(before, bound, download, require_deep=True),
                'raw_strict_verdict_overridden': False,
                'source_fidelity': 'NOT_ASSESSED', 'strict_blank_program_replay': 'NOT_RUN',
                'customer_delivery': 'NOT_ASSESSED'}
    except (ValueError, TypeError, KeyError) as exc:
        return {'status': 'BLOCKED', 'reason': str(exc), 'contract': CONTRACT}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['before', 'bound', 'download']:
        p.add_argument(key, type=Path)
    p.add_argument('--output', type=Path)
    args=p.parse_args()
    result=audit_stable_stages(*(json.loads(getattr(args, key).read_text(encoding='utf8')) for key in ['before','bound','download']))
    text=json.dumps(result, ensure_ascii=False, indent=2)+'\n'
    if args.output:
        args.output.write_text(text, encoding='utf8')
    print(json.dumps({'status': result['status'], 'contract': CONTRACT,
                      'raw_strict_status': result.get('raw_strict_three_stage',{}).get('status')}))
    return 0 if result['status']=='PASS_WITH_DECLARED_PRECISION' else 1


if __name__=='__main__':
    raise SystemExit(main())
