# encoding: UTF-8
# Stages 3-5. Exact targets are supplied to the guarded writer.
def fg(parent,name)
  parent.entities.grep(Sketchup::Group).find { |g| g.name==name }
end
def cg(parent,name)
  g=parent.entities.add_group; g.name=name; g
end
def bx(parent,name,x,y,z,w,d,h,mat)
  g=cg(parent,name)
  f=g.entities.add_face([[x,y,z],[x+w,y,z],[x+w,y+d,z],[x,y+d,z]].map { |p| p.map { |v| v.mm } })
  f.reverse! if f.normal.z<0
  f.pushpull(h.mm)
  g.entities.grep(Sketchup::Face).each { |q| q.material=mat; q.back_material=mat }
  g
end
def mt(model,name,rgb)
  m=model.materials[name] || model.materials.add(name); m.color=Sketchup::Color.new(*rgb); m
end
def panel(parent,name,x,y,z,w,h,side,mat)
  side==0 ? bx(parent,name,x,y,z,w,26,h,mat) : bx(parent,name,x,y,z,26,w,h,mat)
end
def floor_z(k)
  k==0 ? 0 : 4200+(k-1)*3100
end
def ell(parent,name,x,y,z,rx,ry,rz,mat)
  g=cg(parent,name)
  rings=[]
  7.times do |i|
    a=-Math::PI/2+Math::PI*(i+0.02)/6.04
    rings << 10.times.map do |j|
      b=2*Math::PI*j/10
      [(x+rx*Math.cos(a)*Math.cos(b)).mm,(y+ry*Math.cos(a)*Math.sin(b)).mm,(z+rz*Math.sin(a)).mm]
    end
  end
  6.times do |i|
    10.times do |j|
      n=(j+1)%10
      f=g.entities.add_face(rings[i][j],rings[i][n],rings[i+1][n],rings[i+1][j])
      if f
        f.material=mat; f.back_material=mat
        f.edges.each { |e| e.soft=true; e.smooth=true }
      end
    end
  end
  g
end
def tree(parent,name,x,y,z,size,leaf,bark)
  g=cg(parent,name)
  bx(g,'TRUNK',x-50,y-50,z,100,100,size*0.65,bark)
  ell(g,'CROWN_A',x,y,z+size*0.74,size*0.37,size*0.32,size*0.42,leaf)
  ell(g,'CROWN_B',x+size*0.18,y-size*0.1,z+size*0.88,size*0.24,size*0.23,size*0.3,leaf)
  g
end
stone=mt(model,'Warm_limestone',[207,191,162])
light=mt(model,'Light_opaque_panel',[219,211,191])
dark=mt(model,'Bronze_mullion',[72,77,74])
glasses=[[131,161,176],[151,177,186],[101,133,147],[171,188,190]].each_with_index.map { |rgb,i| mt(model,"Glass_#{i}",rgb) }
floor=mt(model,'Slab_interior',[170,164,149])
roofmat=mt(model,'Terrace_paving',[179,174,155])
soil=mt(model,'Planter_soil',[76,68,49])
green=mt(model,'Leaf_mid',[70,102,51])
green2=mt(model,'Leaf_light',[100,125,65])
bark=mt(model,'Bark',[106,89,65])
railglass=mt(model,'Balustrade_glass',[157,182,177]); railglass.alpha=0.45
b=fg(root,'BUILDING')
# Retain the actual verified sample and its independent wall, no duplicated sample bay.
vols=[['TOWER',0,0,18000,14400,18],['LEFT_UPPER',-46800,3600,14400,18000,7],['LEFT_STREET',-32400,0,10800,10800,4]]
vols.each do |name,x,y,w,d,n|
  v=fg(b,name); m=fg(v,'MASSING'); clear_owned_contents.call(['BUILDING',name,'MASSING'])
  n.times do |k|
    next if name=='TOWER' && k==1
    z=floor_z(k)
    bx(m,"FLOOR_#{k.to_s.rjust(2,'0')}",x+50,y+50,z-220,w-100,d-100,220,floor)
  end
  bx(m,'CORE_INFERRED',x+w*0.35,y+d*0.55,0,w*0.30,d*0.28,floor_z(n),light)
