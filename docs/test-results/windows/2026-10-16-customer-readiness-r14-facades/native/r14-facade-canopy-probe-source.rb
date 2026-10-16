# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise '"9696d964-83e0-43a8-b095-e382e53daa2c"' unless m.guid=="9696d964-83e0-43a8-b095-e382e53daa2c"
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==14
def fp_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def fp_child(g,n);v=fp_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing '+n unless v.size==1;v.first;end
def fp_walk(g,t,path,out)
 mat=g.material
 out<<[g,t,path] if g.get_attribute('KStudio','clear_portal_mm') || g.name=='EDITABLE_COVER'
 fp_es(g).each{|e|fp_walk(e,t*e.transformation,path+[e.name],out) if e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)}
end
def fp_names(h);h ? h[1].select{|e|e.respond_to?(:name)}.map(&:name) : [];end
env=fp_child(r,'ENVELOPE_OUTER');inner=fp_child(env,'INNER_GLAZING');room=fp_child(fp_child(r,'INTERIOR'),'ROOM_FRONT_COMPLETION');can=fp_child(env,'BUFFER_CANOPIES');items=[]
[[inner,r.transformation*env.transformation*inner.transformation,['ENVELOPE_OUTER','INNER_GLAZING']],[room,r.transformation*fp_child(r,'INTERIOR').transformation*room.transformation,['INTERIOR','ROOM_FRONT_COMPLETION']],[can,r.transformation*env.transformation*can.transformation,['ENVELOPE_OUTER','BUFFER_CANOPIES']]].each{|g,t,p|fp_walk(g,t,p,items)}
apertures=[];floor=[];panes=[]
items.each do |g,t,path|
 portal=g.get_attribute('KStudio','clear_portal_mm')
 if portal
  aa,bb,y,z,top=portal;xc=(aa+bb)/2
  [900,1900].each do |h|
   [-1,1].each do |sign|
    o=Geom::Point3d.new(xc.mm,(y-sign*50).mm,(z+h).mm);hit=m.raytest([o,Geom::Vector3d.new(0,sign,0)],true);dist=hit ? o.distance(hit[0]).to_mm : nil;apertures<<{path:path,height_mm:h,sign:sign,first_distance_mm:dist,names:fp_names(hit),passed:dist.nil?||dist>100.01}
   end
  end
  side=path.find{|x|x.start_with?('INNER_GLASS_')};inside=side ? (side.split('_')[-2]=='0' ? 1 : -1) : 1;ys=side ? [y-inside*500,y+inside*100,y+inside*1000] : [11600,y-400,y+100]
  ys.each do |py|
   o=Geom::Point3d.new(xc.mm,py.mm,(z+50).mm);hit=m.raytest([o,Geom::Vector3d.new(0,0,-1)],true);hz=hit ? hit[0].z.to_mm : nil;floor<<{path:path,xy_mm:[xc,py],level_mm:z,first_z_mm:hz,names:fp_names(hit),passed:!!(hit&&(hz-z).abs<0.1&&fp_names(hit).include?('FLOORS'))}
  end
 else
  faces=fp_es(g).grep(Sketchup::Face).select{|f|f.normal.z.abs>0.5};raise 'Missing actual cover face' if faces.empty?
  f=faces.max_by{|v|v.vertices.sum{|q|(t*q.position).z}/v.vertices.length};points=f.vertices.map{|v|t*v.position};mid=Geom::Point3d.new(*(0..2).map{|k|points.sum{|p|p[k]}/points.length});mat=f.material||g.material;raise 'Cover material missing' unless mat
  hit=m.raytest([mid+Geom::Vector3d.new(0,0,10.mm),Geom::Vector3d.new(0,0,-1)],true)
  below=mid-Geom::Vector3d.new(0,0,16.mm);back=m.raytest([below,Geom::Vector3d.new(0,0,-1)],true);dist=back ? below.distance(back[0]).to_mm : nil
  panes<<{path:path,effective_material:mat.name,alpha:mat.alpha,actual_panel_first_hit:!!(hit&&hit[1].include?(g)),backing_first_distance_mm:dist,backing_names:fp_names(back),passed:mat.alpha<1&&hit&&hit[1].include?(g)&&(dist.nil?||dist>100)}
 end
end
contacts=[];bounds=[]
(0..3).each do |k|
 g=fp_child(can,"CANOPY_#{k}");content=fp_child(g,"CANOPY_#{k}_CONTENT");lf=fp_child(content,"CANOPY_#{k}_LIGHT_FRAME");le=fp_es(lf);ledger=fp_child(lf,'INNER_EDGE_LEDGER');outer=fp_child(lf,'OUTER_EDGE_BEAM')
 le.select{|e|e.respond_to?(:name)&&e.name.start_with?('RAFTER_')}.each do |rf|
  [ledger,outer].each do |support|
   overlaps=(0..2).map{|j|[rf.bounds.max[j],support.bounds.max[j]].min-[rf.bounds.min[j],support.bounds.min[j]].max};contacts<<{canopy:k,rafter:rf.name,support:support.name,overlap_mm:overlaps.map(&:to_mm),passed:overlaps.all?{|v|v>=-0.01.mm}}
  end
 end
 b=g.bounds;bounds<<{canopy:k,min_mm:b.min.to_a.map(&:to_mm),max_mm:b.max.to_a.map(&:to_mm)}
end
{revision:14,geometry_writes:0,actual_portals:items.count{|g,t,p|g.get_attribute('KStudio','clear_portal_mm')},aperture_controls:apertures,floor_controls:floor,transparent_cover_controls:panes,rafter_support_contacts:contacts,canopy_bounds:bounds,status:(apertures+floor+panes+contacts).all?{|x|x[:passed]} ? 'PASS_SELECTED_NATIVE_CONTROLS' : 'FAIL',limitations:'Actual selected centre rays/real floor first hits/cover material and no-backing samples; support tests for actual axis-aligned box members. Not full human body routes, source-exact door count or structural/code certification.'}
