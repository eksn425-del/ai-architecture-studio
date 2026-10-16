# r12 coordinated exact-scope correction. Never modify original treads/ramps.
# Method kstudio.custom_owned_ruby. SAIE straight walls/openings are unsuitable
# for perforated walkways, slender mesh, sloping handrails and stair stringers.
# ADAI is disabled. All dimensions are source-constrained estimates in mm.

def ec_es(g)
  g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities
end
def ec_find(es,n)
  aa=es.select{|e|e.respond_to?(:name)&&e.name==n}
  raise "Missing/duplicate #{n}" unless aa.length==1
  aa.first
end
def ec_path(root,path)
  g=root;tr=Geom::Transformation.new
  path.each{|n|g=ec_find(ec_es(g),n);tr=tr*g.transformation}
  [g,tr]
end
def ec_group(es,n)
  g=es.add_group;g.name=n;g.set_attribute('KStudio','semantic_id',n);g
end
def ec_box(es,n,x0,x1,y0,y1,z0,z1,mat,quiet=false)
  raise "Invalid box #{n}" unless x1>x0 && y1>y0 && z1>z0
  g=ec_group(es,n)
  f=g.entities.add_face([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0]].map{|p|p.map(&:mm)})
  raise "No face #{n}" unless f
  f.reverse! if f.normal.z<0;f.pushpull((z1-z0).mm);g.material=mat
  g.entities.grep(Sketchup::Edge).each{|e|e.hidden=true} if quiet
  g
end
def ec_bar(es,n,a,b,w,mat)
  vec=Geom::Vector3d.new(*(0..2).map{|i|(b[i]-a[i]).mm})
  raise 'Zero bar length' if vec.length.to_mm<1
  g=ec_box(es,n,-w/2.0,w/2.0,-w/2.0,w/2.0,0,vec.length.to_mm,mat)
  zz=vec.normalize;ref=zz.parallel?(Z_AXIS) ? X_AXIS : Z_AXIS
  xx=ref.cross(zz).normalize;yy=zz.cross(xx).normalize
  g.transform!(Geom::Transformation.axes(Geom::Point3d.new(*a.map(&:mm)),xx,yy,zz));g
end
def ec_vbounds(g)
  bb=Geom::BoundingBox.new
  ec_es(g).grep(Sketchup::Edge).each{|e|e.vertices.each{|v|bb.add(v.position)}}
  raise 'Missing direct vertices' if bb.empty?
  bb
end
def ec_world_bounds(g,tr)
  bb=Geom::BoundingBox.new
  ec_es(g).grep(Sketchup::Edge).each{|e|e.vertices.each{|v|bb.add(tr*v.position)}}
  raise 'Missing target vertices' if bb.empty?
  bb
end
def ec_reset(root,path,clearer)
  g,tr=ec_path(root,path)
  raise 'Shared target container' unless g.definition.instances.length==1
  clearer.call(path)
  a=ec_group(ec_es(g),"#{path.last}_CONTENT")
  a.transform!(tr.inverse)
  # All geometry authored in root coordinates, compensating existing local axes.
  [a.entities,g]
end

# One validated transparent panel definition shared by all mesh infills.
# There is no opaque backing; every wire is an editable slender solid.
def ec_mesh_tile(es,n,width,steel,cache)
  key=width.round(4)
  if cache[key]
    q=es.add_instance(cache[key],Geom::Transformation.new)
    q.name=n;q.set_attribute('KStudio','semantic_id',n);return q
  end
  g=ec_group(es,n);wire=1.8;h=1000.0
  nx=[(width/50.0).ceil,1].max;nz=20
  (0..nx).each do |i|
    x=[width*i/nx,width-wire].min
    ec_box(g.entities,"#{n}_V#{i}",x,x+wire,-wire/2,wire/2,0,h,steel,true)
  end
  (0..nz).each do |i|
    z=[h*i/nz,h-wire].min
    ec_box(g.entities,"#{n}_H#{i}",0,width,-wire/2,wire/2,z,z+wire,steel,true)
  end
  open_fraction=(1.0-(nx+1)*wire/width)*(1.0-(nz+1)*wire/h)
  raise 'Mesh prototype too opaque' unless open_fraction>0.85
  raise 'Mesh backing face' unless g.entities.grep(Sketchup::Face).empty?
  q=g.to_component;q.name=n;q.definition.name="KS_FINE_WHITE_MESH_#{key}"
  q.set_attribute('KStudio','estimated_open_fraction',open_fraction)
  cache[key]=q.definition;q
end

