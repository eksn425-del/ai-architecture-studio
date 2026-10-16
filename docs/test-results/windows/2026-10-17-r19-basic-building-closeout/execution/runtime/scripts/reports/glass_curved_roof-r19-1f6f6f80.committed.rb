INF_FINISH_TARGETS=[[["FLOORS", "L0"], 76291, [76310]], [["FLOORS", "L1"], 76319, [76530]], [["FLOORS", "L2_PARTIAL_SOUTH"], 76635, [76645, 76654]], [["FLOORS", "L2_PARTIAL_EAST"], 76663, [76673, 76874]], [["FLOORS", "L3"], 76979, [76989]], [["ROOF_TIMBER", "CURVED_SHELL"], 77873, []], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_0"], 75680, [75702]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_1"], 75712, [75734]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_2"], 75744, [75766]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_3"], 75776, [75798]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_4"], 75808, [75830]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z0_5"], 75840, [75862]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_0"], 75872, [75894]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_1"], 75904, [75926]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_2"], 75936, [75958]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_3"], 75968, [75990]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_4"], 76000, [76022]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z3600_5"], 76032, [76054]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_0"], 76064, [76086]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_1"], 76096, [76118]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_2"], 76128, [76150]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_3"], 76160, [76182]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_4"], 76192, [76214]], [["INTERIOR", "FURNITURE_SIMPLIFIED", "TABLE_Z10800_5"], 76224, [76246]]]
INF_SOFT_EDGE_IDS=[78525, 78528, 78530, 78532, 78534, 78536, 78538, 78540, 78542, 78544, 78546, 78548, 78550, 78552, 78554, 78556, 78558, 78560, 78562, 78564, 78566, 78568, 78570, 78572, 78574, 78576, 78578, 78580, 78582, 78584, 78586, 78588, 78590, 78592, 78594, 78596, 78598, 78600, 78602, 78604, 78606, 78608, 78610, 78612, 78614, 78616, 78618, 78620, 78622, 78624, 78626, 78628, 78630, 78632, 78634, 78636, 78638, 78640, 78642, 78644, 78646, 78648, 78650, 78652, 78654, 78656, 78658, 78660, 78662, 78664, 78666, 78668, 78670, 78672, 78674, 78676, 78678, 78680, 78682, 78688, 78690, 78692, 78694, 78696, 78698, 78700, 78702, 78704, 78706, 78708, 78710, 78712, 78714, 78716, 78718, 78720, 78722, 78724, 78726, 78728, 78730, 78732, 78734, 78736, 78738, 78740, 78742, 78744, 78746, 78748, 78750, 78752, 78754, 78756, 78758, 78760, 78762, 78764, 78766, 78768, 78770, 78772, 78774, 78776, 78778, 78780, 78782, 78784, 78786, 78788, 78790, 78792, 78794, 78796, 78798, 78800, 78802, 78804, 78806, 78808, 78810, 78812, 78814, 78816, 78818, 78820, 78822, 78824, 78826, 78828, 78830, 78832, 78834, 78836, 78838, 78840, 78842, 78844]
INF_V_MEMBERS=[[2500, 150, 9850, 5000, 10330, 10050, 35], [2500, 10150, 19850, 15000, 10330, 10050, 35], [7500, 150, 9850, 5000, 10330, 10050, 35], [7500, 10150, 19850, 15000, 10330, 10050, 35], [17500, 150, 9850, 5000, 10330, 10050, 35], [17500, 10150, 19850, 15000, 10330, 10050, 35], [27500, 150, 9850, 5000, 10330, 10050, 35], [27500, 10150, 19850, 15000, 10330, 10050, 35], [32500, 150, 9850, 5000, 10330, 10050, 35], [32500, 10150, 19850, 15000, 10330, 10050, 35], [37500, 10150, 19850, 15000, 10330, 10050, 35], [42500, 150, 9850, 5000, 10330, 10050, 35], [42500, 10150, 19850, 15000, 10330, 10050, 35], [47500, 150, 9850, 5000, 10330, 10050, 35], [47500, 10150, 19850, 15000, 10330, 10050, 35]]
# Source04 visible slim spiral shaft, pale mineral floors/white tables,
# pale timber soffit between concrete beams and shallow V steel members.
# kstudio.custom_owned_ruby: SAIE wall/opening helpers do not fit helical
# support roots, slender V rods or constrained material/edge edits. ADAI off.
# Native approved parameters are inserted below; no runtime file access.

