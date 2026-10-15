# Eight-source reconstruction. All dimensions mm; only injected owned root.
def rb_group(entities, name)
  g=entities.add_group
  g.name=name
  g.set_attribute('KStudio','semantic_id',name)
  g
end
def rb_box(entities,name,x,y,z,dx,dy,dz,mat)
  g=rb_group(entities,name)
  f=g.entities.add_face([x.mm,y.mm,z.mm],[(x+dx).mm,y.mm,z.mm],[(x+dx).mm,(y+dy).mm,z.mm],[x.mm,(y+dy).mm,z.mm])
  f.reverse! if f.normal.z<0
  f.pushpull(dz.mm)
  g.material=mat
  g
end
def rb_face(entities,name,points,mat)
  g=rb_group(entities,name)
  f=g.entities.add_face(points.map{|p|p.map(&:mm)})
  f.material=mat; f.back_material=mat
  g
end
def rb_bar(entities,name,a,b,width,mat)
  v=Geom::Vector3d.new(*(0..2).map{|i|(b[i]-a[i]).mm})
  len=v.length
  g=rb_box(entities,name,-width/2.0,-width/2.0,0,width,width,len.to_mm,mat)
  z=v.normalize
  reference=z.parallel?(Z_AXIS) ? X_AXIS : Z_AXIS
  x=reference.cross(z).normalize
  y=z.cross(x).normalize
  g.transform!(Geom::Transformation.axes(Geom::Point3d.new(*a.map(&:mm)),x,y,z))
  g
end
def rb_rail(entities,name,a,b,mat)
  g=rb_group(entities,name)
  length=Math.sqrt((b[0]-a[0])**2+(b[1]-a[1])**2)
  n=(length/1500).ceil
  (0..n).each do |i|
    t=i.to_f/n
    p=(0..2).map{|j|a[j]+(b[j]-a[j])*t}
    rb_bar(g.entities,"#{name}_POST_#{i}",p,[p[0],p[1],p[2]+1100],35,mat)
  end
  [120,550,1100].each{|h|rb_bar(g.entities,"#{name}_RAIL_#{h}",[a[0],a[1],a[2]+h],[b[0],b[1],b[2]+h],30,mat)}
  g
end
concrete=model.materials.add('KS_Concrete_Light'); concrete.color='#bdbbb5'
steel=model.materials.add('KS_White_Steel'); steel.color='#eceeea'
timber=model.materials.add('KS_Timber_Honey'); timber.color='#cba778'
glass=model.materials.add('KS_Clear_Glass'); glass.color='#c9dfe0'; glass.alpha=0.13
green=model.materials.add('KS_Green_Panel'); green.color='#668679'
groundmat=model.materials.add('KS_Ground'); groundmat.color='#d4d3cf'
dark=model.materials.add('KS_Core'); dark.color='#666665'
frame=rb_group(root.entities,'STRUCTURE_EXISTING')
# Representative column converted to component, then repeated at measured bays.
col=rb_box(frame.entities,'COLUMN_PROTOTYPE',-180,-180,0,360,360,10800,concrete).to_component
col.name='COLUMN_X00_Y00'
definition=col.definition
definition.name='EXISTING_CONCRETE_COLUMN_360'
col.transform!(Geom::Transformation.translation([0,0,0]))
(0..10).each do |i|
  [0,10000,20000].each_with_index do |y,j|
    next if i==0 && j==0
    c=frame.entities.add_instance(definition,Geom::Transformation.translation([(i*5000).mm,y.mm,0]))
    c.name="COLUMN_X#{i}_Y#{j}"
    c.set_attribute('KStudio','semantic_id',c.name)
  end
end
[3600,7200,10800].each do |z|
  [0,10000,20000].each_with_index{|y,j|rb_box(frame.entities,"LONG_BEAM_Z#{z}_Y#{j}",-180,y-180,z-480,50360,360,480,concrete)}
  (0..10).each{|i|rb_box(frame.entities,"CROSS_BEAM_Z#{z}_X#{i}",i*5000-150,0,z-420,300,20000,420,concrete)}
