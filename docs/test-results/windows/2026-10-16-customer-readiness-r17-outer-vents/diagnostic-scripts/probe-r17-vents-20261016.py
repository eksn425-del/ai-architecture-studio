from pathlib import Path
import json,sys,time
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
D=R/'runtime/exterior-completion-20261016';a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity()
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==17
def vo_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def vo_find(g,n);a=vo_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing/ambiguous '+n unless a.length==1;a.first;end
def vo_names(h);h ? h[1].select{|e|e.respond_to?(:name)}.map(&:name) : [];end
def vo_inside(g,t,world)
 p=t.inverse*world;zs=vo_es(g).grep(Sketchup::Face).filter_map{|f|q=Geom.intersect_line_plane([p,Z_AXIS],f.plane);q&&[Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(q)) ? q.z : nil};zs.length>=2&&p.z>=zs.min-0.1.mm&&p.z<=zs.max+0.1.mm
end
def vo_ends(g,t)
 pts=vo_es(g).grep(Sketchup::Edge).flat_map{|e|e.vertices.map(&:position)};raise 'Empty bar' if pts.empty?;lo=pts.map(&:z).min;hi=pts.map(&:z).max;[t*Geom::Point3d.new(0,0,lo),t*Geom::Point3d.new(0,0,hi)]
end
env=vo_find(r,'ENVELOPE_OUTER');et=r.transformation*env.transformation;vents=vo_find(env,'OUTER_EAVE_VENTS');vt=et*vents.transformation
openings=[];solids=[];contacts=[];panes=[];loops=[]
['NORTH','SOUTH'].each do |side|
 (1..19).each do |n|
  bay=vo_find(env,"#{side}_BAY_#{n}");bt=et*bay.transformation;gl=vo_find(bay,'GLASS');gt=bt*gl.transformation
  loops<<{side:side,bay:n,physical_pid:gl.persistent_id,actual_faces:vo_es(gl).grep(Sketchup::Face).length,actual_inner_loops:vo_es(gl).grep(Sketchup::Face).sum{|f|f.loops.count{|l|!l.outer?}}}
  sg=side=='NORTH' ? 1 : -1;y=sg==1 ? 24000 : -4000
  [750,1450,2150].product([12700,13200]).each do |x,z|
   p=Geom::Point3d.new((-4000+n*2900+x).mm,(y+sg*5).mm,z.mm);h=m.raytest([p,Geom::Vector3d.new(0,-sg,0)],true);d=h ? p.distance(h[0]).to_mm : nil;openings<<{side:side,bay:n,local_sample_mm:[x,z],first_distance_mm:d,names:vo_names(h),passed:d.nil?||d>50}
  end
  [[1450,12100],[1450,12500],[1450,13460],[40,13000]].each do |x,z|
   p=Geom::Point3d.new((-4000+n*2900+x).mm,(y+sg*5).mm,z.mm);h=m.raytest([p,Geom::Vector3d.new(0,-sg,0)],true);d=h ? p.distance(h[0]).to_mm : nil;solids<<{side:side,bay:n,local_sample_mm:[x,z],first_distance_mm:d,names:vo_names(h),passed:!!(d&&(d-5).abs<0.2&&vo_names(h).include?('GLASS'))}
  end
  v=vo_find(vents,"#{side}_VENT_BAY_#{n}");t=vt*v.transformation;header=vo_find(v,'HINGE_HEADER');ht=t*header.transformation
  2.times do |j|
   clip=vo_find(v,"ROOF_FRAME_CLIP_#{j}");ct=t*clip.transformation;start,finish=vo_ends(clip,ct)
   frame=['MULLION','TRANSOM_13500'].any?{|nn|g=vo_find(bay,nn);vo_inside(g,bt*g.transformation,start)}
   contacts<<{side:side,bay:n,type:'roof_clip',index:j,start_mm:start.to_a.map(&:to_mm),end_mm:finish.to_a.map(&:to_mm),start_in_original_frame:frame,end_in_header:vo_inside(header,ht,finish),passed:frame&&vo_inside(header,ht,finish)}
   stay=vo_find(v,"STAY_#{j}");st=t*stay.transformation;start,finish=vo_ends(stay,st);mul=vo_find(bay,'MULLION');tr=vo_find(bay,'TRANSOM_13500')
   # Right bay edge is the next original mullion. Check actual neighboring bay
   # at x+2900 instead of inventing an absent right mullion in this prototype.
   candidates=vo_es(env).select{|e|e.respond_to?(:name)&&e.name.start_with?(side+'_BAY_')}.map{|b|[vo_find(b,'MULLION'),et*b.transformation]}
   candidates+=vo_es(env).select{|e|e.respond_to?(:name)&&e.name.start_with?('SHORT_MULLION_')}.map{|g|[g,et]}
   frame=candidates.any?{|g,bb|vo_inside(g,bb*g.transformation,start)}
   sash=vo_find(v,j==0 ? 'SASH_EDGE_3' : 'SASH_EDGE_1');end_ok=vo_inside(sash,t*sash.transformation,finish)
   contacts<<{side:side,bay:n,type:'stay',index:j,start_mm:start.to_a.map(&:to_mm),end_mm:finish.to_a.map(&:to_mm),start_in_original_frame:frame,end_in_sash:end_ok,passed:frame&&end_ok}
  end
  pane=vo_find(v,'TRANSPARENT_OUTWARD_DOWN_PANE');pt=t*pane.transformation;faces=vo_es(pane).grep(Sketchup::Face);ps=faces.flat_map{|f|f.vertices.map{|vv|pt*vv.position}};alpha=faces.map{|f|[f.material&&f.material.alpha,f.back_material&&f.back_material.alpha]}
  panes<<{side:side,bay:n,faces:faces.length,actual_z_extent_mm:ps.map{|p|p.z.to_mm}.minmax,actual_outward_extent_mm:ps.map{|p|sg*(p.y.to_mm-y)}.minmax,material_alpha_front_back:alpha,passed:faces.length==1&&alpha.all?{|a|a.all?{|v|v&&v>0&&v<1}}}
 end
end
{status:(openings+solids+contacts+panes).all?{|v|v[:passed]}&&loops.all?{|v|v[:actual_inner_loops]==1} ? 'PASS_SELECTED_NATIVE_VENT_CONTROLS' : 'FAIL',geometry_writes:0,revision:17,root_pid:20606,openings:openings,remaining_solid_glass:solids,frame_hinge_stay_contacts:contacts,translucent_panes:panes,actual_shared_leaf_topology:loops,actual_vent_component_count:vo_es(vents).grep(Sketchup::ComponentInstance).length,actual_vent_definition_count:vo_es(vents).grep(Sketchup::ComponentInstance).map(&:definition).uniq.length,limitation:'Actual finite open/backed rays and bar endpoint/real solid surface tests, not full swept person routes, load design or blanket source fidelity.'}
'''.replace('GUID',json.dumps(i['model_guid']))
f=_generated_script_dir()/('studio-vent-native-controls-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');(D/'r17-vent-probe-source.rb').write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only actual high vent openings glass backing and hinge/stay/frame contacts'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(D/'r17-vent-probe.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'status':v['status'],'controls':{k:{'passed':sum(x['passed'] for x in v[k]),'total':len(v[k])} for k in ['openings','remaining_solid_glass','frame_hinge_stay_contacts','translucent_panes']}},ensure_ascii=False))