end
s=fg(b,'STEPPED_WING'); sm=fg(s,'MASSING'); clear_owned_contents.call(['BUILDING','STEPPED_WING','MASSING'])
13.times do |k|
  x=k<4 ? -21600 : (k<6 ? -10800 : (k<8 ? -8100 : (k<10 ? -5400 : -2700)))
  bx(sm,"FLOOR_#{k.to_s.rjust(2,'0')}",x+50,50,floor_z(k)-220,-x-50,14300,220,floor)
end
# Facade routine: segmented grid, alternating opaque infills, recessed glazed bays.
def facade(parent,label,x,y,w,d,n,bay,stone,light,dark,glasses,railglass,sample=false,left_edge=true,right_edge=true)
  n.times do |k|
    z=floor_z(k); h=k==0 ? 4200 : 3100
    frame=k>=2 && k<=4 ? dark : stone
    row=cg(parent,"#{label}_L#{k.to_s.rjust(2,'0')}")
    count=(w/bay).round
    (count+1).times do |j|
      next if sample && k==1 && (j==4 || j==5)
      bx(row,"FRONT_POST_#{j}",x+j*bay-110,y-300,z,220,500,h,frame)
    end
    count.times do |j|
      next if sample && k==1 && j==4
      xx=x+j*bay
      bx(row,"FRONT_HEAD_#{j}",xx-110,y-300,z+h-220,bay+220,500,220,frame)
      inset=((k*7+j*3)%17==4 && k>1) ? 1200 : 100
      glass=glasses[(k+j)%4]
      panel(row,"FRONT_GLAZING_#{j}",xx+180,y+inset,z+180,bay-360,h-440,0,glass)
      bx(row,"FRONT_MULLION_#{j}",xx+bay*0.54,y+inset-35,z+180,48,65,h-440,dark)
      if (k+j*2)%5==1 && k>0
        panel(row,"FRONT_OPAQUE_#{j}",xx+180,y+70,z+180,bay*0.28,h-440,0,light)
      end
      if inset>100
        panel(row,"FRONT_BALUSTRADE_#{j}",xx+180,y-30,z+180,bay-360,1000,0,railglass)
        bx(row,"FRONT_RAIL_#{j}",xx+160,y-60,z+1170,bay-320,50,50,dark)
      end
      panel(row,"REAR_GLAZING_#{j}",xx+160,y+d-100,z+220,bay-320,h-480,0,glasses[(j+k+2)%4])
      bx(row,"REAR_HEAD_#{j}",xx-110,y+d-200,z+h-220,bay+220,500,220,stone)
      bx(row,"REAR_POST_#{j}",xx-110,y+d-200,z,220,500,h,stone)
    end
    [[0,left_edge],[w,right_edge]].each do |a|
      next unless a[1]
      sx=x+a[0]; right=a[0]>0; sign=right ? 1 : -1
      sidebay=3600.0; cnt=(d/sidebay).round; sb=d/cnt
      (cnt+1).times do |j|
        next if sample && right && k==1 && j==0
        bx(row,"#{right ? 'RIGHT' : 'LEFT'}_POST_#{j}",sx-(right ? 200 : 300),y+j*sb-110,z,500,220,h,frame)
      end
      cnt.times do |j|
        next if sample && right && k==1 && j==0
        yy=y+j*sb
        bx(row,"#{right ? 'RIGHT' : 'LEFT'}_HEAD_#{j}",sx-(right ? 200 : 300),yy-110,z+h-220,500,sb+220,220,frame)
        recessed=right && ((k*3+j)%11==2) && k>0
        gx=sx-sign*(recessed ? 1400 : 100)
        panel(row,"#{right ? 'RIGHT' : 'LEFT'}_GLASS_#{j}",gx,yy+180,z+180,sb-360,h-440,1,glasses[(k+j+1)%4])
        bx(row,"#{right ? 'RIGHT' : 'LEFT'}_MULLION_#{j}",gx-25,yy+sb*0.54,z+180,65,48,h-440,dark)
        if (k+j)%6==2 && !recessed
          panel(row,"SIDE_OPAQUE_#{right}_#{j}",sx-sign*70,yy+180,z+180,sb*0.25,h-440,1,light)
        end
        if recessed
          panel(row,"SIDE_BALUSTRADE_#{j}",sx-sign*30,yy+180,z+180,sb-360,1000,1,railglass)
          bx(row,"SIDE_RAIL_#{j}",sx-50,yy+160,z+1170,50,sb-320,50,dark)
        end
      end
    end
  end
