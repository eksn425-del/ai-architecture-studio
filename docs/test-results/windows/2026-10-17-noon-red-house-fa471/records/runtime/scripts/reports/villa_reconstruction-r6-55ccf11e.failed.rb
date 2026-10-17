# Units: millimeters. All geometry belongs to supplied root.
# LIVE MODEL: revision 3, root PID 19. Revision 4 branch below is UNEXECUTED.
# Host stopped further geometry writes after first build plus two corrections.
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
# Revision 6: approved junction / roof / courtyard local repair.
find_group=lambda do |path|
 e=root.entities;g=nil
 path.each{|n|g=e.grep(Sketchup::Group).find{|v|v.name==n};raise "Missing #{n}" unless g;e=g.entities};g
end
metal=model.materials['Anthracite metal'];brick=model.materials['Warm terracotta brick'];glazing=model.materials['Grey transparent glazing'];concrete=model.materials['Warm grey concrete']
soil=model.materials.add('Courtyard soil r6');soil.color=Sketchup::Color.new(67,57,42)
leaf=model.materials.add('Courtyard leaves r6');leaf.color=Sketchup::Color.new(75,104,54)
mortar=model.materials.add('Repair mortar r6');mortar.color=Sketchup::Color.new(133,109,88)
tones=[]
[[143,91,67],[153,101,76],[147,96,72],[158,107,81],[140,90,68],[150,98,73],[155,103,76]].each_with_index{|rgb,i|m=model.materials.add("Repair brick r6 #{i}");m.color=Sketchup::Color.new(*rgb);tones<<m}
reset=lambda{|p|clear_owned_contents.call(p);find_group.call(p).entities}
# Non-coplanar material coursing, no duplicate veneer over old finish.
finish=lambda do |a,name,x,y,z,w,h,side=false|
 g=grp(a,name);e=g.entities
 point=lambda{|u,v|side ? [x.mm,(y+u).mm,(z+v).mm] : [(x+u).mm,y.mm,(z+v).mm]}
 (0...(h/65.0).ceil).each do |r|
  b=r*65.0+3;t=[h,(r+1)*65.0-3].min;next if t<=b
  (-1..(w/330.0).ceil).each do |c|
   l=[0,c*330.0+(r%2)*165+3].max;rr=[w,(c+1)*330.0+(r%2)*165-3].min;next if rr<=l
   f=e.add_face(point.call(l,b),point.call(rr,b),point.call(rr,t),point.call(l,t));next unless f
   f.material=tones[(r*19+c*7+r*c).abs%tones.size];f.back_material=f.material
  end
 end
 e.grep(Sketchup::Edge).each{|ed|ed.hidden=true}
end
# Exact leaf coping repairs. Butt joins avoid overlapping coplanar caps.
p=['INFERRED_RIGHT_WALL','INFERRED_RIGHT_WALL_COPING'];a=reset.call(p)
box(a,'CENTERED_RIGHT_CAP',10920,280,10700,310,11750,65,metal)
p=['MASS_LEFT','LEFT_RETURN','LEFT_RETURN_COPING'];a=reset.call(p)
box(a,'CENTERED_LEFT_CAP',-280,350,8200,310,11400,65,metal)
p=['INFERRED_REAR_WALL','INFERRED_REAR_WALL_COPING'];a=reset.call(p)
box(a,'REAR_CAP_BUTT',-280,11750,10700,11200,280,65,metal)
# Fill confirmed rear-left gap within the existing rear assembly, preserving openings.
a=find_group.call(['INFERRED_REAR_WALL','INFERRED_REAR_WALL_INFERRED_ASSEMBLY']).entities
box(a,'LEFT_CORNER_MASONRY_CLOSURE',-250,0,0,250,250,10700,brick)
# Front right corner: face top cap joins side cap without projecting strip.
# Roof link: align main slope with left roof. Build tapered deck and upstand in its existing leaf.
p=['ROOF_LEFT','INFERRED_REAR_ROOF_LINK'];a=reset.call(p)
g=grp(a,'SLOPED_LINK_DECK');e=g.entities
f=e.add_face([3550.mm,4400.mm,10486.5.mm],[4900.mm,4400.mm,10486.5.mm],[4900.mm,11750.mm,10376.25.mm],[3550.mm,11750.mm,10376.25.mm]);f.reverse! if f.normal.z<0;f.pushpull(-65.mm);g.material=metal
box(a,'LINK_MAIN_ROOF_UPSTAND',4850,4400,10376,50,7350,240,metal)
# Replace overlapping side fascias with separate extents; rear gutter has an open trough.
[['ROOF_TOP',3390,0,12120,5050,4400],['ROOF_LEFT',-100,3500,10320,3650,8800]].each do |n,x,y,z,w,d|
 [['LEFT',x],['RIGHT',x+w-90]].each do |edge,xx|
  a=reset.call([n,"#{n}_#{edge}_FASCIA"])
  box(a,"#{edge}_BUTT_FASCIA",xx,y+110,z,90,d-250,180,metal)
 end
 a=reset.call([n,"#{n}_REAR_GUTTER"])
 box(a,'TROUGH_BASE',x,y+d-140,z-25,w,140,25,metal)
 box(a,'TROUGH_OUTER_LIP',x,y+d-25,z,w,25,100,metal)
 box(a,'TROUGH_INNER_LIP',x,y+d-140,z,w,20,70,metal)
 box(a,'OUTLET',x+160,y+d-110,z-90,90,70,65,metal)
