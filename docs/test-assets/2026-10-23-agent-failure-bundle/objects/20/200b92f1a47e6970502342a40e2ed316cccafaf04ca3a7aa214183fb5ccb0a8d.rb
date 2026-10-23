# encoding: UTF-8
# r5 review: strengthen existing layered low-wing pockets; one small neighbor top row.
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
stone=model.materials['Warm_limestone']; light=model.materials['Light_opaque_panel']; glass=model.materials['Glass_2']; guard=model.materials['Balustrade_glass']; dark=model.materials['Bronze_mullion']; paving=model.materials['Terrace_paving']; green=model.materials['Leaf_mid']; green2=model.materials['Leaf_light']; soil=model.materials['Planter_soil']
p=fg(fg(fg(fg(root,'BUILDING'),'LEFT_STREET'),'ROOF'),'PLANTED_POCKETS'); clear_owned_contents.call(['BUILDING','LEFT_STREET','ROOF','PLANTED_POCKETS'])
[[ -32400,7200,2700,8100,13500,16600],[-32400,3600,5400,5400,16600,19700]].each_with_index do |a,i|
  x,w,y,d,z,top=a; g=cg(p,"POCKET_#{i}")
  bx(g,'BACKING',x+100,y+d-200,z,w-200,200,top-z,light)
  bx(g,'GLAZED_BACK_OF_RECESS',x+200,y+1000,z+150,w-400,30,top-z-500,glass)
  bx(g,'RIGHT_GLASS',x+w-850,y+200,z+150,30,d-400,top-z-500,glass)
  bx(g,'FRONT_RETURN_LEFT',x,y,z,200,1000,top-z,light)
  bx(g,'FRONT_RETURN_RIGHT',x+w-200,y,z,200,1000,top-z,light)
  (w/1800).to_i.times { |j| bx(g,"POST_#{j}",x+j*1800-150,y,z,300,650,top-z,stone) }
  bx(g,'ROOF_SLAB',x+50,y+50,top-220,w-100,d-100,220,paving)
  bx(g,'FRONT_BEAM',x-150,y,top-350,w+300,650,350,stone)
  bx(g,'RIGHT_BEAM',x+w-400,y,top-350,650,d,350,stone)
  bx(g,'FRONT_SOLID_PARAPET',x+80,y+80,top,w-160,220,450,stone)
  bx(g,'RIGHT_SOLID_PARAPET',x+w-220,y+80,top,220,d-160,450,stone)
  bx(g,'FRONT_UPPER_GUARD',x+100,y+150,top+450,w-200,24,650,guard)
  bx(g,'RIGHT_UPPER_GUARD',x+w-150,y+100,top+450,24,d-200,650,guard)
  bx(g,'FRONT_TOPRAIL',x,y+130,top+1100,w,50,50,dark)
  bx(g,'RIGHT_TOPRAIL',x+w-160,y,top+1100,50,d,50,dark)
end
pv=fg(fg(root,'VEGETATION'),'LEFT_POCKET_INSTANCES'); clear_owned_contents.call(['VEGETATION','LEFT_POCKET_INSTANCES'])
[[ -32150,3100,16600,6600,800],[-32150,5750,19700,3100,800],[-24700,3000,13500,2000,900]].each_with_index do |a,i|
  x,y,z,w,d=a; g=cg(pv,"INTEGRATED_PLANTED_EDGE_#{i}")
  bx(g,'PLANTER',x,y,z,w,d,650,stone); bx(g,'SOIL',x+80,y+80,z+650,w-160,d-160,40,soil)
  cnt=(w/900).floor
  cnt.times do |j|
    xx=x+450+j*900
    crown(g,"SHRUB_#{j}",xx,y+d/2,z+1050,530,340,500,j.even? ? green : green2)
    crown(g,"TREE_#{j}",xx,y+d/2,z+1800+(j%2)*200,500,400,1000,green)
  end
end
nf=fg(fg(fg(root,'CONTEXT'),'RIGHT_NEIGHBOR'),'VISIBLE_FACADE')
levels=[5400,8800,12200,15600,19000,22400,26500]
8.times do |k|
  9.times do |j|
    w=fg(nf,"WINDOW_#{k}_#{j}"); bar=fg(nf,"WINDOW_BAR_#{k}_#{j}")
    if k==7
      clear_owned_contents.call(['CONTEXT','RIGHT_NEIGHBOR','VISIBLE_FACADE',w.name]); clear_owned_contents.call(['CONTEXT','RIGHT_NEIGHBOR','VISIBLE_FACADE',bar.name])
    else
      top=k==6; tw=top ? 900 : 1300; th=top ? 900 : 2500
      ww=(w.bounds.max.x-w.bounds.min.x).to_mm; hh=(w.bounds.max.z-w.bounds.min.z).to_mm
      w.transform!(Geom::Transformation.scaling(w.bounds.min,tw/ww,1,th/hh))
      tx=21800+j*2500+(top ? 250 : 50)
      w.transform!(Geom::Transformation.translation([(tx-w.bounds.min.x.to_mm).mm,0,(levels[k]-w.bounds.min.z.to_mm).mm]))
      bh=(bar.bounds.max.z-bar.bounds.min.z).to_mm; bar.transform!(Geom::Transformation.scaling(bar.bounds.min,1,1,th/bh))
      bar.transform!(Geom::Transformation.translation([(tx+tw/2-bar.bounds.min.x.to_mm).mm,0,(levels[k]-bar.bounds.min.z.to_mm).mm]))
    end
  end
end
