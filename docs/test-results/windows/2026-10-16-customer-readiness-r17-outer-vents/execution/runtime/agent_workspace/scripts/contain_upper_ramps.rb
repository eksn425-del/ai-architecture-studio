# r7 local edit: upper flights, dependent platforms and six apron plates only.
# kstudio.custom_owned_ruby: in-place native sloping solids and plate clipping;
# installed SAIE straight wall/opening cannot implement these slab/ramp systems.
# ADAI unavailable. No whole-root rebuild or reparenting.
def ur_find(es,n)
  a=es.select{|e|e.respond_to?(:name) && e.name==n};raise "Missing/duplicate #{n}" unless a.length==1;a.first
end
def ur_es(g)
  g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities
end
def ur_group(es,n)
  g=es.add_group;g.name=n;g.set_attribute('KStudio','semantic_id',n);g
end
def ur_box(es,n,x0,x1,y0,y1,z0,z1,mat)
  g=ur_group(es,n)
  f=g.entities.add_face([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0]].map{|p|p.map(&:mm)})
  f.reverse! if f.normal.z<0;f.pushpull((z1-z0).mm);g.material=mat;g
end
def ur_bar(es,n,a,b,w,mat)
  v=Geom::Vector3d.new(*(0..2).map{|i|(b[i]-a[i]).mm})
  g=ur_box(es,n,-w/2.0,w/2.0,-w/2.0,w/2.0,0,v.length.to_mm,mat)
  z=v.normalize;ref=z.parallel?(Z_AXIS) ? X_AXIS : Z_AXIS;x=ref.cross(z).normalize;y=z.cross(x).normalize
  g.transform!(Geom::Transformation.axes(Geom::Point3d.new(*a.map(&:mm)),x,y,z));g
end
def ur_rail(es,n,a,b,mat)
  g=ur_group(es,n);nn=[((Geom::Point3d.new(*a.map(&:mm))).distance(Geom::Point3d.new(*b.map(&:mm))).to_mm/1300).ceil,1].max
  (0..nn).each{|i|t=i.to_f/nn;p=(0..2).map{|j|a[j]+(b[j]-a[j])*t};ur_bar(g.entities,"#{n}_P#{i}",p,[p[0],p[1],p[2]+1100],35,mat)}
  [120,550,1100].each{|h|ur_bar(g.entities,"#{n}_H#{h}",[a[0],a[1],a[2]+h],[b[0],b[1],b[2]+h],30,mat)};g
end
def ur_points(g,tr)
  ur_es(g).grep(Sketchup::Edge).flat_map{|e|e.vertices}.uniq.map{|v|tr*v.position}
end
def ur_faces(g,tr,out)
  ur_es(g).each do |e|
    if e.is_a?(Sketchup::Face)
      out<<[e,tr]
    elsif e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance)
      ur_faces(e,tr*e.transformation,out)
    end
  end
end
raise 'Wrong model root' unless root.persistent_id==20606
ramps=ur_find(root.entities,'RAMPS');ext=ur_find(root.entities,'CIRCULATION_EXTERNAL')
gal=ur_find(ext.entities,'GALLERIES');land=ur_find(ext.entities,'LANDINGS')
mat=model.materials['KS_White_Steel'];raise 'Missing material' unless mat
delta=Geom::Transformation.translation([2400.mm,(10000.0*(1-26.0/28.0)).mm,0])*Geom::Transformation.scaling(1,26.0/28.0,1)
[2,3].each do |i|
  g=ur_find(ramps.entities,"RAMP_#{i}")
  raise 'Unexpected ramp PID' unless g.persistent_id=={2=>79027,3=>79055}[i]
  old=ur_points(g,ramps.transformation*g.transformation)
  raise 'Unexpected prior ramp X' unless (old.map{|p|p.x.to_mm}.min+6300).abs<0.1
  g.transform!(ramps.transformation.inverse*delta*ramps.transformation)
  ['OUTER','INNER'].each do |side|
    rail=ur_find(ext.entities,"RAMP_#{i}_#{side}");rail.transform!(ext.transformation.inverse*delta*ext.transformation)
  end
  pts=ur_points(g,ramps.transformation*g.transformation)
  raise 'Ramp outside glass' unless pts.all?{|p|p.x.to_mm>-4000 && p.x.to_mm<0}
  [-3000,23000].zip([(i-1)*3600,i*3600]).each do |yy,zz|
    cap=pts.select{|p|(p.y.to_mm-yy).abs<0.01}
    raise 'Ramp cap disconnected' if cap.empty? || (cap.map{|p|p.z.to_mm}.max-zz).abs>0.01
  end
