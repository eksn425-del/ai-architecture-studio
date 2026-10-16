# Source1/2: unchanged white buffer perimeter, concave unequal timber roof.
# Source3/4: floor-specific glazing below retained concrete headers.
# Source5/7/8: occupied floors, partial mezzanine, room-front recesses and vents.
# Source6: distinct retained frame, timber addition and light greenhouse skin.
# kstudio.custom_owned_ruby: compatible licensed SAIE wall methods are root-only;
# they cannot author these exact new nested room leaves without reparenting.
# Transparent frames/covers also do not fit SAIE solid wall/opening geometry.
# ADAI disabled. All new detail dimensions estimated. No retained solid edited.

def ff_es(g)
  g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities
end
def ff_find(es,n)
  q=es.select{|e|e.respond_to?(:name)&&e.name==n}
  raise "Missing/duplicate #{n}" unless q.length==1
  q.first
end
def ff_path(root,path)
  g=root;tr=Geom::Transformation.new
  path.each{|n|g=ff_find(ff_es(g),n);tr=tr*g.transformation}
  [g,tr]
end
def ff_group(es,n)
  g=es.add_group;g.name=n;g.set_attribute('KStudio','semantic_id',n);g
end
def ff_content(root,path,clearer)
  g,tr=ff_path(root,path)
  raise 'Shared target' unless g.definition.instances.length==1
  pid=g.persistent_id;clearer.call(path)
  c=ff_group(ff_es(g),"#{path.last}_CONTENT");c.transform!(tr.inverse)
  raise 'Target PID changed' unless g.persistent_id==pid
  [c.entities,g]
end
def ff_new(root,path)
  p,tr=ff_path(root,path[0...-1])
  raise 'Creation leaf exists' if ff_es(p).any?{|e|e.respond_to?(:name)&&e.name==path.last}
  g=ff_group(ff_es(p),path.last);g.transform!(tr.inverse);g
end
def ff_box(es,n,x0,x1,y0,y1,z0,z1,mat)
  raise "Invalid box #{n}" unless x1>x0 && y1>y0 && z1>z0
  g=ff_group(es,n)
  f=g.entities.add_face([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0]].map{|p|p.map(&:mm)})
  raise 'Box missing' unless f
  f.reverse! if f.normal.z<0;f.pushpull((z1-z0).mm);g.material=mat;g
end
def ff_glass(es,n,x0,x1,y,z0,z1,mat)
  return if x1-x0<1 || z1-z0<1
  g=ff_group(es,n)
  f=g.entities.add_face([[x0,y,z0],[x1,y,z0],[x1,y,z1],[x0,y,z1]].map{|p|p.map(&:mm)})
  raise 'Glass missing' unless f
  f.material=mat;f.back_material=mat;g
end
def ff_bar(es,n,a,b,w,mat)
  v=Geom::Vector3d.new(*(0..2).map{|i|(b[i]-a[i]).mm})
  raise 'Zero bar' if v.length.to_mm<1
  g=ff_box(es,n,-w/2.0,w/2.0,-w/2.0,w/2.0,0,v.length.to_mm,mat)
  zz=v.normalize;ref=zz.parallel?(Z_AXIS) ? X_AXIS : Z_AXIS
  xx=ref.cross(zz).normalize;yy=zz.cross(xx).normalize
  g.transform!(Geom::Transformation.axes(Geom::Point3d.new(*a.map(&:mm)),xx,yy,zz));g
end
def ff_floor(floors,x,y,z)
  pt=Geom::Point3d.new(x.mm,y.mm,z.mm)
  ff_es(floors).any? do |g|
    next false unless g.is_a?(Sketchup::Group)||g.is_a?(Sketchup::ComponentInstance)
    p=g.transformation.inverse*pt
    ff_es(g).grep(Sketchup::Face).any? do |f|
      next false unless f.vertices.all?{|v|(v.position.z-p.z).abs<0.01.mm}
      [Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(p))
    end
  end
