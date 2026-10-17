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

# Revision 5: continuous inferred side/rear masonry, roof closure and front strip width.
find_group=lambda do |path|
  e=root.entities;g=nil
  path.each{|n|g=e.grep(Sketchup::Group).find{|v|v.name==n};raise "Missing #{n}" unless g;e=g.entities};g
end
metal=model.materials['Anthracite metal'];glazing=model.materials['Grey transparent glazing'];brick=model.materials['Warm terracotta brick']
mortar=model.materials.add('Side mortar r5');mortar.color=Sketchup::Color.new(143,117,96)
tones=[]
[[148,96,72],[155,103,77],[152,100,74],[160,107,81],[145,94,70],[154,101,75],[150,99,76]].each_with_index{|rgb,i|m=model.materials.add("Side brick r5 #{i}");m.color=Sketchup::Color.new(*rgb);tones<<m}
def hide_wall_edges(g)
  g.entities.grep(Sketchup::Edge).each{|e|e.hidden=true}
  g.entities.grep(Sketchup::Group).each{|c|hide_wall_edges(c) if c.name.include?('_WALL_')}
end
finish=lambda do |a,name,len,ht,ops,origin,ux,uy|
  g=grp(a,name);e=g.entities
  point=lambda{|u,z,depth|[(origin[0]+ux[0]*u+uy[0]*depth).mm,(origin[1]+ux[1]*u+uy[1]*depth).mm,z.mm]}
  rect=lambda do |u,z,w,h,depth,mat|
    f=e.add_face(point.call(u,z,depth),point.call(u+w,z,depth),point.call(u+w,z+h,depth),point.call(u,z+h,depth));if f;f.material=mat;f.back_material=mat;end
  end
  pitch=65.0;bond=300.0
  (0...(ht/pitch).ceil).each do |r|
    z0=r*pitch;z1=[ht,(r+1)*pitch].min
    zz=([z0,z1]+ops.flat_map{|o|[o[1],o[1]+o[3]]}.select{|z|z>z0 && z<z1}).uniq.sort
    zz.each_cons(2) do |b,t|
      spans=[[0.0,len.to_f]];mid=(b+t)/2
      ops.select{|o|mid>o[1] && mid<o[1]+o[3]}.each do |o|
        spans=spans.flat_map{|l,h|[[l,[h,o[0]].min],[[l,o[0]+o[2]].max,h]].select{|l,h|h>l}}
      end
      spans.each do |l,h|
        rect.call(l,b,h-l,t-b,0,mortar)
        c0=((l-r%2*bond/2)/bond).floor;c1=((h-r%2*bond/2)/bond).ceil
        (c0...c1).each do |c|
          left=[l,c*bond+r%2*bond/2+4].max;right=[h,(c+1)*bond+r%2*bond/2-4].min
          low=[b,z0+4].max;high=[t,z1-3].min
          next if right<=left || high<=low
          rect.call(left,low,right-left,high-low,1.5,tones[(r*37+c*13+r*c).abs%tones.length])
        end
      end
    end
  end
  e.grep(Sketchup::Edge).each{|ed|ed.hidden=true}
end
[['INFERRED_RIGHT_WALL',11720,10700,[[7000,1400,1200,900],[7000,4300,1200,900],[7000,7300,1200,900]],[11201,280],[0,1],[1,0]],
 ['INFERRED_REAR_WALL',10700,10700,[[4000,260,2400,2200],[1800,3800,1200,1500],[7200,3800,1200,1500],[1800,6800,1200,1500],[7200,6800,1200,1500],[4300,8900,1400,1500]],[250,12001],[1,0],[0,1]],
 ['LEFT_RETURN',11650,8200,[[5000,900,800,1500],[5000,3800,800,1500],[5000,6800,800,1400]],[-251,350],[0,1],[-1,0]]].each do |n,len,ht,ops,origin,ux,uy|
  path=n=='LEFT_RETURN' ? ['MASS_LEFT','LEFT_RETURN'] : [n]
  a=find_group.call(path).entities
  a.grep(Sketchup::Group).each{|g|hide_wall_edges(g) if g.name.include?('ASSEMBLY')}
  finish.call(a,"#{n}_CONTINUOUS_BRICK",len,ht,ops,origin,ux,uy)
end
# Close the previously exposed strip between the left rear pavilion and right main roof.
a=find_group.call(['ROOF_LEFT']).entities
box(a,'INFERRED_REAR_ROOF_LINK',3550,4400,10335,1350,7350,65,metal)
box(a,'LEFT_ROOF_DOWNPIPE',-110,12000,0,85,85,10370,metal)
# Front strip 1300mm wide, estimated from image ratio; preserve center and head.
[['LOW_LEFT_PIER',6000,3000,2100,3000],['HIGH_LEFT_PIER',4900,6000,3200,4700],['RIGHT_PIER',9400,3000,1800,7700],['WINDOW_APRON',8100,2900,1300,100],['WINDOW_HEAD',8100,9400,1300,1300]].each do |n,x,z,w,h|
  path=['MASS_RIGHT_BRICK',n];clear_owned_contents.call(path);a=find_group.call(path).entities
  box(a,"#{n}_SOLID",x,0,z,w,280,h,brick)
  # Same editable coursing on each source-supported pier.
  finish.call(a,"#{n}_BRICK",w,h,[],[x,-1],[1,0],[0,-1]) if z==0
  g=grp(a,"#{n}_BRICK_COURSING");finish.call(g.entities,"#{n}_FINISH",w,h,[],[x,-1],[1,0],[0,-1]);g.transform!(Geom::Transformation.translation([0,0,z.mm]))
  a.grep(Sketchup::Group).each{|g|hide_wall_edges(g) if g.name.include?('SOLID')}
end
clear_owned_contents.call(['FRONT_NARROW_WINDOW']);a=find_group.call(['FRONT_NARROW_WINDOW']).entities
window(a,'WIDENED_FOUR_SECTION_STRIP',8100,30,3000,1300,6400,metal,glazing,1,4)
box(a,'UPPER_PAIR_VERTICAL',8720,30,6400,55,120,2935,metal)
box(a,'CENTRAL_BAND',8100,20,6150,1300,170,320,metal)
