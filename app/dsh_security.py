"""Tool-level production policy, explicitly NOT an operating-system sandbox.

Official orchestration remains intact. Unconfined process/file capabilities
require a separate operator-selected development profile. Project file access
uses the reviewed workspace proxy; native writes use ProjectRuby only.
"""
import os

RESTRICTED_PLUGINS = tuple('tool-plugin-manager plugin-manager config-editor settings remote-access typert-gateway tool-workflow tool-working-directory tool-bash tool-pwsh tool-jobs tool-fs tool-fs-search workspace-dependencies skill-office agent-instructions'.split())


def execution_policy():
    value=os.environ.get('KSTUDIO_DSH_EXECUTION_POLICY','production-file-proxy')
    if value not in ('production-file-proxy','trusted-development'):
        raise ValueError('Unknown DSH execution policy.')
    return value


def trusted_development():
    return execution_policy()=='trusted-development'


def production_restrictions():
    return () if trusted_development() else RESTRICTED_PLUGINS


def evidence():
    return {'policy':execution_policy(),'os_sandbox':False,
            'arbitrary_subprocess':trusted_development(),
            'file_access':'same-user unrestricted' if trusted_development() else 'reviewed project workspace proxy',
            'subagents':'read-only tools','native_writer':'ProjectRuby',
            'remaining_boundary':'Host/SDK and SketchUp Ruby run as the current user. A malicious local process or arbitrary Ruby is not OS-confined.'}