end
def ff_instance(es,n,key,cache)
  if cache[key]
    q=es.add_instance(cache[key],Geom::Transformation.new);q.name=n
    q.set_attribute('KStudio','semantic_id',n);return q
  end
  g=ff_group(es,n);yield(g.entities)
  q=g.to_component;q.name=n;q.definition.name="KS_FINISH_#{key}"
  cache[key]=q.definition;q
end
def ff_window_frame(es,n,w,h,steel,cache)
  ff_instance(es,n,"FRAME_#{w.round(2)}_#{h.round(2)}",cache) do |ee|
    ff_box(ee,'LEFT',0,40,-30,30,0,h,steel)
    ff_box(ee,'RIGHT',w-40,w,-30,30,0,h,steel)
    ff_box(ee,'SILL',40,w-40,-30,30,0,40,steel)
    ff_box(ee,'HEAD',40,w-40,-30,30,h-40,h,steel)
    ff_box(ee,'TRANSOM',40,w-40,-25,25,h-720,h-680,steel) if h>2000
  end
end
def ff_leaf(es,n,x,y,base,depth,steel,glass)
  # Door leaf is parked90degrees INWARD, never in the exterior gallery.
  ya,yb=[y,y+depth].minmax;g=ff_group(es,n)
  ff_box(g.entities,'HINGE',x-12,x+12,ya,ya+25,base,base+2400,steel)
  ff_box(g.entities,'FREE_STILE',x-12,x+12,yb-25,yb,base,base+2400,steel)
  ff_box(g.entities,'LEAF_HEAD',x-12,x+12,ya,yb,base+2375,base+2400,steel)
  ff_box(g.entities,'LEAF_BASE',x-12,x+12,ya,yb,base,base+25,steel)
  f=g.entities.add_face([[x,ya+25,base+25],[x,yb-25,base+25],[x,yb-25,base+2375],[x,ya+25,base+2375]].map{|p|p.map(&:mm)})
  raise 'Door leaf missing' unless f
  f.material=glass;f.back_material=glass;g
end
def ff_portal(es,n,x0,x1,y,base,inside,steel,glass)
  g=ff_group(es,n);a=(x0+x1)/2.0-800;b=a+1600
  ff_box(g.entities,'JAMB_L',a-40,a,y-30,y+30,base,base+2400,steel)
  ff_box(g.entities,'JAMB_R',b,b+40,y-30,y+30,base,base+2400,steel)
  ff_box(g.entities,'HEADER',x0,x1,y-30,y+30,base+2400,base+2440,steel)
  ff_glass(g.entities,'SIDELIGHT_L',x0,a-40,y,base+40,base+2400,glass)
  ff_glass(g.entities,'SIDELIGHT_R',b+40,x1,y,base+40,base+2400,glass)
  ff_box(g.entities,'SIDE_SILL_L',x0,a-40,y-25,y+25,base,base+40,steel) if a-40-x0>1
  ff_box(g.entities,'SIDE_SILL_R',b+40,x1,y-25,y+25,base,base+40,steel) if x1-b-40>1
  ff_leaf(g.entities,'LEFT_OPEN_INWARD',a,y,base,inside*800,steel,glass)
  ff_leaf(g.entities,'RIGHT_OPEN_INWARD',b,y,base,inside*800,steel,glass)
  # Real aperture evidence: no direct or nested glass plane covers its centre.
  g.set_attribute('KStudio','clear_portal_mm',[a,b,y,base,base+2400])
  g.set_attribute('KStudio','threshold','no sill or backing glass across aperture')
  [a,b,g]
end
def ff_solid_strip(es,n,x0,x1,y0,y1,z0,z1,mat)
  ff_box(es,n,x0,x1,[y0,y1].min,[y0,y1].max,z0,z1,mat)
end

