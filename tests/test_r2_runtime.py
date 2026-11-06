import base64
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from PIL import Image

from app.dsh_configuration import resolve_configuration
from app.dsh_images import image_block
from app.dsh_runtime import write_profile
from app.k_architecture import ArchitectureContext
from app.spatial_handoff import bounded_conversation
from tests.test_k_architecture import graph


def connection(**changes):
    return {'mode':'compatible','api_base':'https://example.invalid/v1','model':'openai/test',
            'api_key':'fake-only','reasoning_effort':'provider-default',**changes}


@pytest.mark.parametrize('protocol,mode',[('openai-completions','compatible'),('openai-responses','codex-responses')])
@pytest.mark.parametrize('effort,wire',[('provider-default',None),('low','low'),('high','high')])
def test_effective_config_profile_and_no_claimed_reporting(tmp_path,protocol,mode,effort,wire):
    config=resolve_configuration(connection(mode=mode,reasoning_effort=effort))
    assert config.protocol==protocol
    evidence=config.evidence()
    assert evidence['effective']['wire_reasoning_effort']==wire
    assert set(evidence['reported'].values())=={None}
    path=tmp_path/'profile.json'
    write_profile(path,api_base=config.endpoint,model=config.model,protocol=protocol,
                  effective_configuration=config,full_capabilities=True)
    rows=json.loads(path.read_text(encoding='utf-8'))
    profile=next(r['config'] for r in rows if r.get('id')=='llm-pi-ai')['providers']['kstudio-bai']
    assert profile['api']==protocol
    assert profile['models'][0]['contextWindow']==16384
    assert profile['models'][0]['input']==['text']
    if effort=='provider-default':
        assert profile['models'][0]['reasoningEfforts'] is False
    else:
        assert profile['models'][0]['reasoningEfforts']['off'] is None
    assert config.compaction()['retainTokens']+config.compaction()['maxTokens'] < config.context_window-config.max_output_tokens-config.compaction()['headroomTokens']


def test_unknown_capabilities_and_changed_destination_do_not_inherit_pass():
    known=resolve_configuration(connection(api_base='https://api.b.ai/v1',model='deepseek-v4.1-flash'))
    unknown=resolve_configuration(connection(model='deepseek-v4.1-flash'))
    assert known.vision and not unknown.vision
    assert unknown.verification_status=='NOT_RUN'
    claimed=resolve_configuration(connection(capabilities_json=json.dumps({'context_window':64000,'max_output_tokens':8192,'vision':True,'tools':True,'streaming':True})))
    assert claimed.context_window==64000 and claimed.vision
    assert claimed.capability_source=='user_declared_unverified' and claimed.verification_status=='NOT_RUN'
    with pytest.raises(ValueError):resolve_configuration(connection(reasoning_effort='max'))
    with pytest.raises(ValueError):resolve_configuration(connection(capabilities_json='{"context_window":8192,"max_output_tokens":8192}'))


@pytest.mark.parametrize('fmt,suffix,mime',[('PNG','.png','image/png'),('JPEG','.jpg','image/jpeg'),('WEBP','.webp','image/webp'),('GIF','.gif','image/png')])
def test_images_preserve_pixels_and_originals(tmp_path,fmt,suffix,mime):
    path=tmp_path/('source'+suffix);Image.new('RGB',(12,8),'red').save(path,format=fmt)
    original=path.read_bytes();block,receipt=image_block(path)
    assert block['mimeType']==mime and path.read_bytes()==original
    import io
    with Image.open(io.BytesIO(base64.b64decode(block['data']))) as sent:
        assert sent.size==(12,8)
        assert sent.convert('RGB').getpixel((2,2))[0]>240
    assert receipt['frame']==(0 if fmt=='GIF' else None)


def test_image_disguise_damage_bomb_orientation_and_first_frame(tmp_path):
    path=tmp_path/'wrong.jpg';Image.new('RGB',(9,6)).save(path,format='PNG')
    with pytest.raises(ValueError):image_block(path)
    path=tmp_path/'bad.png';path.write_bytes(b'not an image')
    with pytest.raises(ValueError):image_block(path)
    path=tmp_path/'large.png';Image.new('RGB',(20,20)).save(path)
    with pytest.raises(ValueError):image_block(path,max_pixels=100)
    path=tmp_path/'oriented.jpg';im=Image.new('RGB',(12,8),'red');exif=Image.Exif();exif[274]=6;im.save(path,exif=exif)
    block,receipt=image_block(path)
    import io
    assert Image.open(io.BytesIO(base64.b64decode(block['data']))).size==(8,12)
    assert receipt['exif_orientation']==6 and receipt['sent_sha256']!=receipt['original_sha256']
    path=tmp_path/'animated.gif';im.save(path,save_all=True,append_images=[Image.new('RGB',(12,8),'blue')])
    block,receipt=image_block(path)
    assert Image.open(io.BytesIO(base64.b64decode(block['data']))).convert('RGB').getpixel((1,1))==(255,0,0)
    assert receipt['frame']==0