def inf_find(es,name)
  a=es.select{|e|(e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)) && e.name==name}
  raise "Missing/duplicate #{name}" unless a.length==1
  a.first
end
def inf_entities(g)
  g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities
end
def inf_path(root,path)
  path.inject(root){|g,n|inf_find(inf_entities(g),n)}
end
def inf_group(es,name)
  g=es.add_group;g.name=name;g.set_attribute('KStudio','semantic_id',name);g
end
def inf_bar(es,name,a,b,w,mat)
  g=inf_group(es,name);v=Geom::Vector3d.new(*(0..2).map{|i|(b[i]-a[i]).mm});len=v.length
  raise 'Zero member' if len<0.001
  q=w/2.0
  f=g.entities.add_face([[-q,-q,0],[q,-q,0],[q,q,0],[-q,q,0]].map{|p|p.map(&:mm)})
  f.reverse! if f.normal.z<0;f.pushpull(len);g.material=mat
  zz=v.normalize;ref=zz.parallel?(Z_AXIS) ? X_AXIS : Z_AXIS
  xx=ref.cross(zz).normalize;yy=zz.cross(xx).normalize
  g.transformation=Geom::Transformation.axes(Geom::Point3d.new(*a.map(&:mm)),xx,yy,zz)
  raise 'Non-solid member' unless g.manifold?
  g
end
def inf_polar(r,a,z)
  [37000+r*Math.cos(a),6500+r*Math.sin(a),z]
end
def inf_contains(g,p)
  q=g.transformation.inverse*Geom::Point3d.new(*p.map(&:mm))
  fs=inf_entities(g).grep(Sketchup::Face)
  raise 'No solid faces' if fs.empty?
  fs.all?{|f|f.normal.dot(q-f.vertices.first.position)<=0.00001}
end
def inf_face_contact(g,p)
  q=g.transformation.inverse*Geom::Point3d.new(*p.map(&:mm))
  inf_entities(g).grep(Sketchup::Face).any?{|f|[Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(q))}
end
def inf_shape(g)
  es=inf_entities(g)
  [g.persistent_id,g.transformation.to_a,
   es.grep(Sketchup::Edge).map{|e|[e.persistent_id,e.vertices.map{|v|[v.persistent_id,v.position.to_a]}]},
   es.grep(Sketchup::Face).map{|f|[f.persistent_id,f.normal.to_a,f.loops.map{|l|l.vertices.map{|v|v.persistent_id}}]}]