end
# L1 north arrival of the lowest flight is strictly preserved, including all
# five named north-pad/guard children. Only south departure pad is reduced.
l1=ur_find(land.entities,'LANDING_L1');es=l1.entities
vv=es.grep(Sketchup::Edge).flat_map{|e|e.vertices}.uniq
pt=ext.transformation*land.transformation*l1.transformation
es.transform_by_vectors(vv,vv.map{|v|p=pt*v.position;dx=p.x.to_mm*(3950.0/8500.0)-p.x.to_mm;Geom::Vector3d.new(dx.mm,0,0).transform(pt.inverse)})
# Reuse the four existing south guard containers; northern children untouched.
g=ur_find(es,'LANDING_L1_GUARD_0');w=Geom::Transformation.scaling(3950.0/8500.0,1,1);g.transform!(pt.inverse*w*pt)
g=ur_find(es,'LANDING_L1_GUARD_1');w=Geom::Transformation.translation([4550.mm,0,0]);g.transform!(pt.inverse*w*pt)
g=ur_find(es,'LANDING_L1_GUARD_2')
w=Geom::Transformation.translation([-3950.mm,-4000.mm,0])*Geom::Transformation.rotation(ORIGIN,Z_AXIS,90.degrees)*Geom::Transformation.scaling(1000.0/2200.0,1,1)*Geom::Transformation.translation([8500.mm,4000.mm,0])
g.transform!(pt.inverse*w*pt)
# Flat inner pads fill exact notches in the apron, with no coincident slab face.
[[2,7200,[-1,1]],[3,10800,[1]]].each do |lev,z,sides|
  name="LANDING_L#{lev}";g=ur_find(land.entities,name)
  clear_owned_contents.call(['CIRCULATION_EXTERNAL','LANDINGS',name])
  sides.each do |side|
    a,b=side<0 ? [-4000,-3000] : [23000,24000]
    ur_box(g.entities,"L#{lev}_INNER_FLAT_#{side}",-3950,-1650,a,b,z-150,z,mat)
    a,b=side<0 ? [-6200,-4000] : [24000,26200]
    ur_box(g.entities,"L#{lev}_REDUCED_OUTSIDE_#{side}",-3950,0,a,b,z-160,z,mat)
    yy=side<0 ? a : b
    [[[-3950,yy,z],[0,yy,z]],[[-3950,a,z],[-3950,b,z]],[[0,a,z],[0,b,z]]].each_with_index{|ab,i|ur_rail(g.entities,"L#{lev}_EDGE_#{side}_#{i}",ab[0],ab[1],mat)}
  end
end
patches=[]
[7200,10800].each do |z|
  [[0,-4000,0,54000],[1,20000,24000,54000],[2,0,20000,0]].each do |side,y0,y1,xmax|
    name="GALLERY_Z#{z}_SIDE#{side}";g=ur_find(gal.entities,name)
    clear_owned_contents.call(['CIRCULATION_EXTERNAL','GALLERIES',name])
    es=g.entities
    ur_box(es,"#{name}_GLASS_EDGE",-4000,-3950,y0,y1,z-150,z,mat)
    ur_box(es,"#{name}_RETURN_STRIP",-1650,xmax,y0,y1,z-150,z,mat)
    # Only top-storey south flat is retained here; other flat strips belong
    # to landing containers, filling the notch precisely.
    if z==10800 && side==0
      ur_box(es,"#{name}_SOUTH_FLAT",-3950,-1650,-4000,-3000,z-150,z,mat)
    end
    ga=[y0,-3000].max;gb=[y1,23000].min
    ur_rail(es,"#{name}_SLOT_GUARD",[-1650,ga,z],[-1650,gb,z],mat) if gb>ga
    patches<<g
  end
end
# Native face probes: ensure no retained apron face blocks a flight or the
# 2.2m head zone. Stacked flight underside is 3440mm above the lower surface.
faces=[]
gal.entities.select{|e|e.respond_to?(:name) && e.name.start_with?('GALLERY_')}.each{|g|ur_faces(g,ext.transformation*gal.transformation*g.transformation,faces)}
[2,3].each{|i|g=ur_find(ramps.entities,"RAMP_#{i}");ur_faces(g,ramps.transformation*g.transformation,faces)}
land.entities.each{|g|ur_faces(g,ext.transformation*land.transformation*g.transformation,faces) if g.is_a?(Sketchup::Group)}
[2,3].each do |i|
  (0..26).each do |k|
    yy=-3000+k*1000.0;zz=(i-1)*3600+3600.0*(yy+3000)/26000
    xx=-2800.0
    faces.each do |f,tr|
      pp=f.vertices.map{|v|tr*v.position};next if pp.length<3
      next unless xx>=pp.map{|p|p.x.to_mm}.min-0.01 && xx<=pp.map{|p|p.x.to_mm}.max+0.01 && yy>=pp.map{|p|p.y.to_mm}.min-0.01 && yy<=pp.map{|p|p.y.to_mm}.max+0.01
      nn=(pp[1]-pp[0]).cross(pp[2]-pp[0]);next if nn.z.abs<0.00001
      hitz=pp[0].z-(nn.x*(xx.mm-pp[0].x)+nn.y*(yy.mm-pp[0].y))/nn.z
      gap=hitz.to_mm-zz;next unless gap>1 && gap<2200
      point=Geom::Point3d.new(xx.mm,yy.mm,hitz).transform(tr.inverse)
      c=f.classify_point(point)
      raise "Obstructed flight #{i}, Y#{yy}, gap#{gap}" if [Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(c)
    end
  end
end
raise 'Wrong nominal stacked clearance' unless (3600-160)>=2200
