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
test('actual SDK length failure names output settings and never auto-retries or rebuilds',()=>{
 const ctx=vm.createContext({});vm.runInContext(fn,ctx);
 const result=ctx.friendlyError(new Error('Official DeepSeek Harness ended with error; PI_AI_ERROR: Response incomplete: length'));
 assert.match(result,/单次输出达到上限/);assert.match(result,/不是 SU 连接失败/);
 assert.match(result,/计划和已保存模型仍保留/);assert.match(result,/推理档位或输出设置/);
 assert.match(result,/不会自动重试或重建/);assert.doesNotMatch(result,/无几何写入|已建成|已完成模型/);
});
test('failed approval is not reinserted as a draft that blocks approval',()=>{
 const guard=src.match(/if \(!\$\("conversation-input"\)\.value\.trim\(\) && !approvalGesture\) \$\("conversation-input"\)\.value = message;/);
 assert.ok(guard);
 const input={value:''};const ctx=vm.createContext({$:()=>input,message:'确认',approvalGesture:'plan_button'});
 vm.runInContext(guard[0],ctx);assert.equal(input.value,'');
 ctx.approvalGesture=undefined;vm.runInContext(guard[0],ctx);assert.equal(input.value,'确认');
});
test('specific consumed-plan cause survives a generic SDK transport wrapper',()=>{
 const ctx=vm.createContext({});vm.runInContext(fn,ctx);
 const result=ctx.friendlyError(new Error('Official DeepSeek Harness TRANSPORT: This pending plan was already consumed or replaced.'));
 assert.match(result,/批准记录已使用或已更新/);assert.match(result,/检查空白副本并恢复批准/);
 assert.match(result,/普通问题仍可继续交流/);assert.doesNotMatch(result,/本地运行状态|API 连接中断/);
});
