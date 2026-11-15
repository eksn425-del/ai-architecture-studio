import {test} from 'node:test';
import assert from 'node:assert/strict';
import {apply} from '../app/dsh_host_tools.mjs';

test('official plugin keeps host provenance in system section without adding tools',async()=>{
 const originalFetch=globalThis.fetch;
 const oldUrl=process.env.KSTUDIO_TOOLS_URL,oldToken=process.env.KSTUDIO_TOOLS_TOKEN;
 const calls=[],sections=[],registered=[];
 process.env.KSTUDIO_TOOLS_URL='http://127.0.0.1:12345';process.env.KSTUDIO_TOOLS_TOKEN='unit-test-only';
 globalThis.fetch=async(url,options)=>{
  assert.equal(options.headers.Authorization,'Bearer unit-test-only');calls.push(url);
  const data=url.endsWith('/tools')?[{name:'read_model',description:'read',inputSchema:{type:'object'}}]:url.endsWith('/task')?{text:'Exact user {{text}}; summary is not authorization'}:{ok:true};
  return {ok:true,json:async()=>data};
 };
 try{
  const hooks=new Map();
  await apply({tools:{register:x=>registered.push(x),schemas:()=>registered},attachments:{},
    systemPrompt:{section:x=>sections.push(x)},on:(event,handler)=>hooks.set(event,handler)});
  assert.equal(registered.length,1);assert.equal(sections.length,1);
  assert.equal(typeof hooks.get('llm/stream'),'function');
  assert.equal(sections[0].interpolate,false);
  assert.match(sections[0].text,/Exact user \{\{text\}\}/);
  assert.deepEqual(calls.map(x=>new URL(x).pathname),['/tools','/task','/inventory']);
 }finally{
  globalThis.fetch=originalFetch;
  for(const [key,value] of [['KSTUDIO_TOOLS_URL',oldUrl],['KSTUDIO_TOOLS_TOKEN',oldToken]]){
   if(value===undefined)delete process.env[key];else process.env[key]=value;
  }
 }
});

test('full SDK keeps native tools and observes later MCP generations',async()=>{
 const originalFetch=globalThis.fetch;
 const keys=['KSTUDIO_TOOLS_URL','KSTUDIO_TOOLS_TOKEN','KSTUDIO_DSH_CAPABILITIES'];
 const old=Object.fromEntries(keys.map(k=>[k,process.env[k]]));
 const registered=[{name:'read'},{name:'subagent'}], snapshots=[], sections=[];
 let changed;
 process.env.KSTUDIO_TOOLS_URL='http://127.0.0.1:12345';
 process.env.KSTUDIO_TOOLS_TOKEN='unit-test-only';
 process.env.KSTUDIO_DSH_CAPABILITIES='full';
 globalThis.fetch=async(url,options)=>{
  if(url.endsWith('/inventory')) snapshots.push(JSON.parse(options.body).names);
  return {ok:true,json:async()=>url.endsWith('/tools')?[]:url.endsWith('/task')?{instructions:'Architectural extension'}:{ok:true}};
 };
 try{
  await apply({tools:{register:x=>registered.push(x),schemas:()=>registered},attachments:{},
    systemPrompt:{section:x=>sections.push(x)},on:(event,handler)=>{if(event==='tools/change')changed=handler;}});
  registered.push({name:'mcp__adai__sketchup_project_begin'});changed();
  await new Promise(resolve=>setImmediate(resolve));
  assert.deepEqual(snapshots.at(-1),registered.map(x=>x.name));
  assert.equal(sections[0].name,'kstudio:architecture');
 }finally{
  globalThis.fetch=originalFetch;
  for(const k of keys){if(old[k]===undefined)delete process.env[k];else process.env[k]=old[k];}
 }
});

test('full plugin cancels actual official Agent payload and blocks child model commits',async()=>{
 const originalFetch=globalThis.fetch;
 const keys=['KSTUDIO_TOOLS_URL','KSTUDIO_TOOLS_TOKEN','KSTUDIO_DSH_CAPABILITIES'];
 const old=Object.fromEntries(keys.map(k=>[k,process.env[k]]));
 const handlers={}, nativeEvents=[]; let cancelled=false, stops=0;
 process.env.KSTUDIO_TOOLS_URL='http://127.0.0.1:12345';
 process.env.KSTUDIO_TOOLS_TOKEN='unit-test-only';process.env.KSTUDIO_DSH_CAPABILITIES='full';
 globalThis.fetch=async(url,options)=>{if(url.endsWith('/native-event')) nativeEvents.push(JSON.parse(options.body)); return {ok:true,json:async()=>url.endsWith('/tools')?[]:url.endsWith('/control')?{cancelled}: {}};};
 try {
  await apply({tools:{register:()=>{},schemas:()=>[]},attachments:{},systemPrompt:{section:()=>{}},on:(e,h)=>{handlers[e]=h;}});
  handlers['agent/created']({agent:{id:'parent',cancel:c=>{assert.equal(c.kind,'user');stops++;}}});
  const decision=await handlers['tools/pre-execute']({agent:{id:'child'},name:'sketchup_apply_parts'},async()=>({kind:'allow'}));
  assert.equal(decision.kind,'deny');
  const originalError=new Error('native tool failed');
  await assert.rejects(handlers['tools/execute']({name:'read',callId:'failure-1'},async()=>{throw originalError;}),e=>e===originalError);
  assert.equal(nativeEvents.at(-1).success,false);
  assert.equal(nativeEvents.at(-1).call_id,'failure-1');
  cancelled=true;
  await new Promise(resolve=>setTimeout(resolve,600));
  assert.ok(stops>0);
  assert.equal((await handlers['tools/pre-execute']({name:'read'},async()=>({kind:'allow'}))).kind,'cancel');
 } finally {
  handlers.dispose?.();globalThis.fetch=originalFetch;
  for(const k of keys){if(old[k]===undefined)delete process.env[k];else process.env[k]=old[k];}
 }
});
