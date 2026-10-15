# Source sheets 1/2 end views; sheets 3/7 confirm perimeter reception.
# Local repair on existing r4. kstudio.custom_owned_ruby: existing sloped
# profiles/rails cannot be represented by SAIE straight walls; ADAI disabled.
def rc_find(entities,name)
  a=entities.select{|e|e.respond_to?(:name) && e.name==name}
  raise "Nonunique #{name}" unless a.length==1
  a.first
end
def rc_entities(g)
  g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities
end
def rc_group(entities,name)
  g=entities.add_group;g.name=name;g.set_attribute('KStudio','semantic_id',name);g
end
def rc_box(entities,name,x,y,z,dx,dy,dz,mat)
  g=rc_group(entities,name)
  f=g.entities.add_face([x.mm,y.mm,z.mm],[(x+dx).mm,y.mm,z.mm],[(x+dx).mm,(y+dy).mm,z.mm],[x.mm,(y+dy).mm,z.mm])
  f.reverse! if f.normal.z<0;f.pushpull(dz.mm);g.material=mat;g
end
def rc_bar(entities,name,a,b,w,mat)
  v=Geom::Vector3d.new(*(0..2).map{|i|(b[i]-a[i]).mm})
  g=rc_box(entities,name,-w/2.0,-w/2.0,0,w,w,v.length.to_mm,mat)
  z=v.normalize;ref=z.parallel?(Z_AXIS) ? X_AXIS : Z_AXIS
  x=ref.cross(z).normalize;y=z.cross(x).normalize
  g.transform!(Geom::Transformation.axes(Geom::Point3d.new(*a.map(&:mm)),x,y,z));g
end
def rc_rail(entities,name,a,b,mat)
  g=rc_group(entities,name);n=([(b[0]-a[0]).abs,(b[1]-a[1]).abs].max/1400.0).ceil
  n=[n,1].max
  (0..n).each{|i|t=i.to_f/n;p=(0..2).map{|j|a[j]+(b[j]-a[j])*t};rc_bar(g.entities,"#{name}_POST_#{i}",p,[p[0],p[1],p[2]+1100],35,mat)}
  [120,550,1100].each{|h|rc_bar(g.entities,"#{name}_H#{h}",[a[0],a[1],a[2]+h],[b[0],b[1],b[2]+h],30,mat)};g
end
raise 'Wrong root' unless root.persistent_id==20606
ramps=rc_find(root.entities,'RAMPS');ext=rc_find(root.entities,'CIRCULATION_EXTERNAL')
steel=model.materials['KS_White_Steel'];raise 'Missing material' unless steel
raise 'Already corrected' if rc_find(rc_entities(ramps),'RAMP_1').get_attribute('KStudio','ramp_direction_repaired',false)
mirror=Geom::Transformation.translation([0,20000.mm,0])*Geom::Transformation.scaling(1,-1,1)
[[1,0],[3,-2200]].each do |i,dx|
  g=rc_find(rc_entities(ramps),"RAMP_#{i}")
  parent=ramps.transformation
  world=Geom::Transformation.translation([dx.mm,0,0])*mirror
  g.transform!(parent.inverse*world*parent)
  g.set_attribute('KStudio','ramp_direction_repaired',true)
  ['OUTER','INNER'].each do |side|
    rail=rc_find(ext.entities,"RAMP_#{i}_#{side}")
    rail.transform!(ext.transformation.inverse*world*ext.transformation)
  end
end
landings=rc_find(ext.entities,'LANDINGS')
# Existing containers retained. North/south pads join the fixed end gallery;
# its clear west strip supplies same-level return, not another sloped flight.
specs=[
 ['LANDING_L0',0,[[-8500,-6200,2200,2200]],[]],
 ['LANDING_L1',3600,[[-8500,-6200,8500,2200],[-8500,24000,8500,2200]],[
  [[-8500,-6200],[0,-6200]],[[-8500,-6200],[-8500,-4000]],[[-8500,-4000],[-6300,-4000]],[[0,-6200],[0,-4000]],
  [[-8500,26200],[0,26200]],[[-8500,24000],[-8500,26200]],[[-6300,24000],[-4000,24000]],[[0,24000],[0,26200]]]],
 ['LANDING_L2',7200,[[-6300,24000,6600,2200],[-6300,-6200,6300,2200]],[
  [[-6300,26200],[300,26200]],[[-6300,24000],[-6300,26200]],[[300,24000],[300,26200]],
  [[-6300,-6200],[0,-6200]],[[-6300,-6200],[-6300,-4000]],[[0,-6200],[0,-4000]]]],
 ['LANDING_L3',10800,[[-6300,24000,6300,2200]],[
  [[-6300,26200],[0,26200]],[[-6300,24000],[-6300,26200]],[[0,24000],[0,26200]]]]
]
specs.each do |name,z,pads,edges|
  g=rc_find(landings.entities,name);ge=rc_entities(g)
  # Deform the existing solid into the first pad, retaining every original face.
  vv=ge.grep(Sketchup::Edge).flat_map{|e|e.vertices}.uniq
  tr=g.transformation;pp=vv.map{|v|tr*v.position}
  xmin=pp.map{|p|p.x.to_mm}.min;xmax=pp.map{|p|p.x.to_mm}.max
  ymin=pp.map{|p|p.y.to_mm}.min;ymax=pp.map{|p|p.y.to_mm}.max
  first=pads.first
  shifts=vv.map do |v|
    p=tr*v.position
    xx=first[0]+(p.x.to_mm-xmin)/(xmax-xmin)*first[2]
    yy=first[1]+(p.y.to_mm-ymin)/(ymax-ymin)*first[3]
    tr.inverse*Geom::Vector3d.new((xx-p.x.to_mm).mm,(yy-p.y.to_mm).mm,0)
  end
  ge.transform_by_vectors(vv,shifts)
  pads.drop(1).each_with_index{|p,i|rc_box(ge,"#{name}_PAD_ADDED_#{i}",p[0],p[1],z-160,p[2],p[3],160,steel)}
  edges.each_with_index{|edge,i|rc_rail(ge,"#{name}_GUARD_#{i}",edge[0]+[z],edge[1]+[z],steel)}
end
# Fixed gallery guards are host-protected; receiving gates remain unresolved.
# Numerical source-direction checks in root coordinates, not camera projection.
[[1,-8500,0,3600],[2,-6300,3600,7200],[3,-6300,7200,10800]].each do |i,x,lo,hi|
  g=rc_find(rc_entities(ramps),"RAMP_#{i}");tr=ramps.transformation*g.transformation
  pts=rc_entities(g).grep(Sketchup::Edge).flat_map{|e|e.vertices}.uniq.map{|v|tr*v.position}
  [-4000,24000].zip([lo,hi]).each do |y,z|
    cap=pts.select{|p|(p.y.to_mm-y).abs<0.1};raise "Missing ramp cap #{i}" if cap.empty?
    raise "Wrong ramp direction #{i}" if (cap.map{|p|p.z.to_mm}.max-z).abs>0.1
  end
  raise 'Ramp intersects gallery footprint' unless pts.map{|p|p.x.to_mm}.max < -4000
end

