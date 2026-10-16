from pathlib import Path
import sys,json,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
D=R/'runtime/exterior-completion-20261016';P=R/'runtime/projects/architecture-project-4f0e4';a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();policy=json.loads((P/'runtime/active_edit_scope.json').read_text(encoding='utf8'))
body='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'Identity' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==13
def im_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def im_child(g,n);v=im_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Ambiguous/missing' unless v.size==1;v.first;end
def im_tile(g)
 return g if g.is_a?(Sketchup::ComponentInstance)&&g.definition.name.start_with?('KS_FINE_WHITE_MESH_')
 im_es(g).each{|e|next unless e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance);v=im_tile(e);return v if v};nil
end
def im_hits(g,t,origin,dir)
 hits=[];im_es(g).each do |e|
  if e.is_a?(Sketchup::Face)
   inv=t.inverse;o=inv*origin;v=dir.transform(inv);p=Geom.intersect_line_plane([o,v],e.plane);next unless p&&[Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(e.classify_point(p));wp=t*p;d=(wp-origin).dot(dir);hits<<d.to_mm if d>=0&&d.to_mm<=200
  elsif e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)
   hits.concat(im_hits(e,t*e.transformation,origin,dir))
  end
 end;hits
end
out=[];paths=JSON.parse(PATHS)
paths.select{|p|p.last.start_with?('LONG_RAIL_','RAMP_','LANDING_L1_GUARD_')||p.last.end_with?('_SLOT_GUARD')}.each do |path|
 g=r;path.each{|n|g=im_child(g,n)};tile=im_tile(g);raise 'Missing mesh' unless tile
 vs=im_es(tile).select{|e|e.respond_to?(:name)&&e.name.match?(/_V\\d+$/)}.sort_by{|e|e.name[/_V(\\d+)$/,1].to_i};hs=im_es(tile).select{|e|e.respond_to?(:name)&&e.name.match?(/_H\\d+$/)}.sort_by{|e|e.name[/_H(\\d+)$/,1].to_i}
 uo=(vs[0].bounds.max.x+vs[1].bounds.min.x)/2;us=(vs[1].bounds.min.x+vs[1].bounds.max.x)/2;zo=(hs[0].bounds.max.z+hs[1].bounds.min.z)/2;zs=(hs[1].bounds.min.z+hs[1].bounds.max.z)/2
 [[uo,zo,false,'open_cell'],[us,zo,true,'vertical_wire'],[uo,zs,true,'horizontal_wire']].each do |u,z,expected,label|
  hits=im_hits(tile,Geom::Transformation.new,Geom::Point3d.new(u,-100.mm,z),Y_AXIS);out<<{path:path,label:label,expected_wire:expected,actual_face_intersections_mm:hits,passed:(!hits.empty?)==expected}
 end
end
{revision:13,geometry_writes:0,method:'Actual native face-plane intersections restricted to real mesh prototype and all nested wire transforms; no hiding/geometry changes; adjacent glass cannot occlude controls',controls:out,status:out.all?{|x|x[:passed]} ? 'PASS_ISOLATED_MESH_SAMPLES' : 'FAIL'}
'''.replace('GUID',json.dumps(i['model_guid'])).replace('PATHS',json.dumps(json.dumps(policy['allowed_paths'])))
f=_generated_script_dir()/('studio-r13-isolated-mesh-'+str(time.time_ns())+'.rb');f.write_text(body,encoding='utf8');(D/'r13-isolated-mesh-source.rb').write_text(body,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only actual mesh faces excluding unrelated occlusion'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v
(D/'r13-isolated-mesh-probe.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'status':v['status'],'pass':sum(x['passed'] for x in v['controls']),'total':len(v['controls'])}));assert v['status']=='PASS_ISOLATED_MESH_SAMPLES'
