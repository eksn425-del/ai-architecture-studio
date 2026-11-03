"""Additive official SDK composition; no replacement agent loop.

Opt-in until native tool, approval and desktop delivery acceptance is complete.
External MCP servers are explicitly configured, never inferred from a skill.
"""
from pathlib import Path
import json
import os


def enabled():
    return os.environ.get('KSTUDIO_DSH_CAPABILITIES', 'protected') == 'full'


def provider_retry_policy():
    # Use the official durable step retry executor, never re-run a committed
    # tool or the whole modeling turn. Permanent credential/quota errors stop.
    return {'mode': 'normal', 'maxRetries': 2,
            'retryableCodes': ['RATE_LIMIT', 'SERVER', 'TIMEOUT', 'TRANSPORT'],
            'backoff': {'initialDelayMs': 1000, 'maxDelayMs': 10000, 'jitterRatio': 0.1}}


def full_rows(*, api_base, model, protocol, max_tokens, host_plugin):
    rows = [
        {'id': 'session-telemetry-otel', 'disabled': True},
        {'id': 'llm-pi-ai', 'config': {'providers': {'kstudio-bai': {
            'apiKeyEnv': 'KSTUDIO_DSH_API_KEY', 'api': protocol, 'baseURL': api_base,
            'models': [{'id': model, 'name': model, 'contextWindow': 131072,
                        'maxTokens': max_tokens, 'input': ['text', 'image'],
                        'reasoningEfforts': {'low': 'low', 'high': 'high'}}],
            'retryPolicy': provider_retry_policy()}}}},
        {'id': 'agent-default-model', 'config': {'provider': 'kstudio-bai', 'model': model}},
        # Keep the official compactor, but size its reserve for this 128k gateway.
        # Upstream's 64k headroom plus our 32k completion reservation leaves only
        # 32k for messages and caused repeated compaction during the native trial.
        {'id': 'compaction-basic', 'config': {'headroomTokens': 8192,
                                            'maxTokens': 4096, 'retainTokens': 16384}},
        {'id': 'agent-instructions', 'config': {'projectRootMarkers':['.kstudio-project','.git'], 'maxBytes':65536}},
        {'insert': [{'id': 'kstudio-host-tools', 'name': Path(host_plugin).as_posix()}]},
    ]
    # Preserve upstream implementations for compaction, tools, MD and subagents.
    # Runtime adapters and installed packages own their normal registrations.
    roots = json.loads(os.environ.get('KSTUDIO_DSH_SKILL_DIRS', '[]'))
    if not isinstance(roots, list) or any(not isinstance(p, str) or not Path(p).is_dir() for p in roots):
        raise ValueError('Skill roots must be existing directories.')
    if roots:
        rows.append({'id': 'skill-filesystem', 'config': {'customSkillDirs': roots}})
    config_path = os.environ.get('KSTUDIO_DSH_MCP_CONFIG')
    if config_path:
        servers = json.loads(Path(config_path).read_text(encoding='utf-8'))
        if not isinstance(servers, dict):
            raise ValueError('MCP configuration must map names to configurations.')
        entries=[]
        import re
        for name, config in servers.items():
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,32}', name) or not isinstance(config, dict):
                raise ValueError('Invalid MCP server name/configuration.')
            if config.get('transport') not in ('stdio', 'streamable-http'):
                raise ValueError('MCP requires an explicit supported transport.')
            entries.append({'id': 'kstudio-mcp-'+name, 'name': '@deepseek-ai/dsh-mcp-client',
                            'config': {**config, 'serverName': name}})
        rows.append({'insert': entries})
    return rows
