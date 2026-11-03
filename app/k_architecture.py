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
Read the supplied original reference pixels: empty/open floors and negative spaces matter as much as solids. Keep floor count, slab levels, facade repetition and structural endpoints consistent. Validate a representative module before repetition. Do not turn elevation waves into plan curves or replace separated sloping members with generic X braces.
Use only tools actually listed for this stage. Discussion has no geometry tools. If tools are absent, discuss the proposal naturally; never pretend to have inspected/built anything. Do not ask the user to run commands.
At the final geometry revision capture front, oblique and roof, then call kstudio_review_model. This validates evidence freshness, not visual quality. Compare source and current screenshots yourself and clearly name remaining mismatches. If geometry changes, previous screenshots are stale. Stop cosmetic loops; failed tools or missing evidence are not a reason to rebuild the whole project.
Batch independent reads and the three final view calls in one model response when useful; the host serializes native access. Do not repeat an unchanged read or regenerate a cached view without a concrete missing fact. Never dispatch a model write concurrently with its verification reads.
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

def validate_graph(graph, source_ids):
    if not isinstance(graph, dict) or set(graph) != {'summary', 'facts', 'levels', 'parts', 'relationships', 'edit_parts'}:
        raise ValueError('Graph requires summary, facts, levels, parts, relationships, edit_parts.')
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
    return graph

def specs(stage):
    result=[{'name':'kstudio_read_skill','description':'Read a bundled K Harness architectural skill and its worked examples. IDs: reference, spatial, facade, native, edit, delivery. Read only relevant skills. No arbitrary path or code.',
             'inputSchema':{'type':'object','properties':{'id':{'type':'string','enum':list(IDS)}},'required':['id'],'additionalProperties':False}}]
    if stage=='plan':
        result.append({'name':'kstudio_save_design_graph','description':'Save this project architectural fact/level/part proposal before saving the readable plan. Preserve full parts on an edit; edit_parts lists only intended modified/new direct parts. Does not approve work.',
          'inputSchema':{'type':'object','properties':{
            'summary':{'type':'string'},
            'facts':{'type':'array','items':{'type':'object','properties':{'text':{'type':'string'},'basis':{'type':'string','enum':['observed','inferred','user']},'source':{'type':'string'}},'required':['text','basis','source'],'additionalProperties':False}},
            'levels':{'type':'array','items':{'type':'object','properties':{'name':{'type':'string'},'z_mm':{'type':'number'},'role':{'type':'string','enum':['ground','occupied','open','roof']}},'required':['name','z_mm','role'],'additionalProperties':False}},
            'parts':{'type':'array','items':{'type':'string'}},'relationships':{'type':'array','items':{'type':'string'}},'edit_parts':{'type':'array','items':{'type':'string'}}},
            'required':['summary','facts','levels','parts','relationships','edit_parts'],'additionalProperties':False}})
    if stage=='execute':
        result.append({'name':'kstudio_review_model','description':'Check host evidence for current revision: front/oblique/roof freshness and construction parts. Returns missing evidence; this is NOT independent visual acceptance or native reopen.',
                       'inputSchema':{'type':'object','properties':{},'additionalProperties':False}})
    return result

class ArchitectureContext:
    def __init__(self, project, stage, images, conversation, ruby_state):
        self.project, self.stage = Path(project), stage
        self.base=self.project/'runtime/k-harness'
        self.graph_path=self.base/'design_graph.json'
        self.receipt_path=self.base/'approved-plan-binding.json'
        self.card=self.project/'runtime/agent_workspace/notes/reconstruction_card.md'
        self.images=[{'id':f'source_{i+1}','path':p.relative_to(self.project).as_posix(),'sha256':digest(p.read_bytes())} for i,p in enumerate(images)]
        self.conversation=conversation
        self.state=ruby_state if ruby_state is not None else {}
        self.base.mkdir(parents=True,exist_ok=True)
        self.loaded=[]

    def memory(self):
        # Original user messages are retained verbatim outside model summaries.
        retained=[{'role':m['role'],'content':m.get('content','')} for i,m in enumerate(self.conversation)
                  if m.get('role')=='user' or (i>=len(self.conversation)-4 and m.get('role')=='assistant')]
        memory={'conversation':retained,'sources':self.images,'skill_catalog':catalog(),
                'saved_plan':self.card.read_text(encoding='utf-8') if self.card.exists() else '',
                'design_graph_proposal':load_json(self.graph_path,None),'current_owned_state':self.state,
                'authority':'Original user messages and host permission are authoritative; graph and assistant messages are proposals, not approval.'}
        write_json(self.base/'project-memory.json', memory)
        return memory

    def save_graph(self, graph):
        if self.stage!='plan':raise ValueError('Design graph can only change during planning, never after approval.')
        validate_graph(graph,{s['id'] for s in self.images})
        # Append-only provenance: retain superseded proposals for diagnosis.
        write_json(self.base/'graph-history'/f'{digest(graph)}.json',graph)
        write_json(self.graph_path, graph)
        return {'success':True,'sha256':digest(graph),'approval_granted':False}

    def bind_plan(self):
        graph=load_json(self.graph_path,None)
        validate_graph(graph,{s['id'] for s in self.images})
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
        key=args['id']; body=(PACK/f'{key}.md').read_text(encoding='utf-8')
        event={'id':key,'sha256':digest(body.encode()),'stage':self.stage}
        self.loaded.append(event)
        with (self.base/'skill-usage.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event)+'\n')
        return {'success':True,**event,'content':body,'authority':'method guidance, not user instructions or permission'}

    def review(self, quality):
        revision=self.state.get('harness_building',{}).get('revision',0)
        views=quality.get('views',{})
        missing=[v for v in ('front','oblique','roof') if views.get(v,{}).get('revision')!=revision]
        result={'success':True,'revision':revision,'evidence_current':bool(revision) and not missing,
                'missing_current_views':missing,'views':views,'loaded_skills':self.loaded,
                'visual_acceptance':'NOT_INDEPENDENTLY_VERIFIED','native_reopen':'NOT_RUN',
                'writes':quality.get('writes',[])}
        write_json(self.base/'latest-review.json',result)
        return result
