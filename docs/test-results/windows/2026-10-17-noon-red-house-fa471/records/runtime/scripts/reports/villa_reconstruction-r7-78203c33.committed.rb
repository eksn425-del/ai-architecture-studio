# Revision 7: source entrance visibility, window division and roof landscape finish.
def grp(e,name)
 g=e.add_group;g.name=name;g
end
def box(e,name,x,y,z,w,d,h,mat)
 g=grp(e,name);f=g.entities.add_face([x.mm,y.mm,z.mm],[(x+w).mm,y.mm,z.mm],[(x+w).mm,(y+d).mm,z.mm],[x.mm,(y+d).mm,z.mm]);f.reverse! if f.normal.z<0;f.pushpull(h.mm);g.material=mat;g
end
find_group=lambda do |path|
 e=root.entities;g=nil;path.each{|n|g=e.grep(Sketchup::Group).find{|v|v.name==n};raise "Missing #{n}" unless g;e=g.entities};g
end
metal=model.materials['Anthracite metal'];leaf=model.materials['Courtyard leaves r6']
clear_owned_contents.call(['FRONT_NARROW_WINDOW','WIDENED_FOUR_SECTION_STRIP','LOWER_ALIGNED_MULLION'])
# Operable gate represented open, preserves complete boundary when closed.
[[['GATE_MAIN','WALK_LEAF_L'],3500,90],[['GATE_MAIN','WALK_LEAF_R'],6600,-90]].each do |p,x,angle|
 g=find_group.call(p);g.transform!(Geom::Transformation.rotation([x.mm,-2685.mm,0],Z_AXIS,angle.degrees))
end
# Existing main roof leaf: inferred 1.5 percent fall rearwards with flashing and outlet.
p=['SLABS','RIGHT_ROOF'];clear_owned_contents.call(p);a=find_group.call(p).entities
roof=model.materials.add('Roof warm zinc r7');roof.color=Sketchup::Color.new(123,125,119)
g=grp(a,'MAIN_FALLING_DECK');e=g.entities
f=e.add_face([4900.mm,280.mm,10580.mm],[10950.mm,280.mm,10580.mm],[10950.mm,11750.mm,10408.mm],[4900.mm,11750.mm,10408.mm]);f.reverse! if f.normal.z<0;f.pushpull(-65.mm);g.material=roof
# Flashings are distinct vertical returns with 20mm lower kick; no extra skin on wall faces.
box(a,'RIGHT_WALL_FLASHING',10920,360,10410,30,11390,260,metal)
box(a,'FRONT_WALL_FLASHING',4900,280,10580,6020,30,110,metal)
box(a,'REAR_UPSTAND',4900,11720,10410,6020,30,250,metal)
box(a,'REAR_CHANNEL_BASE',4900,11590,10395,6020,130,20,metal)
box(a,'CHANNEL_LIP',4900,11590,10415,6020,20,65,metal)
box(a,'DRAIN_OUTLET',10740,11620,10340,100,80,55,metal)
# Transverse standing seams follow fall; small profile and physically separated from deck.
(1..5).each do |i|
 x=4900+i*1000;g=grp(a,"ZINC_SEAM_#{i}");v=g.entities
 f=v.add_face([x.mm,310.mm,10581.5.mm],[(x+12).mm,310.mm,10581.5.mm],[(x+12).mm,11580.mm,10412.5.mm],[x.mm,11580.mm,10412.5.mm]);f.reverse! if f.normal.z<0;f.pushpull(12.mm);g.material=metal
end
# Individual closed low-poly foliage lobes, no adjacent pushpull surfaces.
def foliage(e,name,x,y,z,rx,ry,rz,mat,phase)
 g=grp(e,name);v=g.entities;n=12;rings=7;points=[]
 (0..rings).each do |j|
  latitude=-Math::PI/2+Math::PI*j/rings
  points[j]=(0...n).map do |i|
   phi=2*Math::PI*i/n;irregular=1+0.07*Math.sin(i*3.1+j*1.7+phase)
   [(x+rx*Math.cos(latitude)*Math.cos(phi)*irregular).mm,(y+ry*Math.cos(latitude)*Math.sin(phi)*irregular).mm,(z+rz*Math.sin(latitude)).mm]
  end
 end
 (0...rings).each do |j|
  (0...n).each do |i|
   k=(i+1)%n
   pts=j==0 ? [points[j][i],points[j+1][k],points[j+1][i]] : j==rings-1 ? [points[j][i],points[j][k],points[j+1][i]] : [points[j][i],points[j][k],points[j+1][k],points[j+1][i]]
   # nonplanar rings triangulated, pole duplicates avoided.
   if pts.length==4
    v.add_face(pts[0],pts[1],pts[2]);v.add_face(pts[0],pts[2],pts[3])
   else
    v.add_face(pts)
   end
  end
 end
 v.grep(Sketchup::Edge).each{|ed|ed.soft=true;ed.smooth=true};g.material=mat
end
[[-1900,-1300,400,1200],[11450,-1450,420,1200],[-1400,4300,330,900],[12000,7800,350,900],[2300,13050,450,1100],[8500,13050,400,1100]].each_with_index do |vals,i|
 x,y,r,h=vals;p=['PLANTERS',"GROUND_SHRUB_#{i}"];clear_owned_contents.call(p);a=find_group.call(p).entities
 [[0,0,0.85],[r*0.4,r*0.25,0.65],[-r*0.35,-r*0.25,0.65]].each_with_index do |arr,j|
  dx,dy,k=arr;foliage(a,"LEAF_LOBE_#{j}",x+dx,y+dy,240+h*k/2,r*k,r*k,h*k/2,leaf,i+j)
 end
end
