const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const src=fs.readFileSync(path.join(__dirname,'../app/static/studio.js'),'utf8');
const fn=src.slice(src.indexOf('function friendlyError('),src.indexOf('\nfunction setStatus('));

test('SDK transport error gives recovery guidance without blaming key or SketchUp',()=>{
 const ctx=vm.createContext({});vm.runInContext(fn,ctx);
 const result=ctx.friendlyError(new Error('Official DeepSeek Harness ended with error; TRANSPORT: Connection error.'));
 assert.match(result,/API 连接中断/);assert.match(result,/原会话恢复/);
 assert.match(result,/不能说明 Key 无效/);assert.match(result,/不代表 SU 连接失败/);
});
test('provider truncation is distinguished from SU and preserves recovery guidance',()=>{
 const ctx=vm.createContext({});vm.runInContext(fn,ctx);
 const result=ctx.friendlyError(new Error('Response incomplete: length'));
 assert.match(result,/长度限制/);assert.match(result,/不是 SU 连接失败/);assert.match(result,/重新批准/);
});
test('failed approval is not reinserted as a draft that blocks approval',()=>{
 const guard=src.match(/if \(!\$\("conversation-input"\)\.value\.trim\(\) && !approvedPlanSha256\) \$\("conversation-input"\)\.value = message;/);
 assert.ok(guard);
 const input={value:''};const ctx=vm.createContext({$:()=>input,message:'确认',approvedPlanSha256:'approved'});
 vm.runInContext(guard[0],ctx);assert.equal(input.value,'');
 ctx.approvedPlanSha256=undefined;vm.runInContext(guard[0],ctx);assert.equal(input.value,'确认');
});