end
raise 'Wrong root' unless root.persistent_id==20606
steel=model.materials['KS_White_Steel'];raise 'Missing original steel' unless steel
cir=inf_path(root,['CIRCULATION_INTERNAL']);interior=inf_path(root,['INTERIOR'])
surface_groups=INF_FINISH_TARGETS.map{|p,pid,ids|g=inf_path(root,p);raise 'Wrong surface PID' unless g.persistent_id==pid;g}
surface_shapes=surface_groups.map{|g|inf_shape(g)}
shaft_ids=[1326020,1333697,1341030];collar_ids=[1326474,1334151,1341484]
contacts=0
3.times do |k|
  stair=inf_find(cir.entities,"SPIRAL_L#{k}_L#{k+1}")
  core=inf_find(stair.entities,"S#{k}_CONTINUOUS_CORE")
  collar=inf_find(stair.entities,"S#{k}_CORE_BASE_COLLAR")
  raise 'Core PID/transform mismatch' unless core.persistent_id==shaft_ids[k] && collar.persistent_id==collar_ids[k] && core.transformation.identity? && collar.transformation.identity?
  raise 'Shared target' unless [core,collar].all?{|g|g.definition.instances.length==1}
  base=k*3600.0
  clear_owned_contents.call(['CIRCULATION_INTERNAL',stair.name,core.name])
  f=core.entities.add_face(core.entities.add_circle([37000.mm,6500.mm,base.mm],Z_AXIS,150.mm,64))
  f.reverse! if f.normal.z<0;f.pushpull(3600.mm);core.material=steel
  # Every retained support is queried directly; new roots overlap its actual
  # start and meet the unchanged underside of its corresponding tread.
  24.times do |i|
    a=(45+330.0*(i+0.5)/24)*Math::PI/180
    h=base+(i+1)*150.0
    old=inf_find(stair.entities,"S#{k}_RADIAL_SUPPORT_#{i}")
    tread=inf_find(stair.entities,"S#{k}_TREAD_#{i}")
    origin=old.transformation*ORIGIN
    z=origin.z.to_mm
    raise 'Unexpected original support' unless (z-(h-125)).abs<0.01
    bracket=inf_bar(core.entities,"IF_S#{k}_TREAD_ROOT_#{i}",inf_polar(145,a,z),inf_polar(405,a,z),50,steel)
    raise 'Root misses shaft' unless inf_contains(core,inf_polar(147,a,z)) && inf_contains(bracket,inf_polar(147,a,z))
    raise 'Root misses old support' unless inf_contains(old,inf_polar(380,a,z)) && inf_contains(bracket,inf_polar(380,a,z))
    raise 'Root misses tread underside' unless inf_face_contact(tread,inf_polar(380,a,h-100)) && inf_contains(bracket,inf_polar(380,a,h-100))
    contacts+=3
  end
  landing=inf_find(stair.entities,"S#{k}_TOP_LANDING")
  [Math::PI/9,Math::PI/4].each_with_index do |a,j|
    old=inf_find(stair.entities,"S#{k}_LANDING_SUPPORT_#{j}")
    old_z=(old.transformation*ORIGIN).z.to_mm
    z=base+3467.5
    raise 'Unexpected landing gap' unless (old_z-(base+3450)).abs<0.01
    bracket=inf_bar(core.entities,"IF_S#{k}_LANDING_ROOT_#{j}",inf_polar(145,a,z),inf_polar(425,a,z),65,steel)
    raise 'Landing root misses core' unless inf_contains(core,inf_polar(147,a,z)) && inf_contains(bracket,inf_polar(147,a,z))
    raise 'Landing root misses old support' unless inf_contains(old,inf_polar(410,a,base+3460)) && inf_contains(bracket,inf_polar(410,a,base+3460))
    raise 'Landing root misses plate' unless inf_face_contact(landing,inf_polar(410,a,base+3500)) && inf_contains(bracket,inf_polar(410,a,base+3500))
    contacts+=3
  end
  if k==0
    bottom=inf_find(stair.entities,'S0_BOTTOM_LANDING')
    a=Math::PI/9
    inf_bar(core.entities,'IF_S0_BOTTOM_LANDING_ROOT',inf_polar(145,a,base),inf_polar(425,a,base),65,steel)
    raise 'Bottom plate contact failed' unless inf_face_contact(bottom,inf_polar(400,a,base))
  end
  clear_owned_contents.call(['CIRCULATION_INTERNAL',stair.name,collar.name])
  f=collar.entities.add_face(collar.entities.add_circle([37000.mm,6500.mm,base.mm],Z_AXIS,225.mm,64))
  f.reverse! if f.normal.z<0;f.pushpull(35.mm);collar.material=steel
end
floor_mat=model.materials.add('IF_Pale_Mineral_R19');floor_mat.color=Sketchup::Color.new(234,233,225)
ceiling_mat=model.materials.add('IF_Pale_Birch_Ceiling_R19');ceiling_mat.color=Sketchup::Color.new(233,216,183)
table_mat=model.materials.add('IF_Pale_White_Tabletop_R19');table_mat.color=Sketchup::Color.new(244,242,233)
face_count=0
INF_FINISH_TARGETS.each do |path,pid,ids|
  g=inf_path(root,path)
  ids.each do |id|
    f=inf_entities(g).grep(Sketchup::Face).find{|e|e.persistent_id==id}
    raise 'Approved face missing' unless f
    mat=path.first=='INTERIOR' ? table_mat : (f.normal.z<0 ? ceiling_mat : floor_mat)
    f.material=mat;f.back_material=mat;face_count+=1
  end
