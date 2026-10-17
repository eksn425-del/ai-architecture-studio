// Production JavaScript with controlled I/O. Not a browser/native-model claim.
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
function sandbox(program, extra) {
  const ctx = vm.createContext(extra);
  vm.runInContext(program, ctx);
  return ctx;
}
function uploads({ role = 'auto', text = '', afterPost = () => {} } = {}) {
  const state = { projectId: 'session & one', project: { context: { references: [] } }, busy: false };
  const nodes = {}, requests = [], messages = [];
  const $ = id => nodes[id] ||= { value: id === 'reference-role' ? role : id === 'conversation-input' ? text : '', append() {} };
  const ctx = sandbox(production('sourceImages', 'uploadFile', 'uploadAttachments'), {
    state, $, document: { createElement: () => ({}) },
    api: async (url, options) => {
      if (!options) return state.project;
      requests.push({ url, options });
      afterPost($, requests.length);
      return { path: 'inputs/reference/upload.png', filename: 'upload.png' };
    },
    showToast: text => messages.push(text), friendlyError: e => e.message,
    updateHeader() {}, beginProgress() {}, endProgress() {},
  });
  return { ctx, state, $, requests, messages };
}
const image = (name = 'reference.png') => ({ name, type: 'image/png', size: 100 });
const query = request => new URL(request.url, 'http://localhost').searchParams;