raise 'Wrong root' unless root.persistent_id==20606
steel=model.materials['KS_White_Steel'];glass=model.materials['KS_Clear_Glass']
wallmat=model.materials['KS_Concrete_Light'];rubber=model.materials['KS_Core']
raise 'Existing materials missing' unless steel&&glass&&wallmat&&rubber
covermat=model.materials.add('KS_Buffer_Translucent_R14');covermat.color='#e3eeee';covermat.alpha=0.42
floors=ff_find(root.entities,'FLOORS');structure=ff_find(root.entities,'STRUCTURE_EXISTING')
raise 'Unexpected floor axes' unless floors.transformation.identity? && structure.transformation.identity?
clearer=clear_owned_contents;cache={};doors=[];room_doors=[];targets=[]
frames=ff_new(root,['ENVELOPE_OUTER','INNER_GLAZING','LOWER_LONG_SIDE_FRAMING'])

# Stage1: actual floor and concrete-header checks BEFORE representative modules.
[0,1].each do |side|
  y=side==0 ? 0.0 : 20000.0;inside=side==0 ? 1 : -1
  [0,3600,7200].each do |base|
    longbeam=ff_find(structure.entities,"LONG_BEAM_Z#{base+3600}_Y#{side==0 ? 0 : 2}")
    raise 'Header elevation mismatch' unless (longbeam.bounds.min.z.to_mm-(base+3120)).abs<0.1
  end
  (0...20).each do |i|
    path=['ENVELOPE_OUTER','INNER_GLAZING',"INNER_GLASS_#{side}_#{i}"]
    g,tr=ff_path(root,path)
    raise 'Unexpected original glass' unless g.definition.instances.length==1 && tr.identity?
    targets<<[path,g.persistent_id]
  end
end

# Stages2/3/4: representative level window, then actual floor-specific variants.
targets.each do |path,pid|
  side,i=path.last.split('_').last(2).map(&:to_i)
  y=side==0 ? 0.0 : 20000.0;inside=side==0 ? 1 : -1
  lo=i*2500.0;hi=lo+2500
  x0=lo+(i.even? ? 180 : 30);x1=hi-(i.odd? ? 180 : 30)
  es,g=ff_content(root,path,clearer)
  [0,3600,7200].each do |base|
    # Existing ground service core and existing green panel remain the enclosure.
    next if side==1 && base==0 && i>=18
    next if side==1 && base==7200 && [12,13].include?(i)
    top=base+3120;floor_inside=ff_floor(floors,(lo+hi)/2,y+inside*100,base)
    want_door=i.odd? && floor_inside
    level=ff_group(es,"LEVEL_#{base}_#{want_door ? 'RECESSED_ENTRY' : 'WINDOW'}")
    if want_door
      left=x0+25;right=x1-25;recess=600;yy=y+inside*recess
      a,b,portal=ff_portal(level.entities,'DOOR',left+60,right-60,yy,base,inside,steel,glass)
      # Source-constrained solid returns/small overhead soffit, open along approach.
      ff_solid_strip(level.entities,'RECESS_RETURN_L',left,left+60,y,yy,base,base+2440,wallmat)
      ff_solid_strip(level.entities,'RECESS_RETURN_R',right-60,right,y,yy,base,base+2440,wallmat)
      ff_solid_strip(level.entities,'RECESS_HEAD',left,right,y,yy,base+2400,base+2480,steel)
      ff_glass(level.entities,'HEADLIGHT',x0+40,x1-40,y,base+2480,top-40,glass)
      ff_box(level.entities,'HEAD_FRAME',x0,x1,y-30,y+30,top-40,top,steel)
      [left,right-40].each_with_index{|x,k|ff_box(level.entities,"OUTER_STILE_#{k}",x,x+40,y-30,y+30,base,top,steel)}
      ff_box(level.entities,'FIT_TRIM_L',x0,left,y-30,y+30,base,top,steel)
      ff_box(level.entities,'FIT_TRIM_R',right,x1,y-30,y+30,base,top,steel)
      # Portal centre and both approaches sit on unchanged actual floor faces.
      [y+inside*100,yy+inside*100,yy+inside*1000].each do |py|
        raise 'Door over missing slab' unless ff_floor(floors,(a+b)/2,py,base)
      end
      doors<<[path.last,base,a,b,yy]
    else
      # White source-observed opaque lower band, narrow upper opening subdivision.
      sill=base+(base==0 ? 450 : 600)
      ff_box(level.entities,'OPAQUE_BASE',x0,x1,y-60,y+60,base,sill,wallmat)
      ff_glass(level.entities,'LOWER_FIXED',x0+40,x1-40,y,sill+40,base+2400,glass)
      ff_glass(level.entities,'UPPER_FIXED',x0+40,x1-40,y,base+2440,top-40,glass)
      q=ff_window_frame(frames.entities,"FRAME_#{side}_#{i}_#{base}",x1-x0,top-sill,steel,cache)
      q.transform!(Geom::Transformation.translation([x0.mm,y.mm,sill.mm]))
    end
    level.set_attribute('KStudio','occupied_floor',floor_inside)
  end
  raise 'Container PID changed' unless g.persistent_id==pid