end
raise 'Wrong face count' unless face_count==25
shell=inf_path(root,['ROOF_TIMBER','CURVED_SHELL'])
edges=shell.entities.grep(Sketchup::Edge)
INF_SOFT_EDGE_IDS.each do |id|
  e=edges.find{|q|q.persistent_id==id};raise 'Approved seam absent' unless e && e.faces.length==2
  raise 'Unexpected crease' unless e.faces[0].normal.angle_between(e.faces[1].normal)<5*Math::PI/180
  e.soft=true;e.smooth=true
end
raise 'Changed constrained surface geometry' unless surface_shapes==surface_groups.map{|g|inf_shape(g)}
# Add the exact approved new ceiling leaf. All existing beams/slabs remain intact.
raise 'Ceiling leaf already present' if interior.entities.any?{|e|e.respond_to?(:name)&&e.name=='CEILING_TENSION_MEMBERS'}
ceiling=inf_group(interior.entities,'CEILING_TENSION_MEMBERS')
structure=inf_path(root,['STRUCTURE_EXISTING'])
ceiling_contacts=0
INF_V_MEMBERS.each_with_index do |v,i|
  x,y0,y1,ym,za,zm,w=v
  g=inf_group(ceiling.entities,"IF_V_BAY_#{i+1}")
  a=[x,y0,za];b=[x,ym,zm];c=[x,y1,za]
  inf_bar(g.entities,"IF_V#{i+1}_LEFT",a,b,w,steel)
  inf_bar(g.entities,"IF_V#{i+1}_RIGHT",b,c,w,steel)
  [a,c].each_with_index do |p,j|
    beam=inf_find(structure.entities,"LONG_BEAM_Z10800_Y#{(p[1]/10000.0).round}")
    raise 'V endpoint misses actual beam solid' unless inf_contains(beam,p)
    ceiling_contacts+=1
    inf_bar(g.entities,"IF_V#{i+1}_FIXING_#{j}",[p[0],p[1],10314],[p[0],p[1],10322],60,steel)
  end
  # A thin center hanger ties the shallow V vertex to retained ceiling slab.
  start=Geom::Point3d.new(x.mm,ym.mm,10450.mm)
  hit=model.raytest([start,Z_AXIS],true)
  raise 'V center has no retained slab above' unless hit && (hit[0].z.to_mm-10550).abs<0.1
  inf_bar(g.entities,"IF_V#{i+1}_CENTRE_HANGER",b,[x,ym,10555],18,steel)
end
# Authorized native display correction; original materials are already pale.
# This is view shading, not a geometry change or a renderer claim.
model.shadow_info['Dark']=80
model.shadow_info['Light']=15
model.shadow_info['UseSunForAllShading']=true
model.shadow_info['DisplayShadows']=false
# Re-probe all 216 original walking samples without changing any beam/plate.
fails=[];min_clear=1.0e9
3.times do |k|
  24.times do |i|
    a=(45+330.0*(i+0.5)/24)*Math::PI/180
    [650,1150,1600].each do |r|
      z=k*3600+(i+1)*150
      p=Geom::Point3d.new(*inf_polar(r,a,z+2).map(&:mm))
      hit=model.raytest([p,Z_AXIS],true)
      if hit
        d=hit[0].z.to_mm-z;min_clear=[min_clear,d].min
        fails<<[k,i,r,d.round(2)] if d<2100
      end
    end
  end
end
# Preserve and report pre-existing clearances; do not falsely certify them.
puts "INTERIOR_FINISH: 300mm shafts;450mm collars;#{contacts} solid support contacts;25 finish faces;#{INF_SOFT_EDGE_IDS.length} smooth joins;15 shallow V assemblies and#{ceiling_contacts} actual beam contacts;216 headroom rays min_mm=#{min_clear.round(2)}, below2100=#{fails.inspect}; original slab/roof/table primitives unchanged."
