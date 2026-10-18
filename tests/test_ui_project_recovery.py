"""Execute production JavaScript with controlled I/O; these are not UI/native tests."""
import json
from pathlib import Path
import shutil
import subprocess
import pytest

SOURCE = (Path(__file__).parents[1] / 'app/static/studio.js').read_text(encoding='utf-8')

def function(name):
    marker = ('async function ' if 'async function ' + name + '(' in SOURCE else 'function ') + name + '('
    start = SOURCE.index(marker)
    end = SOURCE.find('\nfunction ', start+1)
    async_end = SOURCE.find('\nasync function ', start+1)
    end = min(x for x in [end, async_end] if x >= 0)
    return SOURCE[start:end] + "\n"

def run(program):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required for frontend regression')
    result = subprocess.run([node, '-e', program], capture_output=True, text=True, encoding='utf-8', check=True, timeout=10)
    return json.loads(result.stdout)

STUB = '''
const state={projectId:'old',project:{context:{project_id:'old'},agent_session:{}},planEditing:true,tab:'design',busy:false};
let projectLoadGeneration=0, progressGeneration=0, observingTurn=false, observedRunningTurn=false;
const nodes={}; const $=id=>nodes[id]||(nodes[id]={value:'old draft'});
const saveDraft=()=>{}; const restoreDraft=()=>{}; const localStorage={setItem:()=>{}};
const loadParameterPlan=async()=>{}; const artifactByType=()=>null; const setTab=()=>{};
const updateHeader=()=>{}; const setStatus=()=>{}; const showToast=()=>{};
const renderLiveActivity=()=>{}; const beginProgress=()=>{}; const startLiveProgress=()=>{}; const renderTurnControls=()=>{};
'''

def test_failed_project_switch_preserves_visible_project_identity():
    result=run(STUB + "const api=async()=>{throw Error('offline')};\n" + function('loadProject') + '''
(async()=>{try{await loadProject('new')}catch(_){};console.log(JSON.stringify({id:state.projectId,visible:state.project.context.project_id,editing:state.planEditing}));})();
''')
    assert result == {'id':'old','visible':'old','editing':True}

def test_late_project_response_cannot_overwrite_newer_selection():
    result=run(STUB + '''
const pending={}; const api=path=>new Promise(resolve=>pending[path.split('/').at(-1)]=resolve);
''' + function('loadProject') + '''
(async()=>{const a=loadProject('a'),b=loadProject('b');pending.b({context:{project_id:'b'},agent_session:{}});await b;pending.a({context:{project_id:'a'},agent_session:{}});await a;console.log(JSON.stringify({id:state.projectId,visible:state.project.context.project_id}));})();
''')
    assert result == {'id':'b','visible':'b'}

def test_progress_lookup_blocks_repeat_submit_until_status_known():
    result=run(STUB + '''
let resolve; const api=()=>new Promise(r=>resolve=r);
''' + function('observeRunningTurn') + '''
(async()=>{const pending=observeRunningTurn();const pendingBusy=state.busy;resolve({running:true});await pending;console.log(JSON.stringify({pendingBusy,busy:state.busy,observing:observingTurn}));})();
''')
    assert result == {'pendingBusy':True,'busy':True,'observing':True}

def test_stale_progress_response_does_not_claim_another_projects_turn():
    result=run(STUB + '''
let resolve; const api=()=>new Promise(r=>resolve=r);
''' + function('observeRunningTurn') + '''
(async()=>{const pending=observeRunningTurn();state.projectId='new';resolve({running:true});await pending;console.log(JSON.stringify({observing:observingTurn}));})();
''')
    assert result == {'observing':False}


def test_progress_outage_keeps_repeat_send_locked_and_starts_readonly_retry():
    result=run(STUB + "const api=async()=>{throw Error('offline')};\n" + function('observeRunningTurn') + "\n(async()=>{await observeRunningTurn();console.log(JSON.stringify({busy:state.busy,observing:observingTurn}));})();")
    assert result == {'busy':True,'observing':True}


