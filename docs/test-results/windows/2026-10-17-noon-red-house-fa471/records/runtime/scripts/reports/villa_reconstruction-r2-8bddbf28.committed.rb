# Units: millimeters. All geometry belongs to supplied root.
def grp(e, name)
  g=e.add_group; g.name=name; g
end
def box(e,name,x,y,z,w,d,h,mat)
  g=grp(e,name)
  f=g.entities.add_face([x.mm,y.mm,z.mm],[(x+w).mm,y.mm,z.mm],[(x+w).mm,(y+d).mm,z.mm],[x.mm,(y+d).mm,z.mm])
  f.reverse! if f.normal.z < 0
  f.pushpull(h.mm)
  g.material=mat
  g
end
def glass(e,name,x,y,z,w,h,mat)
  box(e,name,x,y,z,w,22,h,mat)
end
def window(e,name,x,y,z,w,h,metal,glazing,cols=1,rows=1)
  g=grp(e,name); a=g.entities; t=65.0
  glass(a,'GLASS',x+t,y+65,z+t,w-2*t,h-2*t,glazing)
  box(a,'JAMB_L',x,y,z,t,120,h,metal); box(a,'JAMB_R',x+w-t,y,z,t,120,h,metal)
  box(a,'HEAD',x,y,z+h-t,w,120,t,metal); box(a,'SILL',x,y,z,w,120,t,metal)
  (1...cols).each{|i| box(a,"MULLION_#{i}",x+w*i/cols-t/2,y,z,t,120,h,metal)}
  (1...rows).each{|i| box(a,"TRANSOM_#{i}",x,y,z+h*i/rows-t/2,w,120,t,metal)}
  g
end
def rail(e,name,x,y,z,w,metal,glazing)
  g=grp(e,name); a=g.entities
  [0,w/2,w-40].each_with_index{|v,i| box(a,"POST_#{i}",x+v,y,z,40,45,1050,metal)}
  box(a,'TOP_RAIL',x,y,z+1010,w+40,50,40,metal)
  glass(a,'GLASS',x+45,y+14,z+90,w-50,900,glazing)
  box(a,'LOW_RAIL',x,y,z+40,w,45,35,metal)
  g