def test_spatial_facts_survive_restart_but_cannot_be_erased_by_facade_edit(tmp_path):
    image=tmp_path/'source.png';image.write_bytes(b'source')
    c=ArchitectureContext(tmp_path,'plan',[image],[],{})
    g=graph();g['spatial']={'coordinate_frame':{'units':'mm','x':'right','front':'-Y','up':'+Z','origin':'入口左前柱脚'},
       'scale_anchors':['层高3300mm为估计'], 'critical_features':[{'id':'terrace_void','kind':'void','parts':['Slabs'],
       'description':'错层平台3300mm且中庭保持开敞','basis':'observed','source':'source_1'}], 'remaining_work':['平台连接未建造']}
    c.save_graph(g);c.card.parent.mkdir(parents=True,exist_ok=True);c.card.write_text('批准的错层方案',encoding='utf-8');c.bind_plan()
    resumed=ArchitectureContext(tmp_path,'execute',[image],[],{'harness_building':{'root_pid':9,'revision':2}})
    memory=resumed.memory()['spatial_handoff']
    assert memory['spatial_facts']==g['spatial'] and memory['keep_parts']==['Slabs','Glazing']
    assert memory['native_identity_and_revision']['revision']==2
    assert resumed.execution_parts()=={'Roof'}
    resumed.stage='plan'
    changed=graph()
    with pytest.raises(ValueError,match='空间事实'):resumed.save_graph(changed)
    assert json.loads(c.graph_path.read_text(encoding='utf-8'))==g


def test_bounded_history_archives_old_messages_without_fabricated_summary():
    messages=[{'role':'user','content':str(n)*1000} for n in range(40)]
    result=bounded_conversation(messages,max_chars=5000,max_messages=4)
    assert result[-1]==messages[-1] and len(result)<len(messages)
    assert all(item in messages for item in result)
    with pytest.raises(ValueError):bounded_conversation([{'role':'user','content':'x'*12001}])


@pytest.mark.parametrize('full',[False,True])
def test_ablation_keeps_tools_memory_config_permissions_identical(tmp_path,monkeypatch,full):
    monkeypatch.setenv('KSTUDIO_DSH_CAPABILITIES','full' if full else 'protected')
    monkeypatch.setenv('KSTUDIO_DSH_EXECUTION_POLICY','production-file-proxy')
    from app.deepseek_studio import DeepSeekStudioRuntime
    (tmp_path/'state').mkdir();(tmp_path/'state/project_context.json').write_text(json.dumps({'conversation':[{'role':'user','content':'看看这座楼'}]}),encoding='utf-8')
    requests=[]
    for arm in ('native','architecture'):
        monkeypatch.setenv('KSTUDIO_DSH_GUIDANCE',arm)
        runtime=DeepSeekStudioRuntime(tmp_path,connection=connection(reasoning_effort='high'),mcp=None)
        def capture(**kwargs):requests.append(kwargs);return SimpleNamespace(reply='test')
        monkeypatch.setattr(runtime,'_official_turn',capture)
        runtime.respond(project_dir=tmp_path,thread_id=None,prompt='看看这座楼',mcp_enabled=False)
    for field in ('prompt','specs','images','reasoning_effort','new_session_on_binding_change'):
        assert requests[0][field]==requests[1][field]
    assert requests[0]['instructions']!=requests[1]['instructions']