end
raise 'Insufficient long-side actual portals' unless doors.length>=40

# Room-front volumes from source7: existing eighteen transverse partitions stay.
# Two sets of ten5m rooms; all front landings use actual Y>=11000 occupied slab.
room=ff_new(root,['INTERIOR','ROOM_FRONT_COMPLETION'])
[3600,7200].each do |base|
  (1...10).each do |i|
    part=ff_find(root.entities,"PARTITION_Z#{base}_B#{i}")
    bb=part.bounds
    raise 'Divider not at expected front' unless (bb.min.y.to_mm-12000).abs<0.1 && (bb.max.y.to_mm-20000).abs<0.1
  end
  (0...10).each do |i|
    lo=i*5000.0+60;hi=(i+1)*5000.0-60;front=12000.0;inset=12800.0
    g=ff_group(room.entities,"ROOM_Z#{base}_BAY#{i}_RECESSED_FRONT")
    a=i*5000+2700.0;b=i*5000+4500.0
    # Real front wall segments with a return to the door behind; no wall at portal.
    [[lo,a],[b,hi]].each_with_index do |ab,k|
      ff_box(g.entities,"FRONT_OPAQUE_#{k}",ab[0],ab[1],11940,12060,base,base+2400,wallmat)
      ff_glass(g.entities,"FRONT_CLERESTORY_#{k}",ab[0],ab[1],front,base+2440,base+3060,glass)
      ff_box(g.entities,"CLERESTORY_HEAD_#{k}",ab[0],ab[1],11970,12030,base+3060,base+3100,steel)
      ff_box(g.entities,"CLERESTORY_SILL_#{k}",ab[0],ab[1],11970,12030,base+2400,base+2440,steel)
    end
    ff_box(g.entities,'RETURN_LEFT',a-60,a+60,front,inset,base,base+3100,wallmat)
    ff_box(g.entities,'RETURN_RIGHT',b-60,b+60,front,inset,base,base+3100,wallmat)
    aa,bb,portal=ff_portal(g.entities,'INSET_ROOM_DOOR',a+60,b-60,inset,base,1,steel,glass)
    ff_box(g.entities,'DOOR_HEAD_PANEL',a+60,b-60,inset-60,inset+60,base+2440,base+3100,wallmat)
    ff_box(g.entities,'INSET_SOFFIT',a-60,b+60,front,inset,base+3100,base+3140,steel)
    [11600,12400,12900,13800].each do |py|
      raise 'Room door approach has no retained slab' unless ff_floor(floors,(aa+bb)/2,py,base)
    end
    room_doors<<[base,i,aa,bb,inset]
  end
end

