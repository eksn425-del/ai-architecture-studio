from pathlib import Path
import json,sys,time,argparse,hashlib
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
p=argparse.ArgumentParser();p.add_argument('--revision',type=int,required=True);p.add_argument('--stage',choices=['before','after'],required=True);z=p.parse_args();D=R/'runtime/exterior-completion-20261016';dest=D/f'r15-finish-shape-{z.stage}-r{z.revision}.json';assert not dest.exists();a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity()
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==REVISION
def fs_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def fs_child(g,n);v=fs_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing/duplicate' unless v.length==1;v.first;end
def fs_loop(l)
 p=l.vertices.map{|v|v.position.to_a.map(&:to_mm)};{outer:l.outer?,points:p.each_index.map{|j|p.rotate(j)}.min}
end
def fs_node(g,depth=0)
 raise 'Depth' if depth>24
 a=fs_es(g).map do |e|
  if e.is_a?(Sketchup::Face)
   {type:'Face',pid:e.persistent_id,normal:e.normal.to_a.map{|v|v.round(12)},loops:e.loops.map{|l|fs_loop(l)}.sort_by{|v|JSON.generate(v)},hidden:e.hidden?,tag:e.layer.name}
  elsif e.is_a?(Sketchup::Edge)
   {type:'Edge',pid:e.persistent_id,points:e.vertices.map{|v|v.position.to_a.map(&:to_mm)}.sort,hidden:e.hidden?,soft:e.soft?,smooth:e.smooth?,tag:e.layer.name}
  elsif e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)
   fs_node(e,depth+1)
  else
   raise 'Unsupported finish shape entity '+e.typename
  end
 end
 {type:g.typename,pid:g.persistent_id,name:g.name,definition_name:g.definition.name,local_transform:g.transformation.to_a.each_with_index.map{|v,j|(12..14).include?(j) ? v.to_mm : v.round(12)},hidden:g.hidden?,locked:g.locked?,tag:g.layer.name,entities:a.sort_by{|v|JSON.generate(v)}}
end
paths=[['FLOORS','L3'],['ROOF_TIMBER','CURVED_SHELL']];rows=paths.map{|p|g=r;p.each{|n|g=fs_child(g,n)};{path:p,shape:fs_node(g)}}
{revision:REVISION,geometry_writes:0,contract:'All target group/face/edge PIDs, exact vertex mm and topology/winding, names/flags/tags/translations; dimensionless normals/matrix coefficients12decimals as separately declared stable contract; materials excluded only',targets:rows}
'''.replace('GUID',json.dumps(i['model_guid'])).replace('REVISION',str(z.revision))
f=_generated_script_dir()/('studio-finish-shape-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only complete roof/slab finish-only shape and identity baseline'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;v['shape_sha256']=hashlib.sha256(json.dumps(v['targets'],sort_keys=True,separators=(',',':')).encode()).hexdigest();dest.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
if z.stage=='after':
 old=json.loads((D/'r15-finish-shape-before-r14.json').read_text(encoding='utf8'));out={'revision':z.revision,'geometry_writes':0,'status':'PASS' if old['targets']==v['targets'] else 'FAIL','before_sha256':old['shape_sha256'],'after_sha256':v['shape_sha256'],'contract':v['contract']};(D/'r15-finish-only-shape-audit.json').write_text(json.dumps(out,indent=2),encoding='utf8');assert out['status']=='PASS'
print('Finish-only complete shape/identity capture',z.stage,z.revision,v['shape_sha256'])
