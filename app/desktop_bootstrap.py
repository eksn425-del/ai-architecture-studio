"""Packaged BYOK bootstrap: all executable dependencies belong to the bundle."""
from __future__ import annotations

import os
import json
import hashlib
import uuid
from pathlib import Path


def relocated_public_connector(settings: dict, bundle: Path) -> dict | None:
    """Recognize only immutable version slots of this same K Studio installation.

    Pure path/settings decision shared with the runtime resolver. Never redirect
    a custom connector merely because its filename resembles ours.
    """
    bundle = Path(bundle).resolve()
    current = bundle.parent
    if bundle.name != '_internal' or current.parent.name.lower() != 'versions':
        return None
    command = settings.get('command')
    env = settings.get('env', {})
    if (not isinstance(command, str) or settings.get('args') != [] or
            not isinstance(env, dict) or not isinstance(env.get('KSTUDIO_PUBLIC_CONNECTOR_ROOT'), str) or
            not isinstance(env.get('ARCHFLOW_GENERATED_SCRIPT_DIR'), str)):
        return None
    paired = Path(env['KSTUDIO_PUBLIC_CONNECTOR_ROOT'])
    scripts = Path(env['ARCHFLOW_GENERATED_SCRIPT_DIR'])
    old = Path(command)
    if (not paired.is_absolute() or not scripts.is_absolute() or
            scripts.resolve() != (paired / 'generated_scripts').resolve() or
            not old.is_absolute() or old.is_symlink() or old.name.lower() != 'kstudioconnector.exe'):
        return None
    old = old.resolve()
    if old.parent.parent != current.parent or old.parent == current:
        return None
    executable = current / 'KStudioConnector.exe'
    if executable.is_symlink() or not executable.is_file():
        raise RuntimeError('当前安装版本缺少 K Studio 连接器程序，原连接配置已保留，请修复安装。')
    changed = dict(settings, command=str(executable))
    cwd = settings.get('cwd')
    if isinstance(cwd, str) and Path(cwd).is_absolute():
        if Path(cwd).resolve() == old.parent:
            changed['cwd'] = str(current)
        elif Path(cwd).resolve() == old.parent / '_internal':
            changed['cwd'] = str(bundle)
    return changed


def migrate_public_connector(bundle: Path, data: Path) -> dict:
    """Backup exact bytes, then relocate only a known product bridge atomically."""
    target = Path(data) / 'bridge.json'
    if not target.exists() and not target.is_symlink():
        return {'status': 'not_configured'}
    if target.is_symlink() or not target.is_file():
        raise RuntimeError('连接配置不是普通文件，未进行升级覆盖。请检查本机 bridge.json。')
    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('duplicate configuration field')
            value[key] = item
        return value
    try:
        original = target.read_bytes()
        settings = json.loads(original.decode('utf-8-sig'), object_pairs_hook=unique_object)
        if (not isinstance(settings, dict) or not isinstance(settings.get('command'), str) or
            not settings['command'].strip() or not isinstance(settings.get('args', []), list) or
            not isinstance(settings.get('env', {}), dict) or
            not isinstance(settings.get('cwd', ''), (str, type(None)))):
            raise ValueError('invalid configuration structure')
    except (ValueError, UnicodeError, OSError) as error:
        raise RuntimeError('本机连接配置损坏，已保留原 bridge.json；请修复配置后重试，升级未覆盖它。') from error
    changed = relocated_public_connector(settings, bundle)
    if changed is None:
        return {'status': 'preserved'}
    backups = Path(data) / 'bridge-backups'
    if backups.is_symlink() or (hasattr(backups, 'is_junction') and backups.is_junction()):
        raise RuntimeError('连接配置备份目录发生重定向，原配置已保留。')
    backups.mkdir(exist_ok=True)
    backup = backups / ('bridge-' + hashlib.sha256(original).hexdigest() + '.json')
    if backup.exists() or backup.is_symlink():
        if backup.is_symlink() or backup.read_bytes() != original:
            raise RuntimeError('连接配置备份校验失败，原配置已保留。')
    else:
        with backup.open('xb') as stream:
            stream.write(original)
            stream.flush()
            os.fsync(stream.fileno())
    temporary = target.with_name('bridge.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write((json.dumps(changed, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        if target.is_symlink() or target.read_bytes() != original:
            raise RuntimeError('连接配置在升级期间发生变化，未覆盖新的配置，请重试。')
        os.replace(temporary, target)
    except OSError as error:
        raise RuntimeError('连接配置升级未完成，原配置和备份已保留，请重试。') from error
    finally:
        temporary.unlink(missing_ok=True)
    return {'status': 'relocated', 'backup': str(backup)}


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
    connector_upgrade = migrate_public_connector(bundle, data)
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
        'KSTUDIO_DSH_NATIVE_WRITER': 'typed',
        'KSTUDIO_DSH_SDK_SITE': str(bundle),
        'KSTUDIO_DSH_BIN': str(launcher),
        'KSTUDIO_DSH_MAX_OUTPUT_TOKENS': '32768',
        'PATH': str(node.parent) + os.pathsep + os.environ.get('PATH', ''),
    })
    adai = bundle / 'third-party/adai/skill'
    if adai.is_dir():
        os.environ['KSTUDIO_DSH_SKILL_DIRS'] = json.dumps([str(adai)])
    return {'runtime': runtime, 'settings': settings, 'node': node, 'launcher': launcher,
            'connector_upgrade': connector_upgrade}