test('upload selector defaults to auto, with target and defect overrides', () => {
  const select = html.match(/<select id="reference-role"[^>]*>(.*?)<\/select>/)[1];
  assert.match(select, /^<option value="auto" selected>自动判断（可更正）<\/option>/);
  assert.match(select, /value="target_building"/);
  assert.match(select, /value="defect_location"/);
  assert.doesNotMatch(source, /请先选择图片用途/);
});
for (const role of ['', 'auto', 'target_building', 'defect_location']) {
  test(`upload proceeds with ${role || 'blank'} selector and preserves explicit choice`, async () => {
    const { ctx, requests, state } = uploads({ role });
    await ctx.uploadAttachments([image()]);
    assert.equal(requests.length, 1);
    assert.equal(query(requests[0]).get('evidence_role'), role || 'auto');
    assert.equal(query(requests[0]).get('batch_image_count'), '1');
    assert.equal(state.busy, false);
  });
}
test('context and filename are encoded without adding query parameters or using filename as role', async () => {
  const text = '这张是待修问题：屋顶 A&B？\n不要复制旧模型 #定位 + "比较"';
  const { ctx, requests } = uploads({ text });
  await ctx.uploadAttachments([image('defect & evidence_role=target_building #.png')]);
  const params = query(requests[0]);
  assert.equal(params.get('role_context'), text);
  assert.equal(params.get('filename'), 'defect & evidence_role=target_building #.png');
  assert.deepEqual(params.getAll('evidence_role'), ['auto']);
  assert.equal(requests[0].url.includes('session%20%26%20one'), true);
  assert.equal(new URL(requests[0].url, 'http://localhost').hash, '');
});
test('a mixed batch captures the same composer context, role and image-only count before upload', async () => {
  const { ctx, requests } = uploads({ text: '两个建筑角度', afterPost: ($, count) => {
    if (count === 1) { $('conversation-input').value = '下一条草稿'; $('reference-role').value = 'defect_location'; }
  } });
  await ctx.uploadAttachments([image('front.png'), { name: 'notes.txt', type: 'text/plain', size: 10 }, image('rear.png')]);
  assert.equal(requests.length, 3);
  for (const request of [requests[0], requests[2]]) {
    assert.equal(query(request).get('evidence_role'), 'auto');
    assert.equal(query(request).get('role_context'), '两个建筑角度');
    assert.equal(query(request).get('batch_image_count'), '2');
  }
  assert.equal(query(requests[1]).has('evidence_role'), false);
  assert.equal(query(requests[1]).has('role_context'), false);
});
test('existing limits still reject an oversized image batch before upload', async () => {
  const { ctx, requests, messages } = uploads();
  await ctx.uploadAttachments(Array.from({ length: 9 }, (_, i) => image(`${i}.png`)));
  assert.equal(requests.length, 0);
  assert.ok(messages.some(value => value.includes('最多使用 8 张')));
});
function markup(ref, busy = false) {
  return sandbox(production('escapeHtml', 'referenceRoleMarkup'), { state: { busy } }).referenceRoleMarkup(ref);
}
test('auto role label explains the server decision and remains correctable', () => {
  const rendered = markup({ source: 'inputs/reference/first.png', evidence_role: 'target_building', role_origin: 'context_default', role_reason: 'first_image_new_project' });
  assert.match(rendered, /自动判断 · 首张参考图，按目标建筑使用/);
  assert.match(rendered, /<option value="target_building" selected>/);
  assert.match(rendered, /data-reference-role="inputs\/reference\/first.png"/);
  assert.doesNotMatch(rendered, /context_default|first_image_new_project/);
});
test('unknown and legacy images remain pending without client-side promotion', () => {
  for (const roleOrigin of ['legacy', 'awaiting_context']) {
    const ref = { source: 'inputs/reference/old.png', evidence_role: 'unknown', role_origin: roleOrigin, role_reason: 'needs_current_context' };
    const rendered = markup(ref);
    assert.match(rendered, /<option value="" selected>待确认用途/);
    assert.match(rendered, /请说明这张图的用途/);
    assert.doesNotMatch(rendered, /<option value="target_building" selected>/);
    assert.equal(ref.evidence_role, 'unknown');
  }
});
test('user correction and ambiguous decisions display understandable labels', () => {
  assert.match(markup({ source: 'inputs/reference/x.png', evidence_role: 'defect_location', role_origin: 'user', role_reason: 'explicit_user_correction' }), /已手动确认 · 已按你的选择更正/);
  assert.match(markup({ source: 'inputs/reference/x.png', evidence_role: 'unknown', role_origin: 'awaiting_context', role_reason: 'mixed_or_conflicting_context' }), /图片用途有歧义，请确认/);
});
test('role review escapes filenames and never renders unknown provenance as raw HTML', () => {
  const rendered = markup({ source: 'inputs/reference/<img src=x onerror="bad">.png', evidence_role: 'unknown', role_origin: '<b>unsafe</b>', role_reason: '<script>unsafe</script>' }, true);
  assert.doesNotMatch(rendered, /<img|<script|<b>/);
  assert.match(rendered, /&lt;img/);
  assert.match(rendered, /aria-label="更正图片用途" disabled/);
});
function correction({ busy = false, failure = false } = {}) {
  const state = { projectId: 'p & one', project: { agent_session: { reconstruction_state: 'planned' } }, busy };
  let change;
  const requests = [], notices = [];
  const marker = '$("reference-role-review").addEventListener("change",';
  const start = source.indexOf(marker);
  const end = source.indexOf('\n});', start) + 4;
  assert.ok(start >= 0 && end > start);
  sandbox(source.slice(start, end), {
    state, $: () => ({ addEventListener: (type, callback) => { change = callback; } }),
    updateHeader() {}, showToast: text => notices.push(text), friendlyError: e => e.message,
    api: async (url, options) => {
      requests.push({ url, options });
      if (failure) throw Error('offline');
      return options ? {} : { agent_session: { reconstruction_state: 'clarifying', approved_plan_sha256: null } };
    },
  });
  return { change, state, requests, notices };
}
test('correcting a role PATCHes exact source then reloads invalidated approval state', async () => {
  const { change, requests, state, notices } = correction();
  const sourcePath = 'inputs/reference/target & old.png';
  await change({ target: { dataset: { referenceRole: sourcePath }, value: 'defect_location' } });
  assert.equal(requests[0].url, '/api/projects/p%20%26%20one/reference-role');
  assert.equal(requests[0].options.method, 'PATCH');
  assert.deepEqual(JSON.parse(requests[0].options.body), { source: sourcePath, evidence_role: 'defect_location' });
  assert.equal(state.project.agent_session.reconstruction_state, 'clarifying');
  assert.equal(state.project.agent_session.approved_plan_sha256, null);
  assert.ok(notices.some(text => text.includes('重新整理并批准建模计划')));
  assert.equal(state.busy, false);
});
test('blank role and in-flight work cannot submit a correction', async () => {
  for (const [busy, value] of [[false, ''], [true, 'target_building']]) {
    const { change, requests } = correction({ busy });
    await change({ target: { dataset: { referenceRole: 'inputs/reference/x.png' }, value } });
    assert.equal(requests.length, 0);
  }
});
test('failed role correction keeps the old server state and releases busy status', async () => {
  const { change, state, notices } = correction({ failure: true });
  await change({ target: { dataset: { referenceRole: 'inputs/reference/x.png' }, value: 'target_building' } });
  assert.equal(state.project.agent_session.reconstruction_state, 'planned');
  assert.equal(state.busy, false);
  assert.deepEqual(notices, ['offline']);
});
