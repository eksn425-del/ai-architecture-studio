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
