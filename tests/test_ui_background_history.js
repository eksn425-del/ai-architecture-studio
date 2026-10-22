const {test}=require('node:test');const assert=require('node:assert/strict');const vm=require('node:vm');const fs=require('node:fs');
const src=fs.readFileSync(require('node:path').join(__dirname,'../app/static/studio.js'),'utf8');
function production(...names){return names.map(n=>{const at=src.search(new RegExp('^(?:async )?function '+n+'\\(','m'));assert.notEqual(at,-1);return src.slice(at,src.indexOf('\n}',at)+2);}).join('\n');}
function fixture(){
 const state={projectId:'a',busy:true,runningProjectId:'a',project:{agent_session:{},context:{conversation:[]}}};const nodes={},calls=[];
 const $=id=>nodes[id]||={value:'',hidden:false,setAttribute(){},querySelector(){return {};},classList:{remove(){}}};
 const context=vm.createContext({state,$,document:{body:{classList:{remove(){}}}},updateHeader(){},showResults(){},showToast(){},friendlyError:e=>e.message,loadProject:async id=>{calls.push(id);state.projectId=id;},observeRunningTurn:async()=>calls.push('observe'),setInterval:()=>1,clearInterval(){},renderTurnControls:()=>calls.push('render'),renderWorkflowChecks(){},escapeHtml:x=>x,saveDraft(){},endProgress(){},beginProgress(){}});
 vm.runInContext('let progressGeneration=0,progressTimer=null,liveProgressTimer=null,observingTurn=false,observedRunningTurn=false;'+production('browseProject','startLiveProgress'),context);
 return {state,$,calls,context};
}
test('history remains readable during an API turn without releasing writer/send lock',async()=>{
 const f=fixture();await f.context.browseProject('b');assert.equal(f.state.projectId,'b');assert.equal(f.state.busy,true);assert.equal(f.state.runningProjectId,'a');assert.deepEqual(f.calls,['b']);
 await f.context.browseProject('a');assert.equal(f.state.projectId,'a');assert.equal(f.state.busy,true);
});
test('background poll stays on original project and never renders its preview into another chat',async()=>{
 const f=fixture();await f.context.browseProject('b');const urls=[];
 f.context.api=async url=>{urls.push(url);return {running:true,stage:'running',elapsed_seconds:3,preview_url:'/a.png',committed_revisions:[]};};
 f.context.startLiveProgress();await new Promise(r=>setImmediate(r));
 assert.deepEqual(urls,['/api/projects/a/agent/progress']);assert.equal(f.$('preview-canvas').innerHTML,undefined);
 assert.match(f.$('operation-progress').textContent,/后台运行/);
});
test('a completed background observer never reloads the active historical conversation or clears its draft',async()=>{
 const f=fixture();f.state.projectId='b';f.$('conversation-input').value='给b的草稿';
 vm.runInContext('observingTurn=true;observedRunningTurn=true;',f.context);
 f.context.api=async()=>({running:false});f.context.startLiveProgress();await new Promise(r=>setImmediate(r));
 assert.equal(f.state.projectId,'b');assert.equal(f.state.busy,false);assert.equal(f.state.runningProjectId,null);
 assert.equal(f.$('conversation-input').value,'给b的草稿');assert.equal(f.calls.includes('a'),false);
});
test('the sidebar no longer disables history buttons just because a turn is busy',()=>{
 const context=vm.createContext({state:{busy:true,projectId:'a',runningProjectId:'a'},projectList:[{project_id:'a',project_name:'A'},{project_id:'b',project_name:'B'}],escapeHtml:x=>x,$:id=>nodes[id]||={}});const nodes={};
 vm.runInContext(production('renderProjectHistory'),context);context.renderProjectHistory();
 assert.doesNotMatch(nodes['project-history'].innerHTML,/disabled/);assert.match(nodes['project-history'].innerHTML,/运行中/);
});