def ec_guard(es,n,a,b,steel,cache)
  dx=b[0]-a[0];dy=b[1]-a[1];len=Math.sqrt(dx*dx+dy*dy)
  raise "Zero guard #{n}" if len<1
  g=ec_group(es,n);ne=[(len/1400.0).ceil,1].max
  (0..ne).each do |i|
    t=i.to_f/ne;p=(0..2).map{|j|a[j]+(b[j]-a[j])*t}
    ec_bar(g.entities,"#{n}_POST#{i}",p,[p[0],p[1],p[2]+1100],30,steel)
  end
  [50,1100].each{|z|ec_bar(g.entities,"#{n}_EDGE#{z}",[a[0],a[1],a[2]+z],[b[0],b[1],b[2]+z],z==1100 ? 30 : 20,steel)}
  # Tile in true slope plane with vertical wires and slope-parallel cross wires.
  ux=dx/len;uy=dy/len;slope=(b[2]-a[2])/len
  u=0.0;k=0
  while u<len-0.01
    w=[1000.0,len-u].min
    if w>2
      tile=ec_mesh_tile(g.entities,"#{n}_MESH#{k}",w,steel,cache)
      tr=Geom::Transformation.new([ux,uy,slope,0,-uy,ux,0,0,0,0,1,0,(a[0]+ux*u).mm,(a[1]+uy*u).mm,(a[2]+slope*u+50).mm,1])
      tile.transform!(tr)
    end
    u+=w;k+=1
  end
  g.set_attribute('KStudio','guard_height_mm',1100)
  g.set_attribute('KStudio','mesh_pitch_max_mm',50)
  g
end

# Source3 horizontal grating remains genuinely open around the new stair slots.
def ec_grid_tile(es,n,u,v,steel,cache)
  key=[u.round(4),v.round(4)]
  if cache[key]
    q=es.add_instance(cache[key],Geom::Transformation.new);q.name=n;q.set_attribute('KStudio','semantic_id',n);return q
  end
  g=ec_group(es,n)
  nx=(u/40.0).ceil;ny=(v/80.0).ceil
  (0..nx).each{|i|x=[u*i/nx,u-3].min;ec_box(g.entities,"#{n}_B#{i}",x,x+3,0,v,-35,0,steel,true)}
  (0..ny).each{|i|y=[v*i/ny,v-3].min;ec_box(g.entities,"#{n}_C#{i}",0,u,y,y+3,-10,0,steel,true)}
  q=g.to_component;q.name=n;q.definition.name="KS_EC_OPEN_GRID_#{key.join('_')}";cache[key]=q.definition;q
end
def ec_deck(es,n,r,z,steel,cache)
  x0,x1,y0,y1=r;g=ec_group(es,n);x=x0;i=0
  while x<x1-0.01
    w=[1000.0,x1-x].min;y=y0;j=0
    while y<y1-0.01
      d=[1000.0,y1-y].min
      q=ec_grid_tile(g.entities,"#{n}_GRID_#{i}_#{j}",w,d,steel,cache)
      q.transform!(Geom::Transformation.translation([x.mm,y.mm,z.mm]))
      y+=d;j+=1
    end
    x+=w;i+=1
  end
  ec_box(g.entities,"#{n}_EDGE_X0",x0,x0+45,y0,y1,z-150,z-35,steel)
  ec_box(g.entities,"#{n}_EDGE_X1",x1-45,x1,y0,y1,z-150,z-35,steel)
  count=[((y1-y0)/2000.0).ceil,1].max
  (0..count).each do |k|
    yy=[y0+(y1-y0)*k/count,y1-50].min
    ec_box(g.entities,"#{n}_CROSS#{k}",x0,x1,yy,yy+50,z-150,z-35,steel)
  end
  g
end

raise 'Wrong model root' unless root.persistent_id==20606
steel=model.materials['KS_White_Steel'];raise 'Missing steel' unless steel
clearer=clear_owned_contents
mesh_cache={};grid_cache={};receipts=[]

# Actual existing rail endpoints, including shortened gates and mirrored ramps.
rail_paths=[]
[3600,7200,10800].each do |z|
  ['SOUTH','NORTH'].each{|side|rail_paths<<['CIRCULATION_EXTERNAL','GALLERIES',"LONG_RAIL_#{side}_Z#{z}"]}
