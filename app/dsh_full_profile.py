"""Additive official SDK composition; no replacement agent loop.

Opt-in until native tool, approval and desktop delivery acceptance is complete.
External MCP servers are explicitly configured, never inferred from a skill.
"""
from pathlib import Path
import json
import os


def enabled():
    return os.environ.get('KSTUDIO_DSH_CAPABILITIES', 'protected') == 'full'


def provider_retry_policy(max_retries=2):
    # Use the official durable step retry executor, never re-run a committed
    # tool or the whole modeling turn. Permanent credential/quota errors stop.
    return {'mode': 'normal', 'maxRetries': max_retries,
            'retryableCodes': ['RATE_LIMIT', 'SERVER', 'TIMEOUT', 'TRANSPORT'],
            'backoff': {'initialDelayMs': 1000, 'maxDelayMs': 10000, 'jitterRatio': 0.1}}


def full_rows(*, api_base, model, protocol, max_tokens, host_plugin, effective_configuration=None):
    if effective_configuration is None:
        from .dsh_configuration import resolve_configuration
        effective_configuration = resolve_configuration({'api_base': api_base, 'model': model, 'mode': 'codex-responses' if protocol == 'openai-responses' else 'compatible', 'reasoning_effort': 'provider-default'})
    rows = [
        {'id': 'session-telemetry-otel', 'disabled': True},
        {'id': 'llm-pi-ai', 'config': {'providers': {'kstudio-bai': {
            'apiKeyEnv': 'KSTUDIO_DSH_API_KEY', 'api': protocol, 'baseURL': api_base,
            'models': [effective_configuration.model_descriptor()],
            'retryPolicy': provider_retry_policy(effective_configuration.request_retries)}}}},
        {'id': 'agent-default-model', 'config': {'provider': 'kstudio-bai', 'model': model, **({} if effective_configuration.sdk_effort is None else {'reasoningEffort':effective_configuration.sdk_effort})}},
        {'id': 'compaction-basic', 'config': effective_configuration.compaction()},
        *[{'id':tool,'config':{'provider':provider,'toolName':name,'modelSelectionSettings':False,'agentOptions':{'provider':'kstudio-bai','model':model,**({} if effective_configuration.sdk_effort is None else {'reasoningEffort':effective_configuration.sdk_effort}),'maxTokens':effective_configuration.max_output_tokens}}}
          for tool,provider,name in (('tool-subagent','spawn','subagent'),('tool-subagent-fork','fork','subagent_fork'))],
        {'id': 'agent-instructions', 'config': {'projectRootMarkers':['.kstudio-project','.git'], 'maxBytes':65536}},
        {'insert': [{'id': 'kstudio-host-tools', 'name': Path(host_plugin).as_posix()}]},
    ]
    from .dsh_security import production_restrictions
    rows.extend({'id': name, 'disabled': True} for name in production_restrictions())
    # Preserve upstream implementations for compaction, tools, MD and subagents.
    # Runtime adapters and installed packages own their normal registrations.
    roots = json.loads(os.environ.get('KSTUDIO_DSH_SKILL_DIRS', '[]'))
    if not isinstance(roots, list) or any(not isinstance(p, str) or not Path(p).is_dir() for p in roots):
        raise ValueError('Skill roots must be existing directories.')
    rows.append({'id':'skill-filesystem','config':{'customSkillDirs':roots,'includeDefaultRoots':False,'watch':False}})
    config_path = os.environ.get('KSTUDIO_DSH_MCP_CONFIG')
    if config_path:
        from .dsh_security import trusted_development
        if not trusted_development():
            raise ValueError('External MCP processes are unavailable in the production file-proxy profile; use the reviewed host connector.')
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
