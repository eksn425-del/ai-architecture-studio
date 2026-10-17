// Production functions with controlled DOM/I/O stubs. No provider, browser or native GUI is exercised.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../app/static/studio.js'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, '../app/static/index.html'), 'utf8');
function production(...names) {
  return names.map(name => {
    const start = source.search(new RegExp(`^(?:async )?function ${name}\\(`, 'm'));
    assert.notEqual(start, -1, `${name} must exist`);
    return source.slice(start, source.indexOf('\n}', start) + 2);
  }).join('\n');
}
function composer({ text = '', stage = 'planned', ready = true, refs = [], history = [] } = {}) {
  const requests = [], notices = [], nodes = {};
  const state = {
    projectId: 'p', busy: false, planEditing: false,
    displayedPlan: { projectId: 'p', sha256: 'a'.repeat(64), pendingPlanId: 'pending-p' },
    project: { agent_session: { reconstruction_state: stage, status: ready ? 'ready' : 'conversation' },
      context: { references: refs, conversation: history, brief: { source_files: [] }, site: { source_files: [] } } },
  };
  const $ = id => nodes[id] ||= {
    value: id === 'conversation-input' ? text : id === 'workflow-mode' ? 'image_reconstruction' : 'economy',
    open: false, hidden: false,
  };
  const context = vm.createContext({
    $, state, TextEncoder, setTimeout, clearTimeout, crypto: require('node:crypto').webcrypto,
    localStorage: { setItem() {} }, saveDraft() {}, routeInfo: () => ({ model: 'stub-only' }), setBusy() {},
    showResults() {}, beginProgress() {}, setStatus() {}, startLiveProgress() {}, loadParameterPlan: async () => {},
    updateHeader() {}, showToast: text => notices.push(text), setTab() {}, friendlyError: e => e.message,
    endProgress() {}, observeRunningTurn: async () => {}, loadProject: async () => {},
    openConnectDialog: () => notices.push('connection requested'),
    isBuildApproval() { throw Error('Legacy keyword routing must never run'); },
    projectFileUrl: value => '/files/' + value.split('/').map(encodeURIComponent).join('/'),
    api: async (url, options) => {
      requests.push({ url, body: options && JSON.parse(options.body) });
      return { project: state.project, reply: 'controlled response', agent: {} };
    },
  });
  vm.runInContext('let pendingMessage=null;\n' + production('escapeHtml', 'executionUserMessage', 'sourceImages', 'pendingImages',
    'pendingAttachmentSources', 'referenceRoleMarkup', 'renderReferenceComposer', 'renderAttachments', 'sendConversation', 'correctReferenceRole', 'renderTurnControls', 'renderNativeTurnEvent', 'cancelConversationTurn'), context);
  return { context, state, $, nodes, requests, notices };
}
for (const text of ['我批准', '确认', '好，照做', '不要开始建模', '我批准，但是屋顶要改为双坡', '如果我批准会怎样？', '  我批准\n请保留原图。  ']) {
  test(`normal text reaches the contextual host verbatim and auto: ${text}`, async () => {
    const { context, requests } = composer({ text });
    await context.sendConversation(null);
    assert.equal(requests.length, 1);
    assert.equal(requests[0].body.message, text);
    assert.equal(requests[0].body.agent_action, 'auto');
    assert.equal(requests[0].body.approved_plan_sha256, 'a'.repeat(64));
    assert.equal(requests[0].body.approved_pending_plan_id, 'pending-p');
    assert.match(requests[0].body.client_request_id, /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/);
    assert.equal(Object.hasOwn(requests[0].body, 'approval_gesture'), false);
  });
}
test('plan editing mode cannot reroute a normal message by itself', async () => {
  const { context, state, requests } = composer({ text: '为什么要加这堵墙？' });
  state.planEditing = true;
  await context.sendConversation(null);
  assert.equal(requests[0].body.agent_action, 'auto');
  assert.equal(requests[0].body.message, '为什么要加这堵墙？');
});
test('explicit approval only adds a gesture for a clean composer and current displayed plan', async () => {
  const { context, requests } = composer({ text: '  \n ' });
  await context.sendConversation(null, 'execute');
  assert.equal(requests.length, 1);
  assert.equal(requests[0].body.agent_action, 'execute');
  assert.equal(requests[0].body.approval_gesture, 'plan_button');
  assert.equal(requests[0].body.approved_plan_sha256, 'a'.repeat(64));
  assert.equal(requests[0].body.message, '确认，按当前计划开始建模。');
});
test('approval button with a changed draft sends the draft, never a forged approval gesture', async () => {
  const text = '  先把宽度改成12米，不要开始。\n';
  const { context, requests } = composer({ text });
  await context.sendConversation(null, 'execute');
  assert.equal(requests.length, 1);
  assert.equal(requests[0].body.message, text);
  assert.equal(requests[0].body.agent_action, 'auto');
  assert.equal(Object.hasOwn(requests[0].body, 'approval_gesture'), false);
});
for (const reason of ['missing snapshot', 'missing pending plan ID', 'other project', 'pending image', 'pending document', 'plan editing']) {
  test(`clean approval is blocked while ${reason}, with composer state retained`, async () => {
    const { context, state, requests, $ } = composer({ text: '\n ' });
    if (reason === 'missing snapshot') state.displayedPlan = null;
    if (reason === 'missing pending plan ID') delete state.displayedPlan.pendingPlanId;
    if (reason === 'other project') state.displayedPlan.projectId = 'q';
    if (reason === 'pending image') state.project.context.references.push({ type: 'image', source: 'inputs/reference/new.png' });
    if (reason === 'pending document') state.project.context.brief.source_files.push('inputs/brief/new.txt');
    if (reason === 'plan editing') state.planEditing = true;
    const before = JSON.stringify(state);
    await context.sendConversation(null, 'execute');
    assert.equal(requests.length, 0);
    assert.equal($('conversation-input').value, '\n ');
    assert.equal(JSON.stringify(state), before);
  });
}
test('a failed draft submission restores the original exact text', async () => {
  const text = '  屋顶改低一点\n';
  const { context, $, state } = composer({ text });
  context.api = async () => { throw Error('controlled offline'); };
  await context.sendConversation(null, 'execute');
  assert.equal($('conversation-input').value, text);
  assert.equal(state.busy, false);
});
test('repeat clicks are ignored and a next-turn draft survives the pending response', async () => {
  const { context, $, state } = composer({ text: '我批准' });
  let resolve, calls = 0;
  context.api = async () => { calls++; return new Promise(r => resolve = r); };
  const first = context.sendConversation(null);
  $('conversation-input').value = '  下一条草稿\n';
  await context.sendConversation(null, 'execute');
  resolve({ project: state.project, reply: 'controlled response', agent: {} });
  await first;
  assert.equal(calls, 1);
  assert.equal($('conversation-input').value, '  下一条草稿\n');
});
const image = (name, extra = {}) => ({ type: 'image', source: `inputs/reference/${name}`, evidence_role: 'target_building',
  role_origin: 'user', role_reason: 'explicit_user_correction', ...extra });