end
vols.each do |name,x,y,w,d,n|
  v=fg(b,name); f=cg(v,'FACADE')
  facade(f,name,x,y,w,d,n,3600.0,stone,light,dark,glasses,railglass,name=='TOWER',name!='TOWER',true)
end
sf=cg(s,'FACADE')
[['LINK',-21600,10800,4],['STEP_1',-10800,2700,6],['STEP_2',-8100,2700,8],['STEP_3',-5400,2700,10],['STEP_4',-2700,2700,13]].each do |a|
  facade(sf,a[0],a[1],0,a[2],14400,a[3],a[2]==10800 ? 3600.0 : 2700.0,stone,light,dark,glasses,railglass,false,true,false)
end
# Roofs: finish profiles cannot be made with the straight-wall-only helper.
def roofedge(parent,name,x,y,w,d,z,roofmat,stone,dark,railglass)
  g=cg(parent,name)
  bx(g,'ROOF_DECK',x+50,y+50,z-220,w-100,d-100,220,roofmat)
  bx(g,'FRONT_COPING',x-110,y-300,z, w+220,500,180,stone)
  bx(g,'LEFT_COPING',x-300,y,z,500,d,180,stone)
  bx(g,'REAR_COPING',x-110,y+d-200,z,w+220,500,180,stone)
  panel(g,'FRONT_GUARD_GLASS',x+100,y-70,z+180,w-200,820,0,railglass)
  bx(g,'FRONT_TOPRAIL',x,y-100,z+1000,w,45,45,dark)
  panel(g,'LEFT_GUARD_GLASS',x-70,y+100,z+180,d-200,820,1,railglass)
  bx(g,'LEFT_TOPRAIL',x-100,y,z+1000,45,d,45,dark)
  bx(g,'REAR_PARAPET',x,y+d-180,z,w,180,800,stone)
  g
end
vols.each do |name,x,y,w,d,n|
  roofedge(fg(b,name),'ROOF',x,y,w,d,floor_z(n),roofmat,stone,dark,railglass)
end
tr=cg(s,'TERRACES')
terraces=[[-21600,10800,13500],[-10800,2700,19700],[-8100,2700,25900],[-5400,2700,32100],[-2700,2700,41400]]
terraces.each_with_index { |a,i| roofedge(tr,"TERRACE_#{i}",a[0],0,a[1],14400,a[2],roofmat,stone,dark,railglass) }
# Add lightweight neighbour detail without changing its approved envelope.
nb=fg(fg(root,'CONTEXT'),'RIGHT_NEIGHBOR')
nf=cg(nb,'VISIBLE_FACADE')
8.times do |k|
  10.times do |j|
    xx=21800+j*2170; zz=4900+k*2950
    bx(nf,"WINDOW_#{k}_#{j}",xx,8450,zz,1000,36,k<5 ? 1850 : 1000,dark)
    bx(nf,"WINDOW_BAR_#{k}_#{j}",xx+490,8400,zz,32,60,k<5 ? 1850 : 1000,stone)
  end
end
10.times { |j| bx(nf,"SHOP_#{j}",21400+j*2200,8400,0,1600,80,3900,dark) }
bx(nf,'GREEN_ENDWALL',44010,8500,0,110,16000,29000,green)
# Source-authorized planting is outside occupied envelope, grouped separately.
veg=cg(root,'VEGETATION'); vr=cg(veg,'ROOF_INSTANCES'); vt=cg(veg,'TERRACE_INSTANCES'); vs=cg(veg,'STREET_INSTANCES')
def planter(parent,name,x,y,z,w,d,stone,soil,leaf)
  g=cg(parent,name)
  bx(g,'BOX',x,y,z,w,d,550,stone)
  bx(g,'SOIL',x+80,y+80,z+550,w-160,d-160,40,soil)
  ell(g,'SHRUB',x+w*0.5,y+d*0.5,z+850,w*0.43,d*0.43,450,leaf)
  g