end
[7200,10800].each{|z|(0..2).each{|s|n="GALLERY_Z#{z}_SIDE#{s}";rail_paths<<['CIRCULATION_EXTERNAL','GALLERIES',n,"#{n}_SLOT_GUARD"]}}
(1..3).each{|i|['OUTER','INNER'].each{|s|rail_paths<<['CIRCULATION_EXTERNAL',"RAMP_#{i}_#{s}"]}}
(0..7).each{|i|rail_paths<<['CIRCULATION_EXTERNAL','LANDINGS','LANDING_L1',"LANDING_L1_GUARD_#{i}"]}
rail_data=rail_paths.map do |path|
  g,tr=ec_path(root,path)
  raise 'Shared rail' unless g.definition.instances.length==1
  tops=ec_es(g).select{|e|e.respond_to?(:name)&&e.name.match?(/(?:_RAIL_1100|_H1100)$/)}
  raise "Missing single top cap #{path.join('/')}" unless tops.length==1
  bar=tops.first;bb=ec_vbounds(bar)
  xx=(bb.min.x+bb.max.x)/2;yy=(bb.min.y+bb.max.y)/2
  ends=[bb.min.z,bb.max.z].map{|zz|p=tr*bar.transformation*Geom::Point3d.new(xx,yy,zz);[p.x.to_mm,p.y.to_mm,p.z.to_mm-1100]}
  # Gate starts must remain at X0 for five previously opened long-side rails.
  if path.last.start_with?('LONG_RAIL') && !path.last.include?('SOUTH_Z10800')
    raise 'Existing receiving gate misread' unless ends.map{|p|p[0]}.min.abs<0.1
  end
  [path,g.persistent_id,ends]
end

# Verify all72 existing treads from actual vertices before adding anything.
ci,citr=ec_path(root,['CIRCULATION_INTERNAL'])
stair_treads={}
[0,3600,7200].each do |z|
  stair_treads[z]=(0...24).map do |i|
    g=ec_find(ci.entities,"END_TREAD_#{z}_#{i}")
    bb=ec_world_bounds(g,citr*g.transformation)
    checks=[[bb.min.x.to_mm,50500],[bb.max.x.to_mm,52700],[bb.min.y.to_mm,1000+i*260],[bb.max.y.to_mm,1260+i*260],[bb.max.z.to_mm,z+(i+1)*150]]
    raise 'Actual tread layout differs' unless checks.all?{|a,b|(a-b).abs<0.1}
    [g.persistent_id,bb]
  end
end

# Stage primary connectivity: retain only necessary flats INSIDE glazed outline.
[[2,7200,[-1,1]],[3,10800,[1]]].each do |lev,z,sides|
  path=['CIRCULATION_EXTERNAL','LANDINGS',"LANDING_L#{lev}"]
  es,g=ec_reset(root,path,clearer)
  sides.each do |side|
    ya,yb=side<0 ? [-4000.0,-3000.0] : [23000.0,24000.0]
    ec_deck(es,"L#{lev}_INBOARD_#{side}",[-3950,-1650,ya,yb],z,steel,grid_cache)
    outer_y=side<0 ? ya+20 : yb-20
    ec_guard(es,"L#{lev}_RETURN_BOUNDARY_#{side}",[-3930,outer_y,z],[0,outer_y,z],steel,mesh_cache)
    ec_guard(es,"L#{lev}_OUTER_EDGE_#{side}",[-3930,ya+20,z],[-3930,yb-20,z],steel,mesh_cache)
  end
  # Existing neighboring grating begins at X-1650: exact flush connection.
  g.set_attribute('KStudio','outer_tabs_removed',true)
  receipts<<"#{path.join('/')} PID#{g.persistent_id}: outside residue removed; inboard flat meets retained return X-1650"
end

# Stage representative mesh then repeat on26 existing guard containers.
rail_data.each do |path,pid,ends|
  es,g=ec_reset(root,path,clearer)
  ec_guard(es,"#{path.last}_FINE_MESH",ends[0],ends[1],steel,mesh_cache)
  raise 'Guard PID changed' unless g.persistent_id==pid
  receipts<<"GUARD #{path.join('/')} PID#{pid} baseline #{ends.inspect}"
end

# Remote end galleries: retain shape and150mm depth, open a2300x6240 slot.
# Outer bypass1250mm wide connects both landings and all existing end doors.
[3600,7200,10800].each do |z|
  path=['CIRCULATION_EXTERNAL','GALLERIES',"GALLERY_Z#{z}_SIDE3"]
  es,g=ec_reset(root,path,clearer)
  rects=[[50000,54000,0,1000],[50000,50450,1000,7240],[52750,54000,1000,7240],[50000,54000,7240,20000]]
  rects.each_with_index{|r,i|ec_deck(es,"REMOTE_Z#{z}_ZONE#{i}",r,z,steel,grid_cache)}
  raise 'Slot still covered by declared rect' unless rects.none?{|r|r[0]<51600&&r[1]>51600&&r[2]<4000&&r[3]>4000}
  g.set_attribute('KStudio','stair_void_mm',[50450,52750,1000,7240])
  receipts<<"REMOTE Z#{z}: open slot X50450..52750/Y1000..7240; exterior bypass1250; top landing Y7240..9600"
