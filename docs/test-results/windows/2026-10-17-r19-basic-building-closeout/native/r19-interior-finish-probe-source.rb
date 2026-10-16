INF_FINISH_TARGETS=[[["FLOORS", "L0"], 76291, [76310]], [["FLOORS", "L1"], 76319, [76530]], [["FLOORS", "L2_PARTIAL_SOUTH"], 76635, [76645, 76654]], [["FLOORS", "L2_PARTIAL_EAST"], 76663, [76673, 76874]], [["FLOORS", "L3"], 76979, [76989]], [["ROOF_TIMBER", "CURVED_SHELL"], 77873, []], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_0"], 75680, [75702]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_1"], 75712, [75734]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_2"], 75744, [75766]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_3"], 75776, [75798]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_4"], 75808, [75830]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_5"], 75840, [75862]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_0"], 75872, [75894]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_1"], 75904, [75926]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_2"], 75936, [75958]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_3"], 75968, [75990]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_4"], 76000, [76022]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_5"], 76032, [76054]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_0"], 76064, [76086]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_1"], 76096, [76118]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_2"], 76128, [76150]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_3"], 76160, [76182]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_4"], 76192, [76214]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_5"], 76224, [76246]]]
INF_SOFT_EDGE_IDS=[78525, 78528, 78530, 78532, 78534, 78536, 78538, 78540, 78542, 78544, 78546, 78548, 78550, 78552, 78554, 78556, 78558, 78560, 78562, 78564, 78566, 78568, 78570, 78572, 78574, 78576, 78578, 78580, 78582, 78584, 78586, 78588, 78590, 78592, 78594, 78596, 78598, 78600, 78602, 78604, 78606, 78608, 78610, 78612, 78614, 78616, 78618, 78620, 78622, 78624, 78626, 78628, 78630, 78632, 78634, 78636, 78638, 78640, 78642, 78644, 78646, 78648, 78650, 78652, 78654, 78656, 78658, 78660, 78662, 78664, 78666, 78668, 78670, 78672, 78674, 78676, 78678, 78680, 78682, 78688, 78690, 78692, 78694, 78696, 78698, 78700, 78702, 78704, 78706, 78708, 78710, 78712, 78714, 78716, 78718, 78720, 78722, 78724, 78726, 78728, 78730, 78732, 78734, 78736, 78738, 78740, 78742, 78744, 78746, 78748, 78750, 78752, 78754, 78756, 78758, 78760, 78762, 78764, 78766, 78768, 78770, 78772, 78774, 78776, 78778, 78780, 78782, 78784, 78786, 78788, 78790, 78792, 78794, 78796, 78798, 78800, 78802, 78804, 78806, 78808, 78810, 78812, 78814, 78816, 78818, 78820, 78822, 78824, 78826, 78828, 78830, 78832, 78834, 78836, 78838, 78840, 78842, 78844]
INF_V_MEMBERS=[[2500, 150, 9850, 5000, 10330, 10050, 35], [2500, 10150, 19850, 15000, 10330, 10050, 35], [7500, 150, 9850, 5000, 10330, 10050, 35], [7500, 10150, 19850, 15000, 10330, 10050, 35], [17500, 150, 9850, 5000, 10330, 10050, 35], [17500, 10150, 19850, 15000, 10330, 10050, 35], [27500, 150, 9850, 5000, 10330, 10050, 35], [27500, 10150, 19850, 15000, 10330, 10050, 35], [32500, 150, 9850, 5000, 10330, 10050, 35], [32500, 10150, 19850, 15000, 10330, 10050, 35], [37500, 10150, 19850, 15000, 10330, 10050, 35], [42500, 150, 9850, 5000, 10330, 10050, 35], [42500, 10150, 19850, 15000, 10330, 10050, 35], [47500, 150, 9850, 5000, 10330, 10050, 35], [47500, 10150, 19850, 15000, 10330, 10050, 35]]
# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise '"884fd0ee-4b8b-49a2-ac14-5cff4d77166d"' unless m.guid=="884fd0ee-4b8b-49a2-ac14-5cff4d77166d"
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==19
def fp_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def fp_child(g,n);v=fp_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing '+n unless v.size==1;v.first;end
def fp_path(r,p);g=r;t=r.transformation;p.each{|n|g=fp_child(g,n);t=t*g.transformation};[g,t];end
def fp_contains(g,t,p)
 q=t.inverse*Geom::Point3d.new(*p.map(&:mm));fs=fp_es(g).grep(Sketchup::Face)
 !fs.empty? && fs.all?{|f|f.normal.dot(q-f.vertices.first.position)<=0.00001}