end
[[0,0,18000,14400,56900],[-46800,3600,14400,18000,22800],[-32400,0,10800,10800,13500]].each_with_index do |a,i|
  x,y,w,d,z=a
  (w/3000).floor.times do |j|
    planter(vr,"ROOF_#{i}_PLANTER_#{j}",x+600+j*2800,y+600,z,2200,1300,stone,soil,j.even? ? green : green2)
    tree(vr,"ROOF_#{i}_TREE_#{j}",x+1700+j*2800,y+1250,z+590,1700+(j%3)*300,green,bark)
  end
end
terraces.each_with_index do |a,i|
  x,w,z=a
  [1800,5200,8800,12200].each_with_index do |yy,j|
    planter(vt,"T#{i}_P#{j}",x+500,yy,z,[w-1000,2500].min,1200,stone,soil,green2)
    tree(vt,"T#{i}_TREE#{j}",x+[w*0.5,1700].min,yy+600,z+590,1700+(j%2)*500,green,bark)
  end
end
[-43000,-35500,-27000,-17000,-8000,4000,13000,25000,36000].each_with_index do |x,i|
  planter(vs,"STREET_BED_#{i}",x-1700,-3100,0,3400,1800,stone,soil,green)
  tree(vs,"STREET_TREE_#{i}",x,-2200,590,4500+(i%3)*300,green,bark)
end
# Foreground intersection, rail track, curbs and contact lines.
asphalt=mt(model,'Asphalt',[67,74,82]); pave=mt(model,'Paving',[153,155,151]); white=mt(model,'Marking',[204,211,210]); ballast=mt(model,'Ballast',[100,107,111]); steel=mt(model,'Rail_steel',[157,162,164]); sleeper=mt(model,'Sleeper',[111,112,106]); wire=mt(model,'Contact_wire',[43,46,44])
env=cg(root,'ENVIRONMENT'); road=cg(env,'INTERSECTION'); curbs=cg(env,'CURBS'); tracks=cg(env,'TRACKS'); wires=cg(env,'CONTACT_WIRES')
bx(road,'MAIN_ROAD',-66000,-39000,-380,126000,33000,200,asphalt)
bx(road,'CROSS_STREET',-58000,-53000,-380,12000,74000,200,asphalt)
bx(curbs,'BUILDING_SIDEWALK',-46800,-6000,-180,106800,6000,180,pave)
bx(curbs,'FAR_CORNER_PAVEMENT',-66000,-6000,-180,8000,27000,180,pave)
bx(curbs,'FOREGROUND_PAVEMENT',-42000,-53000,-300,102000,7000,200,pave)
bx(curbs,'CURB_FRONT',-46800,-6150,-180,106800,150,160,stone)
18.times do |i|
  bx(road,"LANE_DASH_#{i}",-64000+i*7000,-22500,-171,2800,180,12,white)
end
12.times do |i|
  bx(road,"CROSSING_#{i}",-57500,-7000-i*1200,-170,10500,470,12,white)
end
bx(tracks,'TRACK_BED',-66000,-45500,-500,126000,6500,240,ballast)
180.times do |i|
  bx(tracks,"SLEEPER_#{i}",-66000+i*700,-43300,-260,210,2800,180,sleeper)
end
[-42717.5,-41282.5].each_with_index do |y,i|
  bx(tracks,"RAIL_FOOT_#{i}",-66000,y-75,-80,126000,150,20,steel)
  bx(tracks,"RAIL_WEB_#{i}",-66000,y-18,-60,126000,36,100,steel)
  bx(tracks,"RAIL_HEAD_#{i}",-66000,y-36,40,126000,72,35,steel)
  bx(wires,"CONTACT_#{i}",-66000,y,6000,126000,18,18,wire)
  bx(wires,"MESSENGER_#{i}",-66000,y,6800,126000,14,14,wire)
  13.times { |j| bx(wires,"DROPPER_#{i}_#{j}",-66000+j*10000,y,6018,14,14,780,wire) }
end
