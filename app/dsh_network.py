"""Honor existing user proxy settings in the bundled Node process only."""
import os
import urllib.request
from urllib.parse import urlparse


def node_network_environment(environ=None, registry=None):
    env = os.environ if environ is None else environ
    result = {}
    # An explicit Node opt-out remains an opt-out. Never change machine settings.
    if env.get('NODE_USE_ENV_PROXY') == '0':
        return {'NODE_USE_ENV_PROXY': '0'}
    explicit = any(name.lower() in {'http_proxy', 'https_proxy', 'all_proxy'} for name in env)
    if registry is None:
        registry = {}
        if not explicit and os.name == 'nt':
            try:
                registry = urllib.request.getproxies_registry()
            except OSError:
                pass
    for scheme in ('http', 'https'):
        name = scheme + '_proxy'
        if name in env or name.upper() in env:
            value = env.get(name, env.get(name.upper(), ''))
        elif explicit:
            value = env.get('all_proxy', env.get('ALL_PROXY', ''))
        else:
            value = registry.get(scheme, '')
        # Node supports HTTP(S) proxies. Do not reinterpret SOCKS/PAC as HTTP.
        if value and urlparse(value).scheme in {'http', 'https'}:
            result[name.upper()] = value
            result[name] = value
    if not result:
        return {}
    bypass = env.get('no_proxy', env.get('NO_PROXY', registry.get('no', '')))
    entries = [part.strip() for part in bypass.replace(';', ',').split(',') if part.strip() and part.strip() != '<local>']
    for host in ('localhost', '127.0.0.1', '::1', '[::1]'):
        if host not in entries:
            entries.append(host)
    result.update(NODE_USE_ENV_PROXY='1', NO_PROXY=','.join(entries), no_proxy=','.join(entries))
    return result
