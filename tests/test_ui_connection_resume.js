const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');const vm=require('node:vm');
const source=fs.readFileSync('app/static/studio.js','utf8');
function production(...names){return names.map(name=>{
  const start=source.search(new RegExp(`^(?:async )?function ${name}\\(`,'m'));assert.notEqual(start,-1);
  return source.slice(start,source.indexOf('\n}',start)+2);
}).join('\n');}
function fixture(){
  const nodes={},calls=[],notices=[];
  const $=id=>nodes[id]||={value:'',open:false,disabled:false,showModal(){this.open=true;},close(){this.open=false;}};
  const state={projectId:'p',busy:false,displayedPlan:{pendingPlanId:'plan-1'}};
  const context=vm.createContext({$,state,api:async()=>({reachable:false}),
    startAgentSession:async()=>true,loadParameterPlan:async()=>{},
    sendConversation:async(_,action)=>calls.push({action,text:$('conversation-input').value}),
    showToast:m=>notices.push(m),friendlyError:e=>e.message});
  vm.runInContext('let connectDialogGeneration=0,pendingExecutionProject=null,pendingConnectionDraft=null,pendingConnectionPlanId=null;\n'+
    production('openConnectDialog','closeConnectDialog','isCurrentConnectDialog','connectCurrentProject','api'),context);
  // Keep the actual API parser independently testable; connector calls use a controlled transport.
  context.api=async()=>({reachable:false});
  return {context,state,$,calls,notices};
}
test('connection-only does not submit an existing modeling draft',async()=>{
  const f=fixture();f.$('conversation-input').value='开始建模';
  f.context.openConnectDialog();await f.context.connectCurrentProject();assert.deepEqual(f.calls,[]);
});
test('confirmed recovery resends the exact original request through auto',async()=>{
  const f=fixture();const text='  开始建模\n';f.$('conversation-input').value=text;
  f.context.openConnectDialog(false,text);await f.context.connectCurrentProject();
  assert.deepEqual(f.calls,[{action:'auto',text}]);
});
for(const change of ['draft','plan','project'])test(`connection continuation stops on changed ${change}`,async()=>{
  const f=fixture();f.$('conversation-input').value='开始建模';f.context.openConnectDialog(false,'开始建模');
  f.context.startAgentSession=async()=>{
    if(change==='draft')f.$('conversation-input').value='不要执行';
    if(change==='project')f.state.projectId='another';
    return true;
  };
  if(change==='plan')f.context.loadParameterPlan=async()=>{f.state.displayedPlan.pendingPlanId='plan-2';};
  await f.context.connectCurrentProject();assert.deepEqual(f.calls,[]);
});
test('API parser keeps the host recovery code and human message',async()=>{
  const f=fixture();vm.runInContext(production('api'),f.context);
  f.context.fetch=async()=>({ok:false,status:409,headers:{get:()=> 'application/json'},json:async()=>({detail:{code:'SKETCHUP_CONNECTION_REQUIRED',message:'连接后再继续'}})});
  await assert.rejects(f.context.api('/fixture'),e=>e.code==='SKETCHUP_CONNECTION_REQUIRED'&&e.message==='连接后再继续');
});
