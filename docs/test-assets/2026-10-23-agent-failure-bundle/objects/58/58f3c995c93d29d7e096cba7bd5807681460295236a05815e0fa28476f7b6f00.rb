# encoding: UTF-8
# r4 review: full-depth side loggias, layered left-wing planted pockets, neighbour rhythm.
def fg(p,n); p.entities.grep(Sketchup::Group).find { |g| g.name==n }; end
def cg(p,n); g=p.entities.add_group; g.name=n; g; end
def bx(p,n,x,y,z,w,d,h,m)
  g=cg(p,n); f=g.entities.add_face([[x,y,z],[x+w,y,z],[x+w,y+d,z],[x,y+d,z]].map { |q| q.map { |v| v.mm } }); f.reverse! if f.normal.z<0; f.pushpull(h.mm)
  g.entities.grep(Sketchup::Face).each { |q| q.material=m; q.back_material=m }; g.entities.grep(Sketchup::Edge).each { |e| e.hidden=true }; g
end
def crown(p,n,x,y,z,rx,ry,rz,m)
  g=cg(p,n); rings=[]
  7.times do |i|
    a=-Math::PI/2+Math::PI*(i+0.02)/6.04
    rings << 10.times.map { |j| b=Math::PI*2*j/10; [(x+rx*Math.cos(a)*Math.cos(b)).mm,(y+ry*Math.cos(a)*Math.sin(b)).mm,(z+rz*Math.sin(a)).mm] }
  end
  6.times do |i|
    10.times do |j|
      nn=(j+1)%10; f=g.entities.add_face(rings[i][j],rings[i][nn],rings[i+1][nn],rings[i+1][j]); if f; f.material=m; f.back_material=m; end
    end
  end
  g.entities.grep(Sketchup::Edge).each { |e| e.hidden=true; e.soft=true; e.smooth=true }; g
end
stone=model.materials['Warm_limestone']; light=model.materials['Light_opaque_panel']; dark=model.materials['Bronze_mullion']; glass=model.materials['Glass_2']; guard=model.materials['Balustrade_glass']; paving=model.materials['Terrace_paving']; green=model.materials['Leaf_mid']; green2=model.materials['Leaf_light']; soil=model.materials['Planter_soil']
b=fg(root,'BUILDING'); tf=fg(fg(b,'TOWER'),'FACADE')
locations=[[4,1],[7,3],[8,0],[11,2],[15,1],[5,3],[8,3],[11,3],[14,3]]
locations.each do |k,j|
  row=fg(tf,"TOWER_L#{k.to_s.rjust(2,'0')}"); z=4200+(k-1)*3100; yy=j*3600
  gl=fg(row,"RIGHT_GLASS_#{j}"); mu=fg(row,"RIGHT_MULLION_#{j}")
  dx=16000-gl.bounds.min.x.to_mm
  gl.transform!(Geom::Transformation.translation([dx.mm,0,0]))
  mu.transform!(Geom::Transformation.translation([dx.mm,0,0]))
  op=fg(row,"SIDE_OPAQUE_true_#{j}")
  if op
    odx=16000-op.bounds.min.x.to_mm; op.transform!(Geom::Transformation.translation([odx.mm,0,0]))
  end
  g=cg(row,"LOGGIA_#{j}_DEPTH")
  bx(g,'FLOOR',16000,yy+180,z+5,1950,3240,100,paving)
  bx(g,'RETURN_NEAR',16000,yy+170,z+100,1900,110,2780,light)
  bx(g,'RETURN_FAR',16000,yy+3320,z+100,1900,110,2780,light)
  bx(g,'SOFFIT',16000,yy+180,z+2880,1900,3240,110,light)
  oldguard=fg(row,"SIDE_BALUSTRADE_#{j}")
  if oldguard
    dd=17930-oldguard.bounds.min.x.to_mm; oldguard.transform!(Geom::Transformation.translation([dd.mm,0,0]))
  else
    bx(g,'GUARD_GLASS',17930,yy+280,z+150,24,3040,1000,guard)
    bx(g,'HANDRAIL',17920,yy+270,z+1150,45,3060,45,dark)
  end
  bx(g,'EDGE_POST_NEAR',17920,yy+270,z+105,45,45,1045,dark)
  bx(g,'EDGE_POST_FAR',17920,yy+3290,z+105,45,45,1045,dark)
end
# Left 7/6/5/4-storey transition: two small glazed pavilions support occupied roof pockets.
lr=fg(fg(b,'LEFT_STREET'),'ROOF'); pockets=cg(lr,'PLANTED_POCKETS')
[[ -32400,5400,13500,16600],[-32400,2700,16600,19700]].each_with_index do |a,i|
  x,w,z,top=a; y=7200; d=3600; g=cg(pockets,"POCKET_#{i}")
  bx(g,'BACKING',x+100,y+3400,z,w-200,200,top-z,light)
  bx(g,'FRONT_GLASS',x+150,y+500,z+150,w-300,30,top-z-400,glass)
  bx(g,'RIGHT_GLASS',x+w-500,y+150,z+150,30,d-300,top-z-400,glass)
  [x,x+w/2,x+w].each_with_index { |xx,j| bx(g,"POST_#{j}",xx-150,y,z,300,650,top-z,stone) }
  bx(g,'ROOF_SLAB',x+50,y+50,top-220,w-100,d-100,220,paving)
  bx(g,'FRONT_BEAM',x-150,y,top-320,w+300,650,320,stone)
  bx(g,'RIGHT_BEAM',x+w-400,y,top-320,650,d,320,stone)
  bx(g,'RIGHT_GUARD',x+w-50,y+100,top,24,d-200,1050,guard)
  bx(g,'RIGHT_TOPRAIL',x+w-60,y,top+1050,50,d,50,dark)
  bx(g,'FRONT_GUARD',x+100,y+150,top,w-200,24,1050,guard)
  bx(g,'FRONT_TOPRAIL',x,y+130,top+1050,w,50,50,dark)
end
# New planting leaf separate from building geometry; retain prior roof and terrace plants.
pv=cg(fg(root,'VEGETATION'),'LEFT_POCKET_INSTANCES')
[[ -29200,7800,16600,1600,1000],[-31900,7800,19700,1700,1200],[-26400,7800,13500,1500,1100],[-30000,3000,13500,2200,1200]].each_with_index do |a,i|
  x,y,z,w,d=a; g=cg(pv,"POCKET_PLANT_#{i}")
  bx(g,'PLANTER',x,y,z,w,d,600,stone); bx(g,'SOIL',x+80,y+80,z+600,w-160,d-160,40,soil)
  crown(g,'SHRUB',x+w/2,y+d/2,z+1000,w*0.43,d*0.43,600,green2)
  crown(g,'CANOPY',x+w/2,y+d/2,z+1950,700,600,1100,green)
end
# Neighbor: nine single punched openings rather than two pale-divided slits per opening.
nf=fg(fg(fg(root,'CONTEXT'),'RIGHT_NEIGHBOR'),'VISIBLE_FACADE')
8.times do |k|
  9.times do |j|
    w=fg(nf,"WINDOW_#{k}_#{j}"); bar=fg(nf,"WINDOW_BAR_#{k}_#{j}")
    if k==5 || k==6 || k==7
      target=k==5 ? 1850 : 1200
      [w,bar].each do |q|
        h=(q.bounds.max.z-q.bounds.min.z).to_mm; q.transform!(Geom::Transformation.scaling(q.bounds.min,1,1,target/h))
      end
    end
    bar.entities.grep(Sketchup::Face).each { |f| f.material=dark; f.back_material=dark }
  end
end
