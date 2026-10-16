# ARCHFLOW_GENERATED_SCRIPT
load "E:/K AI 产品建模网站/app/adopted_sketchup_helpers.rb"
m=Sketchup.active_model;raise '"d994f5b5-7aa1-43cd-8a0f-f2218fef4347"' unless m.guid=="d994f5b5-7aa1-43cd-8a0f-f2218fef4347"
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==18
paths=JSON.parse("[[\"FLOORS\", \"L0\"], [\"FLOORS\", \"L1\"], [\"FLOORS\", \"L2_PARTIAL_SOUTH\"], [\"FLOORS\", \"L2_PARTIAL_EAST\"], [\"FLOORS\", \"L3\"], [\"ROOF_TIMBER\", \"CURVED_SHELL\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_0\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_1\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_2\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_3\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_4\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_5\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_0\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_1\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_2\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_3\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_4\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_5\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_0\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_1\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_2\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_3\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_4\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_5\"]]");geo=JSON.parse("[[\"CIRCULATION_INTERNAL\", \"SPIRAL_L0_L1\", \"S0_CONTINUOUS_CORE\"], [\"CIRCULATION_INTERNAL\", \"SPIRAL_L0_L1\", \"S0_CORE_BASE_COLLAR\"], [\"CIRCULATION_INTERNAL\", \"SPIRAL_L1_L2\", \"S1_CONTINUOUS_CORE\"], [\"CIRCULATION_INTERNAL\", \"SPIRAL_L1_L2\", \"S1_CORE_BASE_COLLAR\"], [\"CIRCULATION_INTERNAL\", \"SPIRAL_L2_L3\", \"S2_CONTINUOUS_CORE\"], [\"CIRCULATION_INTERNAL\", \"SPIRAL_L2_L3\", \"S2_CORE_BASE_COLLAR\"]]");faces=[];seams=[];rows=[]
paths.each do |p|
 g=KStudioProfessionalHelpers.named_owned_group(r,p,true);direct=g.entities.grep(Sketchup::Face)
 allowed=if p[0]=='FLOORS'
  direct.select{|f|p[1]=='L3' ? f.normal.z< -0.99 : (f.normal.z>0.99||p[1].start_with?('L2_')&&f.normal.z< -0.99)}
 elsif p[0]=='INTERIOR'
  direct.select{|f|f.normal.z>0.99}
 else
  []
 end
 faces+=allowed.map(&:persistent_id)
 if p[0]=='ROOF_TIMBER'
  seams=g.entities.grep(Sketchup::Edge).select{|e|e.faces.length==2&&e.faces[0].normal.angle_between(e.faces[1].normal)<5*Math::PI/180}.map(&:persistent_id)
 end
 rows<<{path:p,pid:g.persistent_id,allowed_material_faces:allowed.map{|f|{pid:f.persistent_id,normal:f.normal.to_a,actual_z_mm:f.vertices.map{|v|v.position.z.to_mm}.minmax}},direct_faces:direct.length}
end
raise 'Surface masks unexpected' unless faces.length==25&&faces.uniq.length==25&&seams.length==158
geo_rows=geo.map{|p|g=KStudioProfessionalHelpers.named_owned_group(r,p,true);{path:p,pid:g.persistent_id,actual_bounds_mm:[g.bounds.min.to_a.map(&:to_mm),g.bounds.max.to_a.map(&:to_mm)]}}
interior=KStudioProfessionalHelpers.named_owned_group(r,['INTERIOR']);raise 'New leaf exists' if interior.entities.any?{|e|e.respond_to?(:name)&&e.name=='CEILING_TENSION_MEMBERS'}
slab=KStudioProfessionalHelpers.named_owned_group(r,['FLOORS','L3']);face=slab.entities.grep(Sketchup::Face).find{|f|f.normal.z< -0.99};holes=face.loops.reject(&:outer?).map{|l|l.vertices.map{|v|v.position.to_a.map(&:to_mm)}}
members=[];omitted=[]
10.times do |n|
 x=2500+n*5000
 [[150,9850],[10150,19850]].each do |ya,yb|
  intersects=holes.any? do |poly|
   [x-20,x,x+20].any? do |xx|
    ys=[];poly.each_with_index do |p,j|
     q=poly[(j+1)%poly.length];next if (q[0]-p[0]).abs<0.00001
     tt=(xx-p[0])/(q[0]-p[0]);ys<<p[1]+tt*(q[1]-p[1]) if tt>=0&&tt<=1
    end
    ys.length>=2&&ys.min-20<yb&&ys.max+20>ya
   end
  end
  row={x_mm:x,y0_mm:ya,y1_mm:yb,middle_y_mm:(ya+yb)/2.0,attach_z_mm:10330,middle_z_mm:10050,width_mm:35}
  (intersects ? omitted : members)<<row
 end
end
raise 'Expected source-consistent hole-safe V layout' unless members.length==15&&omitted.length==5
frame=KStudioProfessionalHelpers.named_owned_group(r,['STRUCTURE_EXISTING']);beam_bases=(0..2).map{|n|g=frame.entities.find{|e|e.respond_to?(:name)&&e.name=="LONG_BEAM_Z10800_Y#{n}"};raise 'Actual beam missing' unless g;g.bounds.min.z.to_mm};raise 'Actual beam supports differ' unless beam_bases.all?{|z|(z-10320).abs<0.1}
cir=KStudioProfessionalHelpers.named_owned_group(r,['CIRCULATION_INTERNAL']);gaps=3.times.flat_map do |k|
 st=cir.entities.find{|g|g.respond_to?(:name)&&g.name=="SPIRAL_L#{k}_L#{k+1}"};landing=st.entities.find{|g|g.respond_to?(:name)&&g.name=="S#{k}_TOP_LANDING"}
 2.times.map{|j|sp=st.entities.find{|g|g.respond_to?(:name)&&g.name=="S#{k}_LANDING_SUPPORT_#{j}"};{spiral:k,support:j,actual_support_top_mm:sp.bounds.max.z.to_mm,actual_landing_bottom_mm:landing.bounds.min.z.to_mm,gap_mm:landing.bounds.min.z.to_mm-sp.bounds.max.z.to_mm}}
end
{geometry_writes:0,revision:18,root_pid:20606,finish_targets:rows,geometry_targets:geo_rows,face_material_pids:faces,soft_smooth_edge_pids:seams,actual_approved_v_members:members,omitted_v_members_above_actual_holes:omitted,actual_old_upper_beam_soffits_mm:beam_bases,actual_old_landing_support_gaps:gaps,new_leaf_absent:true,display_diagnosis:'Native neutralDark80/Light15/UseSunForAllShadingtrue controls reveal existing pale roof/L3; original settings restored. Geometry/material unchanged in tests. Not actual source-quality PASS.'}
