"""Pre-registration of bounded, auditable modeling ablations; does not call a model."""
import hashlib
import json
from pathlib import Path

CLASSES=('facade_layers','split_level_cantilever_stairs','multi_view_spatial')
ARMS=('official_dsh_baseline','kstudio_minimal','kstudio_architecture')


def template():
    common={'provider_configuration':None,'dsh_version':None,'tools_sha256':None,
            'memory_strategy':'r2-spatial-handoff','single_writer':True,
            'repetitions_per_arm':None,'budget':{'currency':'CNY','maximum':None,'authorization':None},
            'max_corrections_per_part':2,'stop_on':['budget_exhausted','unknown_native_commit','cancelled','auth_or_quota_failure'],
            'review':{'deterministic':True,'source_matched_human':True,'independent_ai':'NOT_RUN'},
            'no_model_substitution':True}
    return {'schema_version':1,'status':'NOT_REGISTERED','common':common,'arms':list(ARMS),
            'cases':[{'id':kind,'classification':kind,'source_manifest':[], 'source_status':'NOT_SELECTED',
                      'natural_task':'','scale_anchors':[],'critical_features':[],
                      'occluded_inference_rule':'Coherent bounded estimates, explicitly labeled inferred; no invented measurement.',
                      'success_criteria':['source-visible critical geometry preserved','KEEP unchanged','saved/downloaded native reopen matches','editable semantic groups'],
                      'failure_criteria':['missing or changed critical spatial feature','protected geometry changed','unknown commit repeated','native reopen mismatch'],
                      'tolerances':{},'result':'NOT_RUN'} for kind in CLASSES]}


def register(path, specification):
    """Freeze complete criteria before a bounded run, without spending authorization.

    Source manifests identify local files by SHA/order/role, not public paths.
    A fresh registration never rewrites an earlier experiment's criteria.
    """
    value=json.loads(json.dumps(specification,allow_nan=False))
    if value.get('schema_version')!=1 or set(value.get('arms',[]))!=set(ARMS):
        raise ValueError('All three prespecified comparison arms are required.')
    common=value['common'];budget=common['budget']
    if not isinstance(common.get('provider_configuration'),dict) or not common.get('dsh_version') or not common.get('tools_sha256'):
        raise ValueError('Register exact effective model configuration, DSH version and tools first.')
    if (type(common.get('repetitions_per_arm')) is not int or not 1<=common['repetitions_per_arm']<=5
        or type(budget.get('maximum')) not in (int,float) or budget['maximum']<=0 or not budget.get('authorization')):
        raise ValueError('A finite authorized budget and bounded repeat count are required.')
    cases=value.get('cases',[])
    if set(c.get('classification') for c in cases)!=set(CLASSES):raise ValueError('Register all three source classes.')
    for case in cases:
        sources=case.get('source_manifest',[])
        if (not sources or not case.get('natural_task') or not case.get('critical_features') or not case.get('tolerances')
            or not case.get('success_criteria') or not case.get('failure_criteria')):
            raise ValueError('Freeze source evidence, task, critical features, tolerances and pass/fail criteria.')
        if case['classification']=='multi_view_spatial' and len(sources)<2:
            raise ValueError('A single photo cannot stand in for a multi-view benchmark.')
        for index,source in enumerate(sources):
            sha=source.get('sha256','')
            if (source.get('order')!=index or source.get('role')!='target_building' or len(sha)!=64
                or any(c not in '0123456789abcdef' for c in sha)):
                raise ValueError('Invalid ordered source hash or target role.')
    value['status']='REGISTERED_NOT_RUN'
    body=json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)
    receipt={'specification_sha256':hashlib.sha256(body.encode()).hexdigest(),'specification':value}
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,ensure_ascii=False,indent=2)
    return receipt


def assert_equal_conditions(left,right):
    """Guidance/skill invocation may differ; configuration, tools and inputs may not."""
    for key in ('effective_configuration','source_manifest','tools_sha256','memory_strategy','permissions','dsh_version','budget','task'):
        if key not in left or key not in right or left[key]!=right[key]:
            raise ValueError(f'Ablation conditions differ or are missing: {key}')