end
if root.entities.to_a.empty?
brick=model.materials.add('Warm terracotta brick'); brick.color=Sketchup::Color.new(157,91,65)
metal=model.materials.add('Anthracite metal'); metal.color=Sketchup::Color.new(36,42,43)
glazing=model.materials.add('Grey transparent glazing'); glazing.color=Sketchup::Color.new(133,157,164); glazing.alpha=0.48
concrete=model.materials.add('Warm grey concrete'); concrete.color=Sketchup::Color.new(155,150,138)
inside=model.materials.add('Warm internal reveals'); inside.color=Sketchup::Color.new(176,147,104)
green=model.materials.add('Planting'); green.color=Sketchup::Color.new(69,91,55)
# Stage 1: source supported primary shell. Adjacent solids kept independent.
left=grp(root.entities,'MASS_LEFT')
box(left.entities,'FRONT_SOLID',0,100,2900,3500,250,5300,metal)
box(left.entities,'LEFT_RETURN',0,350,0,250,11650,8200,brick)
box(left.entities,'REAR_PAVILION',250,4000,8200,3250,8000,2100,metal)
right=grp(root.entities,'MASS_RIGHT_BRICK'); a=right.entities
# True stepped silhouette and unobstructed narrow aperture.
box(a,'LOW_LEFT_PIER',6000,0,3000,2200,280,3000,brick)
box(a,'HIGH_LEFT_PIER',4900,0,6000,3300,280,4700,brick)
box(a,'RIGHT_PIER',9300,0,3000,1900,280,7700,brick)
box(a,'WINDOW_APRON',8200,0,3000,1100,280,200,brick)
box(a,'WINDOW_HEAD',8200,0,9400,1100,280,1300,brick)
# Suitable actual wrapped SAIE straight wall calls, all under owned root.
saie_wall.call({'name'=>'INFERRED_RIGHT_WALL','centerline'=>[[11075,280],[11075,12000]],'thickness_mm'=>250,'height_mm'=>10700,'elevation_mm'=>0})
saie_wall.call({'name'=>'INFERRED_REAR_WALL','centerline'=>[[250,11875],[10950,11875]],'thickness_mm'=>250,'height_mm'=>10700,'elevation_mm'=>0})
top=grp(root.entities,'MASS_TOP_GLAZED')
box(top.entities,'LEFT_FRAME',3500,350,8600,140,3800,3520,metal)
box(top.entities,'REAR_ENCLOSURE',3640,4000,8600,4560,250,3520,metal)
box(top.entities,'RIGHT_FRAME',8060,350,8600,140,3800,3520,metal)
slabs=grp(root.entities,'SLABS')
[2900,5900,8600].each_with_index{|z,i| box(slabs.entities,"FLOOR_#{i}",250,1500,z-180,10700,10250,180,concrete)}
box(slabs.entities,'GROUND',250,1500,100,10700,10250,160,concrete)
box(slabs.entities,'RIGHT_ROOF',4900,280,10400,6050,11470,180,concrete)
box(root.entities,'ROOF_TOP',3390,0,12120,5050,4400,180,metal)
box(root.entities,'ROOF_LEFT',-100,3500,10320,3650,8800,180,metal)
box(root.entities,'PARAPET_RIGHT',4850,-40,10700,6400,400,75,brick)
box(root.entities,'GROUND_CANOPY',0,-150,2720,11200,1800,180,metal)
box(root.entities,'BALCONY_LOWER',3300,-180,2820,2900,1700,180,metal)
box(root.entities,'BALCONY_UPPER',3400,-100,5820,1700,1620,180,metal)
# Stage 2 representative opening/rail. Primary glazed planes establish void depth.
window(root.entities,'FRONT_NARROW_WINDOW',8200,130,3200,1100,6200,metal,glazing,1,4)
window(root.entities,'TOP_GLAZING',3640,350,8600,4420,3450,metal,glazing,3,2)
bg=grp(root.entities,'BALCONY_GLAZING')
window(bg.entities,'LOWER',3500,1250,3000,2500,2600,metal,glazing,3,1)
window(bg.entities,'UPPER',3500,1250,6000,1400,2400,metal,glazing,2,1)
window(root.entities,'GROUND_LEFT_GLAZING',300,650,300,3000,2420,metal,glazing,3,1)
entry=grp(root.entities,'ENTRY')
box(entry.entities,'BACK_WALL',3300,1800,260,4000,200,2460,inside)
box(entry.entities,'DOUBLE_DOOR',4300,1750,260,1800,70,2200,metal)
box(entry.entities,'DOOR_SEAM',5185,1740,260,15,15,2200,concrete)
box(entry.entities,'JAMB_RIGHT',7100,0,0,250,1800,2720,brick)
rail(root.entities,'RAIL_LOWER',3300,-170,3000,2900,metal,glazing)
rail(root.entities,'RAIL_UPPER',3400,-90,6000,1700,metal,glazing)
clad=grp(root.entities,'CLADDING_LEFT')
box(clad.entities,'EDGE_TRIM',0,45,2900,60,60,5300,metal)
site=grp(root.entities,'SITE')
box(site.entities,'COURT',-1000,-3000,-150,14200,15500,150,concrete)
box(root.entities,'BOUNDARY_LEFT',-1500,-2700,0,5000,250,2200,brick)
box(root.entities,'BOUNDARY_RIGHT',8000,-2700,0,4900,250,2200,brick)
gate=grp(root.entities,'GATE_MAIN')
box(gate.entities,'FRAME',6600,-2730,0,1200,60,2200,metal)
gate2=grp(root.entities,'GATE_LEFT')
box(gate2.entities,'FRAME',-2600,-2730,0,1000,60,2200,metal)
steps=grp(root.entities,'ENTRY_STEPS')
box(steps.entities,'STEP_1',3600,-2600,0,2900,1700,100,concrete)
box(steps.entities,'STEP_2',3750,-1700,100,2600,1200,100,concrete)
box(steps.entities,'ENTRY_LANDING',3900,-700,200,2300,2450,60,concrete)
plant=grp(root.entities,'PLANTERS')
box(plant.entities,'LOWER_TROUGH',3550,0,3050,2200,380,400,metal)
box(plant.entities,'UPPER_TROUGH',3550,50,6050,1200,330,350,metal)
else
  metal=model.materials['Anthracite metal']; brick=model.materials['Warm terracotta brick']
  concrete=model.materials['Warm grey concrete']; green=model.materials['Planting']; glazing=model.materials['Grey transparent glazing']
  find_group=lambda do |path|
    e=root.entities; g=nil
    path.each do |n|
      g=e.grep(Sketchup::Group).find{|v| v.name==n}
      raise "Missing owned group #{path.join('/')}" unless g
      e=g.entities
    end
    g
  end
  # Stage 3/4: editable masonry quads, continuous running bond across wall segments.
  mortar=model.materials.add('Mortar warm sand r2'); mortar.color=Sketchup::Color.new(149,120,96)
  tones=[]
  [[160,104,79],[170,112,85],[151,93,70],[179,121,91],[166,103,75],[145,91,69],[174,115,89]].each_with_index do |rgb,i|
    m=model.materials.add("Brick tone r2 #{i}"); m.color=Sketchup::Color.new(*rgb); tones << m
  end
  brick_finish=lambda do |g,x,y,z,w,h|
    g.entities.grep(Sketchup::Edge).each{|ed| ed.hidden=true}
    s=grp(g.entities,'BRICK_COURSING'); a=s.entities
    f=a.add_face([x.mm,(y-0.5).mm,z.mm],[(x+w).mm,(y-0.5).mm,z.mm],[(x+w).mm,(y-0.5).mm,(z+h).mm],[x.mm,(y-0.5).mm,(z+h).mm]); f.material=mortar; f.back_material=mortar
    pitch=90.0; bond=360.0
    first=(z/pitch).floor; last=((z+h)/pitch).ceil
    (first...last).each do |r|
      b=[z,r*pitch+7].max; t=[z+h,(r+1)*pitch-4].min
      next if t<=b
      c0=((x-(r%2)*bond/2)/bond).floor; c1=((x+w-(r%2)*bond/2)/bond).ceil
      (c0...c1).each do |c|
        l=[x,c*bond+(r%2)*bond/2+5].max; rr=[x+w,(c+1)*bond+(r%2)*bond/2-5].min
        next if rr<=l
        f=a.add_face([l.mm,(y-2).mm,b.mm],[rr.mm,(y-2).mm,b.mm],[rr.mm,(y-2).mm,t.mm],[l.mm,(y-2).mm,t.mm])
        m=tones[(r*7+c*13+c*r).abs%tones.length]; f.material=m; f.back_material=m
      end
    end
    a.grep(Sketchup::Edge).each{|ed| ed.hidden=true}
  end
  [['LOW_LEFT_PIER',6000,3000,2200,3000],['HIGH_LEFT_PIER',4900,6000,3300,4700],['RIGHT_PIER',9300,3000,1900,7700],['WINDOW_APRON',8200,3000,1100,200],['WINDOW_HEAD',8200,9400,1100,1300]].each do |n,x,z,w,h|
    brick_finish.call(find_group.call(['MASS_RIGHT_BRICK',n]),x,0,z,w,h)
  end
  brick_finish.call(find_group.call(['BOUNDARY_LEFT']),-1500,-2700,0,5000,2200)
  brick_finish.call(find_group.call(['BOUNDARY_RIGHT']),8000,-2700,0,4900,2200)
  cl=find_group.call(['CLADDING_LEFT']).entities
  (0..7).each{|i| box(cl,"STANDING_SEAM_#{i}",i*485+35,45,2900,28,72,5300,metal)}
  box(cl,'HORIZONTAL_JOINT',0,30,5850,3500,30,24,metal)
  box(cl,'TERRACE_TOP_TRIM',0,25,8160,3500,95,65,metal)
  box(cl,'BRICK_LEFT_EDGE',-250,45,2900,250,280,5900,brick)
  clear_owned_contents.call(['SLABS','FLOOR_2'])
  sf=find_group.call(['SLABS','FLOOR_2']).entities
  box(sf,'TOP_ROOM_FLOOR',3500,500,8420,4700,3750,180,metal)
  box(sf,'LEFT_TERRACE_FLOOR',250,350,8020,3250,11400,180,metal)
  # Dark entrance recess, connected head and returns.
  dark=model.materials.add('Entry shadow r2'); dark.color=Sketchup::Color.new(38,36,30)
  door=model.materials.add('Entry doors r2'); door.color=Sketchup::Color.new(46,43,37)
  clear_owned_contents.call(['ENTRY','BACK_WALL'])
  e=find_group.call(['ENTRY','BACK_WALL']).entities
  box(e,'DARK_BACK',3300,1820,260,4000,180,2460,dark)
  box(e,'DARK_HEADER',3300,1150,2360,4000,680,360,dark)
  box(e,'LEFT_REVEAL',3300,650,260,240,1170,2460,dark)
  box(e,'RIGHT_REVEAL',6860,650,260,240,1170,2460,dark)
  clear_owned_contents.call(['ENTRY','DOUBLE_DOOR'])
  e=find_group.call(['ENTRY','DOUBLE_DOOR']).entities
  box(e,'LEFT_LEAF',4300,1730,260,895,90,2030,door)
  box(e,'RIGHT_LEAF',5205,1730,260,895,90,2030,door)
  box(e,'HANDLE_L',5150,1695,1000,15,35,310,concrete)
  box(e,'HANDLE_R',5230,1695,1000,15,35,310,concrete)
  clear_owned_contents.call(['ENTRY','DOOR_SEAM'])
  box(find_group.call(['ENTRY','DOOR_SEAM']).entities,'SEAM',5195,1720,260,10,15,2030,dark)
  # Source-visible four lights and heavier middle band.
  clear_owned_contents.call(['FRONT_NARROW_WINDOW'])
  ng=find_group.call(['FRONT_NARROW_WINDOW']).entities
  glass(ng,'CONTINUOUS_GLASS',8280,185,3280,940,6040,glazing)
  box(ng,'DEEP_JAMB_L',8200,30,3200,90,220,6200,metal)
  box(ng,'DEEP_JAMB_R',9210,30,3200,90,220,6200,metal)
  box(ng,'HEAD',8200,30,9310,1100,220,90,metal)
  box(ng,'SILL',8200,30,3200,1100,220,90,metal)
  [4750,7850].each_with_index{|z,i|box(ng,"CROSSBAR_#{i}",8200,30,z-40,1100,220,80,metal)}
  box(ng,'CENTRAL_BAND',8200,30,6150,1100,220,320,metal)
  box(ng,'UPPER_VERTICAL',8620,60,6470,55,145,2840,metal)
  box(ng,'LOWER_VERTICAL',8630,60,3290,50,145,2860,metal)
  # Stage 5: source metal gate bars within original FRAME containers.
  [['GATE_MAIN',6600,1200],['GATE_LEFT',-2600,1000]].each do |n,x,w|
    clear_owned_contents.call([n,'FRAME']); a=find_group.call([n,'FRAME']).entities
    box(a,'POST_L',x,-2730,0,50,70,2200,metal)
    box(a,'POST_R',x+w-50,-2730,0,50,70,2200,metal)
    box(a,'TOP',x,-2730,2150,w,70,50,metal)
    box(a,'BOTTOM',x,-2730,40,w,70,40,metal)
    box(a,'MID',x,-2730,1050,w,65,35,metal)
    (1...(w/75).floor).each{|i|box(a,"BAR_#{i}",x+i*75,-2720,80,16,40,2070,metal)}
  end
  plants=find_group.call(['PLANTERS']).entities
  box(plants,'LEFT_TERRACE_TROUGH',150,400,8200,3200,800,350,metal)
  crown=lambda do |name,x,y,z,rx,ry,rz|
    g=grp(plants,name); a=g.entities; rings=6; seg=10
    (0...rings).each do |j|
      p1=-Math::PI/2+j*Math::PI/rings; p2=-Math::PI/2+(j+1)*Math::PI/rings
      (0...seg).each do |i|
        t1=i*2*Math::PI/seg; t2=(i+1)*2*Math::PI/seg
        pts=[[p1,t1],[p1,t2],[p2,t2],[p2,t1]].map{|p,t|[(x+rx*Math.cos(p)*Math.cos(t)).mm,(y+ry*Math.cos(p)*Math.sin(t)).mm,(z+rz*Math.sin(p)).mm]}.uniq
        next if pts.length<3
        f=a.add_face(pts)
        if f; f.material=green; f.back_material=green; end
      end
    end
    a.grep(Sketchup::Edge).each{|ed|ed.soft=true;ed.smooth=true}
  end
  9.times{|i|crown.call("TERRACE_SHRUB_#{i}",350+i*350,800+(i%3)*130,8600+(i%4)*230,420,400,600+(i%3)*150)}
  7.times{|i|crown.call("BALCONY_LOW_SHRUB_#{i}",3750+i*290,180,3530,230,210,240)}
  4.times{|i|crown.call("BALCONY_UPPER_SHRUB_#{i}",3700+i*270,200,6520,240,210,220)}
  5.times{|i|crown.call("ROOF_SHRUB_#{i}",8400+i*380,900,10850,380,450,300)}
  find_group.call(['INFERRED_RIGHT_WALL']).material=brick
  find_group.call(['INFERRED_REAR_WALL']).material=brick
end
