# Source4 interior, source5/7 plans; inferred concealed joints. Scoped r14 edit.
# kstudio.custom_owned_ruby: helical/open wire/suspended fabric systems do not
# fit SAIE straight opaque walls. ADAI disabled. Preserve all existing slabs.
def ic_find(es,name)
  a=es.select{|e| (e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)) && e.name==name}
  raise "Missing/duplicate #{name}" unless a.length==1
  a.first
end
def ic_group(es,name)
  g=es.add_group;g.name=name;g.set_attribute('KStudio','semantic_id',name);g
end
def ic_face(es,pts,mat)
  f=es.add_face(pts.map{|p|p.map(&:mm)});raise 'Face failed' unless f
  f.material=mat;f.back_material=mat;f
end
def ic_box(es,name,x,y,z,w,d,h,mat)
  g=ic_group(es,name)
  f=ic_face(g.entities,[[x,y,z],[x+w,y,z],[x+w,y+d,z],[x,y+d,z]],mat)
  f.reverse! if f.normal.z<0;f.pushpull(h.mm);g.material=mat;g
end
def ic_bar(es,name,a,b,width,mat,cache)
  v=Geom::Vector3d.new(*(0..2).map{|i|(b[i]-a[i]).mm});len=v.length
  raise 'Zero bar' if len.to_f<0.001
  if cache.empty?
    g=ic_box(es,name,-0.5,-0.5,0,1,1,1,mat).to_component
    g.definition.name='IC_Reused_Unit_Square_Bar_R15'
    g.definition.entities.grep(Sketchup::Face).each{|f|f.material=nil;f.back_material=nil}
    g.definition.entities.grep(Sketchup::Edge).each{|e|e.hidden=true}
    cache[:definition]=g.definition
  else
    g=es.add_instance(cache[:definition],Geom::Transformation.new)
  end
  g.name=name;g.set_attribute('KStudio','semantic_id',name);g.material=mat
  z=v.normalize;reference=z.parallel?(Z_AXIS) ? X_AXIS : Z_AXIS
  x=reference.cross(z).normalize;y=z.cross(x).normalize
  g.transformation=Geom::Transformation.axes(Geom::Point3d.new(*a.map(&:mm)),x,y,z)*Geom::Transformation.scaling(width,width,len.to_mm)
  g
end
def ic_sector(es,name,cx,cy,ri,ro,aa,bb,z,thick,mat)
  g=ic_group(es,name);n=[((bb-aa).abs*ro/90).ceil,2].max
  outer=(0..n).map{|i|a=aa+(bb-aa)*i/n;[cx+ro*Math.cos(a),cy+ro*Math.sin(a),z-thick]}
  inner=(0..n).map{|i|a=bb+(aa-bb)*i/n;[cx+ri*Math.cos(a),cy+ri*Math.sin(a),z-thick]}
  f=ic_face(g.entities,outer+inner,mat);f.reverse! if f.normal.z<0;f.pushpull(thick.mm)
  g.material=mat;g
end
def ic_polar(r,a,z)
  [37000+r*Math.cos(a),6500+r*Math.sin(a),z]
end
def ic_shape(g)
  g.entities.grep(Sketchup::Edge).map{|e|[e.persistent_id,e.vertices.map{|v|v.position.to_a}]}+
    g.entities.grep(Sketchup::Face).map{|f|[f.persistent_id,f.loops.map{|l|l.vertices.map{|v|v.position.to_a}}]}
