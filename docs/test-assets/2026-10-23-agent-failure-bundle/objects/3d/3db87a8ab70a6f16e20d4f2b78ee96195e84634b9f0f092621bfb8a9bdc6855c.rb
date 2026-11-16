# encoding: UTF-8
# Approved local correction. Keep row/container PIDs, rear facade, floors and roofs.
# Pass 1 proves the source-visible 6/5 grid in TOWER_L16 before replication.
pass = 'sample'
def ng(p,n)
  a=p.entities.grep(Sketchup::Group).select { |g| g.name==n }
  raise "Expected unique #{n}" unless a.length==1
  a.first
end
def child(p,n)
  raise "Duplicate #{n}" if p.entities.grep(Sketchup::Group).any? { |g| g.name==n }
  g=p.entities.add_group; g.name=n; g
end
def box(p,n,x,y,z,w,d,h,m)
  raise 'Nonpositive dimension' unless [w,d,h].all? { |v| v>0 }
  g=child(p,n)
  f=g.entities.add_face([[x,y,z],[x+w,y,z],[x+w,y+d,z],[x,y+d,z]].map { |q| q.map { |v| v.mm } })
  f.reverse! if f.normal.z<0
  f.pushpull(h.mm)
  g.entities.grep(Sketchup::Face).each { |q| q.material=m; q.back_material=m }
  g.entities.grep(Sketchup::Edge).each { |e| e.hidden=true }
  g
end
def reaxis(g,axis,j,newj,pitch)
  anchor=[0,0,0]; anchor[axis]=(j*3600).mm
  factors=[1,1,1]; factors[axis]=pitch/3600.0
  delta=[0,0,0]; delta[axis]=(newj*pitch-j*3600).mm
  g.transform!(Geom::Transformation.translation(delta)*Geom::Transformation.scaling(Geom::Point3d.new(anchor),*factors))
end
b=ng(root,'BUILDING'); tower=ng(b,'TOWER'); facade=ng(tower,'FACADE')
stone=model.materials['Warm_limestone']; dark=model.materials['Bronze_mullion']
glass=model.materials['Glass_1']; light=model.materials['Light_opaque_panel']
rows=pass=='sample' ? [16] : (0..17).to_a.reject { |k| k==16 }
rows.each do |k|
  name="TOWER_L#{k.to_s.rjust(2,'0')}"; row=ng(facade,name)
  path=['BUILDING','TOWER','FACADE',name]
  z=k==0 ? 0 : 4200+(k-1)*3100; h=k==0 ? 4200 : 3100
  finish=k>=2 && k<=4 ? dark : stone
  # Retain and resize the existing deep infill/return assemblies as complete units.
  # Existing front j0..4 -> new j0,1,3,4,5; side j0..3 -> new j0,1,3,4.
  row.entities.grep(Sketchup::Group).each do |g|
    nn=g.name
    if nn.start_with?('FRONT_POST_','FRONT_HEAD_','RIGHT_POST_','RIGHT_HEAD_')
      clear_owned_contents.call(path+[nn])
    elsif nn.start_with?('FRONT_GLAZING_','FRONT_MULLION_','FRONT_OPAQUE_','FRONT_BALUSTRADE_','FRONT_RAIL_')
      j=nn.split('_').last.to_i; newj=[0,1,3,4,5][j]
      reaxis(g,0,j,newj,3000.0)
    elsif nn.start_with?('RIGHT_GLASS_','RIGHT_MULLION_','SIDE_BALUSTRADE_','SIDE_RAIL_','SIDE_OPAQUE_true_','LOGGIA_')
      j=nn.start_with?('LOGGIA_') ? nn.split('_')[1].to_i : nn.split('_').last.to_i
      reaxis(g,1,j,[0,1,3,4][j],2880.0)
    end
  end
  # New grid is nested in the existing row, never a building/root replacement.
  grid=child(row,'SOURCE_VISIBLE_GRID_6X5')
  7.times { |j| box(grid,"FRONT_AXIS_#{j}",j*3000-165,-300,z,330,500,h,finish) }
  6.times { |j| box(grid,"FRONT_BEAM_#{j}",j*3000-165,-300,z+h-308,3330,500,308,finish) }
  6.times { |j| box(grid,"RIGHT_AXIS_#{j}",17800,j*2880-165,z,500,330,h,finish) }
  5.times { |j| box(grid,"RIGHT_BEAM_#{j}",17800,j*2880-165,z+h-308,500,3210,308,finish) }
  # Only the newly introduced bays need new infills. Others retain existing depth.
  front_missing=k==1 ? [2,5] : [2]
  side_missing=k==1 ? [0,2] : [2]
  front_missing.each do |j|
    x=j*3000
    box(grid,"FRONT_NEW_GLASS_#{j}",x+150,100,z+180,2700,26,h-488,glass)
    box(grid,"FRONT_NEW_STILE_#{j}",x+1620,65,z+180,48,65,h-488,dark)
    box(grid,"FRONT_NEW_OPAQUE_#{j}",x+150,70,z+180,620,26,h-488,light) if k>0 && [3,6,10,14,17].include?(k)
  end
  side_missing.each do |j|
    y=j*2880
    box(grid,"RIGHT_NEW_GLASS_#{j}",17900,y+150,z+180,26,2580,h-488,glass)
    box(grid,"RIGHT_NEW_STILE_#{j}",17875,y+1510,z+180,65,48,h-488,dark)
    box(grid,"RIGHT_NEW_OPAQUE_#{j}",17930,y+150,z+180,26,620,h-488,light) if k>0 && [2,5,9,13,16].include?(k)
  end
