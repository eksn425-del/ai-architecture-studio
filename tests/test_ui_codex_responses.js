// Actual settings functions and listeners, all endpoint responses are fixtures.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../app/static/studio.js'), 'utf8');
function fixture() {
  const nodes = {}, calls = [];
  const $ = id => nodes[id] ||= {value:'', checked:false, disabled:false, handlers:{},
    addEventListener(event, fn) { this.handlers[event] = fn; }, focus() {},
    showModal() {this.open=true;}, close() {this.open=false; this.handlers.close?.();},
    querySelector() {return $('model-settings-submit');}};
  const state = {modelRouter:{economy:{provider:'litellm', model:'openai/legacy-model',reasoning_effort:'low'},providers:{
    litellm:{credential_configured:true,model:'openai/legacy-model',api_base:'https://legacy.example.test/v1'},
    'codex-responses':{credential_configured:false}
  }}};
  let responder=async () => state.modelRouter;
  const context=vm.createContext({$, state, routeInfo:()=>state.modelRouter.economy,
    refreshTierLabels(){}, updateHeader(){}, friendlyError:error=>error.message, showToast(){},
    api:async (url, opts)=>{calls.push({url,opts}); return responder(url,opts);}});
  const start=source.indexOf('function sameSavedApiConnection(');
  const end=source.indexOf('\nasync function deleteProject(',start);
  vm.runInContext(source.slice(start,end),context);
  return {$,state,context,calls,setResponder(fn){responder=fn;}};
}
function selectApi(f) {
  f.$('provider-mode').value='codex-responses'; f.context.applyApiProvider();
  f.$('api-model').value='vendor/exact-model'; f.$('api-base').value='https://api.example.test/v1';
}
test('explicit API choice resets prior key/consent and warns about memory-only shared Codex engine',()=>{
  const f=fixture(); f.$('api-key').value='old-fixture'; f.$('responses-compatible').checked=true;
  selectApi(f);
  assert.equal(f.$('api-key').value,''); assert.equal(f.$('responses-compatible').checked,false);
  assert.equal(f.$('responses-acknowledgement').hidden,false);
  assert.equal(f.context.sameSavedApiConnection(),false);
  assert.match(f.$('provider-storage-note').textContent,/内存/);
  assert.match(f.$('provider-protocol-note').textContent,/同一个 Codex App Server/);
  assert.match(f.$('provider-storage-note').textContent,/预算/);
});
test('reopening an API connection retains raw model and requires fresh key and consent',()=>{
  const f=fixture(); f.state.modelRouter.economy={provider:'codex-responses',model:'vendor/raw',reasoning_effort:'high'};
  f.state.modelRouter.providers['codex-responses']={credential_configured:true,model:'vendor/raw',api_base:'https://api.example.test/v1'};
  f.context.openModelSettings();
  assert.equal(f.$('api-model').value,'vendor/raw'); assert.equal(f.$('api-effort').value,'high');
  assert.equal(f.$('api-key').value,''); assert.equal(f.$('responses-compatible').checked,false);
  assert.equal(f.context.sameSavedApiConnection(),false);
  f.$('api-key').value='not-real'; f.$('responses-compatible').checked=true;
  f.$('model-settings-dialog').handlers.cancel();
  assert.equal(f.$('api-key').value,''); assert.equal(f.$('responses-compatible').checked,false);
});
test('missing consent never submits; repeat save click dispatches once with exact API contract', async()=>{
  const f=fixture(); selectApi(f); f.$('api-key').value='fixture-only';
  const submit=f.$('model-settings-form').handlers.submit;
  await submit({preventDefault(){}}); assert.equal(f.calls.length,0);
  f.$('responses-compatible').checked=true;
  let done; f.setResponder(()=>new Promise(resolve=>{done=resolve;}));
  const first=submit({preventDefault(){}}); await submit({preventDefault(){}});
  assert.equal(f.calls.length,1);
  const body=JSON.parse(f.calls[0].opts.body);
  assert.equal(body.mode,'codex-responses'); assert.equal(body.model,'vendor/exact-model');
  assert.equal(body.protocol,'responses'); assert.equal(body.compatibility_acknowledged,true);
  done({...f.state.modelRouter,credential_storage:'memory-only'}); await first;
  assert.equal(f.$('api-key').value,''); assert.equal(f.$('model-settings-submit').disabled,false);
});
test('forget targets only selected API memory credential and does not choose native or legacy route',async()=>{
  const f=fixture(); selectApi(f);
  f.state.modelRouter.economy={provider:'codex-responses',model:'vendor/raw'};
  await f.$('forget-api-key').handlers.click();
  assert.equal(f.calls[0].url,'/api/model-settings/credential?mode=codex-responses');
  assert.equal(f.calls[0].opts.method,'DELETE');
  assert.equal(f.state.modelRouter.economy.provider,'codex-responses');
  assert.equal(f.state.modelRouter.providers.litellm.credential_configured,true);
  assert.match(f.$('model-settings-status').textContent,/未切换/);
});