end
raise 'Wrong owned root' unless root.persistent_id==20606
cir=ic_find(root.entities,'CIRCULATION_INTERNAL');interior=ic_find(root.entities,'INTERIOR')
floors=ic_find(root.entities,'FLOORS');roof=ic_find(root.entities,'ROOF_TIMBER')
shell=ic_find(roof.entities,'CURVED_SHELL');l3=ic_find(floors.entities,'L3')
raise 'Unexpected shared target or transform' unless [cir,interior,floors].all?{|g|g.definition.instances.length==1 && g.transformation.identity?}
raise 'Unexpected finish identities' unless shell.persistent_id==77873 && l3.persistent_id==76979
raise 'Shared finish geometry' unless [shell,l3].all?{|g|g.definition.instances.length==1}
shape_shell=ic_shape(shell);shape_floor=ic_shape(l3)
steel=model.materials['KS_White_Steel'];raise 'Missing white steel' unless steel
pale=model.materials.add('IC_Pale_Mineral_Floor_R15');pale.color=Sketchup::Color.new(225,224,216)
wood=model.materials.add('IC_Pale_Birch_R15');wood.color=Sketchup::Color.new(233,216,183)
fabric=model.materials.add('IC_Translucent_White_Fabric_R15');fabric.color=Sketchup::Color.new(249,247,239);fabric.alpha=0.30
silver=model.materials.add('IC_Table_Frame_R15');silver.color=Sketchup::Color.new(178,181,177)
bar_cache={}
bar=lambda{|es,name,a,b,width,mat|ic_bar(es,name,a,b,width,mat,bar_cache)}
# Read actual soffit profile through existing transforms; do not use old heights.
st=roof.transformation*shell.transformation;samples={}
shell.entities.grep(Sketchup::Edge).flat_map{|e|e.vertices}.uniq.each do |v|
  p=st*v.position;y=p.y.to_mm.round(4);z=p.z.to_mm
  samples[y]=z if !samples.key?(y)||z<samples[y]
end
ys=samples.keys.sort;raise 'Invalid actual roof' unless ys.length>=41
soffit=lambda do |y|
  i=ys.bsearch_index{|v|v>=y};i=1 if !i||i<1
  a,b=ys[i-1],ys[i];samples[a]+(samples[b]-samples[a])*(y-a)/(b-a)
end
# Rebuild only contents, preserving each of the three actual container PIDs.
3.times do |k|
  path=['CIRCULATION_INTERNAL',"SPIRAL_L#{k}_L#{k+1}"]
  g=ic_find(cir.entities,path.last)
  raise 'Unexpected spiral identity' unless g.persistent_id==[45402,47708,50014][k]
  g.make_unique if g.definition.instances.length>1
  clear_owned_contents.call(path);z=k*3600.0;es=g.entities
  core=ic_group(es,"S#{k}_CONTINUOUS_CORE")
  disk=core.entities.add_face(core.entities.add_circle([37000.mm,6500.mm,z.mm],[0,0,1],370.mm,64))
  disk.reverse! if disk.normal.z<0;disk.pushpull(3600.mm);core.material=steel
  collar=ic_group(es,"S#{k}_CORE_BASE_COLLAR")
  cf=collar.entities.add_face(collar.entities.add_circle([37000.mm,6500.mm,z.mm],[0,0,1],470.mm,64))
  cf.reverse! if cf.normal.z<0;cf.pushpull(35.mm);collar.material=steel
  24.times do |i|
    a=(45.0+330.0*i/24)*Math::PI/180;b=(45.0+330.0*(i+1)/24)*Math::PI/180
    h=z+(i+1)*150
    ic_sector(es,"S#{k}_TREAD_#{i}",37000,6500,350,1700,a,b,h,100,steel)
    mid=(a+b)/2
    bar.call(es,"S#{k}_RADIAL_SUPPORT_#{i}",ic_polar(360,mid,h-125),ic_polar(1640,mid,h-125),50,steel)
    # At the final tread the outer rail opens directly onto the landing sector.
    next if i==23
    bar.call(es,"S#{k}_POST_#{i}",ic_polar(1715,a,h),ic_polar(1715,a,h+1100),20,steel)
    8.times do |j|
      aa=a+(b-a)*j/8;bb=a+(b-a)*(j+1)/8
      za=z+i*150+j*150.0/8;zb=z+i*150+(j+1)*150.0/8
      bar.call(es,"S#{k}_TOP_#{i}_#{j}",ic_polar(1715,aa,za+1100),ic_polar(1715,bb,zb+1100),28,steel)
      bar.call(es,"S#{k}_MESH_V_#{i}_#{j}",ic_polar(1715,aa,za+165),ic_polar(1715,aa,za+1080),3,steel)
      (1..18).each do |m|
        bar.call(es,"S#{k}_MESH_H_#{i}_#{j}_#{m}",ic_polar(1715,aa,za+165+m*50),ic_polar(1715,bb,zb+165+m*50),3,steel)
      end
      bar.call(es,"S#{k}_BOTTOM_#{i}_#{j}",ic_polar(1715,aa,za+160),ic_polar(1715,bb,zb+160),16,steel)
    end
  end
  # Real planar landing reaches 100mm onto the unchanged surrounding floor.
  ic_sector(es,"S#{k}_TOP_LANDING",37000,6500,350,2400,Math::PI/12,Math::PI/4,z+3600,100,steel)
  ic_sector(es,"S#{k}_TOP_OUTER_BRIDGE",37000,6500,1700,2400,0,Math::PI/12,z+3600,100,steel)
  ic_sector(es,"S#{k}_BOTTOM_LANDING",37000,6500,350,2400,0,Math::PI/4,z,100,steel) if k==0
  [0,Math::PI/4].each_with_index do |a,j|
    support_a=j==0 ? Math::PI/9 : a
    bar.call(es,"S#{k}_LANDING_SUPPORT_#{j}",ic_polar(390,support_a,z+3450),ic_polar(2350,support_a,z+3450),65,steel)
    bar.call(es,"S#{k}_LANDING_RAIL_#{j}",ic_polar(1720,a,z+4700),ic_polar(2330,a,z+4700),25,steel)
    (0..12).each do |n|
      r=1720+(2330-1720)*n/12.0
      bar.call(es,"S#{k}_LANDING_WIRE_#{j}_#{n}",ic_polar(r,a,z+3620),ic_polar(r,a,z+4680),3,steel)
    end
    (1..21).each{|n|bar.call(es,"S#{k}_LANDING_CROSS_#{j}_#{n}",ic_polar(1720,a,z+3600+n*50),ic_polar(2330,a,z+3600+n*50),3,steel)}
  end
  g.set_attribute('KStudio','outer_radius_mm',1700)
  g.set_attribute('KStudio','landing_sector_deg','0..45')
