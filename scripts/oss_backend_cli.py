from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.oss_backends import discover_oss_backends  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect or call explicitly enabled reusable OSS backends without using an architecture LLM."
    )
    parser.add_argument("action", choices=("status", "list", "call"))
    parser.add_argument("--backend", default="saie", help="Backend ID, for example saie or archflow")
    parser.add_argument("--tool", help="Raw upstream tool name for the call action")
    parser.add_argument("--arguments", default="{}", help="JSON object passed to the upstream tool")
    parser.add_argument(
        "--project-dir",
        type=Path,
        help="AI Architecture Studio project directory. Required by project-scoped backends such as ArchFlow.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    backends = discover_oss_backends()
    if args.action == "status":
        payload = {
            "saie_enabled_env": os.environ.get("ARCH_STUDIO_ENABLE_SAIE", ""),
            "archflow_enabled_env": os.environ.get("ARCH_STUDIO_ENABLE_ARCHFLOW", ""),
            "active_backends": sorted(backends),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    backend = backends.get(args.backend)
    if backend is None:
        print(
            json.dumps(
                {
                    "error": f"Backend {args.backend!r} is not active.",
                    "hint": "Install/verify the upstream package first, then enable its ARCH_STUDIO flag.",
                },
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    if args.action == "list":
        print(json.dumps(backend.list_tools(), indent=2, ensure_ascii=False))
        return 0

    if not args.tool:
        raise SystemExit("--tool is required for call")
    try:
        arguments = json.loads(args.arguments)
    except json.JSONDecodeError as error:
        raise SystemExit(f"--arguments must be valid JSON: {error}") from error
    if not isinstance(arguments, dict):
        raise SystemExit("--arguments must decode to a JSON object")
    project_dir = args.project_dir.resolve() if args.project_dir else None
    result = backend.call_for_agent(args.tool, arguments, project_dir=project_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0 if result.get("success") else 3


if __name__ == "__main__":
    raise SystemExit(main())
