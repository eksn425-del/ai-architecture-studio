from app.dsh_network import node_network_environment


def test_proxy_inherited_and_host_tools_stay_local():
    env = {'HTTPS_PROXY': 'http://proxy.test:2080', 'NO_PROXY': 'internal.test'}
    got = node_network_environment(env, {})
    assert got['NODE_USE_ENV_PROXY'] == '1'
    assert got['https_proxy'] == env['HTTPS_PROXY']
    assert set(got['NO_PROXY'].split(',')) >= {'internal.test', 'localhost', '127.0.0.1', '[::1]'}
    assert 'NODE_USE_ENV_PROXY' not in env


def test_windows_static_proxy_for_gui_without_shell_environment():
    got = node_network_environment({}, {'http': 'http://proxy.test:2080', 'https': 'http://proxy.test:2080', 'no': '*.internal;<local>'})
    assert got['HTTPS_PROXY'] == 'http://proxy.test:2080'
    assert '*.internal' in got['NO_PROXY']
    assert '<local>' not in got['NO_PROXY']


def test_explicit_lowercase_and_optout_are_preserved():
    got = node_network_environment({'https_proxy': 'http://chosen.test', 'HTTPS_PROXY': 'http://other.test'}, {})
    assert got['HTTPS_PROXY'] == 'http://chosen.test'
    assert node_network_environment({'NODE_USE_ENV_PROXY':'0', 'HTTPS_PROXY':'http://chosen.test'}, {}) == {'NODE_USE_ENV_PROXY':'0'}


def test_no_guessed_proxy_or_registry_override():
    assert node_network_environment({}, {}) == {}
    assert node_network_environment({'HTTPS_PROXY':''}, {'https':'http://registry.test'}) == {}
    assert node_network_environment({'ALL_PROXY':'socks5://localhost:1080'}, {}) == {}


def test_transport_attempt_zero_is_unknown_billing():
    from app.dsh_runtime import reported_usage
    event = {'type':'assistant/attempt', 'data':{'stream':[{'chunk':{'type':'usage', 'usage':{'inputTokens':0,'outputTokens':0,'totalTokens':0}}}]}}
    assert reported_usage([event]) == (None, None)
