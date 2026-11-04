import {test} from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtempSync,readFileSync,existsSync} from 'node:fs';
import path from 'node:path';
import {toolDenial} from '../app/dsh_tool_policy.mjs';
import {apply} from '../app/dsh_host_tools.mjs';

test('actual hook prevents subprocess, second MCP, and child writes; root proxy remains',async()=>{
 const events={},registered=[];let executions=0;
 const oldFetch=globalThis.fetch,old={...process.env};
 process.env.KSTUDIO_TOOLS_URL='http://127.0.0.1:12345';process.env.KSTUDIO_TOOLS_TOKEN='dummy';
 process.env.KSTUDIO_DSH_CAPABILITIES='full';process.env.KSTUDIO_DSH_EXECUTION_POLICY='production-file-proxy';
 const names=['workspace_read','workspace_write','sketchup_run_workspace_ruby','kstudio_save_design_graph'];
 globalThis.fetch=async url=>({ok:true,json:async()=>url.endsWith('/tools')?names.map(name=>({name,inputSchema:{type:'object'}})):url.endsWith('/control')?{cancelled:false}:{}});
 try{
  await apply({tools:{register:x=>registered.push(x),schemas:()=>registered},attachments:{},systemPrompt:{section(){}},on:(e,h)=>{events[e]=h;}});
  events['agent/created']({agent:{id:'root',cancel(){}}});
  // Real child process only runs if policy delegates. It prints a fixed canary;
  // denied paths cannot reach the process, regardless of command spelling.
  const next=async()=>{executions++;return spawnSync(process.execPath,['-e','process.stdout.write("executed")'],{encoding:'utf8'}).stdout;};
  for(const name of ['pwsh','bash','workflow','read','write','edit','mcp__second__eval','mcp__adai__sketchup_runtime','unknown_new_tool'])
   assert.equal((await events['tools/pre-execute']({agent:{id:'root'},name,arguments:{command:'harmless text',action:'startup'}},next)).kind,'deny');
  for(const name of ['workspace_write','sketchup_run_workspace_ruby','kstudio_save_design_graph','subagent_fork','send_message'])
   assert.equal((await events['tools/pre-execute']({agent:{id:'child'},name},next)).kind,'deny');
  assert.equal(executions,0);
  assert.equal(await events['tools/pre-execute']({agent:{id:'root'},name:'workspace_write'},next),'executed');
  assert.equal(await events['tools/pre-execute']({agent:{id:'child'},name:'workspace_read'},next),'executed');
  assert.equal(executions,2);
 }finally{events.dispose?.();globalThis.fetch=oldFetch;for(const key of Object.keys(process.env))if(!(key in old))delete process.env[key];Object.assign(process.env,old);}
});

test('trusted development is explicitly unconfined but never a child or second writer escape',()=>{
 const context={rootAgentId:'root',hostNames:new Set(),policy:'trusted-development'};
 assert.equal(toolDenial({agent:{id:'root'},name:'pwsh'},context),null);
 assert.ok(toolDenial({agent:{id:'child'},name:'pwsh'},context));
 assert.ok(toolDenial({agent:{id:'root'},name:'mcp__other__write'},context));
 assert.ok(toolDenial({name:'workspace_write'},context));
});
