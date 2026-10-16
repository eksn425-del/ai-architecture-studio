from pathlib import Path
import sys,json,time,argparse
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
p=argparse.ArgumentParser();p.add_argument('--revision',type=int,required=True);z=p.parse_args();O=R/'runtime/exterior-completion-20261016/west-entry-recovery';a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity()
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'Wrong GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Wrong revision' unless r.get_attribute('sketchup_architect','revision')==REV
def es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def box(r,path)
 g=r;t=r.transformation
 path.each_with_index{|n,j|x=es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing/ambiguous '+n unless x.length==1;g=x.first;t*=g.transformation if j<path.length-1}
 pts=(0..7).map{|j|t*g.bounds.corner(j)}
 {pid:g.persistent_id,path:path,min_mm:(0..2).map{|k|pts.map{|v|v[k].to_mm}.min},max_mm:(0..2).map{|k|pts.map{|v|v[k].to_mm}.max}}
end
base=['ENVELOPE_OUTER','LOWER_END_WEST_ADDITION','LEVEL_7200_BAY_6'];leaves=['DOOR_LEFT_OPEN_90','DOOR_RIGHT_OPEN_90'].map{|n|box(r,base+[n])};guard=box(r,['CIRCULATION_EXTERNAL','GALLERIES','GALLERY_Z7200_SIDE2','GALLERY_Z7200_SIDE2_SLOT_GUARD']);deck=box(r,['CIRCULATION_EXTERNAL','GALLERIES','GALLERY_Z7200_SIDE2','GALLERY_Z7200_SIDE2_RETURN_STRIP'])
width=leaves.map{|v|v[:min_mm][0]}.min-guard[:max_mm][0];rays=[]
[-1250,-850,-450].each do |x|
 [7600,8300,9100].each do |h|
  origin=Geom::Point3d.new(x.mm,14500.mm,h.mm);hit=m.raytest([origin,Y_AXIS],true);dist=hit ? origin.distance(hit[0]).to_mm : nil;clear=!hit||dist>3500
  rays<<{x_mm:x,z_mm:h,start_y_mm:14500,test_length_mm:3500,first_hit_distance_mm:dist,first_hit_names:hit ? hit[1].select{|e|e.respond_to?(:name)}.map(&:name) : [],clear:clear}
 end
end
{revision:REV,root_pid:20606,geometry_writes:0,door_leaves:leaves,slot_guard:guard,return_deck:deck,narrowest_guard_to_leaf_width_mm:width,ray_controls:rays,clear_count:rays.count{|v|v[:clear]},blocked_count:rays.count{|v|!v[:clear]},status:width>=1500 && rays.all?{|v|v[:clear]} ? 'PASS_SAMPLED_RETURN_CLEARANCE' : 'OBSTRUCTED_OR_NARROW',limitation:'Nine actual selected side-approach rays and native widths, not full-building route certification.'}
'''.replace('GUID',json.dumps(i['model_guid'])).replace('REV',str(z.revision))
f=_generated_script_dir()/('studio-west-return-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only actual west L2 door-to-return approach geometry'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;dest=O/f'r{z.revision}-actual-return-clearance.json';assert not dest.exists();dest.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v[k] for k in ['revision','status','narrowest_guard_to_leaf_width_mm','clear_count','blocked_count']}))