test('submitted image role controls are outside the composer and collapsed by default', () => {
  const form = html.slice(html.indexOf('<form id="conversation-form"'), html.indexOf('</form>', html.indexOf('<form id="conversation-form"')));
  assert.doesNotMatch(form, /submitted-reference/);
  assert.match(html, /<details id="submitted-reference-history"[^>]* hidden>/);
  assert.doesNotMatch(html.match(/<details id="submitted-reference-history"[^>]*>/)[0], / open(?:[ >])/);
});
test('pending files and images are separated from submitted history, including legacy message receipts', () => {
  const refs = [image('sent.png', { submitted_at: '2026-10-17', evidence_model_revisions: { model: 5 } }),
    image('legacy.png'), image('new.png')];
  const history = [{ metadata: { attachments: ['inputs/reference/legacy.png', 'inputs/brief/old.txt'] } }];
  const { context, state, $, nodes } = composer({ refs, history });
  state.project.context.brief.source_files = ['inputs/brief/old.txt', 'inputs/brief/new.txt'];
  context.renderReferenceComposer(); context.renderAttachments();
  assert.deepEqual(Array.from(context.pendingAttachmentSources()), ['inputs/reference/new.png', 'inputs/brief/new.txt']);
  assert.match(nodes['reference-gallery'].innerHTML, /new\.png/);
  assert.doesNotMatch(nodes['reference-gallery'].innerHTML, /sent\.png|legacy\.png/);
  assert.match(nodes['reference-role-review'].innerHTML, /new\.png/);
  assert.doesNotMatch(nodes['reference-role-review'].innerHTML, /sent\.png|legacy\.png/);
  assert.match(nodes['submitted-reference-roles'].innerHTML, /sent\.png/);
  assert.match(nodes['submitted-reference-roles'].innerHTML, /legacy\.png/);
  assert.match(nodes['submitted-reference-roles'].innerHTML, /model: r5/);
  assert.match(nodes['attachment-list'].innerHTML, /new\.txt/);
  assert.doesNotMatch(nodes['attachment-list'].innerHTML, /old\.txt/);
  assert.equal($('submitted-reference-history').open, false);
  $('submitted-reference-history').open = true;
  context.renderReferenceComposer();
  assert.equal($('submitted-reference-history').open, true);
});
test('ambiguous roles stay visible and unpromoted even after submission', () => {
  const ref = image('uncertain.png', { submitted_at: '2026-10-17', evidence_role: 'unknown', role_origin: 'awaiting_context',
    role_reason: 'mixed_or_conflicting_context', evidence_model_revisions: { 'model<x>': 6 } });
  const { context, nodes } = composer({ refs: [ref] });
  const before = JSON.stringify(ref);
  context.renderReferenceComposer();
  assert.equal(nodes['reference-ambiguity'].hidden, false);
  assert.match(nodes['reference-ambiguity'].textContent, /1 张图片用途尚未确认/);
  assert.match(nodes['submitted-reference-roles'].innerHTML, /图片用途有歧义，请确认/);
  assert.match(nodes['submitted-reference-roles'].innerHTML, /model&lt;x&gt;: r6/);
  assert.match(nodes['submitted-reference-roles'].innerHTML, /<option value="" selected>/);
  assert.equal(JSON.stringify(ref), before);
});
test('submission hides pending attachment controls rather than forcing per-image choices', () => {
  const { context, nodes } = composer({ refs: [image('new.png')] });
  vm.runInContext('pendingMessage="controlled pending message";', context);
  context.renderReferenceComposer(); context.renderAttachments();
  assert.equal(nodes['reference-role-review'].hidden, true);
  assert.equal(nodes['reference-gallery'].hidden, true);
  assert.equal(nodes['attachment-list'].hidden, true);
});
test('manual correction invalidates the displayed approval snapshot while preserving source-specific PATCH', async () => {
  const { context, state, requests } = composer();
  await context.correctReferenceRole({ target: { dataset: { referenceRole: 'inputs/reference/original.png' }, value: 'defect_location' } });
  assert.deepEqual(requests[0].body, { source: 'inputs/reference/original.png', evidence_role: 'defect_location' });
  assert.equal(state.displayedPlan, null);
  assert.match(source, /\$\("submitted-reference-roles"\)\.addEventListener\("change", correctReferenceRole\)/);
});