def test_completion_sync_retries_without_overlapping_reads_or_early_unlock():
    stub = STUB.replace('const startLiveProgress=()=>{};', '')
    result=run(stub + function('loadProject') + function('startLiveProgress') + '''
let tick; const loads=[]; const setInterval=f=>(tick=f,1); const clearInterval=()=>{};
let progressTimer=null,liveProgressTimer=null;
const endProgress=()=>{progressGeneration++};
const api=path=>path.endsWith('/progress')?Promise.resolve({running:false}):new Promise((resolve,reject)=>loads.push({resolve,reject}));
const flush=()=>new Promise(r=>setImmediate(r));
(async()=>{state.busy=true;observingTurn=true;startLiveProgress();await flush();await tick();await flush();
const concurrentReads=loads.length;loads[0].reject(Error('offline'));await flush();const retainedLock=state.busy&&observingTurn;
const retry=tick();await flush();loads[1].resolve({context:{project_id:'old',conversation:[],version:'new'},agent_session:{}});await retry;
console.log(JSON.stringify({concurrentReads,retainedLock,busy:state.busy,observing:observingTurn,version:state.project.context.version}));})();
''')
    assert result == {'concurrentReads':1,'retainedLock':True,'busy':False,'observing':False,'version':'new'}


def test_recovered_checkpoint_download_uses_model_path_not_manifest_order():
    start=SOURCE.index('function artifactByType(')
    end=SOURCE.index('\nfunction ',start+1)
    result=run('''
const state={project:{model_state:{model_path:'outputs/model/previous.skp'},output_manifest:{model_captures:[
{type:'skp',path:'outputs/model/previous.skp',url:'/previous'},
{type:'skp',path:'outputs/model/newer.skp',url:'/newer'}]}}};
''' + SOURCE[start:end] + "\nconsole.log(JSON.stringify(artifactByType('skp')));")
    assert result['url'] == '/previous'


def test_missing_current_checkpoint_does_not_offer_unrelated_skp():
    start=SOURCE.index('function artifactByType(')
    end=SOURCE.index('\nfunction ',start+1)
    result=run("const state={project:{model_state:{model_path:'missing.skp'},output_manifest:{model_captures:[{type:'skp',path:'old.skp'}]}}};\n" + SOURCE[start:end] + "\nconsole.log(JSON.stringify(artifactByType('skp')));")
    assert result is None


def test_unknown_only_observer_preserves_unsent_repeat_of_old_message():
    stub = STUB.replace('const startLiveProgress=()=>{};', '')
    result=run(stub + function('loadProject') + function('startLiveProgress') + '''
let progressTimer=null,liveProgressTimer=null;
const setInterval=()=>1, clearInterval=()=>{}, endProgress=()=>{progressGeneration++};
const api=async path=>path.endsWith('/progress')?{running:false}:{context:{conversation:[{role:'user',content:'继续'}]},agent_session:{}};
(async()=>{state.busy=true;observingTurn=true;observedRunningTurn=false;$('conversation-input').value='继续';startLiveProgress();await new Promise(r=>setImmediate(r));console.log(JSON.stringify({draft:$('conversation-input').value,busy:state.busy}));})();
''')
    assert result == {'draft':'继续','busy':False}


def test_failed_switch_saves_draft_under_original_project_only():
    stub = STUB.replace('const saveDraft=()=>{}; const restoreDraft=()=>{}; const localStorage={setItem:()=>{}};', '')
    result=run(stub + function('saveDraft') + function('restoreDraft') + function('loadProject') + '''
const storage={};const localStorage={setItem:(k,v)=>storage[k]=v,getItem:k=>storage[k]||null};
const api=async()=>{throw Error('offline')};
(async()=>{$('conversation-input').value='门口别动，只改桌子';try{await loadProject('other')}catch(_){};console.log(JSON.stringify({id:state.projectId,draft:$('conversation-input').value,keys:Object.keys(storage),saved:JSON.parse(storage['kstudio-draft:old'])}));})();
''')
    assert result == {'id':'old','draft':'门口别动，只改桌子','keys':['kstudio-draft:old'],'saved':{'text':'门口别动，只改桌子','editing':True}}