# Separate light buffer roof: all geometry remains inside original100mm depth.
def ff_roof_pane(es,n,u0,u1,v0,v1,z0,z1,mat,axes,cache)
  key="PANE_#{(u1-u0).round(3)}_#{(v1-v0).round(3)}_#{(z1-z0).round(3)}_#{mat.name}"
  q=ff_instance(es,n,key,cache) do |ee|
    w=u1-u0;d=v1-v0;rise=z1-z0
    g=ff_group(ee,'EDITABLE_COVER')
    f=g.entities.add_face([[0,0,0],[w,0,0],[w,d,rise],[0,d,rise]].map{|p|p.map(&:mm)})
    raise 'Cover missing' unless f
    f.reverse! if f.normal.z<0;f.pushpull(6.mm);g.material=mat
  end
  # Local UV directions are orthogonal root XY; varying slope authored in pane.
  origin=axes[0].map.with_index{|x,j|x+axes[1][j]*u0+axes[2][j]*v0};origin[2]=z0
  tr=Geom::Transformation.axes(Geom::Point3d.new(*origin.map(&:mm)),Geom::Vector3d.new(*axes[1]),Geom::Vector3d.new(*axes[2]),Z_AXIS)
  q.transform!(tr);q
end
canopy_specs=[[-4000,0,58000,4000,[1,0,0],[0,-1,0]],[-4000,20000,58000,4000,[1,0,0],[0,1,0]],[0,0,20000,4000,[0,1,0],[-1,0,0]],[50000,0,20000,4000,[0,1,0],[1,0,0]]]
canopy_checks=[]
canopy_specs.each_with_index do |sp,k|
  ox,oy,length,depth,udir,vdir=sp
  path=['ENVELOPE_OUTER','BUFFER_CANOPIES',"CANOPY_#{k}"]
  old,tr=ff_path(root,path);oldbb=old.bounds
  es,g=ff_content(root,path,clearer);axes=[[ox.to_f,oy.to_f,0],udir,vdir]
  # Local assembly parent for frame solids, mapped without altering target axes.
  local=ff_group(es,"CANOPY_#{k}_LIGHT_FRAME")
  local.transform!(Geom::Transformation.axes(Geom::Point3d.new(ox.mm,oy.mm,0),Geom::Vector3d.new(*udir),Geom::Vector3d.new(*vdir),Z_AXIS))
  le=local.entities;module_width=k<2 ? 2900.0 : 2500.0
  count=(length/module_width).ceil
  ff_box(le,'INNER_EDGE_LEDGER',0,length,0,80,13400,13500,steel)
  ff_box(le,'OUTER_EDGE_BEAM',0,length,3920,4000,13400,13500,steel)
  ff_box(le,'START_TRIM',0,40,80,3920,13400,13500,steel)
  ff_box(le,'END_TRIM',length-40,length,80,3920,13400,13500,steel)
  [1000,2000,3000].each{|v|ff_box(le,"PURLIN_#{v}",0,length,v-20,v+20,13400,13465,steel)}
  # Opaque inner flashing and outer eave cap are distinct from translucent panes.
  ff_box(le,'INNER_FLASHING',0,length,80,250,13490,13500,steel)
  ff_box(le,'OUTER_EAVE_CAP',0,length,3750,3920,13490,13500,steel)
  ff_box(le,'DRAIN_CHANNEL_BASE',0,length,3800,3900,13412,13418,steel)
  ff_box(le,'DRIP_EDGE',0,length,3990,4000,13400,13435,steel)
  (0..count).each do |i|
    u=[i*module_width,length-60].min
    ff_box(le,"RAFTER_#{i}",u,u+60,80,3920,13400,13490,steel)
    ff_box(le,"INNER_SUPPORT_CLIP_#{i}",u,u+60,0,110,13400,13500,steel)
  end
  count.times do |i|
    a=i*module_width+60;b=[(i+1)*module_width-15,length-40].min
    raise 'Narrow canopy module' unless b-a>100
    # Inner main panel; no opaque slab underneath.
    ff_roof_pane(es,"CANOPY_#{k}_MAIN_#{i}",a,b,250,2850,13490,13490,covermat,axes,cache)
    # Shallow outward-sloping glazed section, distinct from flat main cover.
    # V grows outwards: fall72mm over900mm; retains actual canopy envelope.
    if i%4==1
      # Three slightly raised glazed louvers leave real unbacked ventilation gaps.
      3.times do |j|
        v=2850+j*300
        ff_roof_pane(es,"CANOPY_#{k}_VENT_#{i}_#{j}",a,b,v,v+260,13488-j*24,13467-j*24,glass,axes,cache)
        [a+80,b-80].each_with_index do |u,h|
          point=axes[0].each_with_index.map{|x,d|x+udir[d]*u+vdir[d]*(v+220)}
          ff_bar(es,"CANOPY_#{k}_VENT_STAY_#{i}_#{j}_#{h}",[point[0],point[1],13420],[point[0],point[1],13473-j*24],12,steel)
        end
      end
    else
      ff_roof_pane(es,"CANOPY_#{k}_SLOPED_#{i}",a,b,2850,3750,13490,13418,glass,axes,cache)
    end
    # Root-mapped glazing pressure bars and end joints.
    ff_box(le,"PANEL_CLAMP_#{i}",a,a+20,250,3750,13480,13500,steel)
    ff_box(le,"PANEL_END_CLAMP_#{i}",b-20,b,250,3750,13480,13500,steel)
  end
  # Bounds are checked in parent coordinates against the original leaf exactly.
  bb=g.bounds
  [0,1,2].each do |d|
    raise 'Canopy exceeded original outer bounds' if bb.min[d]<oldbb.min[d]-0.1.mm || bb.max[d]>oldbb.max[d]+0.1.mm
  end
  raise 'Cover still contains opaque backing slab' unless ff_es(g).grep(Sketchup::Face).empty?
  canopy_checks<<[g.persistent_id,k,count]
