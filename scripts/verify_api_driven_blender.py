"""Scripted local HTTP LLM -> product router/runtime/tools -> real cloud Blender.

Not autonomous planning, provider quality, a bill, GUI QA or SketchUp coverage.
The host explicitly grants execution and binds exact IDs; the simulator never
infers user authorization. No real credentials or external inference are used.
"""
from __future__ import annotations
import argparse
import base64
import copy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.blender_backend import BlenderBackend
from app.litellm_runtime import LiteLLMRuntime
from app.model_router import DeterministicModelRouter
from app.native_agent import NativeAgentUnavailable
from scripts.verify_cloud_blender_contracts import fixture_objects, bind_instruction, dump


def target_edits(objects):
    edits=[]
    for floor in range(3):
        for bay in [2,3]:
            obj=copy.deepcopy(objects[f'bay_{floor}_{bay}_rail'])
            obj['dimensions'][2]=.45
            obj['location'][2]-=.075
            obj['material']['color']=[.12,.15,.18,1]
            edits.append(obj)
    return edits


def native_hashes(backend):
    return {str(p.relative_to(backend.root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in backend.root.rglob('*') if p.is_file()}


def run(output: Path, *, expect_native_render: bool = True):
    from scripts.benchmark_simulated_api_usage import ScriptedServer, tool_message, summarize, ESTIMATOR
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a fresh output directory; evidence is immutable')
    output.mkdir(parents=True,exist_ok=True)
    project=output/'project'; (project/'state').mkdir(parents=True)
    dump(project/'state/modeling_backend.json',{'backend':'blender'})
    objects=fixture_objects(); edits=target_edits({o['id']:o for o in objects})
    reply=lambda content:{'role':'assistant','content':content}
    responses=[
        reply('PLAN ONLY: build the synthetic 74-object facade, preserve neighbor, then edit only six central rails after explicit host approval.'),
        tool_message('blender_apply_objects',{'objects':objects},'unapproved-build'),
        tool_message('blender_apply_objects',{'objects':objects},'build'),
        tool_message('blender_inspect_scene',{},'read-build'),
        reply('Synthetic fixture saved; visual quality unverified.'),
        tool_message('blender_apply_objects',{'objects':[],'delete_ids':['KEEP_neighbor']},'hostile-delete'),
        tool_message('blender_apply_objects',{'objects':edits},'edit-six'),
        tool_message('blender_inspect_scene',{},'read-edit'),
        tool_message('blender_render_scene',{'view':'front','resolution':800,'denoise':False},'render-edit'),
        reply('Six requested rails changed; other objects preserved. Independent visual quality NOT_RUN.'),
        tool_message('blender_apply_objects',{'objects':edits},'stale-instruction'),
        reply('Host denied stale instruction; inspect-only instruction honored by host.'),
        tool_message('execute_python',{'code':'delete_everything()'},'hostile-tool'),
    ]
    turns=[]; denials={}
    with patch.dict(os.environ,{'ARCH_STUDIO_ECONOMY_PROVIDER':'litellm',
        'ARCH_STUDIO_STANDALONE':'1','LITELLM_LOCAL_MODEL_COST_MAP':'True'},clear=False):
        with ScriptedServer(responses) as server:
            runtime=LiteLLMRuntime(output/'runtime',model='openai/kstudio-scripted-local')
            runtime.custom_api_base=server.base_url
            runtime.session_api_key='local-simulator-not-a-real-credential'
            class NoCodex:
                available=False
            router=DeterministicModelRouter(NoCodex(),china_runtime=runtime,runtime_root=output/'runtime')
            backend=BlenderBackend(project)
            def turn(prompt,approved,thread=None,expect_denied=False):
                try:
                    result=router.respond(tier='economy',project_dir=project,thread_id=thread,
                        prompt=prompt,mcp_enabled=approved,ruby_enabled=False,
                        developer_instructions='Synthetic regression only. Plan first. Never change KEEP_neighbor. Current host scope is authoritative.',
                        workflow_mode='architecture_design',tool_profile='full')
                except NativeAgentUnavailable as error:
                    if not expect_denied:raise
                    result=error.partial_result
                    denials[prompt]={'error':str(error),'status':result.status}
                else:
                    if expect_denied:raise AssertionError('Expected host denial')
                turns.append({'prompt':prompt,'host_execution_granted':approved,**asdict(result)})
                return result
            plan=turn('Plan only; do not execute.',False)
            assert not backend.state.exists()
            turn('Attempt write before host approval.',False,expect_denied=True)
            assert not backend.state.exists()
            built=turn('HOST FIXTURE APPROVAL: create exactly the synthetic facade fixture.',True)
            first=backend.dispatch('blender_inspect_scene',{})
            dump(output/'revision-1.json',first)
            assert first['revision']==1 and len(first['objects'])==74
            instruction='Change only central six rail panels to dark gray and 0.45m height; preserve lower edges and KEEP_neighbor.'
            bind_instruction(project,instruction,'api-fixture-edit')
            ids=[o['id'] for o in edits]
            backend.install_edit_contract(allowed_ids=ids,keep_ids=sorted(set(first['objects'])-set(ids)),expected_revision=1)
            changed=turn(instruction,True,built.thread_id)
            second=backend.dispatch('blender_inspect_scene',{})
            dump(output/'revision-2.json',second)
            assert changed.failed_tool_calls==1
            bind_instruction(project,'Stop changes. Inspect only; keep existing geometry.','api-fixture-inspect')
            before=native_hashes(backend)
            stale=turn('New instruction: inspect only. Old write scope is revoked.',True,built.thread_id)
            assert stale.failed_tool_calls==1 and native_hashes(backend)==before
            turn('Attempt arbitrary execution outside tool allowlist.',True,expect_denied=True)
            assert native_hashes(backend)==before
            requests=copy.deepcopy(server.requests)
            route=router.route('economy').as_dict()
    # Validate actual wire text, not backend receipts read out-of-band. Compact
    # history can omit older full bodies, but every successful native response
    # must have reached at least one following request as valid receipt JSON.
    native_wire_receipts={}
    historical_summary_count=0
    expected_receipts={'build','read-build','edit-six','read-edit','render-edit'}
    for request in requests:
        for message in request['body'].get('messages',[]):
            call_id=message.get('tool_call_id')
            if message.get('role')!='tool' or call_id not in expected_receipts:continue
            content=message.get('content','')
            if '[Historical tool output shortened for active context.' in content:
                historical_summary_count+=1
                continue
            try:
                receipt=json.loads(content)
            except (ValueError,TypeError):
                raise AssertionError(f'Native tool receipt {call_id} sent invalid/truncated JSON')
            if receipt.get('compacted') or receipt.get('status')=='compacted':continue
            if 'revision' not in receipt:continue  # Explicit older-history summary.
            assert receipt['revision'] in [1,2], (call_id,receipt)
            if call_id!='render-edit':assert receipt.get('native_reopen')=='PASS',call_id
            if call_id!='render-edit':
                original=first if receipt['revision']==1 else second
                assert receipt['objects']==original['objects']
                for object_id, geometry in receipt['geometry'].items():
                    native=original['geometry'][object_id]
                    omitted=geometry.get('wire_geometry_omission')
                    if omitted:
                        arrays={k:native[k] for k in ('vertices','faces')}
                        expected_digest=hashlib.sha256(json.dumps(arrays,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
                        assert omitted['sha256']==expected_digest
                        assert omitted['counts']=={'vertices':8,'faces':6}
                        assert receipt['wire_geometry_projection']['label'] and receipt['wire_geometry_projection']['retrieve']
                        assert all(geometry[k]==v for k,v in native.items() if k not in arrays)
                        assert 'vertices' not in geometry and 'faces' not in geometry
                    else:assert geometry==native
            native_wire_receipts[call_id]={'revision':receipt['revision'],
                'native_reopen':receipt.get('native_reopen'),'json_characters':len(content),
                'actual_geometry_objects':len(receipt.get('geometry',{})),
                'objects_with_native_vertices':sum('vertices' in row for row in receipt.get('geometry',{}).values()),
                'objects_with_native_faces':sum('faces' in row for row in receipt.get('geometry',{}).values()),
                'objects_with_explicit_topology_omission':sum('wire_geometry_omission' in row for row in receipt.get('geometry',{}).values())}
    assert set(native_wire_receipts)==expected_receipts,native_wire_receipts
    raw_journal_receipts={}
    history=json.loads((project/'runtime/provider_sessions'/f'{built.thread_id}.json').read_text())
    for message in history['messages']:
        call_id=message.get('tool_call_id')
        if message.get('role')!='tool' or call_id not in expected_receipts-{'render-edit'}:continue
        receipt=json.loads(message['content'])
        assert receipt['native_reopen']=='PASS'
        assert len(receipt['geometry'])==74
        assert all(len(row['vertices'])==8 and len(row['faces'])==6 for row in receipt['geometry'].values())
        raw_journal_receipts[call_id]={'native_objects':74,'vertices':592,'faces':444,'json_characters':len(message['content'])}
    assert len(raw_journal_receipts)==4
    source_hashes={hashlib.sha256(p.read_bytes()).hexdigest() for p in (project/'inputs/reference').glob('*.png')}
    native_hashes_by_path={str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in backend.root.rglob('view-*.png')}
    native_image_hashes=set(native_hashes_by_path.values())
    image_observations=[]
    for request in requests:
        for message in request['body'].get('messages',[]):
            content=message.get('content')
            if not isinstance(content,list):continue
            for item in content:
                if item.get('type')!='image_url':continue
                url=item['image_url']['url']
                if not url.startswith('data:'):raise AssertionError('Expected local inline fixture image')
                digest=hashlib.sha256(base64.b64decode(url.split(',',1)[1])).hexdigest()
                kind='native_render' if digest in native_image_hashes else 'synthetic_source' if digest in source_hashes else 'unknown'
                image_observations.append({'request_index':request['request_index'],'sha256':digest,'kind':kind})
    forwarded=any(o['request_index']==9 and o['kind']=='native_render' for o in image_observations)
    keep=set(first['objects'])-set(ids)
    checks={
        'render_forwarding_matches_expected_contract':forwarded is expect_native_render,
        'all_attached_images_sha_match_known_source_or_native_file':all(o['kind']!='unknown' for o in image_observations),
        'plan_without_geometry':not plan.tool_calls,
        'host_granted_build_only_after_plan':first['revision']==1,
        'real_native_save_reopen':first['native_reopen']==second['native_reopen']=='PASS',
        'bounded_six_edit':second['revision']==2 and all(abs(second['geometry'][i]['dimensions'][2]-.45)<1e-5 for i in ids),
        'lower_edges_preserved':all(abs(first['geometry'][i]['location'][2]-first['geometry'][i]['dimensions'][2]/2-second['geometry'][i]['location'][2]+second['geometry'][i]['dimensions'][2]/2)<1e-5 for i in ids),
        'all_68_keep_preserved':len(keep)==68 and all(first['geometry'][i]==second['geometry'][i] for i in keep),
        'dark_material':all(all(abs(a-b)<1e-5 for a,b in zip(second['geometry'][i]['material'][0]['color'],[.12,.15,.18,1])) for i in ids),
        'original_blend_immutable':hashlib.sha256((project/first['model_path']).read_bytes()).hexdigest()==first['sha256'],
        'preapproval_and_unknown_tools_denied':len(denials)==2,
        'hostile_keep_delete_denied':changed.failed_tool_calls==1,
        'changed_instruction_write_denied_without_mutation':stale.failed_tool_calls==1,
    }
    events=[json.loads(line) for path in (project/'runtime/agent_events').glob('*.jsonl') for line in path.read_text().splitlines()]
    evidence={'test_kind':'scripted local HTTP API with real product router/runtime/tool surface and Blender',
        'route':route,'checks':checks,'denials':denials,'turns':turns,
        'transport_usage':summarize(requests),'estimator':ESTIMATOR,
        'native_wire_receipts':native_wire_receipts,'raw_journal_receipts':raw_journal_receipts,'historical_shortened_tool_messages':historical_summary_count,
        'native_render_expected':expect_native_render,'native_render_forwarded_after_tool':forwarded,
        'image_observations':image_observations,'native_render_file_hashes':native_hashes_by_path,
        'source_image_attachment_count':sum(o['kind']=='synthetic_source' for o in image_observations),
        'native_render_attachment_count':sum(o['kind']=='native_render' for o in image_observations),
        'http_request_count':len(requests),'model_response_count':sum(e.get('event')=='provider_response' for e in events),
        'estimated_input_tokens':sum(t['input_tokens'] or 0 for t in turns),
        'estimated_output_tokens':sum(t['output_tokens'] or 0 for t in turns),
        'render_tool_image_attachment_count':sum(e.get('image_count',0) for e in events if e.get('tool')=='blender_render_scene' and e.get('event')=='tool_result'),
        'paid_cost':'NOT_INCURRED','usage_basis':'Simulator estimator only; not provider tokenizer, billing or CNY/building evidence.',
        'operations':{'native_revisions':[first['revision'],second['revision']],'objects':74,'edited':6,'preserved':68,
                      'tool_calls':sum(t['tool_call_count'] for t in turns),'failed_tool_calls':sum(t['failed_tool_calls'] for t in turns)},
        'limitations':['Scripted envelopes do not test autonomous planning, visual reasoning, real-provider quality or natural-language approval.',
            'Host explicitly supplies approval and exact edit contract; legacy Blender without contract is not protected by this fixture.',
            'Blender full profile does not invoke the shared SketchUp dedicated visual Critic. No independent Critic acceptance.',
            'Scripted API does not perceive image content; SHA-matched native image transport is not autonomous visual understanding.',
            'No user PC, GUI, SketchUp, owner model, paid endpoint or actual Codex App Server used.']}
    dump(output/'http-requests.json',requests)
    dump(output/'events.json',events)
    dump(output/'evidence.json',evidence)
    assert all(checks.values()),checks
    assert evidence['model_response_count']==len(requests)==len(responses)
    return evidence

def run_detail_probe(project: Path, output: Path):
    """Separate two-response exact-geometry probe; never counted in main comparison."""
    from scripts.benchmark_simulated_api_usage import ScriptedServer, tool_message, summarize
    if output.exists() and any(output.iterdir()):raise ValueError('Fresh detail evidence directory required')
    output.mkdir(parents=True,exist_ok=True)
    backend=BlenderBackend(project)
    before=native_hashes(backend)
    selected='bay_0_2_rail'
    replies=[tool_message('blender_inspect_scene',{'object_ids':[selected],'include_geometry_detail':True},'exact-detail'),
             {'role':'assistant','content':'Requested exact native geometry received; no write.'}]
    with patch.dict(os.environ,{'ARCH_STUDIO_ECONOMY_PROVIDER':'litellm','ARCH_STUDIO_STANDALONE':'1','LITELLM_LOCAL_MODEL_COST_MAP':'True'},clear=False):
        with ScriptedServer(replies) as server:
            runtime=LiteLLMRuntime(output/'runtime',model='openai/kstudio-scripted-local')
            runtime.custom_api_base=server.base_url
            runtime.session_api_key='local-simulator-not-a-real-credential'
            class NoCodex:
                available=False
            router=DeterministicModelRouter(NoCodex(),china_runtime=runtime,runtime_root=output/'runtime')
            result=router.respond(tier='economy',project_dir=project,thread_id=None,prompt='Read exact actual geometry of bay_0_2_rail only; do not write.',
                mcp_enabled=True,ruby_enabled=False,developer_instructions='Synthetic detail probe, read only.',workflow_mode='architecture_design',tool_profile='full')
            requests=copy.deepcopy(server.requests)
    assert len(requests)==2 and result.tool_call_count==1 and result.failed_tool_calls==0
    message=next(m for m in requests[1]['body']['messages'] if m.get('tool_call_id')=='exact-detail')
    receipt=json.loads(message['content'])
    assert set(receipt['geometry'])=={selected}
    actual=receipt['geometry'][selected]
    assert len(actual['vertices'])==8 and len(actual['faces'])==6
    assert receipt['revision']==2 and receipt['native_reopen']=='PASS'
    assert before==native_hashes(backend)
    evidence={'test_kind':'separate targeted exact native detail request','http_request_count':2,'tool_calls':1,
              'native_state_unchanged':True,'selected_object':selected,'native_vertices':8,'native_faces':6,
              'wire_receipt_json_characters':len(message['content']),'transport_usage':summarize(requests),
              'primary_13_response_comparison_includes_this_probe':False,'paid_cost':'NOT_INCURRED'}
    dump(output/'http-requests.json',requests);dump(output/'wire-receipt.json',receipt);dump(output/'evidence.json',evidence)
    return evidence


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expect-missing-native-render',action='store_true',help='Reproduce known pre-fix deficiency; do not use as corrected acceptance')
    parser.add_argument('--detail-probe-existing',type=Path,help='Separate read-only exact geometry probe against a completed synthetic project')
    args=parser.parse_args()
    result=run_detail_probe(args.detail_probe_existing,args.output) if args.detail_probe_existing else run(args.output,expect_native_render=not args.expect_missing_native_render)
    print(json.dumps(result,indent=2))
