// Offline integration with the installed, unmodified official retry plugin.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {readFileSync} from 'node:fs';
import path from 'node:path';
const root=process.env.KSTUDIO_TEST_DSH_NODE_MODULES;
if(!root) throw new Error('Set KSTUDIO_TEST_DSH_NODE_MODULES to the pinned installation');
const {apply}=await import(pathToFileURL(path.join(root,'@deepseek-ai/dsh-llm-retry/lib/index.js')));
const {resolveRetryPolicy}=await import(pathToFileURL(path.join(root,'@deepseek-ai/dsh-llm/lib/index.js')));
const configured=JSON.parse(readFileSync(process.env.KSTUDIO_TEST_RETRY_POLICY,'utf8'));
function fixture(){
 let projection, state={}, listener, dispose;
 const events=[];
 const ctx={sessionProjections:{register(p){projection=p;state=p.init()},stateOf(){return state}},
  on(name,callback){assert.equal(name,'agent/request-error');listener=callback;return ()=>{}},
  effect(factory){dispose=factory()},logger:{warn(){}}};
 apply(ctx);
 const policy=resolveRetryPolicy(configured,'test');
 assert.equal(policy.mode,'normal');assert.equal(policy.maxRetries,2);
 const instant={...policy,initialDelayMs:0,maxDelayMs:0,jitterRatio:0};
 const session={append(type,data){const event={type,data};events.push(event);state=projection.apply(state,event)}};
 const payload=(code,signal=new AbortController().signal)=>({agent:{session},turn:1,step:4,provider:'fixture',
  failure:{code,message:'synthetic '+code},retryPolicy:instant,signal});
 return {events,listener,payload,dispose};
}
test('official retry retries transient request twice and then stops',async()=>{
 const f=fixture();let delegated=0;
 try{
  assert.deepEqual(await f.listener(f.payload('TRANSPORT'),async()=>{delegated++}),{kind:'retry'});
  assert.deepEqual(await f.listener(f.payload('TIMEOUT'),async()=>{delegated++}),{kind:'retry'});
  assert.equal(await f.listener(f.payload('TRANSPORT'),async()=>{delegated++}),undefined);
  assert.equal(delegated,1);
  assert.deepEqual(f.events.map(e=>e.type),['llm/retry','llm/retry-started','llm/retry','llm/retry-started']);
 }finally{await f.dispose()}
});
test('permanent key/quota errors and cancellation do not schedule another request',async()=>{
 const f=fixture();let delegated=0;
 try{
  for(const code of ['AUTHENTICATION','QUOTA','INVALID_REQUEST']) await f.listener(f.payload(code),async()=>{delegated++});
  assert.equal(delegated,3);assert.equal(f.events.length,0);
  const c=new AbortController();c.abort();
  assert.equal(await f.listener(f.payload('TRANSPORT',c.signal),async()=>{}),undefined);
  assert.equal(f.events.length,0);
 }finally{await f.dispose()}
});
