// Controlled I/O tests execute production functions, not a browser/native-model claim.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../app/static/studio.js'), 'utf8');
function production(...names) {
  return names.map(name => {
    const pattern = new RegExp(`^(?:async )?function ${name}\\(`, 'm');
    const start = source.search(pattern);
    assert.notEqual(start, -1, `${name} must exist`);
    return source.slice(start, source.indexOf('\n}', start) + 2);
  }).join('\n');
}
function context(program, extra = {}) {
  const sandbox = vm.createContext({ ...extra });
  vm.runInContext(program, sandbox);
  return sandbox;
}
const route = { provider: 'codex-app-server', model: 'gpt-6.1-sol', reasoning_effort: 'medium' };
function readiness(messages = [], options = {}) {
  const state = {
    projectId: 'p',
    project: { context: { project_id: 'p', conversation: messages }, agent_session: { ...route, thread_id: 'configured', last_reply: 'old reply' } },
    ...options.state,
  };
  const sandbox = context(production('routeReadinessLabel'), {
    state,
    routeInfo: () => options.route || route,
    routeAvailable: () => options.available !== false,
  });
  return sandbox.routeReadinessLabel('economy');
}
function receipt(overrides = {}) {
  return { role: 'assistant', content: '已整理计划', metadata: { ...route, ...overrides } };
}
test('configured/default session metadata never proves an invocation', () => {
  assert.equal(readiness(), '已检测到本机程序；调用未验证');
  assert.equal(readiness([], { route: { ...route, provider: 'litellm' } }), '已配置；调用未验证');
});
test('a matching recorded assistant response verifies this project and selected route', () => {
  assert.equal(readiness([receipt()]), '本会话已有成功调用');
  assert.equal(readiness([receipt({ provider: 'litellm' })], { route: { ...route, provider: 'litellm' } }), '本会话已有成功调用');
});
for (const [name, messages, options] of [
  ['other provider', [receipt({ provider: 'litellm' })], {}],
  ['other model', [receipt({ model: 'gpt-6-astra' })], {}],
  ['other effort', [receipt({ reasoning_effort: 'low' })], {}],
  ['user metadata', [{ ...receipt(), role: 'user' }], {}],
  ['failed response', [receipt({ status: 'failed' })], {}],
  ['interrupted response', [receipt({ status: 'interrupted' })], {}],
  ['errored response', [receipt({ error: 'offline' })], {}],
  ['empty reply', [{ ...receipt(), content: '' }], {}],
  ['different visible project', [receipt()], { state: { projectId: 'other' } }],
]) {
  test(`${name} cannot verify the current route`, () => assert.equal(readiness(messages, options), '已检测到本机程序；调用未验证'));
}
test('current unavailability takes precedence over a historical successful invocation', () => {
  assert.equal(readiness([receipt()], { available: false }), '本机 Codex 不可用');
});
test('switching to a new project does not carry verification across sessions', () => {
  const state = { projectId: 'p', project: { context: { project_id: 'p', conversation: [receipt()] } } };
  const sandbox = context(production('routeReadinessLabel'), { state, routeInfo: () => route, routeAvailable: () => true });
  assert.equal(sandbox.routeReadinessLabel('economy'), '本会话已有成功调用');
  state.projectId = 'q'; state.project = { context: { project_id: 'q', conversation: [] } };
  assert.equal(sandbox.routeReadinessLabel('economy'), '已检测到本机程序；调用未验证');
});
test('header and both tier labels refresh from the active project receipts', () => {
  const nodes = {}, options = {};
  const $ = id => nodes[id] ||= { querySelector: value => options[value] ||= {} };
  const state = { projectId: 'p', project: { context: { project_id: 'p', conversation: [receipt()] } } };
  const sandbox = context(production('routeReadinessLabel', 'refreshTierLabels'), {
    $, state, routeInfo: tier => tier === 'premium' ? { ...route, model: 'gpt-6-astra' } : route, routeAvailable: () => true,
  });
  sandbox.refreshTierLabels();
  assert.match(nodes['brain-status'].textContent, /本会话已有成功调用/);
  assert.match(options['option[value="economy"]'].textContent, /本会话已有成功调用/);
  assert.match(options['option[value="premium"]'].textContent, /调用未验证/);
});
function connectionContext(api) {
  const nodes = {};
  const state = { projectId: 'p', busy: false };
  const $ = id => nodes[id] ||= { open: false, disabled: false, showModal() { this.open = true; }, close() { this.open = false; } };
  const calls = { start: 0, send: 0 };
  const sandbox = context('let connectDialogGeneration=0,pendingExecutionProject=null;\n' + production('openConnectDialog', 'closeConnectDialog', 'isCurrentConnectDialog', 'checkConnectDialog', 'connectCurrentProject'), {
    $, state, api, friendlyError: e => e.message,
    startAgentSession: async () => { calls.start++; return true; },
    sendConversation: async () => { calls.send++; },
  });
  return { sandbox, nodes, $, state, calls };
}
test('each connection opening resets stale status/buttons and old approval intent', async () => {
  const { sandbox, $ , calls } = connectionContext(async () => ({ reachable: true }));
  sandbox.openConnectDialog(true);
  $('connect-status').textContent = 'old progress'; $('connect-open').disabled = true;
  sandbox.closeConnectDialog(); sandbox.openConnectDialog();
  assert.equal($('connect-status').textContent, '交流与分析无需连接；开始建模前才需要连接。');
  assert.equal($('connect-open').disabled, false);
  await sandbox.connectCurrentProject();
  assert.deepEqual(calls, { start: 1, send: 0 });
});
test('closing and reopening discards a late connection-check response', async () => {
  let resolve;
  const { sandbox, $ } = connectionContext(() => new Promise(r => resolve = r));
  sandbox.openConnectDialog(); const request = sandbox.checkConnectDialog();
  sandbox.closeConnectDialog(); sandbox.openConnectDialog();
  resolve({ reachable: true }); await request;
  assert.equal($('connect-status').textContent, '交流与分析无需连接；开始建模前才需要连接。');
});
test('dismissing before the initial connector check resolves cannot start or execute a model', async () => {
  let resolve;
  const { sandbox, calls } = connectionContext(() => new Promise(r => resolve = r));
  sandbox.openConnectDialog(true); const request = sandbox.connectCurrentProject();
  sandbox.closeConnectDialog(); resolve({ reachable: true }); await request;
  assert.deepEqual(calls, { start: 0, send: 0 });
});
test('a project switch discards pending connector callbacks', async () => {
  let resolve;
  const { sandbox, state, calls } = connectionContext(() => new Promise(r => resolve = r));
  sandbox.openConnectDialog(true); const request = sandbox.connectCurrentProject();
  state.projectId = 'q'; resolve({ reachable: true }); await request;
  assert.deepEqual(calls, { start: 0, send: 0 });
});
test('closing during session startup cancels only the pending automatic execution', async () => {
  let resolve;
  const { sandbox, calls } = connectionContext(async () => ({ reachable: true }));
  sandbox.startAgentSession = () => { calls.start++; return new Promise(r => resolve = r); };
  sandbox.openConnectDialog(true); const request = sandbox.connectCurrentProject();
  await new Promise(r => setImmediate(r)); sandbox.closeConnectDialog(); resolve(true); await request;
  assert.deepEqual(calls, { start: 1, send: 0 });
});
test('repeated connection clicks only start and execute once', async () => {
  let resolve, requests = 0;
  const { sandbox, calls } = connectionContext(() => { requests++; return new Promise(r => resolve = r); });
  sandbox.openConnectDialog(true);
  const first = sandbox.connectCurrentProject(); await sandbox.connectCurrentProject();
  resolve({ reachable: true }); await first;
  assert.equal(requests, 1); assert.deepEqual(calls, { start: 1, send: 1 });
});
test('Escape uses the same cancellation path as the close button', () => {
  assert.match(source, /\$\("connect-dialog"\)\.addEventListener\("cancel", event => \{ event\.preventDefault\(\); closeConnectDialog\(\); \}\)/);
});
function conversationContext() {
  const nodes = {}, calls = { results: [], tabs: [], requests: 0 };
  const state = { projectId: 'p', project: { agent_session: { status: 'ready', reconstruction_state: 'building', ruby_state: { old: { revision: 9 } } } }, busy: false, planEditing: false };
  const $ = id => nodes[id] ||= { value: id === 'conversation-input' ? '请检查当前模型' : id === 'workflow-mode' ? 'image_reconstruction' : 'economy', open: false };
  let resolve;
  const sandbox = context('let pendingMessage=null,pendingExecutionProject=null;\n' + production('sendConversation'), {
    $, state, localStorage: { setItem() {} }, saveDraft() {}, executionUserMessage: x => x || "确认，按当前计划开始建模。", isBuildApproval: () => false,
    sourceImages: () => [], pendingAttachmentSources: () => [], routeInfo: () => route, setBusy() {}, showResults: value => calls.results.push(value),
    beginProgress() {}, setStatus() {}, startLiveProgress() {}, loadParameterPlan: async () => {}, updateHeader() {},
    showToast() {}, setTab: value => calls.tabs.push(value), friendlyError: e => e.message, endProgress() {},
    observeRunningTurn: async () => {}, loadProject: async () => {},
    api: async () => { calls.requests++; return new Promise(r => resolve = r); },
  });
  return { sandbox, state, $, calls, respond: result => resolve(result) };
}
for (const [name, flags, opens] of [
  ['no receipt, even with existing geometry', {}, false],
  ['explicit no-write/no-save', { geometry_committed: false, checkpoint_saved: false }, false],
  ['truthy strings are not receipts', { geometry_committed: 'true', checkpoint_saved: 'true' }, false],
  ['host confirmed geometry commit', { geometry_committed: true, checkpoint_saved: false }, true],
  ['host confirmed checkpoint', { geometry_committed: false, checkpoint_saved: true }, true],
]) {
  test(`result panel: ${name}`, async () => {
    const { sandbox, state, calls, respond } = conversationContext();
    const pending = sandbox.sendConversation(null);
    respond({ project: state.project, reply: 'ok', agent: { agent_action: 'execute', ...flags } });
    await pending;
    assert.equal(calls.results.includes(true), opens);
    assert.equal(calls.tabs.includes('model'), opens);
  });
}
test('serial sending and next draft survive the result gating change', async () => {
  const { sandbox, state, $, calls, respond } = conversationContext();
  const pending = sandbox.sendConversation(null);
  assert.equal($('conversation-input').value, '');
  $('conversation-input').value = '下一条要求'; await sandbox.sendConversation(null);
  respond({ project: state.project, reply: 'ok', agent: { agent_action: 'execute', geometry_committed: false, checkpoint_saved: false } });
  await pending;
  assert.equal(calls.requests, 1); assert.equal($('conversation-input').value, '下一条要求'); assert.equal(state.busy, false);
});

