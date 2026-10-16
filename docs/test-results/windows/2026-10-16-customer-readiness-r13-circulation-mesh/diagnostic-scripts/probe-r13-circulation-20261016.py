from pathlib import Path
import sys,json,time
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();policy=json.loads((P/'runtime/active_edit_scope.json').read_text(encoding='utf8'))
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==13
def cq_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def cq_child(g,n);aa=cq_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing/ambiguous '+n unless aa.length==1;aa.first;end
def cq_path(r,p);g=r;t=r.transformation;p.each{|n|g=cq_child(g,n);t=t*g.transformation};[g,t];end
def cq_bbox(g,t);b=Geom::BoundingBox.new;cq_es(g).grep(Sketchup::Edge).each{|e|e.vertices.each{|v|b.add(t*v.position)}};raise 'No direct vertices' if b.empty?;b;end
def cq_top_at(g,t,x,y)
 line=[t.inverse*Geom::Point3d.new(x.mm,y.mm,0),Geom::Vector3d.new(0,0,1).transform(t.inverse)]
 hits=cq_es(g).grep(Sketchup::Face).filter_map{|f|p=Geom.intersect_line_plane(line,f.plane);p && [Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(p)) ? (t*p).z.to_mm : nil};raise 'Missing solid support surface' if hits.empty?;hits.max
end
def cq_tile(g,t)
 return [g,t] if g.is_a?(Sketchup::ComponentInstance)&&g.definition.name.start_with?('KS_FINE_WHITE_MESH_')
 cq_es(g).each{|e|next unless e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance);v=cq_tile(e,t*e.transformation);return v if v};nil
end
head=[];contacts=[];treads=[]
[0,3600,7200].each do |base|
 (0...24).each do |n|
  path=['CIRCULATION_INTERNAL',"END_TREAD_#{base}_#{n}"];g,t=cq_path(r,path);b=cq_bbox(g,t);top=b.max.z.to_mm;y=(b.min.y.to_mm+b.max.y.to_mm)/2;treads<<{path:path,pid:g.persistent_id,bounds_mm:[b.min.to_a.map(&:to_mm),b.max.to_a.map(&:to_mm)]}
  [50750,51600,52450].each{|x|o=Geom::Point3d.new(x.mm,y.mm,(top+1).mm);hit=m.raytest([o,Z_AXIS],true);d=hit ? o.distance(hit[0]).to_mm+1 : nil;head<<{base:base,tread:n,x_mm:x,walking_z_mm:top,first_overhead_mm:d,names:hit ? hit[1].select{|e|e.respond_to?(:name)}.map(&:name) : [],passed:d.nil?||d>=2200}}
  [50500,52600].each_with_index do |x,j|
   seat,st=cq_path(r,['CIRCULATION_INTERNAL','END_STAIR_COMPLETION',"END_STAIR_Z#{base}_SUPPORT_HANDRAILS","TREAD_SEAT_#{base}_#{j}_#{n}"]);sb=cq_bbox(seat,st);str,tt=cq_path(r,['CIRCULATION_INTERNAL','END_STAIR_COMPLETION',"END_STAIR_Z#{base}_SUPPORT_HANDRAILS","STRINGER_#{base}_#{j}"]);sz=cq_top_at(str,tt,x+50,y);contact=(sb.max.z.to_mm-b.min.z.to_mm).abs<0.01&&sz>=sb.min.z.to_mm&&sz<=sb.max.z.to_mm
   contacts<<{base:base,tread:n,side:j,seat_top_mm:sb.max.z.to_mm,tread_bottom_mm:b.min.z.to_mm,stringer_top_at_seat_mm:sz,seat_bottom_mm:sb.min.z.to_mm,passed:contact}
  end
 end
end
decks=[]
[3600,7200,10800].each do |z|
 name="GALLERY_Z#{z}_SIDE3";g,t=cq_path(r,['CIRCULATION_EXTERNAL','GALLERIES',name]);[[51600,4000,false,'stair_slot'],[51601,8400,true,'landing_bar'],[53311,4000,true,'bypass_bar']].each do |x,y,expected,label|
  o=Geom::Point3d.new(x.mm,y.mm,(z+100).mm);hit=m.raytest([o,Geom::Vector3d.new(0,0,-1)],true);d=hit ? o.distance(hit[0]).to_mm : nil;target=!!(hit&&d<200&&hit[1].include?(g));decks<<{level:z,label:label,expected_deck:expected,actual_deck:target,first_distance_mm:d,names:hit ? hit[1].select{|e|e.respond_to?(:name)}.map(&:name) : [],passed:target==expected}
 end
