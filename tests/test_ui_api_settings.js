// Production configuration UI with DOM fixtures; no credentials or paid requests.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../app/static/studio.js'), 'utf8');
function fixture(saved) {
  const nodes = {};
  const $ = id => nodes[id] ||= {value: '', hidden: false, showModal() { this.open = true; }};
  const state = {modelRouter: {providers: {litellm: saved}}};
  const context = vm.createContext({$, state, routeInfo: () => ({provider: 'litellm', reasoning_effort: 'low'})});
  for (const name of ['sameSavedApiConnection', 'applyApiProvider', 'openModelSettings']) {
    const start = source.indexOf(`function ${name}(`);
    vm.runInContext(source.slice(start, source.indexOf('\n}', start) + 2), context);
  }
  return {context, $};
}
test('compatible API entry exposes model/base fields and clears old secrets', () => {
  const {context, $} = fixture();
  $('provider-mode').value = 'compatible'; $('api-key').value = 'fixture-not-a-key';
  context.applyApiProvider();
  assert.equal($('api-key').value, '');
  assert.equal($('api-model').readOnly, false);
  assert.equal($('api-base').readOnly, false);
  assert.equal($('provider-key-link').hidden, true);
  assert.match($('provider-address-note').textContent, /图片和工具调用/);
});
test('reopen keeps custom connection while withholding its saved key', () => {
  const saved = {credential_configured: true, model: 'openai/vendor/model', api_base: 'https://example.test/v1'};
  const {context, $} = fixture(saved);
  context.openModelSettings();
  assert.equal($('provider-mode').value, 'compatible');
  assert.equal($('api-base').value, saved.api_base);
  assert.equal($('api-model').value, 'vendor/model');
  assert.equal($('api-effort').value, 'low');
  assert.equal($('api-key').value, '');
  assert.equal(context.sameSavedApiConnection(), true);
  $('api-base').value = 'https://other.example.test/v1';
  assert.equal(context.sameSavedApiConnection(), false);
});
test('B.AI and official choices keep fixed host addresses', () => {
  const {context, $} = fixture();
  for (const mode of ['bai', 'deepseek']) {
    $('provider-mode').value = mode;
    context.applyApiProvider();
    assert.equal($('api-base').readOnly, true);
    assert.equal($('provider-key-link').hidden, false);
    assert.equal($('api-model').readOnly, mode === 'deepseek');
  }
});
