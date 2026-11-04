"""Packaged BYOK bootstrap: all executable dependencies belong to the bundle."""
from __future__ import annotations

import os
import json
from pathlib import Path


def configure(bundle: Path, data: Path) -> dict:
    bundle, data = bundle.resolve(), data.resolve()
    node = bundle / 'harness/node.exe'
    entry = bundle / 'harness/node_modules/@deepseek-ai/dsh/lib/bin.js'
    launcher = bundle / 'harness/dsh.cmd'
    required = [node, entry, launcher, bundle / 'app/dsh_host_tools.mjs', bundle / 'app/dsh_tool_policy.mjs', bundle / 'app/dsh_test_budget.mjs',
                bundle / 'app/architecture_skills']
    missing = [str(p.relative_to(bundle)) for p in required if not p.exists()]
    if missing:
        raise RuntimeError('安装包缺少运行组件，请修复安装：' + ', '.join(missing))
    # Drop inherited developer routing only in this process. Never import an
    # account or key from the environment into a fresh personal connection vault.
    for name in tuple(os.environ):
        if name.startswith(('ARCH_STUDIO_', 'KSTUDIO_DSH_')) or name.endswith('_API_KEY'):
            os.environ.pop(name, None)
    settings = data / 'settings'
    runtime = data / 'runtime'
    generated = data / 'generated-scripts'
    for directory in (settings, runtime, generated):
        directory.mkdir(parents=True, exist_ok=True)
    os.environ.update({
        'ARCH_STUDIO_STANDALONE': '1', 'KSTUDIO_PERSONAL_DESKTOP': '1',
        'K_STUDIO_DEPLOYMENT_MODE': 'local', 'WEB_CONCURRENCY': '1',
        'ARCH_STUDIO_RUNTIME_DIR': str(runtime),
        'ARCH_STUDIO_ECONOMY_PROVIDER': 'litellm',
        'ARCH_STUDIO_API_MODEL': '',
        'ARCH_STUDIO_API_KEY_ENV': 'KSTUDIO_NO_INHERITED_API_KEY',
        'ARCH_STUDIO_MCP_CONFIG': str(data / 'bridge.json'),
        'ARCH_STUDIO_CODEX_HOME': str(data / 'agent-runtime'),
        'ARCH_STUDIO_GENERATED_SCRIPT_DIR': str(generated),
        'ARCHFLOW_GENERATED_SCRIPT_DIR': str(generated),
        'KSTUDIO_CONNECTIONS_DIR': str(settings),
        'KSTUDIO_AGENT_ENGINE': 'deepseek-harness',
        'KSTUDIO_DSH_CAPABILITIES': 'full',
        'KSTUDIO_DSH_GUIDANCE': 'architecture',
        'KSTUDIO_DSH_SDK_SITE': str(bundle),
        'KSTUDIO_DSH_BIN': str(launcher),
        'KSTUDIO_DSH_MAX_OUTPUT_TOKENS': '32768',
        'PATH': str(node.parent) + os.pathsep + os.environ.get('PATH', ''),
    })
    adai = bundle / 'third-party/adai/skill'
    if adai.is_dir():
        os.environ['KSTUDIO_DSH_SKILL_DIRS'] = json.dumps([str(adai)])
    return {'runtime': runtime, 'settings': settings, 'node': node, 'launcher': launcher}