@pytest.mark.parametrize('operation,warning', [
    ({'delivery_status':'UNVERIFIED_NATIVE_REOPEN'}, '尚未通过 SketchUp 原生重开'),
    ({'action':'recover_checkpoint'}, '请查看与本文件对应的原生重开核验记录'),
    ({'delivery_status':'VERIFIED'}, '请查看与本文件对应的原生重开核验记录'),
])
def test_download_keeps_candidate_warning_after_save_or_recovery(operation, warning):
    result=run('''
const state={project:{agent_session:{ruby_state:{main:{revision:1}}},model_state:{model_path:'current.skp',last_operation:OPERATION},output_manifest:{model_captures:[{type:'skp',path:'current.skp',url:'/current'},{type:'skp',path:'history.skp',url:'/history'}]}}};
const nodes={};const $=id=>nodes[id]||(nodes[id]={});const artifactTypeLabels={skp:'SketchUp 模型'};
'''.replace('OPERATION', json.dumps(operation)) + function('artifactByType') + function('allArtifacts') + function('renderArtifacts') + function('escapeHtml') + "\nrenderArtifacts();console.log(JSON.stringify({links:$('artifact-links').innerHTML,cards:$('artifact-list').innerHTML}));")
    assert warning in result['links']
    assert '/current' in result['links']
    assert '/history' not in result['links'] + result['cards']


def test_local_codex_configuration_error_is_actionable_not_wrong_provider():
    result = run(function('friendlyError') + '''
console.log(JSON.stringify(friendlyError(new Error('Codex config.toml was not found; local native agent is not configured'))));
''')
    assert '本机 Codex 尚未配置' in result
    assert '无需新建项目' in result
    assert '不是 DeepSeek Key 错误' in result


def test_native_program_detection_does_not_claim_verified_model_call():
    result = run('''const routeInfo=()=>({provider:'codex-app-server'});
const routeAvailable=()=>true;
''' + function('routeReadinessLabel') + "console.log(JSON.stringify(routeReadinessLabel('economy')));")
    assert result == '已检测到本机程序；调用未验证'


def test_missing_native_route_names_codex_not_unrelated_api_provider():
    result = run('''const routeInfo=()=>({provider:'codex-app-server'});
const routeAvailable=()=>false;
''' + function('routeReadinessLabel') + "console.log(JSON.stringify(routeReadinessLabel('economy')));")
    assert result == '本机 Codex 不可用'

@pytest.mark.parametrize('failure', [False, True])
def test_next_draft_survives_turn_success_and_failure(failure):
    stub = '''
const state={projectId:'p',project:{agent_session:{modeling_backend:'blender',reconstruction_state:'building',status:'ready'}},busy:false,planEditing:false};
const nodes={};const $=id=>nodes[id]||(nodes[id]={value:id==='conversation-input'?'first request':'economy',open:false,disabled:false});
let pendingMessage=null,pendingExecutionProject=null,resolve,reject,calls=0;
const localStorage={setItem:()=>{}};
const saveDraft=()=>{},executionUserMessage=x=>x,isBuildApproval=()=>false,sourceImages=()=>[],routeInfo=()=>({model:'simulation'});
const setBusy=()=>{},showResults=()=>{},beginProgress=()=>{},setStatus=()=>{},startLiveProgress=()=>{},loadParameterPlan=async()=>{},updateHeader=()=>{},showToast=()=>{},setTab=()=>{},friendlyError=e=>e.message,endProgress=()=>{},observeRunningTurn=async()=>{},loadProject=async()=>{};
const api=()=>{calls++;return new Promise((r,j)=>{resolve=r;reject=j})};
'''
    result=run(stub + function('sendConversation').split('\ndocument.querySelectorAll')[0] + '''
(async()=>{const p=sendConversation(null);const cleared=$('conversation-input').value==='';
$('conversation-input').value='next request';await sendConversation(null);
''' + ("reject(Error('offline'));" if failure else "resolve({project:state.project,agent:{},reply:'ok'});") + '''
await p;console.log(JSON.stringify({cleared,calls,draft:$('conversation-input').value,busy:state.busy}));})();
''')
    assert result=={'cleared':True,'calls':1,'draft':'next request','busy':False}


