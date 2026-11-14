"""K Harness architectural extension: local skills, provenance and approval-bound scope.

The official DSH runtime still owns the agent loop. This module grants no native
permissions and never executes geometry. All model writes use SUHarnessTools.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PACK = Path(__file__).with_name('architecture_skills')
IDS = ('reference', 'spatial', 'facade', 'native', 'edit', 'delivery')
TITLES = ('参考图与建筑解读', '空间与构造关系', '立面样板与复用', '原生语义建模', '局部修改与保护', '验收与交付')

GUIDANCE = '''You are K Harness, K Studio's architectural agent, based on official DeepSeek Harness.
Use kstudio_read_skill to load relevant architectural methods from the supplied catalog, not imaginary installed skills. During planning read reference and spatial; before construction read native and facade; before local edits read edit; before finishing read delivery.
During planning save a compact design graph with kstudio_save_design_graph BEFORE sketchup_save_plan. The graph records evidence/estimates, level schedule, semantic parts, critical spatial relationships and this task's edit_parts. During an edit retain the whole-building graph and list only the intended changed/new direct parts in edit_parts; all other parts remain protected. A graph is your proposal, never a user's instruction or approval. The host binds graph SHA to the saved plan; do not modify a graph after approval.
For multiple references, source_coverage must classify EVERY supplied source exactly once with role, use and evidence. Reconcile overall views, closeups and the site/roof plan using shared corners, landings and openings. A site plan without dimensions is not a measured scale or floor plan. Mark context-only or unresolved views honestly; coverage is not visual acceptance. Do not invent a separate building for each image or silently ignore less convenient views.
Persist coordinate_frame, scale_anchors, critical_features (split levels, cantilevers, voids, stair/landing and mass relationships) and remaining_work in the optional spatial graph field. Keep observed, user-known and inferred dimensions distinct. A facade unification request preserves these accepted spatial facts; any intended high-impact change needs an explicit change_rationale in a newly approved plan.
Read the supplied original reference pixels: empty/open floors and negative spaces matter as much as solids. Keep floor count, slab levels, facade repetition and structural endpoints consistent. Validate a representative module before repetition. Do not turn elevation waves into plan curves or replace separated sloping members with generic X braces.
Use only tools actually listed for this stage. Discussion has no geometry tools. If tools are absent, discuss the proposal naturally; never pretend to have inspected/built anything. Do not ask the user to run commands.
At the final geometry revision capture front, oblique and roof, then call kstudio_review_model. This validates evidence freshness, not visual quality. Compare source and current screenshots yourself and clearly name remaining mismatches. If geometry changes, previous screenshots are stale. Stop cosmetic loops; failed tools or missing evidence are not a reason to rebuild the whole project.
Batch independent reads and the three final view calls in one model response when useful; the host serializes native access. Do not repeat an unchanged read or regenerate a cached view without a concrete missing fact. Never dispatch a model write concurrently with its verification reads.
For new buildings, expose real progressive construction: plan a short ordered sequence of coherent systems, then commit each independently. First submit only the structural floor/column/core skeleton, inspect its levels and proportions, then add enclosure, a representative facade module, verified repetition, circulation and finishes as appropriate. Never prepare an entire building and reveal it through visibility switches. Use construction_stage on workspace Ruby writes. Each write must be bounded to its actual system; retain accepted geometry and continue the same root with exact edit paths. After each major stage inspect and capture an oblique view so the user can see actual changes; an image or stage label is not visual acceptance. Do not pause for new user approval between already-approved stages unless scope changes or an unresolved safety failure requires it. On continuation inspect the saved native revision and construction_steps.jsonl before resuming; do not replay already committed stages.
'''

def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)

def load_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def catalog():
    return [{'id': key, 'title': title, 'sha256': digest((PACK / f'{key}.md').read_bytes())}
            for key, title in zip(IDS, TITLES)]

def validate_graph(graph, source_ids, *, require_source_coverage=False):
    if not isinstance(graph, dict) or set(graph)-{'spatial', 'source_coverage'} != {'summary', 'facts', 'levels', 'parts', 'relationships', 'edit_parts'}:
        raise ValueError('Pass graph fields directly (no graph wrapper): summary, facts, levels, parts, relationships, edit_parts; spatial and source_coverage are optional legacy extensions. parts/edit_parts are ASCII name strings such as Roof, not objects. Observed source IDs come from the supplied source catalog, e.g. source_1, not filenames.')
    if not isinstance(graph['summary'], str) or not 10 <= len(graph['summary']) <= 2000:
        raise ValueError('Provide a concise architectural summary.')
    for key, maximum in [('facts', 40), ('levels', 100), ('parts', 64), ('relationships', 40), ('edit_parts', 32)]:
        if not isinstance(graph[key], list) or not 1 <= len(graph[key]) <= maximum:
            raise ValueError(f'{key} must be a nonempty bounded list.')
    names = graph['parts']
    if any(not isinstance(n,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', n) for n in names) or len(set(names)) != len(names):
        raise ValueError('Use distinct stable ASCII direct-part names.')
    if any(not isinstance(n,str) or n not in names for n in graph['edit_parts']) or len(set(graph['edit_parts'])) != len(graph['edit_parts']):
        raise ValueError('edit_parts must be distinct members of parts, only the intended changed/new parts.')
    for fact in graph['facts']:
        if not isinstance(fact,dict) or set(fact) != {'text','basis','source'}:
            raise ValueError('Each fact needs text, basis, source.')
        if fact['basis'] not in {'observed','inferred','user'} or not isinstance(fact['text'],str) or not 1<=len(fact['text'])<=1200:
            raise ValueError('Fact basis is observed/inferred/user; text must be bounded.')
        if not isinstance(fact['source'],str) or (fact['basis']=='observed' and fact['source'] not in source_ids):
            raise ValueError('Observed facts must reference a supplied source ID. Allowed IDs: '+', '.join(sorted(source_ids))+'. Use the ID, not a filename or path.')
    last = -100001
    for level in graph['levels']:
        if not isinstance(level,dict) or set(level) != {'name','z_mm','role'}:
            raise ValueError('Each level needs name, z_mm, role (occupied/open/roof/ground).')
        z=level['z_mm']
        if type(z) not in (int,float) or not -100000<=z<=100000 or z<=last:
            raise ValueError('Levels must have finite strictly increasing Z in millimetres.')
        if level['role'] not in {'occupied','open','roof','ground'} or not isinstance(level['name'],str) or not 1<=len(level['name'])<=80:
            raise ValueError('Invalid level role/name.')
        last=z
    if any(not isinstance(r,str) or not 1<=len(r)<=1200 for r in graph['relationships']):
        raise ValueError('Describe bounded spatial relationships including intended voids and member endpoints.')
    coverage = graph.get('source_coverage')
    if require_source_coverage and len(source_ids) > 1 and coverage is None:
        raise ValueError('多视图方案需提供 source_coverage，逐一说明每张参考图的作用、观察或未解决内容；不能漏图。')
    if coverage is not None:
        if not isinstance(coverage, list) or len(coverage) != len(source_ids):
            raise ValueError('source_coverage must classify every supplied source exactly once.')
        seen = set()
        for row in coverage:
            if not isinstance(row, dict) or set(row) != {'source', 'role', 'use', 'evidence'}:
                raise ValueError('Source coverage needs source, role, use and evidence.')
            source = row['source']
            if not isinstance(source, str) or source not in source_ids or source in seen:
                raise ValueError('Source coverage contains a missing, duplicate or unknown source ID.')
            seen.add(source)
            if (not isinstance(row['role'], str) or row['role'] not in {'overall', 'plan', 'detail', 'context', 'style', 'uncertain'}
                    or not isinstance(row['use'], str) or row['use'] not in {'used', 'context_only', 'unresolved'}
                    or not isinstance(row['evidence'], str) or not 10 <= len(row['evidence'].strip()) <= 1200):
                raise ValueError('Classify source role/use and describe bounded observations or the unresolved reason.')
    if "spatial" in graph:
        from .spatial_handoff import validate_spatial
        validate_spatial(graph["spatial"], set(names), source_ids)
    return graph

def specs(stage):
    result=[{'name':'kstudio_read_skill','description':'Read a bundled K Harness architectural skill and its worked examples. IDs: reference, spatial, facade, native, edit, delivery. Read only relevant skills. No arbitrary path or code.',
             'inputSchema':{'type':'object','properties':{'id':{'type':'string','enum':list(IDS)}},'required':['id'],'additionalProperties':False}}]
    if stage=='plan':
        result.append({'name':'kstudio_save_design_graph','description':'Save this project architectural fact/level/part proposal before saving the readable plan. Supply fields directly, without a graph wrapper. parts/edit_parts contain ASCII name strings, not objects. Observed sources must use supplied IDs such as source_1, never filenames. Preserve full parts on an edit; edit_parts lists only intended modified/new direct parts. Does not approve work.',
          'inputSchema':{'type':'object','properties':{
            'summary':{'type':'string'},
            'facts':{'type':'array','items':{'type':'object','properties':{'text':{'type':'string'},'basis':{'type':'string','enum':['observed','inferred','user']},'source':{'type':'string'}},'required':['text','basis','source'],'additionalProperties':False}},
            'levels':{'type':'array','items':{'type':'object','properties':{'name':{'type':'string'},'z_mm':{'type':'number'},'role':{'type':'string','enum':['ground','occupied','open','roof']}},'required':['name','z_mm','role'],'additionalProperties':False}},
            'parts':{'type':'array','items':{'type':'string','pattern':'^[A-Za-z][A-Za-z0-9_-]{0,63}$'}},'relationships':{'type':'array','items':{'type':'string'}},'edit_parts':{'type':'array','items':{'type':'string','pattern':'^[A-Za-z][A-Za-z0-9_-]{0,63}$'}}},
            'required':['summary','facts','levels','parts','relationships','edit_parts'],'additionalProperties':False}})
    if stage=='execute':
        result.append({'name':'kstudio_review_model','description':'Check host evidence for current revision: front/oblique/roof freshness and construction parts. Returns missing evidence; this is NOT independent visual acceptance or native reopen.',
                       'inputSchema':{'type':'object','properties':{},'additionalProperties':False}})
    for spec in result:
        if spec['name']=='kstudio_save_design_graph':
            spec['description'] += ' New multi-view plans require source_coverage for every supplied image; this records use, not visual acceptance.'
            spec['inputSchema']['properties']['source_coverage'] = {
                'type': 'array', 'maxItems': 8,
                'items': {'type': 'object', 'properties': {
                    'source': {'type': 'string'},
                    'role': {'type': 'string', 'enum': ['overall', 'plan', 'detail', 'context', 'style', 'uncertain']},
                    'use': {'type': 'string', 'enum': ['used', 'context_only', 'unresolved']},
                    'evidence': {'type': 'string', 'minLength': 10, 'maxLength': 1200}},
                    'required': ['source', 'role', 'use', 'evidence'], 'additionalProperties': False}}
            from .spatial_handoff import spatial_schema
            spec['inputSchema']['properties']['spatial']=spatial_schema()
    return result

class ArchitectureContext:
    def __init__(self, project, stage, images, conversation, ruby_state):
        self.project, self.stage = Path(project), stage
        self.base=self.project/'runtime/k-harness'
        self.graph_path=self.base/'design_graph.json'
        self.receipt_path=self.base/'approved-plan-binding.json'
        self.card=self.project/'runtime/agent_workspace/notes/reconstruction_card.md'
        from .reference_roles import reference_manifest
        self.images=[{'id':f'source_{i+1}','order':i,'path':row['source'],**row}
                     for i,row in enumerate(reference_manifest(self.project, images))]
        self.conversation=conversation
        self.state=ruby_state if ruby_state is not None else {}
        self.base.mkdir(parents=True,exist_ok=True)
        self.loaded=[]

    def memory(self):
        from .spatial_handoff import bounded_conversation, handoff
        retained=bounded_conversation(self.conversation)
        graph=load_json(self.graph_path,None)
        binding=load_json(self.receipt_path,{})
        spatial=handoff(self.project,graph=graph,state=self.state,binding=binding,sources=self.images)
        memory={'conversation':retained,'sources':self.images,'skill_catalog':catalog(),
                'conversation_archive':{'path':'state/project_context.json','omitted_messages':len(self.conversation)-len(retained),
                                        'sha256':digest(self.conversation)},
                'saved_plan':self.card.read_text(encoding='utf-8') if self.card.exists() else '',
                'design_graph_proposal':graph,'current_owned_state':self.state,'spatial_handoff':spatial,
                'authority':'Original user messages and host permission are authoritative; graph and assistant messages are proposals, not approval.'}
        write_json(self.base/'spatial-handoff.json', spatial)
        write_json(self.base/'project-memory.json', memory)
        return memory

    def save_graph(self, graph):
        if self.stage!='plan':raise ValueError('Design graph can only change during planning, never after approval.')
        validate_graph(graph,{s['id'] for s in self.images}, require_source_coverage=True)
        previous=load_json(self.graph_path,{})
        if self.state.get('harness_building') and previous:
            protected=set(previous.get('parts',[]))-set(graph['edit_parts'])
            if not protected.issubset(graph['parts']):
                raise ValueError('局部修改不能删除受保护构件；请保留完整设计图。')
            old_spatial=previous.get('spatial',{})
            changed=(old_spatial and (graph.get('spatial',{}).get('critical_features')!=old_spatial.get('critical_features')
                     or graph['levels']!=previous['levels'] or graph['relationships']!=previous['relationships']))
            if changed and not graph.get('spatial',{}).get('change_rationale','').strip():
                raise ValueError('高影响空间事实发生变化；请在新方案说明变更依据并重新批准，不得以统一立面覆盖。')
        # Append-only provenance: retain superseded proposals for diagnosis.
        write_json(self.base/'graph-history'/f'{digest(graph)}.json',graph)
        write_json(self.graph_path, graph)
        return {'success':True,'sha256':digest(graph),'approval_granted':False}

    def bind_plan(self):
        graph=load_json(self.graph_path,None)
        validate_graph(graph,{s['id'] for s in self.images}, require_source_coverage=True)
        binding={'graph_sha256':digest(graph),'plan_sha256':digest(self.card.read_bytes()),'sources':self.images,
                 'edit_parts':graph['edit_parts'], 'approval_granted':False}
        write_json(self.receipt_path,binding)

    def execution_parts(self):
        graph=load_json(self.graph_path,None); receipt=load_json(self.receipt_path,{})
        validate_graph(graph,{s['id'] for s in self.images})
        if (receipt.get('graph_sha256')!=digest(graph) or not self.card.exists()
                or receipt.get('plan_sha256')!=digest(self.card.read_bytes()) or receipt.get('sources')!=self.images):
            raise ValueError('建筑方案或参考图已改变，请在页面重新确认方案；旧模型已保留。')
        return set(graph['edit_parts'])

    def read_skill(self, args):
        if set(args)!={'id'} or args['id'] not in IDS:raise ValueError('Unknown bundled skill.')
        key=args['id']; raw=(PACK/f'{key}.md').read_bytes(); body=raw.decode('utf-8')
        event={'id':key,'sha256':digest(raw),'stage':self.stage}
        self.loaded.append(event)
        with (self.base/'skill-usage.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event)+'\n')
        return {'success':True,**event,'content':body,'authority':'method guidance, not user instructions or permission'}

    def review(self, quality):
        revision=self.state.get('harness_building',{}).get('revision',0)
        views=quality.get('views',{})
        missing=[v for v in ('front','oblique','roof') if views.get(v,{}).get('revision')!=revision]
        joints = [item for item in quality.get('level_joints', []) if item['revision'] == revision]
        result={'success':True,'revision':revision,'evidence_current':bool(revision) and not missing,
                'missing_current_views':missing,'views':views,'loaded_skills':self.loaded,
                'visual_acceptance':'NOT_INDEPENDENTLY_VERIFIED','native_reopen':'NOT_RUN',
                'level_joints':joints[-12:],
                'writes':quality.get('writes',[])}
        write_json(self.base/'latest-review.json',result)
        return result