end
# All18 actual table containers receive source4 thin braced metal legs.
furniture=ic_find(interior.entities,'FURNITURE_SIMPLIFIED')
[0,3600,10800].each do |z|
  6.times do |i|
    g=ic_find(furniture.entities,"TABLE_Z#{z}_#{i}")
    raise 'Nonidentity table' unless g.transformation.identity?
    g.make_unique if g.definition.instances.length>1
    # Move the complete tabletop contents away from hole and stair headroom.
    if i==5
      g.entities.transform_entities(Geom::Transformation.translation([0,-2500.mm,0]),g.entities.to_a)
    end
    b=g.bounds;x0=b.min.x.to_mm+160;x1=b.max.x.to_mm-160
    y0=b.min.y.to_mm+120;y1=b.max.y.to_mm-120;top=z+720
    [[x0,y0],[x1,y0],[x1,y1],[x0,y1]].each_with_index{|p,j|bar.call(g.entities,"TABLE_#{z}_#{i}_LEG_#{j}",[p[0],p[1],z],[p[0],p[1],top],30,silver)}
    [y0,y1].each_with_index do |y,j|
      bar.call(g.entities,"TABLE_#{z}_#{i}_APRON_#{j}",[x0,y,top-35],[x1,y,top-35],25,silver)
      bar.call(g.entities,"TABLE_#{z}_#{i}_BRACE_#{j}A",[x0,y,z+250],[x1,y,z+640],14,silver)
      bar.call(g.entities,"TABLE_#{z}_#{i}_BRACE_#{j}B",[x1,y,z+250],[x0,y,z+640],14,silver)
    end
    [x0,x1].each_with_index{|x,j|bar.call(g.entities,"TABLE_#{z}_#{i}_END_#{j}",[x,y0,top-35],[x,y1,top-35],25,silver)}
    raise 'Table still near stair hole' if i==5 && Math.sqrt((37400-37000)**2+(2500-6500)**2)<3300
  end
end
# Existing large rings are protected. Add actual wire infill only outside their
# 0..45deg entrance sector. No changes to old guard containers or slab loops.
mesh=ic_group(cir.entities,'LARGE_CIRCULAR_VOID_MESH')
[3600,7200,10800].each do |z|
  n=252
  n.times do |i|
    a=Math::PI/4+(2*Math::PI-Math::PI/4)*i/n
    b=Math::PI/4+(2*Math::PI-Math::PI/4)*(i+1)/n
    bar.call(mesh.entities,"VOID_Z#{z}_V#{i}",ic_polar(2300,a,z+20),ic_polar(2300,a,z+1080),3,steel)
    (1..21).each{|j|bar.call(mesh.entities,"VOID_Z#{z}_H#{j}_#{i}",ic_polar(2300,a,z+j*50),ic_polar(2300,b,z+j*50),3,steel)}
  end