end
def fp_face(g,t,p)
 q=t.inverse*Geom::Point3d.new(*p.map(&:mm));fp_es(g).grep(Sketchup::Face).any?{|f|[Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(q))}
end
def fp_slab_inside(g,t,p)
 inv=t.inverse;line=[inv*Geom::Point3d.new(p[0].mm,p[1].mm,0),Z_AXIS.transform(inv)]
 zs=fp_es(g).grep(Sketchup::Face).filter_map do |f|
  q=Geom.intersect_line_plane(line,f.plane)
  q&&[Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(q)) ? (t*q).z.to_mm : nil
 end
 {actual_face_intersections_mm:zs,passed:zs.length>=2&&p[2]>=zs.min-0.01&&p[2]<=zs.max+0.01}
end
def fp_polar(rad,ang,z);[37000+rad*Math.cos(ang),6500+rad*Math.sin(ang),z];end
def fp_names(hit);hit ? hit[1].select{|x|x.respond_to?(:name)}.map(&:name) : [];end
cores=[];contacts=[];landings=[];head=[]
3.times do |k|
 stair,t=fp_path(r,['CIRCULATION_INTERNAL',"SPIRAL_L#{k}_L#{k+1}"]);core=fp_child(stair,"S#{k}_CONTINUOUS_CORE");ct=t*core.transformation;collar=fp_child(stair,"S#{k}_CORE_BASE_COLLAR");ft=t*collar.transformation;base=k*3600.0
 [ [core,ct,150],[collar,ft,225] ].each do |g,gt,want|
  points=fp_es(g).grep(Sketchup::Edge).flat_map{|e|e.vertices.map{|v|gt*v.position}};rr=points.map{|p|Math.hypot(p.x.to_mm-37000,p.y.to_mm-6500)}
  cores<<{path:g.name,actual_radius_min_mm:rr.min,actual_radius_max_mm:rr.max,expected_mm:want,passed:rr.all?{|d|(d-want).abs<0.01}}
 end
 24.times do |n|
  old=fp_child(stair,"S#{k}_RADIAL_SUPPORT_#{n}");ot=t*old.transformation;o=ot*ORIGIN;ang=Math.atan2(o.y.to_mm-6500,o.x.to_mm-37000);z=o.z.to_mm;top=base+(n+1)*150.0;tread=fp_child(stair,"S#{k}_TREAD_#{n}");tt=t*tread.transformation;newg=fp_child(core,"IF_S#{k}_TREAD_ROOT_#{n}");nt=ct*newg.transformation
  points=[['shaft',fp_polar(147,ang,z),core,ct],['retained radial support',fp_polar(380,ang,z),old,ot],['retained tread underside',fp_polar(380,ang,top-100),tread,tt]]
  points.each do |label,p,g,gt|
   actual=label=='retained tread underside' ? fp_face(g,gt,p) : fp_contains(g,gt,p)
   contacts<<{spiral:k,tread:n,contact:label,actual_point_mm:p,passed:actual&&fp_contains(newg,nt,p)}
  end
  [650,1150,1600].each do |rad|
   p=fp_polar(rad,ang,top+1);o=Geom::Point3d.new(*p.map(&:mm));hit=m.raytest([o,Z_AXIS],true);d=hit ? hit[0].z.to_mm-top : nil;head<<{spiral:k,tread:n,radius_mm:rad,headroom_mm:d,hit_names:fp_names(hit),passed:d.nil?||d>=2100}
  end
 end
 landing=fp_child(stair,"S#{k}_TOP_LANDING");lt=t*landing.transformation
 2.times do |n|
  old=fp_child(stair,"S#{k}_LANDING_SUPPORT_#{n}");ot=t*old.transformation;o=ot*ORIGIN;ang=Math.atan2(o.y.to_mm-6500,o.x.to_mm-37000);g=fp_child(core,"IF_S#{k}_LANDING_ROOT_#{n}");gt=ct*g.transformation
  [['shaft',fp_polar(147,ang,base+3467.5),core,ct],['retained landing support',fp_polar(410,ang,base+3460),old,ot],['retained plate underside',fp_polar(410,ang,base+3500),landing,lt]].each do |label,p,x,xt|
   actual=label=='retained plate underside' ? fp_face(x,xt,p) : fp_contains(x,xt,p)
   landings<<{spiral:k,landing_support:n,contact:label,point_mm:p,passed:actual&&fp_contains(g,gt,p)}
  end
 end
