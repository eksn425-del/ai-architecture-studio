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

test('the composer has no image classification selector and uploads rely on conversation context', async () => {
  assert.doesNotMatch(html, /id="reference-role"|图片用途|待发送图片用途|更正用途/);
  for (const role of ['', 'auto', 'target_building', 'defect_location']) {
    const { ctx, requests, state } = uploads({ role });
    await ctx.uploadAttachments([image()]);
    assert.equal(requests.length, 1);
    assert.equal(query(requests[0]).get('evidence_role'), 'auto');
    assert.equal(query(requests[0]).get('batch_image_count'), '1');
    assert.equal(state.busy, false);
  }
});
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
function markup(ref) {
  return sandbox(production('escapeHtml', 'referenceSourceMarkup'), { projectFileUrl: p => '/files/' + encodeURIComponent(p) }).referenceSourceMarkup(ref);
}

test('image history provides actual originals and historical versions without classification controls', () => {
  const ref = { source: 'inputs/reference/first.png', evidence_role: 'unknown', role_origin: 'awaiting_context', evidence_model_revisions: { model: 3 } };
  const before = JSON.stringify(ref), rendered = markup(ref);
  assert.match(rendered, /first.png/);
  assert.match(rendered, /model: r3/);
  assert.doesNotMatch(rendered, /<select|target_building|defect_location|用途/);
  assert.equal(JSON.stringify(ref), before);
});

test('image history escapes attachment text and keeps safe local asset links', () => {
  const rendered = markup({ source: 'inputs/reference/<img src=x onerror="bad">.png', evidence_model_revisions: { 'model<x>': 6 } });
  assert.doesNotMatch(rendered, /<script|<x>/);
  assert.match(rendered, /&lt;img/);
  assert.match(rendered, /model&lt;x&gt;: r6/);
  assert.match(rendered, /rel="noreferrer"/);
});