end
# ADAI floor profiles keep real circular voids and a boundary-connected atrium.
floor_parts=[]
circle=lambda{|cx,cy,r| (0...48).map{|i|a=i*2*Math::PI/48;[cx+r*Math.cos(a),cy+r*Math.sin(a)]}}
floor_parts << adai_geometry.profile(root.entities,'L0',[[0,0],[50000,0],[50000,20000],[0,20000]],250,'xy',-250,concrete)
floor_parts << adai_geometry.profile_with_holes(root.entities,'L1',[[0,0],[50000,0],[50000,20000],[0,20000]],[circle.call(37000,6500,2300)],250,'xy',3350,concrete)
floor_parts << adai_geometry.profile(root.entities,'L2_PARTIAL_SOUTH',[[0,11000],[50000,11000],[50000,20000],[0,20000]],250,'xy',6950,concrete)
floor_parts << adai_geometry.profile_with_holes(root.entities,'L2_PARTIAL_EAST',[[30000,0],[50000,0],[50000,11000],[30000,11000]],[circle.call(37000,6500,2300)],250,'xy',6950,concrete)
floor_parts << adai_geometry.profile_with_holes(root.entities,'L3',[[0,0],[50000,0],[50000,20000],[0,20000]],[circle.call(37000,6500,2300),circle.call(12000,10500,1100),circle.call(22500,10500,1100)],250,'xy',10550,timber)
floors=root.entities.add_group(floor_parts); floors.name='FLOORS'
# Asymmetric hanging cross-section, extruded continuously along the long axis.
roof_z=lambda{|y|t=y/20000.0; 13800+8800*(t-0.443)**2}
lower=(0..80).map{|i|y=i*250.0;[y,roof_z.call(y)]}
outline=lower+lower.reverse.map{|p|[p[0],p[1]+180]}
shell=adai_geometry.profile(root.entities,'CURVED_SHELL',outline,50000,'yz',0,timber)
roof=rb_group(root.entities,'ROOF_SUPPORTS')
(0..20).each do |i|
  x=i*2500
  [0,20000].each_with_index do |y,j|
    rb_bar(roof.entities,"TIMBER_POST_#{i}_#{j}",[x,y,10800],[x,y,roof_z.call(y)],110,timber)
  end
end
[0,20000].each_with_index{|y,j|rb_bar(roof.entities,"HIGH_EDGE_#{j}",[0,y,roof_z.call(y)],[50000,y,roof_z.call(y)],180,steel)}
[0,50000].each_with_index do |x,k|
  (0..10).each{|i|y=i*2000;rb_bar(roof.entities,"END_MULLION_#{k}_#{i}",[x,y,10800],[x,y,roof_z.call(y)],65,steel)}
  (0...40).each{|i|y=i*500;rb_face(roof.entities,"END_GLASS_#{k}_#{i}",[[x,y,10800],[x,y+500,10800],[x,y+500,roof_z.call(y+500)],[x,y,roof_z.call(y)]],glass)}
end
roof_all=root.entities.add_group([shell,roof]);roof_all.name='ROOF_TIMBER'
external=rb_group(root.entities,'CIRCULATION_EXTERNAL')
galleries=rb_group(external.entities,'GALLERIES')
[3600,7200,10800].each do |z|
  [[-4000,-4000,58000,4000],[-4000,20000,58000,4000],[-4000,0,4000,20000],[50000,0,4000,20000]].each_with_index do |p,i|
    rb_box(galleries.entities,"GALLERY_Z#{z}_SIDE#{i}",p[0],p[1],z-150,p[2],p[3],150,steel)
  end
  # All circulation edges remain editable; openings at end ramp joins.
  rb_rail(galleries.entities,"LONG_RAIL_SOUTH_Z#{z}",[-4000,-4000,z],[54000,-4000,z],steel)
  rb_rail(galleries.entities,"LONG_RAIL_NORTH_Z#{z}",[-4000,24000,z],[54000,24000,z],steel)