end
vgroup,vt=fp_path(r,['INTERIOR','CEILING_TENSION_MEMBERS']);structure,st=fp_path(r,['STRUCTURE_EXISTING']);vrows=[]
groups=fp_es(vgroup).select{|g|g.respond_to?(:name)&&g.name.match?(/^IF_V_BAY_\d+$/)}
groups.each do |g|
 gt=vt*g.transformation;left=fp_child(g,g.name.sub('IF_V_BAY_','IF_V')+'_LEFT');right=fp_child(g,g.name.sub('IF_V_BAY_','IF_V')+'_RIGHT');lt=gt*left.transformation;rt=gt*right.transformation;a=lt*ORIGIN;b=rt*ORIGIN;c=rt*Geom::Point3d.new(0,0,fp_es(right).grep(Sketchup::Edge).flat_map{|e|e.vertices.map{|v|v.position.z}}.max)
 endpoints=[a,c].map do |p|
  bp=[p.x.to_mm,p.y.to_mm,p.z.to_mm];beam=fp_child(structure,"LONG_BEAM_Z10800_Y#{(bp[1]/10000.0).round}");fp_contains(beam,st*beam.transformation,bp)
 end
 hanger=fp_child(g,g.name.sub('IF_V_BAY_','IF_V')+'_CENTRE_HANGER');ht=gt*hanger.transformation;tip=ht*Geom::Point3d.new(0,0,fp_es(hanger).grep(Sketchup::Edge).flat_map{|e|e.vertices.map{|v|v.position.z}}.max);floor,ft=fp_path(r,['FLOORS','L3']);floorproof=fp_slab_inside(floor,ft,[tip.x.to_mm,tip.y.to_mm,tip.z.to_mm]);floorinside=floorproof[:passed]
 q=[b.x.to_mm,b.y.to_mm,b.z.to_mm];vrows<<{name:g.name,beam_end_contacts:endpoints,center_join:fp_contains(left,lt,q)&&fp_contains(right,rt,q)&&fp_contains(hanger,ht,q),hanger_inside_existing_slab:floorinside,slab_intersection_proof:floorproof,hanger_tip_mm:[tip.x.to_mm,tip.y.to_mm,tip.z.to_mm],midpoint_mm:q,min_clear_above_7200_floor_mm:b.z.to_mm-17.5-7200,passed:endpoints.all?&&floorinside&&fp_contains(left,lt,q)&&fp_contains(right,rt,q)&&fp_contains(hanger,ht,q)}
end
shell,rt=fp_path(r,['ROOF_TIMBER','CURVED_SHELL']);seams=INF_SOFT_EDGE_IDS.map{|id|e=fp_es(shell).grep(Sketchup::Edge).find{|x|x.persistent_id==id};{pid:id,passed:!!(e&&e.soft?&&e.smooth?&&!e.hidden?)}}
materials=INF_FINISH_TARGETS.flat_map do |path,pid,ids|
 g,gt=fp_path(r,path);ids.map do |id|
  f=fp_es(g).grep(Sketchup::Face).find{|x|x.persistent_id==id};want=path.first=='INTERIOR' ? [244,242,233] : (f.normal.z<0 ? [233,216,183] : [234,233,225]);front=f.material ? f.material.color.to_a.take(3) : nil;back=f.back_material ? f.back_material.color.to_a.take(3) : nil;{path:path,face_pid:id,front:front,back:back,expected:want,passed:front==want&&back==want}
 end
end
all=cores+contacts+landings+head+vrows+seams+materials
{revision:19,root_pid:20606,geometry_writes:0,status:all.all?{|x|x[:passed]}&&groups.length==15 ? 'PASS_SELECTED_NATIVE_FINISH_CONTROLS' : 'FAIL',core_collar_radii:cores,tread_root_contacts:contacts,landing_root_contacts:landings,headroom:head,ceiling_v_members:vrows,soft_seams:seams,finish_faces:materials,display_settings:Hash[['Dark','Light','UseSunForAllShading','DisplayShadows'].map{|k|[k,m.shadow_info[k]]}],limitation:'Actual selected solid contacts/rays/primitive materials and soft flags; not full body-volume route, structure/code or exact photographed dimensions. Full protected graph and Surface proof separate.'}