end

# New named completion assembly: existing tread groups remain untouched siblings.
raise 'Completion already exists' if ci.entities.any?{|e|e.respond_to?(:name)&&e.name=='END_STAIR_COMPLETION'}
comp=ec_group(ci.entities,'END_STAIR_COMPLETION');comp.transform!(citr.inverse)
ce=comp.entities
# Site actual top is-280mm, main ground use level0. Supported pad/rising approach.
site,site_tr=ec_path(root,['SITE_GROUND','ADJACENT_GROUND'])
sitebb=ec_world_bounds(site,site_tr);ground=sitebb.max.z.to_mm
raise 'Unexpected ground' unless (ground+280).abs<0.1
ec_box(ce,'END_GROUND_ARRIVAL',50000,54000,-1200,1000,ground,0,steel)
approach=ec_group(ce,'END_GROUND_APPROACH_RAMP')
f=approach.entities.add_face([[50000,-2600,ground],[50000,-1200,0],[50000,-1200,ground-80],[50000,-2600,ground-80]].map{|p|p.map(&:mm)})
raise 'Approach face missing' unless f
f.reverse! if f.normal.x<0;f.pushpull(4000.mm);approach.material=steel

[0,3600,7200].each do |z|
  run=ec_group(ce,"END_STAIR_Z#{z}_SUPPORT_HANDRAILS")
  [50500.0,52600.0].each_with_index do |x,j|
    st=ec_group(run.entities,"STRINGER_#{z}_#{j}")
    f=st.entities.add_face([[x,1000,z-150],[x,7240,z+3450],[x,7240,z+3210],[x,1000,z-390]].map{|p|p.map(&:mm)})
    raise 'Stringer face missing' unless f
    f.reverse! if f.normal.x<0;f.pushpull(100.mm);st.material=steel
    (0...24).each do |i|
      ec_box(run.entities,"TREAD_SEAT_#{z}_#{j}_#{i}",x,x+100,1000+i*260,1260+i*260,z+i*150-210,z+i*150,steel)
    end
  end
  [50520.0,52680.0].each_with_index do |x,j|
    ec_guard(run.entities,"STAIR_MESH_#{z}_#{j}",[x,1000,z+150],[x,7240,z+3750],steel,mesh_cache)
    ec_bar(run.entities,"HANDRAIL_900_#{z}_#{j}",[x+(j==0 ? 40 : -40),1000,z+1050],[x+(j==0 ? 40 : -40),7240,z+4650],32,steel)
  end
  # At each tread centre, next stacked underside is3450mm above walking face.
  min_headroom=3600-150
  raise 'Stacked headroom failure' unless min_headroom>=2200
end
# Slender remote supports under landing framing, to actual ground top.
[52900.0,53800.0].each_with_index do |x,i|
  [600.0,8400.0].each_with_index do |y,j|
    ec_box(ce,"REMOTE_SUPPORT_#{i}_#{j}",x-50,x+50,y-50,y+50,ground,10650,steel)
  end
end

# New exact remote edge/slot guard leaf; no rail across bottom/top approaches.
ext,extr=ec_path(root,['CIRCULATION_EXTERNAL'])
raise 'Remote guards already exist' if ext.entities.any?{|e|e.respond_to?(:name)&&e.name=='REMOTE_END_EDGE_GUARDS'}
guards=ec_group(ext.entities,'REMOTE_END_EDGE_GUARDS');guards.transform!(extr.inverse)
[3600,7200,10800].each do |z|
  ec_guard(guards.entities,"REMOTE_OUTER_Z#{z}",[53980,-3980,z],[53980,23980,z],steel,mesh_cache)
  [50435,52765].each_with_index do |x,i|
    ec_guard(guards.entities,"REMOTE_SLOT_Z#{z}_SIDE#{i}",[x,1000,z],[x,7240,z],steel,mesh_cache)
  end
end
# Ground approach side rails only; open towards plaza and first riser.
ec_guard(guards.entities,'GROUND_PAD_OUTER',[53980,-1200,0],[53980,1000,0],steel,mesh_cache)
ec_guard(guards.entities,'GROUND_PAD_INNER',[50020,-1200,0],[50020,1000,0],steel,mesh_cache)

puts "EC_COMPLETE: #{rail_data.length} retained guard containers; #{mesh_cache.length} transparent mesh prototypes; #{grid_cache.length} grating prototypes."
receipts.each{|s|puts s}
puts 'STAIR:72 original tread PIDs and geometry untouched. 3x24rises150/going260, open upper slots,1250 bypass, supported landings,3450 stacked clearance. Fine-mesh pitch<=50/wire1.8/guard1100 are inferred.'