const { createHash, webcrypto } = require('node:crypto');
function planContext(api, crypto = webcrypto, pending = undefined) {
  const nodes = {}, state = { projectId: 'p', project: { agent_session: { reconstruction_state: 'planned' } }, displayedPlan: { projectId: 'p', sha256: 'old' } };
  const $ = id => nodes[id] ||= { addEventListener() {}, insertAdjacentHTML(position, content) { this.innerHTML = content + (this.innerHTML || ""); } };
  const sandbox = context('let planRequestId=0;\n' + production('escapeHtml', 'parameterPlanMarkup', 'loadParameterPlan'), {
    $, state, api: async target => {
      if (target.endsWith('/agent/pending-plan') && pending !== undefined) {
        if (pending instanceof Error) throw pending;
        return pending;
      }
      if (target.endsWith('/agent/pending-plan')) return { pending_plan_id: 'pending-' + state.projectId,
        plan_sha256: createHash('sha256').update(state.testCard.replace(/\r\n?/g, '\n'), 'utf8').digest('hex') };
      const card = await api(target); state.testCard = card; return card;
    }, crypto, TextEncoder, projectFileUrl: value => value, chatText: value => value,
  });
  return { sandbox, state, $, nodes };
}
test('scope renders explicitly and escapes feature/state without altering unrelated card content', () => {
  const { sandbox } = planContext(async () => '');
  const card = '# Plan\n```json\n{"unrelated":true}\n```\n<design_scope>\n[{"feature_id":"roof<test>","requested_state":"replace&keep"}]\n</design_scope>\nRetain all other geometry.';
  const html = sandbox.parameterPlanMarkup(card);
  assert.match(html, /本轮功能范围/); assert.match(html, /roof&lt;test&gt;：replace&amp;keep/);
  assert.ok(html.includes('```json\n{"unrelated":true}\n```'));
  assert.ok(html.endsWith('Retain all other geometry.'));
  assert.equal(html.includes('<design_scope>'), false);
});
for (const invalid of ['<design_scope>invalid</design_scope>', '<design_scope>{}</design_scope>', '<design_scope>[]</design_scope>', '<design_scope>[{"feature_id":"roof","requested_state":"add"}]</design_scope><design_scope>[]</design_scope>']) {
  test(`malformed or ambiguous scope remains visible: ${invalid}`, () => {
    const { sandbox } = planContext(async () => '');
    const html = sandbox.parameterPlanMarkup(invalid);
    assert.match(html, /格式有误/); assert.ok(html.endsWith(invalid));
  });
}
for (const [name, newline] of [['LF', '\n'], ['CRLF', '\r\n'], ['CR', '\r']]) {
  test(`approved Chinese plan hash matches host universal newlines: ${name}`, async () => {
    const canonical = '# 屋顶改造\n<design_scope>\n[{"feature_id":"入口雨棚","requested_state":"保留现状"}]\n</design_scope>\n';
    const card = canonical.replace(/\n/g, newline);
    const { sandbox, state, $ } = planContext(async () => card);
    await sandbox.loadParameterPlan();
    assert.equal(state.displayedPlan.projectId, 'p');
    assert.equal(state.displayedPlan.sha256, createHash('sha256').update(canonical, 'utf8').digest('hex'));
    assert.match($('parameter-plan-content').innerHTML, /入口雨棚：保留现状/);
    assert.ok($('parameter-plan-content').innerHTML.includes('# 屋顶改造' + newline));
  });
}
test('failed plan load clears old hash and does not leave old plan approvable', async () => {
  const { sandbox, state, $ } = planContext(async () => { throw Error('offline'); });
  await sandbox.loadParameterPlan();
  assert.equal(state.displayedPlan, null); assert.match($('parameter-plan-content').textContent, /重新加载计划/);
});
test('hash failure never presents an unverified approval snapshot', async () => {
  const { sandbox, state } = planContext(async () => '# Plan', { subtle: { digest: async () => { throw Error('unavailable'); } } });
  await sandbox.loadParameterPlan(); assert.equal(state.displayedPlan, null);
});
test('newer project/card wins over a late plan fetch and hash', async () => {
  const pending = [];
  const { sandbox, state, $ } = planContext(() => new Promise(resolve => pending.push(resolve)));
  const first = sandbox.loadParameterPlan(); state.projectId = 'q';
  const second = sandbox.loadParameterPlan(); pending[1]('Q plan'); await second;
  pending[0]('P old plan'); await first;
  assert.equal(state.displayedPlan.projectId, 'q');
  assert.equal(state.displayedPlan.sha256, createHash('sha256').update('Q plan').digest('hex'));
  assert.ok($('parameter-plan-content').innerHTML.endsWith('Q plan'));
});
for (const [name, action, displayedProject, included] of [
  ['explicit execute of displayed plan', 'execute', 'p', true],
  ['auto discussion provides context, not approval', 'auto', 'p', true],
  ['new plan request carries displayed context before invalidation', 'plan', 'p', true],
  ['different-project snapshot', 'auto', 'q', false],
]) {
  test(`approval snapshot is bounded: ${name}`, async () => {
    const { sandbox, state, $ } = conversationContext();
    state.displayedPlan = { projectId: displayedProject, sha256: 'a'.repeat(64), pendingPlanId: 'pending-p' };
    $('conversation-input').value = action === 'execute' ? '' : '请整理计划';
    let body;
    sandbox.api = async (_, options) => { body = JSON.parse(options.body); return { project: state.project, reply: 'ok', agent: {} }; };
    await sandbox.sendConversation(null, action);
    assert.equal(Object.hasOwn(body, 'approved_plan_sha256'), included);
    if (included) assert.equal(body.approved_plan_sha256, 'a'.repeat(64));
    assert.equal(body.approval_gesture, action === 'execute' ? 'plan_button' : undefined);
    if (action === 'plan') assert.equal(state.displayedPlan, null);
  });
}