end

if pass=='replication'
  # The old independent test bay occupies the revised last front/first side bay.
  # Keep its full slab; retire only obsolete frame/glazing contents.
  clear_owned_contents.call(['BUILDING','TOWER','MODULE_PROTOTYPE','FRAME'])
  clear_owned_contents.call(['BUILDING','TOWER','MODULE_PROTOTYPE','GLAZING'])
  reaxis(ng(root,'MODULE_FRONT_WALL'),0,4,5,3000.0)
  plants=ng(ng(root,'VEGETATION'),'BALCONY_INSTANCES')
  [[4,1],[7,3],[8,0],[11,2],[15,1]].each_with_index do |a,i|
    reaxis(ng(plants,"SIDE_BALCONY_#{i}"),1,a[1],[0,1,3,4][a[1]],2880.0)
  end
  # Two existing low-wing pockets. Rooms join the left block at X=-32400.
  # Open fronts/side loggias are recessed inside their retained roof outlines.
  pocket_parent=ng(ng(ng(ng(b,'LEFT_STREET'),'ROOF'),'PLANTED_POCKETS'),'POCKET_0')
  paving=model.materials['Terrace_paving']; guard=model.materials['Balustrade_glass']
  pocket_specs=[[-32400,7200,2700,8100,13500,16600,1800,1800],[-32400,3600,5400,5400,16600,19700,1200,900]]
  pocket_specs.each_with_index do |a,i|
    x,w,y,d,z,top,front_depth,side_depth=a
    path=['BUILDING','LEFT_STREET','ROOF','PLANTED_POCKETS',"POCKET_#{i}"]
    p=ng(ng(ng(ng(b,'LEFT_STREET'),'ROOF'),'PLANTED_POCKETS'),"POCKET_#{i}")
    clear_owned_contents.call(path)
    # Retained deck elevation and envelope, fascia now terminates at wall planes.
    box(p,'DECK',x,y,z,w,d,80,paving)
    box(p,'ROOF_DECK',x,y,top-220,w,d,220,paving)
    box(p,'CONNECTED_LEFT_RETURN',x,y,z+80,200,d,top-z-80,light)
    box(p,'BACK_ENCLOSURE',x,y+d-200,z+80,w,200,top-z-300,light)
    room_right=x+w-side_depth
    back_y=y+front_depth
    # Back of the front outdoor recess: glazed door wall with actual side returns.
    box(p,'RECESS_REAR_GLASS',x+200,back_y,z+80,w-side_depth-400,30,top-z-300,glass)
    box(p,'RECESS_RIGHT_RETURN',room_right-200,y,z+80,200,front_depth,top-z-300,light)
    box(p,'ROOM_RIGHT_GLASS',room_right,back_y,z+80,30,d-front_depth-200,top-z-300,glass)
    box(p,'FRONT_RECESS_CEILING',x+200,y,top-300,w-200,front_depth,80,light)
    box(p,'SIDE_RECESS_CEILING',room_right,back_y,top-300,side_depth,d-front_depth-200,80,light)
    # Pale frame remains aligned to the occupied room/terrace rather than an
    # outboard plate rim. Avoid the old oversized right beam cantilever.
    box(p,'FRONT_LINTEL',x,y,top-350,w,250,350,stone)
    box(p,'RIGHT_LINTEL',x+w-200,y,top-350,200,d,350,stone)
    [x,x+w/2,x+w-200].each_with_index do |xx,j|
      box(p,"FRONT_COLUMN_#{j}",xx,y,z+80,200,250,top-z-80,stone)
    end
    3.times do |j|
      xx=x+200+(w-side_depth-400)*j/2.0
      box(p,"DOOR_STILE_#{j}",xx,back_y-35,z+80,45,70,top-z-300,dark)
    end
    3.times do |j|
      yy=back_y+(d-front_depth-200)*j/2.0
      box(p,"SIDE_DOOR_STILE_#{j}",room_right-35,yy,z+80,70,45,top-z-300,dark)
    end
    # Lower recessed outdoor edge is glass between columns, with end returns.
    box(p,'RECESSED_FRONT_GUARD',x+200,y+100,z+80,w-400,24,1050,guard)
    box(p,'RECESSED_FRONT_HANDRAIL',x+200,y+85,z+1130,w-400,55,45,dark)
    box(p,'SIDE_OUTDOOR_GUARD',x+w-100,y+200,z+80,24,d-400,1050,guard)
    box(p,'SIDE_OUTDOOR_HANDRAIL',x+w-115,y+200,z+1130,55,d-400,45,dark)
    # Roof terrace: solid planting edge and short glazing, no continuous tray rim.
    front_solid=i==0 ? 4400 : 2200
    box(p,'PLANTED_SOLID_EDGE',x+80,y+80,top,front_solid,180,650,stone)
    box(p,'ROOF_FRONT_GLASS',x+front_solid+80,y+150,top,w-front_solid-160,24,1050,guard)
    box(p,'ROOF_FRONT_HANDRAIL',x+front_solid+80,y+130,top+1050,w-front_solid-160,50,45,dark)
    box(p,'ROOF_SIDE_SOLID_RETURN',x+w-180,y+80,top,180,1700,650,stone)
    box(p,'ROOF_SIDE_GLASS',x+w-120,y+1780,top,24,d-1860,1050,guard)
    box(p,'ROOF_SIDE_HANDRAIL',x+w-140,y+1780,top+1050,50,d-1860,45,dark)
  end
end
