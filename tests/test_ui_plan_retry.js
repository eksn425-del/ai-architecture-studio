const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');const vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../app/static/studio.js'),'utf8');
const start=source.indexOf('async function loadParameterPlan(');
const fn=source.slice(start,source.indexOf('\n}',start)+2);
function fixture(staleCache=false){
 const nodes={},calls=[],notices=[];let consumed=true;
 const state={projectId:'p',busy:false,project:{agent_session:{reconstruction_state:'planned'},context:{conversation:[]}}};
 const $=id=>nodes[id]||=( {hidden:false,disabled:false,textContent:'',innerHTML:'',insertAdjacentHTML(_,html){this.innerHTML+=html;},addEventListener(_,fn){this.click=fn;}} );
 const card='same plan';
 const hash=require('node:crypto').createHash('sha256').update(card).digest('hex');
 if(staleCache)consumed=false;
 const context=vm.createContext({$,state,TextEncoder,crypto:require('node:crypto').webcrypto,parameterPlanMarkup:x=>x,projectFileUrl:()=>'/card',showToast:t=>notices.push(t),updateHeader:()=>calls.push({url:'header'}),api:async(url,options)=>{calls.push({url,options});if(url==='/card')return staleCache&&options?.cache!=='no-store'?'previous building plan':card;if(url.endsWith('/retry-plan')){consumed=false;return {execution_started:false};}return {pending_plan_id:consumed?'old':'fresh',plan_sha256:hash,consumed};}});
 vm.runInContext('let planRequestId=0;'+fn,context);
 return {context,state,$,calls,notices};
}
test('failed initial plan requires explicit empty-model check then NEW approval',async()=>{
 const f=fixture();await f.context.loadParameterPlan();
 assert.equal(f.state.displayedPlan,null);
 assert.match(f.$('parameter-plan-content').innerHTML,/retry-empty-plan/);
 assert.match(f.$('parameter-plan-content').innerHTML,/<details><summary>查看当前方案<\/summary>same plan<\/details>/);
 assert.equal(f.calls.some(c=>c.options?.method==='POST'),false);
 const button=f.$('retry-empty-plan');await button.click({currentTarget:button});
 assert.equal(f.state.displayedPlan.pendingPlanId,'fresh');
 assert.equal(f.calls.filter(c=>c.options?.method==='POST').length,1);
 assert.equal(f.calls.some(c=>c.url.endsWith('/conversation')),false);
});
test('stale project cannot renew a different project plan',async()=>{
 const f=fixture();await f.context.loadParameterPlan();f.state.projectId='other';
 await f.$('retry-empty-plan').click({currentTarget:f.$('retry-empty-plan')});
 assert.equal(f.calls.some(c=>c.options?.method==='POST'),false);
});
test('updated local edit plan bypasses a cached previous building card',async()=>{
 const f=fixture(true);await f.context.loadParameterPlan();
 assert.equal(f.state.displayedPlan.pendingPlanId,'fresh');
 assert.equal(f.calls.filter(c=>c.options?.method==='POST').length,0);
 assert.equal(f.calls.find(c=>c.url.endsWith('/pending-plan')).options.cache,'no-store');
});
