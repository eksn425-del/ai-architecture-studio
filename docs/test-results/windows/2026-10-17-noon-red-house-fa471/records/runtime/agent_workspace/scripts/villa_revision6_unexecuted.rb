# UNEXECUTED candidate: writer budget rejected; live revision remains 5.
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

# Revision 6: final scoped source detail pass.
find_group=lambda do |path|
 e=root.entities;g=nil
 path.each{|n|g=e.grep(Sketchup::Group).find{|v|v.name==n};raise "Missing #{n}" unless g;e=g.entities};g
end
metal=model.materials['Anthracite metal']
a=find_group.call(['FRONT_NARROW_WINDOW','WIDENED_FOUR_SECTION_STRIP']).entities
box(a,'LOWER_ALIGNED_MULLION',8720,30,3065,55,120,3085,metal)
mortar=model.materials.add('Recessed sand mortar r6');mortar.color=Sketchup::Color.new(151,123,100)
tones=[]
[[144,94,70],[151,101,76],[158,106,79],[146,97,74],[161,110,83],[153,100,73],[148,100,77],[157,103,76],[141,93,71],[154,105,82],[149,97,71]].each_with_index{|rgb,i|m=model.materials.add("Rough face r6 #{i}");m.color=Sketchup::Color.new(*rgb);tones<<m}
courses=lambda do |path,x,y,z,w,h|
 clear_owned_contents.call(path);a=find_group.call(path).entities
 f=a.add_face([x.mm,y.mm,z.mm],[(x+w).mm,y.mm,z.mm],[(x+w).mm,y.mm,(z+h).mm],[x.mm,y.mm,(z+h).mm]);f.material=mortar;f.back_material=mortar
 pitch=65.0;bond=340.0
 ((z/pitch).floor...((z+h)/pitch).ceil).each do |r|
  b=[z,r*pitch+4].max;t=[z+h,(r+1)*pitch-3].min;next if t<=b
  (((x-r%2*bond/2)/bond).floor...((x+w-r%2*bond/2)/bond).ceil).each do |c|
   l=[x,c*bond+r%2*bond/2+4].max;rr=[x+w,(c+1)*bond+r%2*bond/2-4].min;next if rr<=l
   n=(Math.sin(r*12.9898+c*78.233)*43758.5453).abs
   tone=((n-n.floor)*tones.length).floor
   jitter=(tone%3)*0.7
   f=a.add_face([l.mm,(y-1).mm,(b+jitter).mm],[rr.mm,(y-1).mm,b.mm],[rr.mm,(y-1).mm,(t-jitter).mm],[l.mm,(y-1).mm,t.mm]);next unless f
   f.material=tones[tone];f.back_material=tones[tone];f.reverse! if f.normal.y>0;f.pushpull((1.8+tone%4*0.65).mm)
  end
 end
 a.grep(Sketchup::Edge).each{|ed|ed.hidden=true}
end
[['LOW_LEFT_PIER',6000,3000,2100,3000],['HIGH_LEFT_PIER',4900,6000,3200,4700],['RIGHT_PIER',9400,3000,1800,7700],['WINDOW_APRON',8100,2900,1300,100],['WINDOW_HEAD',8100,9400,1300,1300]].each do |n,x,z,w,h|
 # Existing finish children are translated by z in their parent; use local z0.
 courses.call(['MASS_RIGHT_BRICK',n,"#{n}_BRICK_COURSING","#{n}_FINISH"],x,-1,0,w,h)
end
courses.call(['BOUNDARY_LEFT','BRICK_COURSING'],-1500,-2700,0,5000,2200)
courses.call(['BOUNDARY_RIGHT','BRICK_COURSING'],8000,-2700,0,4900,2200)
