from pathlib import Path
import hashlib, json

root = Path(__file__).resolve().parent
project = root.parent / 'projects/su-1017'
strategy_path = project / 'runtime/agent_workspace/notes/construction_strategy.json'
strategy = json.loads(strategy_path.read_text(encoding='utf-8'))
source = next((project / 'inputs/reference').glob('*.png'))
systems = strategy['systems']
# Lossless pre-execution projection of the real website's approved planning
# data; no second generator, no direct model writer, and no fabricated results.
graph = {
    'schema_version': '2.0', 'project_id': 'su-1017', 'units': 'mm',
    'sources': [{'id': 'ref_front_01', 'type': 'reference_image', 'role': 'geometry_and_proportion',
                 'fingerprint': 'sha256:' + hashlib.sha256(source.read_bytes()).hexdigest(), 'status': 'verified_readable'}],
    'objects': [{'id': s['id'], 'type': s.get('role', 'assembly'), 'parent_id': 'project_root',
                 'planned_paths': s.get('target_paths', []), 'dimensions': {}}
                for s in systems],
    'shared_parameters': strategy['shared_parameters'],
    'website_strategy_sha256': hashlib.sha256(strategy_path.read_bytes()).hexdigest(),
    'forbidden_inventions': ['interior stairs', 'interior partitions', 'furniture', 'landscaping'],
    'unresolved': ['Hidden elevations and fine dimensions are declared inferences, not measured source facts.'],
    'model_binding': {'root_persistent_id': None, 'status': 'awaiting_real_browser_binding'},
}
ids = {s['id'] for s in systems}
plan = {
    'schema_version': '2.0', 'project_id': 'su-1017', 'run_id': 'su-trial-20261017-initial',
    'design_graph_digest': 'sha256:' + hashlib.sha256(json.dumps(graph,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
    'model_units': 'millimeters', 'intent_summary': 'Execute the real website plan for a two-storey exterior only.',
    'steps': [{'id': s['id'], 'object': s['id'], 'action': s.get('method', 'custom_owned_ruby'),
               'parameters': {k: strategy['shared_parameters'][k] for k in s.get('depends_on', []) if k in strategy['shared_parameters']},
               'depends_on': [k for k in s.get('depends_on', []) if k in ids],
               'tag': s['id'], 'component_strategy': 'named_owned_groups',
               'risk': ['single-view inferred depth and hidden elevations'], 'evidence_refs': ['ref_front_01'],
               'preconditions': ['actual blank disposable identity verified by website before write'],
               'postconditions': ['native readback resolves planned semantic paths'],
               'rollback_group': 'project-owned root', 'qa_view': 'source matched front-left and six canonical views'} for s in systems],
}
for name, data in [('design_graph.json', graph), ('buildplan.json', plan)]:
    (root/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Projected',len(systems),'real planned systems; source SHA',graph['sources'][0]['fingerprint'])