end

# Finish: supplementary hall joint leaf; existing hall bays/doors remain immutable.
joints=ff_new(root,['ENVELOPE_OUTER','HALL_WINDOW_JOINTS'])
[['HALL_LONG_SOUTH_ADDITION',0.0,-1],['HALL_LONG_NORTH_ADDITION',20000.0,1]].each do |n,y,out|
  hall,tr=ff_path(root,['ENVELOPE_OUTER',n]);top=hall.bounds.max.z.to_mm
  # Butt-joint trims above the existing open door height; never cross portals.
  (1...20).each do |i|
    x=i*2500.0
    ff_box(joints.entities,"#{n}_JOINT_#{i}",x-12,x+12,y-24,y+24,13250,top-20,steel)
  end
  ya,yb=[y+out*30,y+out*100].minmax
  ff_box(joints.entities,"#{n}_HEAD_FLASHING",55,49945,ya,yb,top-15,top,steel)
end

# Final native no-backing/open-portal check: ray-sized line tests at each entry.
# Direct face classification uses all newly created leaf geometry recursively.
def ff_blocked_by_face(es,point,tr=Geom::Transformation.new)
  es.any? do |e|
    if e.is_a?(Sketchup::Face)
      p=tr.inverse*point
      plane=e.plane;dist=plane[0]*p.x+plane[1]*p.y+plane[2]*p.z+plane[3]
      next false if dist.abs>0.02.mm
      [Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge].include?(e.classify_point(p))
    elsif e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)
      ff_blocked_by_face(ff_es(e),point,tr*e.transformation)
    else
      false
    end
  end
end
doors.each do |name,base,a,b,y|
  leaf,tr=ff_path(root,['ENVELOPE_OUTER','INNER_GLAZING',name])
  [900,1900].each do |h|
    p=Geom::Point3d.new(((a+b)/2).mm,y.mm,(base+h).mm)
    raise 'Portal backed by face' if ff_blocked_by_face(ff_es(leaf),p,tr)
  end
end
puts "LONG_FACADE_FINISH: #{doors.length} floor-supported recessed exterior portals, #{room_doors.length} recessed room entrances,#{cache.length} reusable prototypes."
puts 'Native floor point checks passed at all approaches; no sill or backing glass across portal centres. Existing40glass target containers retained.'
puts "CANOPIES: #{canopy_checks.inspect}; slim frame/open translucent infill/shallow glazed outer fall/vent louvers/pressure bars/eave/drip/flashing; original envelopes retained."
puts "DOOR_SCHEDULE: #{doors.inspect}"
puts "ROOM_DOOR_SCHEDULE: #{room_doors.inspect}"