end
mesh=[];paths=JSON.parse(PATHS)
paths.select{|p|p.last.start_with?('LONG_RAIL_','RAMP_','LANDING_L1_GUARD_')||p.last.end_with?('_SLOT_GUARD')}.each do |path|
 g,t=cq_path(r,path);tile,tt=cq_tile(g,t);raise 'No actual mesh tile' unless tile
 vs=cq_es(tile).select{|e|e.respond_to?(:name)&&e.name.match?(/_V\\d+$/)}.sort_by{|e|e.name[/_V(\\d+)$/,1].to_i};hs=cq_es(tile).select{|e|e.respond_to?(:name)&&e.name.match?(/_H\\d+$/)}.sort_by{|e|e.name[/_H(\\d+)$/,1].to_i};raise 'Insufficient actual mesh wires' unless vs.length>=2&&hs.length>=2
 uopen=(vs[0].bounds.max.x+vs[1].bounds.min.x)/2;usolid=(vs[1].bounds.min.x+vs[1].bounds.max.x)/2;zopen=(hs[0].bounds.max.z+hs[1].bounds.min.z)/2;zsolid=(hs[1].bounds.min.z+hs[1].bounds.max.z)/2
 [[uopen,zopen,false,'open_cell'],[usolid,zopen,true,'vertical_wire'],[uopen,zsolid,true,'horizontal_wire']].each do |u,z,expected,label|
  o=tt*Geom::Point3d.new(u,-100.mm,z);normal=Y_AXIS.transform(tt);normal.normalize!;hit=m.raytest([o,normal],true);d=hit ? o.distance(hit[0]).to_mm : nil;target=!!(hit&&d<200&&hit[1].include?(tile));pass=expected ? target : (!hit||d>=200);mesh<<{path:path,label:label,expected_wire:expected,first_distance_mm:d,actual_tile:target,names:hit ? hit[1].select{|e|e.respond_to?(:name)}.map(&:name) : [],passed:pass}
 end
end
pads=['LANDING_L2','LANDING_L3'].map do |n|
 g,t=cq_path(r,['CIRCULATION_EXTERNAL','LANDINGS',n]);parent=t*g.transformation.inverse;pts=(0..7).map{|j|parent*g.bounds.corner(j)};ys=pts.map{|p|p.y.to_mm};{name:n,world_y_mm:[ys.min,ys.max],passed:ys.min>=-4000.1&&ys.max<=24000.1}
end
{revision:13,root_pid:20606,geometry_writes:0,status:(head+contacts+decks+mesh+pads).all?{|x|x[:passed]} ? 'PASS_SAMPLED_CIRCULATION_AND_MESH' : 'FAIL',headroom_controls:head,tread_seat_stringer_contacts:contacts,remote_deck_controls:decks,mesh_controls:mesh,upper_platform_bounds:pads,existing_treads:treads,limitation:'Actual selected central stair headroom rays, support intersections, openings/grating bars, real mesh holes/wires and source outline. Not exhaustive full-route/body-volume or structural safety certification.'}
'''.replace('GUID',json.dumps(i['model_guid'])).replace('PATHS',json.dumps(json.dumps(policy['allowed_paths'])))
f=_generated_script_dir()/('studio-r13-circulation-probe-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');(D/'r13-circulation-probe-source.rb').write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only actual stair clearance/support and grating/mesh openings'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v
old=json.loads((D/'circulation-preparation/native-coordinates-before-r13.json').read_text(encoding='utf8'))['protected_existing_remote_treads'];lookup={tuple(x['path']):x for x in old};v['old_treads_identity_and_bounds_equal']=all(x['pid']==lookup[tuple(x['path'])]['pid'] and all(abs(a-b)<1e-6 for aa,bb in zip(x['bounds_mm'],lookup[tuple(x['path'])]['world_bounds_mm']) for a,b in zip(aa,bb)) for x in v['existing_treads']);assert v['old_treads_identity_and_bounds_equal'];(D/'r13-circulation-probe.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'status':v['status'],'tests':{k:{'passed':sum(x['passed'] for x in v[k]),'count':len(v[k])} for k in ['headroom_controls','tread_seat_stringer_contacts','remote_deck_controls','mesh_controls','upper_platform_bounds']},'min_sampled_headroom_mm':min(x['first_overhead_mm'] for x in v['headroom_controls'] if x['first_overhead_mm'] is not None),'old72treads_unchanged':True}))