end
# Source4 substantial curved translucent curtains, source7 flexible hall zones.
# Every suspension is fitted to actual retained roof vertex profile.
curtains=ic_group(interior.entities,'HALL_CURTAINS')
zones=[[8000,5000,6000,3200,20,310],[21000,16500,4000,2200,0,220],[34000,15500,7000,3000,0,220]]
zones.each_with_index do |p,k|
  cx,cy,rx,ry,a0,a1=p;g=ic_group(curtains.entities,"HALL_CURTAIN_ZONE_#{k+1}")
  track_z=14050.0;bottom=10850.0;n=240
  point=lambda do |t,fold|
    a=(a0+(a1-a0)*t)*Math::PI/180
    r=fold ? 38*Math.sin(t*2*Math::PI*48) : 0
    [cx+(rx+r)*Math.cos(a),cy+(ry+r)*Math.sin(a)]
  end
  n.times do |i|
    t=i.to_f/n;u=(i+1).to_f/n;v=point.call(t,true);w=point.call(u,true)
    f=ic_face(g.entities,[[v[0],v[1],bottom],[w[0],w[1],bottom],[w[0],w[1],track_z-45],[v[0],v[1],track_z-45]],fabric)
    f.edges.each{|e|e.soft=true;e.smooth=true;e.hidden=true}
    if i%2==0
      a=point.call(t,false);b=point.call([t+2.0/n,1].min,false)
      bar.call(g.entities,"C#{k}_TRACK_#{i}",[a[0],a[1],track_z],[b[0],b[1],track_z],32,steel)
      bar.call(g.entities,"C#{k}_CURTAIN_HOOK_#{i}",[a[0],a[1],track_z-45],[a[0],a[1],track_z],5,steel)
    end
    next unless i%20==0 || i==n-1
    a=point.call(t,false);rz=soffit.call(a[1])
    raise 'Track hits actual timber roof' unless rz-track_z>250
    bar.call(g.entities,"C#{k}_SUSPENSION_#{i}",[a[0],a[1],track_z],[a[0],a[1],rz],10,steel)
    ic_box(g.entities,"C#{k}_ROOF_FIXING_#{i}",a[0]-30,a[1]-30,rz-8,60,60,8,steel)
  end
  g.set_attribute('KStudio','source','source04 upper; source07 hall zoning; inferred placement and joints')
end
# Surface finishes only: all original entity IDs, loops and coordinates audited.
l3.entities.grep(Sketchup::Face).each do |f|
  normal=l3.transformation*f.normal
  if normal.z.abs>0.9
    f.material=pale;f.back_material=pale
  end
end
shell.entities.grep(Sketchup::Face).each{|f|f.material=wood;f.back_material=wood}
raise 'Floor geometry changed by finish' unless shape_floor==ic_shape(l3)
raise 'Roof geometry changed by finish' unless shape_shell==ic_shape(shell)
# Native geometric checks: headroom samples at three radii on every tread.
# Only read model rays; no whole-model geometry edits.
failures=[];minimum=1.0e9
3.times do |k|
  24.times do |i|
    a=(45.0+330.0*(i+0.5)/24)*Math::PI/180
    [650,1150,1600].each do |r|
      z=k*3600+(i+1)*150;p=ic_polar(r,a,z+2)
      hit=model.raytest([Geom::Point3d.new(p.map(&:mm)),Geom::Vector3d.new(0,0,1)],true)
      if hit
        d=hit[0].z.to_mm-z;minimum=[minimum,d].min
        failures<<[k,i,r,d] if d<2100
      end
    end
  end
end
raise "Insufficient native stair headroom #{failures.inspect}" unless failures.empty?
puts "INTERIOR_COMPLETE: three central supports;72treads;18supported tables;three curved translucent zones;native216 headroom rays min_mm=#{minimum.round(2)}; roof/floor IDs loops coordinates unchanged"
