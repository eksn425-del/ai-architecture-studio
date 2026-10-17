from pathlib import Path
import sys,json,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=ad.get_active_model_identity()
source='\n'.join(['# ARCHFLOW_GENERATED_SCRIPT; host read-only measurement','m=Sketchup.active_model',
 'raise "Wrong native document" unless m.guid=='+json.dumps(i['model_guid']),
 'r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==19}',
 'raise "Wrong owned project/revision" unless r && r.get_attribute("sketchup_architect","project_id")=="su-1017" && r.get_attribute("sketchup_architect","revision")==4',
 'names=%w[BALCONY_GUARD_FRONT BALCONY_GUARD_LEFT BALCONY_GUARD_RIGHT]',
 'rails=names.map{|n|g=r.entities.grep(Sketchup::Group).select{|x|x.name==n};raise "Ambiguous rail" unless g.length==1;b=g[0].bounds;{name:n,pid:g[0].persistent_id,min_mm:b.min.to_a.map{|v|v.to_mm},max_mm:b.max.to_a.map{|v|v.to_mm},top_above_deck_mm:b.max.z.to_mm-3000}}',
 '{read_only:true,geometry_writes:0,project_id:"su-1017",root_pid:19,revision:4,rails:rails}'])
f=_generated_script_dir()/('studio-trial-measure-'+str(time.time_ns())+'.rb');f.write_text(source,encoding='utf8');v=ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only railing height verification'});v=v.get('result',v)
if isinstance(v,str):v=json.loads(v)
assert all(abs(r['top_above_deck_mm']-1200)<0.01 for r in v['rails']),v
(R/'runtime/su-trial-20261017/actual-r4-rail-height.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(v,ensure_ascii=False))