end
# Narrow-strip central lower division observed in photograph.
a=find_group.call(['FRONT_NARROW_WINDOW','WIDENED_FOUR_SECTION_STRIP']).entities
box(a,'LOWER_ALIGNED_MULLION',8720,30,3065,55,120,3085,metal)
# Existing finish leaves are cleared, keeping masonry/opening geometry unchanged.
[['LOW_LEFT_PIER',6000,3000,2100,3000],['HIGH_LEFT_PIER',4900,6000,3200,4700],['RIGHT_PIER',9400,3000,1800,7700],['WINDOW_APRON',8100,2900,1300,100],['WINDOW_HEAD',8100,9400,1300,1300]].each do |n,x,z,w,h|
 p=['MASS_RIGHT_BRICK',n,"#{n}_BRICK_COURSING","#{n}_FINISH"]
 a=reset.call(p);finish.call(a,'LONG_RED_BROWN_BOND',x,-3.5,0,w,h)
end
# Boundary prototype: solid masonry, visible coursing and cap; parents retained.
boundary=lambda do |a,name,x,y,w,d|
 g=grp(a,name);box(g.entities,'MASONRY',x,y,0,w,d,1560,brick)
 box(g.entities,'COPING',x-25,y-25,1560,w+50,d+50,40,metal)
 if w>d
  finish.call(g.entities,'OUTER_BOND',x,y-1,0,w,1560)
  finish.call(g.entities,'INNER_BOND',x,y+d+1,0,w,1560)
 else
  finish.call(g.entities,'OUTER_BOND',x-1,y,0,d,1560,true)
  finish.call(g.entities,'INNER_BOND',x+w+1,y,0,d,1560,true)
 end
end
a=reset.call(['BOUNDARY_LEFT'])
boundary.call(a,'FRONT_LEFT',-1500,-2700,5000,200)
boundary.call(a,'WEST_RETURN',-2600,-2500,200,16300)
boundary.call(a,'REAR_RETURN',-2600,13800,15500,200)
a=reset.call(['BOUNDARY_RIGHT'])
boundary.call(a,'FRONT_RIGHT',8000,-2700,4900,200)
boundary.call(a,'EAST_RETURN',12700,-2500,200,16300)
# Closed but editable gate leaves, all have pivots represented by independent groups.
gate=lambda do |a,name,x,w|
 g=grp(a,name);e=g.entities
 box(e,'FRAME_BOTTOM',x,-2685,30,w,60,45,metal);box(e,'FRAME_TOP',x,-2685,1515,w,60,45,metal)
 [x,x+w-45].each_with_index{|xx,i|box(e,"STILE_#{i}",xx,-2685,30,45,60,1530,metal)}
 (1...(w/90).floor).each{|i|box(e,"PICKET_#{i}",x+i*90,-2670,75,20,30,1440,metal)}
end
a=reset.call(['GATE_MAIN']);gate.call(a,'WALK_LEAF_L',3500,1545);gate.call(a,'WALK_LEAF_R',5055,1545);gate.call(a,'RIGHT_SERVICE_LEAF',6600,1400)
a=reset.call(['GATE_LEFT']);gate.call(a,'LEFT_SERVICE_LEAF',-2600,1100)
a=reset.call(['SITE']);box(a,'COURTYARD_PAVING',-2700,-3000,-150,15900,17100,150,concrete)
# Low planting leaves repaired walls and front openings visible.
def shrub(e,name,x,y,z,r,h,mat)
 g=grp(e,name);a=g.entities
 3.times do |i|
  zz=z+i*h/3.0;rr=r*(1-i*0.18)
  f=a.add_circle([(x+(i%2)*60).mm,y.mm,zz.mm],Z_AXIS,rr.mm,10);fc=a.add_face(f);fc.pushpull((h/3.0).mm)
 end
 g.material=mat
end
a=find_group.call(['PLANTERS']).entities
[[-1900,-1300,400,1200],[11450,-1450,420,1200],[-1400,4300,330,900],[12000,7800,350,900],[2300,13050,450,1100],[8500,13050,400,1100]].each_with_index do |v,i|
 x,y,r,h=v
 box(a,"GROUND_PLANTER_#{i}",x-r-80,y-r-80,0,2*r+160,2*r+160,200,metal)
 box(a,"SOIL_#{i}",x-r-45,y-r-45,200,2*r+90,2*r+90,40,soil)
 shrub(a,"GROUND_SHRUB_#{i}",x,y,240,r,h,leaf)
end