def test_image_role_controls_default_to_auto_and_keep_legacy_visible():
    html=(Path(__file__).parents[1]/'app/static/index.html').read_text(encoding='utf-8')
    assert 'id="reference-role"' in html
    assert '<option value="auto" selected>自动判断（可更正）</option>' in html
    assert 'value="target_building">目标建筑图' in html
    assert 'value="defect_location">待修问题截图' in html
    assert 'data-reference-role=' in SOURCE
    assert '待确认用途' in SOURCE
    assert '请先选择图片用途' not in SOURCE


def test_image_upload_without_role_uses_auto():
    program='''const state={projectId:'p',busy:false};const nodes={};const $=id=>nodes[id]||(nodes[id]={value:''});let options;const showToast=()=>{};const sourceImages=()=>[];const beginProgress=()=>{},endProgress=()=>{},updateHeader=()=>{};const uploadFile=async(c,f,t,b,o)=>{options=o;return true};'''
    result=run(program+function('uploadAttachments').split('$("conversation-input").addEventListener')[0]+'''(async()=>{await uploadAttachments([{name:'ref.png',type:'image/png',size:20}]);console.log(JSON.stringify({options,busy:state.busy}));})();''')
    assert result['options'] == {'evidence_role':'auto', 'role_context':'', 'batch_image_count':1}
    assert result['busy'] is False


def test_image_upload_sends_explicit_role_in_query():
    from urllib.parse import parse_qs, urlsplit
    program='''const state={projectId:'p',busy:false};let upload='';const nodes={};const $=id=>nodes[id]||(nodes[id]={value:id==='reference-role'?'defect_location':'',append:()=>{}});const document={createElement:()=>({})};const updateHeader=()=>{};const showToast=()=>{};const friendlyError=e=>e.message;const api=async(path,options)=>{if(options){upload=path;return {path:'inputs/reference/x.png',filename:'x.png'}}return {context:{}}};'''
    result=run(program+function('uploadFile')+'''(async()=>{const ok=await uploadFile('reference',{name:'x.png',type:'image/png'},'reference-files');console.log(JSON.stringify({ok,upload,busy:state.busy}));})();''')
    assert result['ok'] is True
    assert parse_qs(urlsplit(result['upload']).query, keep_blank_values=True) == {
        'filename':['x.png'], 'evidence_role':['defect_location'], 'role_context':[''], 'batch_image_count':['1'],
    }
    assert result['busy'] is False


def test_contextual_controls_keep_features_and_single_approval_gate():
    from html.parser import HTMLParser
    html=(Path(__file__).parents[1]/'app/static/index.html').read_text(encoding='utf-8')
    class IDs(HTMLParser):
        def __init__(self):super().__init__();self.ids=[]
        def handle_starttag(self,tag,attrs):self.ids.extend(v for k,v in attrs if k=='id')
    parser=IDs();parser.feed(html)
    assert len(parser.ids)==len(set(parser.ids))
    for name in ['task-details','workflow-progress','parameter-plan','revise-reconstruction-plan','approve-reconstruction','model-settings-toggle','conversation-tier']:
        assert name in parser.ids
    assert 'reconstructionState !== "planned"' in SOURCE
    assert 'taskDetails.open = reconstructionState === "planned"' in SOURCE
    assert 'taskDetails.dataset.context !== detailContext' in SOURCE
    assert '25 MiB' in html and '转换后最多 8 MiB' in html
    assert '\ufffd' not in html and '\ufffd' not in SOURCE