end
ramp_parts=[]
# Three continuous folded runs in the short-end buffer; exact joint elevations.
[[ -8500,24000,-4000,0,3600],[-6300,-4000,24000,3600,7200],[-4100,24000,-4000,7200,10800]].each_with_index do |p,i|
  x,ya,yb,za,zb=p
  ramp_parts << adai_geometry.profile(root.entities,"RAMP_#{i+1}",[[ya,za-160],[yb,zb-160],[yb,zb],[ya,za]],2200,'yz',x,steel)
  rb_rail(external.entities,"RAMP_#{i+1}_OUTER",[x,ya,za],[x,yb,zb],steel)
  rb_rail(external.entities,"RAMP_#{i+1}_INNER",[x+2200,ya,za],[x+2200,yb,zb],steel)
end
ramps=root.entities.add_group(ramp_parts);ramps.name='RAMPS'
# Keep helper ramp solids as their own root assembly; never reparent live groups.
landings=rb_group(external.entities,'LANDINGS')
rb_box(landings.entities,'LANDING_L0',-8500,24000,-160,6600,2200,160,steel)
rb_box(landings.entities,'LANDING_L1',-8500,-6200,3440,8500,2200,160,steel)
rb_box(landings.entities,'LANDING_L2',-6300,24000,7040,6600,2200,160,steel)
rb_box(landings.entities,'LANDING_L3',-4100,-6200,10640,4100,2200,160,steel)
# Glass skin distinct from inner concrete frame: upper box, lower inset glass.
envelope=rb_group(root.entities,'ENVELOPE_OUTER')
# Curtain wall representative bay: 2900 wide, 6300 high, independent frame/glass.
curtain_module=rb_group(envelope.entities,'CURTAIN_MODULE_00')
rb_face(curtain_module.entities,'GLASS',[[0,0,7200],[2900,0,7200],[2900,0,13500],[0,0,13500]],glass)
rb_box(curtain_module.entities,'MULLION',-30,-30,7200,60,60,6300,steel)
[7200,8250,9300,10800,12000,13500].each{|z|rb_box(curtain_module.entities,"TRANSOM_#{z}",0,-25,z-25,2900,50,50,steel)}
raise 'invalid curtain prototype' unless curtain_module.bounds.width.to_mm>2890
mc=curtain_module.to_component;mc.definition.name='CURTAIN_2900x6300';mc.name='SOUTH_BAY_00'
mc.transform!(Geom::Transformation.translation([-4000.mm,-4000.mm,0]))
(1...20).each{|i|c=envelope.entities.add_instance(mc.definition,Geom::Transformation.translation([(-4000+i*2900).mm,-4000.mm,0]));c.name="SOUTH_BAY_#{i}"}
(0...20).each{|i|c=envelope.entities.add_instance(mc.definition,Geom::Transformation.translation([(-4000+i*2900).mm,24000.mm,0]));c.name="NORTH_BAY_#{i}"}
[-4000,54000].each_with_index do |x,j|
  (0...10).each do |i|
    y=-4000+i*2800
    rb_face(envelope.entities,"SHORT_GLASS_#{j}_#{i}",[[x,y,7200],[x,y+2800,7200],[x,y+2800,13500],[x,y,13500]],glass)
    rb_bar(envelope.entities,"SHORT_MULLION_#{j}_#{i}",[x,y,7200],[x,y,13500],60,steel)
  end
  [7200,8250,9300,10800,12000,13500].each{|z|rb_bar(envelope.entities,"SHORT_TRANSOM_#{j}_#{z}",[x,-4000,z],[x,24000,z],60,steel)}
end
# Low horizontal canopies of the peripheral climate-buffer, not a second roof.
canopy=rb_group(envelope.entities,'BUFFER_CANOPIES')
[[-4000,-4000,58000,4000],[-4000,20000,58000,4000],[-4000,0,4000,20000],[50000,0,4000,20000]].each_with_index{|p,i|rb_box(canopy.entities,"CANOPY_#{i}",p[0],p[1],13400,p[2],p[3],100,steel)}
inner=rb_group(envelope.entities,'INNER_GLAZING')
[0,20000].each_with_index do |y,j|
  (0...20).each do |i|
    x=i*2500
    rb_face(inner.entities,"INNER_GLASS_#{j}_#{i}",[[x,y,0],[x+2500,y,0],[x+2500,y,10800],[x,y,10800]],glass)
    rb_bar(inner.entities,"INNER_POST_#{j}_#{i}",[x,y,0],[x,y,10800],60,steel)
  end