for (const progress of [null, { running: true }, { running: true, cancel_supported: true }, { running: false, cancel_supported: true }, { running: true, cancel_supported: false }]) {
  test(`stop remains unavailable without confirmed active capability: ${JSON.stringify(progress)}`, async () => {
    const { context, $, requests } = composer();
    context.renderTurnControls(progress);
    assert.equal($('cancel-agent-turn').hidden, true);
    await context.cancelConversationTurn();
    assert.equal(requests.length, 0);
  });
}
test('stop requests are separate from send and never unlock or erase the next draft on acknowledgement', async () => {
  const { context, $, state } = composer({ text: '下一条草稿' });
  state.busy = true;
  context.renderTurnControls({ request_id: 'request-1', running: true, cancel_supported: true, cancel_requested: false });
  assert.equal($('cancel-agent-turn').hidden, false);
  let resolve, requests = [];
  context.api = async (url, options) => { requests.push({ url, options }); return new Promise(r => resolve = r); };
  const cancellation = context.cancelConversationTurn();
  await context.cancelConversationTurn();
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, '/api/projects/p/agent/cancel');
  assert.equal(requests[0].options.method, 'POST');
  assert.deepEqual(JSON.parse(requests[0].options.body), { expected_request_id: 'request-1' });
  assert.equal($('cancel-agent-turn').disabled, true);
  assert.match($('cancel-agent-turn-status').textContent, /等待当前操作结束和服务端确认/);
  resolve({ status: 'requested', cancel_requested: true, terminal_confirmed: false, rollback_performed: false });
  await cancellation;
  assert.equal(state.busy, true);
  assert.equal($('conversation-input').value, '下一条草稿');
  assert.doesNotMatch($('cancel-agent-turn-status').textContent, /已停止|已回滚/);
});
test('unknown cancellation outcome stays locked and never claims completion', async () => {
  const { context, $, state } = composer();
  state.busy = true;
  context.renderTurnControls({ request_id: 'request-1', running: true, cancel_supported: true });
  context.api = async () => { throw Error('connection lost'); };
  await context.cancelConversationTurn();
  assert.equal(state.busy, true);
  assert.equal($('cancel-agent-turn').disabled, true);
  assert.match($('cancel-agent-turn-status').textContent, /尚未确认/);
  assert.doesNotMatch($('cancel-agent-turn-status').textContent, /已停止|已回滚/);
});
test('cancel capability never carries to another project', async () => {
  const { context, $, state, requests } = composer();
  context.renderTurnControls({ request_id: 'request-1', running: true, cancel_supported: true });
  state.projectId = 'q';
  context.renderTurnControls();
  await context.cancelConversationTurn();
  assert.equal($('cancel-agent-turn').hidden, true);
  assert.equal(requests.length, 0);
});
test('native event rendering uses text only and omits reasoning, tool arguments and unverified interruption claims', () => {
  const { context, $ } = composer();
  context.renderNativeTurnEvent({ event: 'item/agentMessage/delta', text: '<img onerror=unsafe>进度', reasoning: 'PRIVATE' });
  assert.equal($('native-turn-event').textContent, 'Agent 最新消息：<img onerror=unsafe>进度');
  assert.equal($('native-turn-event').innerHTML, undefined);
  context.renderNativeTurnEvent({ event: 'tool_started', tool: 'model_check', arguments: { token: 'PRIVATE' } });
  assert.equal($('native-turn-event').textContent, '正在调用工具：model_check');
  context.renderNativeTurnEvent({ event: 'reasoning', text: 'PRIVATE' });
  assert.equal($('native-turn-event').hidden, true);
  context.renderNativeTurnEvent({ event: 'turn/completed', status: 'interrupted', interrupted_confirmed: false });
  assert.doesNotMatch($('native-turn-event').textContent, /确认中断/);
  context.renderNativeTurnEvent({ event: 'turn/completed', status: 'interrupted', interrupted_confirmed: true });
  assert.match($('native-turn-event').textContent, /已确认中断/);
  assert.match($('native-turn-event').textContent, /不会自动回滚/);
});
test('native plan progress presents only the allowed step and reported status', () => {
  const { context, $ } = composer();
  context.renderNativeTurnEvent({ event: 'turn/plan/updated', plan: [{ step: '检查模型', status: 'inProgress', arguments: 'PRIVATE' }] });
  assert.equal($('native-turn-event').textContent, '当前步骤：检查模型（处理中）');
});

test('a stale cancellation response cannot affect a newer same-project request', async () => {
  const { context, $, state } = composer();
  state.busy = true;
  context.renderTurnControls({ request_id: 'old-request', running: true, cancel_supported: true });
  const pending = [];
  context.api = async (url, options) => new Promise(resolve => pending.push({ resolve, body: JSON.parse(options.body) }));
  const oldCancel = context.cancelConversationTurn();
  context.renderTurnControls({ request_id: 'new-request', running: true, cancel_supported: true });
  assert.equal($('cancel-agent-turn').disabled, false);
  const newCancel = context.cancelConversationTurn();
  assert.deepEqual(pending.map(item => item.body.expected_request_id), ['old-request', 'new-request']);
  pending[0].resolve({ status: 'not_running' });
  await oldCancel;
  assert.equal(state.turnCancellation.requestId, 'new-request');
  assert.equal(state.turnCancellation.uncertain, false);
  pending[1].resolve({ cancel_requested: true, terminal_confirmed: false });
  await newCancel;
  assert.equal(state.busy, true);
  assert.equal(state.turnCancellation.requestId, 'new-request');
});
