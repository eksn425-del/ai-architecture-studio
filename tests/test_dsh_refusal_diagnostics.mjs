import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {apply,hostRefusalError} from '../app/dsh_host_tools.mjs';

test('error presentation only accepts fixed safe codes, never arbitrary body text',()=>{
  for(const body of [null,[],{code:'private-canary'},{code:'__proto__'},
    {code:'USAGE_RECONCILIATION_REQUIRED',error:'private-canary',message:'private-canary'}]) {
    const error=hostRefusalError(400,body);
    assert.equal(error.retryable,false);
    assert.ok(!error.message.includes('private-canary'));
    assert.ok(!error.message.includes('__proto__'));
  }
});

test('real loopback refusal reaches model middleware with useful safe reason before dispatch',async()=>{
  const requests=[],handlers={},old={...process.env};let dispatched=0;
  const server=createServer(async(req,res)=>{
    for await (const _ of req) {} requests.push(req.url);
    const data=req.url==='/tools'?[]:req.url==='/task'?{test_budget_enabled:true}:
      req.url==='/test-budget/reserve'?{code:'USAGE_RECONCILIATION_REQUIRED',error:'private-canary'}:{ok:true};
    res.writeHead(req.url==='/test-budget/reserve'?400:200,{'Content-Type':'application/json'});res.end(JSON.stringify(data));
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  process.env.KSTUDIO_TOOLS_URL=`http://127.0.0.1:${server.address().port}`;
  process.env.KSTUDIO_TOOLS_TOKEN='local-fixture-token';delete process.env.KSTUDIO_DSH_CAPABILITIES;
  try {
    await apply({tools:{register(){},schemas:()=>[]},attachments:{},systemPrompt:{section(){}},on:(name,handler)=>{handlers[name]=handler;}});
    const stream=handlers['llm/stream']({sessionId:'fixture',provider:'kstudio-bai',model:'fixture',maxTokens:4096},async function*(){dispatched++;});
    await assert.rejects(async()=>{for await(const _ of stream){}},error=>{
      assert.equal(error.code,'USAGE_RECONCILIATION_REQUIRED');assert.equal(error.retryable,false);
      assert.match(error.message,/用量待核对/);assert.match(error.message,/已有模型/);
      assert.ok(!error.message.includes('private-canary'));return true;
    });
    assert.equal(dispatched,0);
    assert.equal(requests.filter(p=>p==='/test-budget/reserve').length,1);
  } finally {
    await new Promise(resolve=>server.close(resolve));
    for(const key of Object.keys(process.env))if(!(key in old))delete process.env[key];Object.assign(process.env,old);
  }
});