end
bracing=rb_group(envelope.entities,'TENSION_BRACING')
(0..10).each do |i|
  x=i*5000
  rb_bar(bracing.entities,"SOUTH_CABLE_#{i}",[x,-4000,3600],[x,0,15500],24,steel)
  rb_bar(bracing.entities,"NORTH_CABLE_#{i}",[x,24000,3600],[x,20000,16500],24,steel)
end
# Main semantic internal circulation; stepped spirals line up with floor voids.
stairs=rb_group(root.entities,'CIRCULATION_INTERNAL')
[0,3600,7200].each_with_index do |z,k|
  spiral=rb_group(stairs.entities,"SPIRAL_L#{k}_L#{k+1}")
  (0...24).each do |i|
    a=i*2*Math::PI/24; b=(i+1)*2*Math::PI/24
    points=[[37000+350*Math.cos(a),6500+350*Math.sin(a)], [37000+2100*Math.cos(a),6500+2100*Math.sin(a)], [37000+2100*Math.cos(b),6500+2100*Math.sin(b)], [37000+350*Math.cos(b),6500+350*Math.sin(b)]]
    step=rb_group(spiral.entities,"TREAD_#{i}")
    f=step.entities.add_face(points.map{|p|[p[0].mm,p[1].mm,(z+(i+1)*150-80).mm]});f.reverse! if f.normal.z<0;f.pushpull(80.mm);step.material=steel
    rb_bar(spiral.entities,"BALUSTER_#{i}",[37000+2100*Math.cos(b),6500+2100*Math.sin(b),z+(i+1)*150],[37000+2100*Math.cos(b),6500+2100*Math.sin(b),z+(i+1)*150+1100],25,steel)
    rb_bar(spiral.entities,"HANDRAIL_#{i}",[37000+2100*Math.cos(a),6500+2100*Math.sin(a),z+i*150+1100],[37000+2100*Math.cos(b),6500+2100*Math.sin(b),z+(i+1)*150+1100],35,steel)
  end
end
[3600,7200,10800].each do |z|
  [2300].each do |r|
    (0...48).each do |i|
      a=i*2*Math::PI/48;b=(i+1)*2*Math::PI/48
      rb_rail(stairs.entities,"VOID_RAIL_#{z}_#{i}",[37000+r*Math.cos(a),6500+r*Math.sin(a),z],[37000+r*Math.cos(b),6500+r*Math.sin(b),z],steel) if i>5
    end
  end
end
# End stair pair follows the plan's east circulation zone.
[0,3600,7200].each do |z|
  (0...24).each{|i|rb_box(stairs.entities,"END_TREAD_#{z}_#{i}",50500,1000+i*260,z+i*150,2200,260,150,steel)}
end
# Main south-side rooms; actual SAIE straight wall helper only where suitable.
partitions=[]
[3600,7200].each do |z|
  (1...10).each do |i|
    partitions << saie_wall.call({'name'=>"PARTITION_Z#{z}_B#{i}",'centerline'=>[[i*5000,12000],[i*5000,20000]],'thickness_mm'=>120,'height_mm'=>3100,'elevation_mm'=>z})
  end
end
interior=root.entities.add_group(partitions);interior.name='INTERIOR'
rb_box(interior.entities,'GREEN_PANEL_SOUTH',30000,19850,7200,4900,150,3100,green)
rb_box(interior.entities,'CORE_EAST',47000,13500,0,3000,6500,3600,dark)
furniture=rb_group(interior.entities,'FURNITURE_SIMPLIFIED')
[0,3600,10800].each{|z|(0...6).each{|i|rb_box(furniture.entities,"TABLE_Z#{z}_#{i}",5000+i*6000,4000,z+720,2400,1000,65,timber)}}
site=rb_group(root.entities,'SITE_GROUND')
rb_box(site.entities,'ADJACENT_GROUND',-12000,-9000,-500,71000,42000,220,groundmat)
root.set_attribute('KStudio','source_count',8)
root.set_attribute('KStudio','dimensions_status','estimated')
root.set_attribute('KStudio','build_stage','primary_form_with_developed_systems')
