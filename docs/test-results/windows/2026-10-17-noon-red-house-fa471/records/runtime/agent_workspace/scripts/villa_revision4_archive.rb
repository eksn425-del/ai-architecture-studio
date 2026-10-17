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
  # Revision 4: deep lower reveal, substantial pavilion frame, physical brick relief.
  find_group=lambda do |path|
    e=root.entities;g=nil
    path.each{|n|g=e.grep(Sketchup::Group).find{|v|v.name==n};raise "Missing #{n}" unless g;e=g.entities};g
  end
  metal=model.materials['Anthracite metal']; glazing=model.materials['Grey transparent glazing']
  warm=model.materials.add('Warm balcony reveal r4');warm.color=Sketchup::Color.new(163,126,79)
  clear_owned_contents.call(['BALCONY_GLAZING','LOWER'])
  e=find_group.call(['BALCONY_GLAZING','LOWER']).entities
  window(e,'RECESSED_SLIDERS',3500,1550,3000,2100,2570,metal,glazing,3,1)
  box(e,'RIGHT_WARM_REVEAL',5600,400,3000,400,1260,2820,warm)
  box(e,'WARM_SOFFIT',3500,400,5570,2100,1260,200,warm)
  clear_owned_contents.call(['MASS_TOP_GLAZED','LEFT_FRAME'])
  box(find_group.call(['MASS_TOP_GLAZED','LEFT_FRAME']).entities,'THICK_LEFT_POST',3500,350,8600,240,3800,3520,metal)
  clear_owned_contents.call(['MASS_TOP_GLAZED','RIGHT_FRAME'])
  box(find_group.call(['MASS_TOP_GLAZED','RIGHT_FRAME']).entities,'THICK_RIGHT_POST',7960,350,8600,240,3800,3520,metal)
  clear_owned_contents.call(['TOP_GLAZING'])
  e=find_group.call(['TOP_GLAZING']).entities
  window(e,'THREE_BAY_FRAME',3740,350,8700,4220,3160,metal,glazing,3,2)
  box(e,'DEEP_HEADER',3500,250,11860,4700,350,260,metal)
  box(e,'LOWER_BASE',3500,250,8500,4700,350,200,metal)
  mortar=model.materials.add('Textured fine mortar r4');mortar.color=Sketchup::Color.new(154,127,105)
  tones=[]
  [[132,87,65],[157,106,80],[144,95,71],[166,113,85],[138,93,72],[151,101,78],[127,83,64],[159,109,86],[143,100,79],[150,96,69],[162,111,84]].each_with_index do |rgb,i|
    m=model.materials.add("Relief brick r4 #{i}");m.color=Sketchup::Color.new(*rgb);tones<<m
  end
  face_rect=lambda do |a,x,y,z,w,h,mat|
    f=a.add_face([x.mm,y.mm,z.mm],[(x+w).mm,y.mm,z.mm],[(x+w).mm,y.mm,(z+h).mm],[x.mm,y.mm,(z+h).mm]);f.material=mat;f.back_material=mat;f
  end
  courses=lambda do |path,x,y,z,w,h|
    clear_owned_contents.call(path);a=find_group.call(path).entities
    face_rect.call(a,x,y-0.6,z,w,h,mortar)
    pitch=65.0;bond=300.0
    ((z/pitch).floor...((z+h)/pitch).ceil).each do |r|
      b=[z,r*pitch+4].max;t=[z+h,(r+1)*pitch-3].min;next if t<=b
      (((x-(r%2)*bond/2)/bond).floor...((x+w-(r%2)*bond/2)/bond).ceil).each do |c|
        l=[x,c*bond+(r%2)*bond/2+4].max;rr=[x+w,(c+1)*bond+(r%2)*bond/2-4].min;next if rr<=l
        tone=(r*73+c*17+r*c*19).abs%tones.length
        f=face_rect.call(a,l,y-1.5,b,rr-l,t-b,tones[tone])
        f.reverse! if f.normal.y>0
        f.pushpull((1.5+(tone%4)*0.8).mm)
      end
    end
    a.grep(Sketchup::Edge).each{|ed|ed.hidden=true}
  end
  [['LOW_LEFT_PIER',6000,3000,2200,3000],['HIGH_LEFT_PIER',4900,6000,3300,4700],['RIGHT_PIER',9300,3000,1900,7700],['WINDOW_APRON',8200,3000,1100,200],['WINDOW_HEAD',8200,9400,1100,1300]].each do |n,x,z,w,h|
    courses.call(['MASS_RIGHT_BRICK',n,'BRICK_COURSING'],x,0,z,w,h)
  end
  courses.call(['BOUNDARY_LEFT','BRICK_COURSING'],-1500,-2700,0,5000,2200)
  courses.call(['BOUNDARY_RIGHT','BRICK_COURSING'],8000,-2700,0,4900,2200)
# Revision 4 approved exterior inference. Work inside existing exact leaf containers.
brick=model.materials['Warm terracotta brick'];concrete=model.materials['Warm grey concrete']
def inferred_wall(e,label,length,height,openings,brick,metal,glazing)
  xs=([0,length]+openings.flat_map{|o|[o[0],o[0]+o[2]]}).uniq.sort
  zs=([0,height]+openings.flat_map{|o|[o[1],o[1]+o[3]]}).uniq.sort
  xs.each_cons(2).with_index do |xx,i|
    zs.each_cons(2).with_index do |zz,j|
      mx=(xx[0]+xx[1])/2.0;mz=(zz[0]+zz[1])/2.0
      next if openings.any?{|o|mx>o[0] && mx<o[0]+o[2] && mz>o[1] && mz<o[1]+o[3]}
      box(e,"#{label}_WALL_#{i}_#{j}",xx[0],0,zz[0],xx[1]-xx[0],250,zz[1]-zz[0],brick)
    end
  end
  openings.each_with_index do |o,i|
    window(e,"#{label}_OPENING_#{i}",o[0],60,o[1],o[2],o[3],metal,glazing,o[2]>1500 ? 2 : 1,1)
    box(e,"#{label}_SILL_#{i}",o[0]-40,-35,o[1]-55,o[2]+80,320,55,metal)
  end
