// Controlled I/O: model status synchronization, not a provider compatibility test.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');const vm=require('node:vm');
const source=fs.readFileSync('app/static/studio.js','utf8');
function production(...names){return names.map(name=>{
  const start=source.search(new RegExp(`^(?:async )?function ${name}\\(`,'m'));
  assert.notEqual(start,-1);return source.slice(start,source.indexOf('\n}',start)+2);
}).join('\n');}
const router=(model,available=true,extra={})=>({economy:{model,provider:'deepseek-harness'},providers:{'deepseek-harness':{available,credential_configured:available,...extra}}});
function fixture(){
  const updates=[],storage=[];const state={modelRouter:router('obsolete-fixture')};
  const context=vm.createContext({state,AbortSignal,Date,Math,api:async()=>({model_router:router('current'),personal_desktop:true}),
    refreshTierLabels:()=>updates.push(state.modelRouter.economy.model),renderJourney(){},
    document:{querySelector:()=>({classList:{toggle(){}}})},localStorage:{setItem:(k,v)=>storage.push([k,v])}});
  vm.runInContext('let modelConfigurationRequest=null,modelConfigurationGeneration=0;\n'+production('routeInfo','routeAvailable','refreshModelConfiguration','notifyModelConfigurationChanged','modelUnavailableMessage','friendlyError'),context);
  return {context,state,updates,storage};
}
test('fresh server configuration replaces a stale tab label without invoking a model',async()=>{
  const f=fixture();const urls=[];f.context.api=async url=>{urls.push(url);return {model_router:router('fresh'),personal_desktop:true};};
  await f.context.refreshModelConfiguration();assert.equal(f.state.modelRouter.economy.model,'fresh');assert.deepEqual(urls,['/api/status']);
});
test('overlapping refreshes share one request and cannot overwrite a later configuration change',async()=>{
  const f=fixture();const resolves=[];f.context.api=()=>new Promise(resolve=>resolves.push(resolve));
  const a=f.context.refreshModelConfiguration(),b=f.context.refreshModelConfiguration();
  assert.equal(resolves.length,1);
  const changed=f.context.notifyModelConfigurationChanged();
  resolves[0]({model_router:router('obsolete-response')});
  await new Promise(setImmediate);assert.equal(resolves.length,2);assert.deepEqual(f.updates,[]);
  resolves[1]({model_router:router('latest')});await Promise.all([a,b,changed]);
  assert.deepEqual(f.updates,['latest']);assert.equal(f.state.modelRouter.economy.model,'latest');
  assert.equal(f.storage.length,1);assert.equal(f.storage[0][0],'kstudio-model-configuration-changed');
  assert.match(f.storage[0][1],/^\d+:0\.\d+$/);
});
test('missing API and missing runtime receive different repair directions',()=>{
  const f=fixture();f.state.modelRouter=router('empty',false);
  assert.match(f.context.modelUnavailableMessage('economy'),/尚未配置或启用模型 API/);
  f.state.modelRouter=router('saved',false,{credential_configured:true,dependency_installed:false});
  assert.match(f.context.modelUnavailableMessage('economy'),/运行组件不可用/);
  assert.doesNotMatch(f.context.modelUnavailableMessage('economy'),/重新填写/);
});
test('actual unavailable-provider failure is actionable instead of generic local-state error',()=>{
  const f=fixture();const message=f.context.friendlyError(new Error('Economy provider unavailable'));
  assert.match(message,/API 连接/);assert.match(message,/图片和草稿仍保留/);assert.match(message,/不是 SketchUp/);
  assert.doesNotMatch(message,/检查本地运行状态/);
});