def test_sdk_initialization_uses_effective_default_and_output(tmp_path,monkeypatch):
    import sys
    from app.dsh_runtime import DSHHostSession
    called={}
    def sdk(**kw):called.update(kw);return SimpleNamespace(close=lambda:None)
    monkeypatch.setitem(sys.modules,'deepseek_harness',SimpleNamespace(DeepSeekHarness=sdk))
    cfg=resolve_configuration(connection())
    host=DSHHostSession(home=tmp_path/'home',workspace=tmp_path,api_base=cfg.endpoint,
        api_key='fixture-secret',model=cfg.model,specs=[],dispatch=lambda *_:{},trace_path=tmp_path/'events.jsonl',
        sdk_site=tmp_path,dsh_bin='unused',protocol=cfg.protocol,
        reasoning_effort=cfg.requested_effort,effective_configuration=cfg)
    try:
        assert called['reasoning_effort'] is None and called['max_tokens']==4096
        profile=json.loads((tmp_path/'home/kstudio.patch.yml').read_text(encoding='utf-8'))
        descriptor=next(r for r in profile if r.get('id')=='llm-pi-ai')['config']['providers']['kstudio-bai']['models'][0]
        assert descriptor['reasoningEfforts'] is False
        assert called['env']['KSTUDIO_DSH_API_KEY']=='fixture-secret'
    finally:host.close()


def test_benchmark_registration_is_finite_immutable_and_rejects_unfair_conditions(tmp_path):
    from app.modeling_benchmark import template,register,assert_equal_conditions
    spec=template()
    with pytest.raises(ValueError):register(tmp_path/'bad.json',spec)
    spec['common'].update(provider_configuration=resolve_configuration(connection()).evidence(),
        dsh_version='0.2.1-rc.5',tools_sha256='a'*64,repetitions_per_arm=1,
        budget={'currency':'CNY','maximum':1,'authorization':'fixture only; no paid calls'})
    for case in spec['cases']:
        count=2 if case['classification']=='multi_view_spatial' else 1
        case.update(source_manifest=[{'order':i,'sha256':str(i)*64,'role':'target_building'} for i in range(count)],
            natural_task='按图还原，保留露台。',critical_features=['露台开敞'],tolerances={'height_ratio':0.02})
    path=tmp_path/'registered.json';receipt=register(path,spec)
    assert receipt['specification']['status']=='REGISTERED_NOT_RUN'
    with pytest.raises(FileExistsError):register(path,spec)
    with pytest.raises(ValueError):assert_equal_conditions({'task':'same'},{'task':'same'})


def test_missing_sdk_setup_keeps_connection_status_usable(tmp_path,monkeypatch):
    from app.local_connections import connection_router
    monkeypatch.setenv('KSTUDIO_AGENT_ENGINE','deepseek-harness')
    monkeypatch.delenv('KSTUDIO_DSH_SDK_SITE',raising=False)
    monkeypatch.delenv('KSTUDIO_DSH_BIN',raising=False)
    native=SimpleNamespace(runtime_root=tmp_path,sketchup_mcp=None,available=False)
    app=SimpleNamespace(state=SimpleNamespace(native_agent=native,store=SimpleNamespace(root=tmp_path)))
    router=connection_router(app,connection())
    status=router.status()['providers']['deepseek-harness']
    assert status['credential_configured'] is True and status['available'] is False
    assert status['execution_safety']['status']=='blocked_missing_deepseek_dependency'
    assert status['effective_configuration']['requested']['reasoning_effort']=='provider-default'


def test_upload_order_and_roles_preserve_site_before_reference(tmp_path):
    from app.dsh_images import attachment_order
    first=tmp_path/'inputs/site/first.png';second=tmp_path/'inputs/reference/second.png'
    for path in (first,second):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'local-source')
    (tmp_path/'state').mkdir();(tmp_path/'state/project_context.json').write_text(json.dumps({'references':[
        {'source':'inputs/site/first.png','evidence_role':'supporting'},
        {'source':'inputs/reference/second.png','evidence_role':'target_building'}]}))
    ordered=attachment_order(tmp_path,[second,first])
    assert ordered==[first,second]
    c=ArchitectureContext(tmp_path,'clarify',ordered,[],{})
    assert [s['role'] for s in c.memory()['sources']]==['supporting','target_building']


def test_changing_provider_discards_stale_capability_declaration(monkeypatch):
    from app.local_connections import normalized_connection
    monkeypatch.setenv('KSTUDIO_AGENT_ENGINE','deepseek-harness')
    old=normalized_connection({**connection(name='first'),'capabilities_json':'{"vision":true}'})
    new=normalized_connection({**old,'api_base':'https://another.invalid/v1','api_key':'new-placeholder'},old)
    assert new['capabilities_json']=='' and not resolve_configuration(new).vision