for (const [label, pending] of [
  ['missing ID', { plan_sha256: createHash('sha256').update('# Plan').digest('hex') }],
  ['mismatched hash', { pending_plan_id: 'pending-p', plan_sha256: 'different' }],
  ['consumed', { pending_plan_id: 'pending-p', plan_sha256: createHash('sha256').update('# Plan').digest('hex'), consumed: true }],
  ['unavailable', Error('controlled offline')],
]) {
  test(`pending plan ${label} retains the readable card but never an approval snapshot`, async () => {
    const { sandbox, state, $ } = planContext(async () => '# Plan', webcrypto, pending);
    await sandbox.loadParameterPlan();
    assert.equal(state.displayedPlan, null);
    assert.match($('parameter-plan-content').innerHTML, /# Plan/);
    assert.match($('parameter-plan-content').innerHTML, label === 'consumed' ? /检查副本并恢复批准按钮/ : /刷新或重新整理计划/);
  });
}

test('executed archived plan stays once in conversation without granting another approval', async () => {
  const card = 'one immutable plan', sha256 = createHash('sha256').update(card).digest('hex');
  const { sandbox, state, $ } = planContext(async () => card, webcrypto, {pending_plan_id:'p',plan_sha256:sha256,consumed:true});
  state.project.agent_session.reconstruction_state='building';
  state.project.context={conversation:[{role:'assistant',metadata:{plan_text:card,plan_sha256:sha256}}]};
  await sandbox.loadParameterPlan();
  assert.equal($('parameter-plan').hidden,true);
  assert.equal(state.displayedPlan,null);
  assert.match($('parameter-plan-content').innerHTML,/已执行/);
  assert.doesNotMatch($('parameter-plan-content').innerHTML,/版本尚未核验/);
});