end
# All coordinates below are inferred; windows avoid the retained floor slabs.
[['INFERRED_RIGHT_WALL',11720,10700,[[7000,1400,1200,900],[7000,4300,1200,900],[7000,7300,1200,900]],11200,280,-90],
 ['INFERRED_REAR_WALL',10700,10700,[[4000,260,2400,2200],[1800,3800,1200,1500],[7200,3800,1200,1500],[1800,6800,1200,1500],[7200,6800,1200,1500],[4300,8900,1400,1500]],250,11750,0],
 ['LEFT_RETURN',11650,8200,[[5000,900,800,1500],[5000,3800,800,1500],[5000,6800,800,1400]],0,350,-90]].each do |n,len,ht,ops,ox,oy,angle|
  path=n=='LEFT_RETURN' ? ['MASS_LEFT','LEFT_RETURN'] : [n]
  clear_owned_contents.call(path);a=find_group.call(path).entities
  g=grp(a,"#{n}_INFERRED_ASSEMBLY")
  inferred_wall(g.entities,n,len,ht,ops,brick,metal,glazing)
  if angle==-90
    # local U follows +Y; local wall thickness faces inward at right, outward at left.
    g.transform!(Geom::Transformation.rotation(ORIGIN,Z_AXIS,90.degrees))
  end
  g.transform!(Geom::Transformation.translation([ox.mm,oy.mm,0]))
  box(a,"#{n}_COPING",n=='LEFT_RETURN' ? -40 : ox-40,n=='LEFT_RETURN' ? 350 : oy-40,ht, n=='INFERRED_REAR_WALL' ? len+80 : 330,n=='INFERRED_REAR_WALL' ? 330 : len+80,65,metal)
  if n=='INFERRED_REAR_WALL'
    box(a,'REAR_LANDING_INFERRED',4150,12000,130,2600,420,130,concrete)
    box(a,'REAR_STEP_INFERRED',4000,12420,0,2900,400,130,concrete)
    [350,10800].each_with_index{|x,i|box(a,"REAR_DOWNPIPE_#{i}",x,12010,0,85,85,10600,metal)}
  elsif n=='INFERRED_RIGHT_WALL'
    box(a,'RIGHT_REAR_DOWNPIPE',11205,11500,0,85,85,10600,metal)
  end
end
# Roof top: shallow fall to rear, perimeter trim, outlet; inferred concealed construction.
[['ROOF_TOP',3390,0,12120,5050,4400],['ROOF_LEFT',-100,3500,10320,3650,8800]].each do |n,x,y,z,w,d|
  clear_owned_contents.call([n]);a=find_group.call([n]).entities
  g=grp(a,"#{n}_FALLING_DECK");v=g.entities
  f=v.add_face([x.mm,y.mm,(z+180).mm],[(x+w).mm,y.mm,(z+180).mm],[(x+w).mm,(y+d).mm,(z+180-d*0.015).mm],[x.mm,(y+d).mm,(z+180-d*0.015).mm])
  f.reverse! if f.normal.z<0;f.pushpull(-65.mm);g.material=metal
  box(a,"#{n}_FRONT_FASCIA",x,y,z,w,110,180,metal)
  box(a,"#{n}_LEFT_FASCIA",x,y,z,90,d,180,metal)
  box(a,"#{n}_RIGHT_FASCIA",x+w-90,y,z,90,d,180,metal)
  box(a,"#{n}_REAR_GUTTER",x,y+d-140,z-20,w,140,100,metal)
end
# Current independent review: retain three top bays and balcony outlines; correct two-leaf entry and lower strip panes.
clear_owned_contents.call(['FRONT_NARROW_WINDOW','LOWER_VERTICAL'])
clear_owned_contents.call(['ENTRY','DOUBLE_DOOR'])
a=find_group.call(['ENTRY','DOUBLE_DOOR']).entities
door=model.materials.add('Entry two leaf dark r4');door.color=Sketchup::Color.new(37,34,29)
box(a,'LEFT_LEAF',4400,1730,260,795,90,2030,door)
box(a,'RIGHT_LEAF',5205,1730,260,795,90,2030,door)
box(a,'HANDLE_L',5150,1695,1000,15,35,310,concrete)
box(a,'HANDLE_R',5230,1695,1000,15,35,310,concrete)
clear_owned_contents.call(['ENTRY','BACK_WALL'])
a=find_group.call(['ENTRY','BACK_WALL']).entities
shadow=model.materials.add('Porch deep shadow r4');shadow.color=Sketchup::Color.new(18,19,17)
box(a,'RECESS_BACK',3300,1830,260,4000,170,2460,shadow)
box(a,'PORCH_HEADER',3300,1150,2290,4000,680,430,shadow)
box(a,'LEFT_REVEAL',3300,650,260,240,1170,2460,shadow)
box(a,'RIGHT_REVEAL',6860,650,260,240,1170,2460,shadow)
