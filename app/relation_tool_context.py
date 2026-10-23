"""Expose measured relation repair plans through the existing Blender tool surface."""
import json
from pathlib import Path
from .repair_relations import plan_relation_repairs,evaluate_relation_repairs
NAMES={'blender_plan_relation_repair','blender_check_relation_repair'}


def prepare_relation_tools(project:Path,backend):
    path=project/'state/blender_relation_repair.json'
    def epoch():
        marker=project/'runtime/relation_execution_epoch.json'
        if marker.is_symlink():raise ValueError('Unsafe approval epoch path')
        return json.loads(marker.read_text(encoding='utf-8')).get('pending_plan_id','') if marker.exists() else ''
    def archive(plan):
        file=project/'runtime/relation_repair_history.jsonl'
        file.parent.mkdir(parents=True,exist_ok=True)
        if file.is_symlink():raise ValueError('Unsafe repair history path')
        with file.open('a',encoding='utf-8') as f:f.write(json.dumps(plan)+'\n')
    def load():
        if path.is_symlink():raise ValueError('Unsafe relation plan path')
        plan=json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
        if plan and plan.get('approval_epoch','') != epoch():
            archive({**plan,'archived_reason':'new_host_approved_plan'})
            path.unlink()
            return None
        return plan
    def save(plan):
        if path.is_symlink() or path.parent.is_symlink():raise ValueError('Unsafe relation plan path')
        path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp')
        if temp.is_symlink():raise ValueError('Unsafe relation temporary path')
        plan['approval_epoch']=epoch()
        temp.write_text(json.dumps(plan,ensure_ascii=False),encoding='utf-8');temp.replace(path)
    def dispatch(name,args):
        scene=backend.dispatch('blender_inspect_scene',{})
        current=load()
        if name=='blender_plan_relation_repair':
            if set(args)!={'review','repairs'}:raise ValueError('Expected review proposal and repairs')
            if current and not current.get('declared_relations_satisfied'):
                return {**current,'note':'Existing unresolved repair plan retained; budget was not reset.'}
            plan=plan_relation_repairs(args['review'],scene,args['repairs'])
            if current:
                archive(current)
        else:
            if name!='blender_check_relation_repair' or args or not current:raise ValueError('No current relation repair plan')
            plan=evaluate_relation_repairs(current,scene)
        save(plan);return plan
    def before_write(arguments):
        plan=load()
        if not plan or plan.get('declared_relations_satisfied'):return
        if plan.get('status')=='blocked' or plan.get('remaining_attempts',0)<=0:
            raise ValueError('Relation repair budget/state requires inspection; no blind repeated write.')
        proposed={x.get('id') for x in arguments.get('objects',[]) if isinstance(x,dict)}|set(arguments.get('delete_ids',[]))
        if not proposed.issubset(set(plan['component_ids'])):
            raise ValueError('Relation repair must protect unrelated components.')
    def after_write():
        plan=load()
        if not plan or plan.get('declared_relations_satisfied'):return None
        result=evaluate_relation_repairs(plan,backend.dispatch('blender_inspect_scene',{}));save(result);return result
    specs=[{'name':'blender_plan_relation_repair','description':'Map agent-proposed issue priorities to exact existing components and measured connections BEFORE local repair. review={issues:[{priority,problem,action}],needs_fix:true}; repairs=[{priority,component_ids,planned_edit,connections:[{a,b,axis:0|1|2,tolerance:metres}]}]. Host keeps all other components and checks each subsequent commit. Two checked attempts; no independent visual PASS implied.','inputSchema':{'type':'object','properties':{'review':{'type':'object'},'repairs':{'type':'array','minItems':1,'maxItems':8,'items':{'type':'object'}}},'required':['review','repairs'],'additionalProperties':False}},
      {'name':'blender_check_relation_repair','description':'Read host-persisted measured relation closure, KEEP and unresolved priorities. Does not change geometry or certify source fidelity.','inputSchema':{'type':'object','properties':{},'additionalProperties':False}}]
    return specs,dispatch,before_write,after_write
