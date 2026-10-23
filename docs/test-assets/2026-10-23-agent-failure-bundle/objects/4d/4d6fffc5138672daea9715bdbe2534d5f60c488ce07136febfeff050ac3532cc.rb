# encoding: UTF-8
# Current independent review r3: targeted frame, terrace, neighbor refinement.
def fg(p,n); p.entities.grep(Sketchup::Group).find { |g| g.name==n }; end
def cg(p,n); g=p.entities.add_group; g.name=n; g; end
def bx(p,n,x,y,z,w,d,h,m)
  g=cg(p,n); f=g.entities.add_face([[x,y,z],[x+w,y,z],[x+w,y+d,z],[x,y+d,z]].map { |q| q.map { |v| v.mm } }); f.reverse! if f.normal.z<0; f.pushpull(h.mm)
  g.entities.grep(Sketchup::Face).each { |q| q.material=m; q.back_material=m }
  g.entities.grep(Sketchup::Edge).each { |e| e.hidden=true }; g
end
def ell(p,n,x,y,z,rx,ry,rz,m)
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
  g.entities.grep(Sketchup::Edge).each { |e| e.soft=true; e.smooth=true; e.hidden=true }; g
end
def scale_at(g,sx,sy,sz,anchor=nil)
  c=anchor || g.bounds.center; g.transform!(Geom::Transformation.scaling(c,sx,sy,sz))
end
stone=model.materials['Warm_limestone']; dark=model.materials['Bronze_mullion']; green=model.materials['Leaf_mid']; green2=model.materials['Leaf_light']; bark=model.materials['Bark']; soil=model.materials['Planter_soil']
b=fg(root,'BUILDING')
['TOWER','STEPPED_WING','LEFT_UPPER','LEFT_STREET'].each do |n|
  f=fg(fg(b,n),'FACADE')
  f.entities.grep(Sketchup::Group).each do |row|
    row.entities.grep(Sketchup::Group).each do |g|
      nn=g.name
      if nn.include?('_POST_')
        nn.include?('FRONT') || nn.include?('REAR') ? scale_at(g,1.5,1,1) : scale_at(g,1,1.5,1)
      elsif nn.include?('_HEAD_')
        a=g.bounds.max; scale_at(g,1,1,1.4,a)
      end
      if nn.include?('_POST_') || nn.include?('_HEAD_') || nn.include?('_MULLION_')
        g.entities.grep(Sketchup::Edge).each { |e| e.hidden=true }
      end
    end
  end
end
# Sample frame follows the same new section while the sample slab/wall/glass stay protected.
fr=fg(fg(fg(b,'TOWER'),'MODULE_PROTOTYPE'),'FRAME')
fr.entities.grep(Sketchup::Group).each do |g|
  if g.name.include?('COLUMN'); scale_at(g,1.5,1,1); else; scale_at(g,1,1,1.4,g.bounds.max); end
  g.entities.grep(Sketchup::Edge).each { |e| e.hidden=true }
end
# Deeper existing terrace coping without touching decks or adjoining walls.
tr=fg(fg(b,'STEPPED_WING'),'TERRACES')
tr.entities.grep(Sketchup::Group).each do |t|
  t.entities.grep(Sketchup::Group).each do |g|
    if g.name.include?('COPING')
      scale_at(g,1,1,1.8,g.bounds.min)
      g.entities.grep(Sketchup::Edge).each { |e| e.hidden=true }
    end
  end
end
veg=fg(root,'VEGETATION'); vt=fg(veg,'TERRACE_INSTANCES'); clear_owned_contents.call(['VEGETATION','TERRACE_INSTANCES'])
terraces=[[-21600,10800,13500],[-10800,2700,19700],[-8100,2700,25900],[-5400,2700,32100],[-2700,2700,41400]]
terraces.each_with_index do |a,i|
  x,w,z=a
  [300,3600,7200,10800].each_with_index do |y,j|
    p=cg(vt,"T#{i}_P#{j}"); pw=w==2700 ? 1000 : 2500
    bx(p,'BOX',x+300,y,z,pw,1200,650,stone)
    bx(p,'SOIL',x+370,y+70,z+650,pw-140,1060,35,soil)
    ell(p,'SHRUB',x+300+pw/2,y+600,z+980,pw*0.46,500,430,green2)
    t=cg(vt,"T#{i}_TREE#{j}"); tx=x+300+pw/2
    bx(t,'TRUNK',tx-45,y+555,z+685,90,90,1100,bark)
    ell(t,'CROWN',tx,y+600,z+2100,600,530,900,green)
  end
end
bal=cg(veg,'BALCONY_INSTANCES')
[[4,1],[7,3],[8,0],[11,2],[15,1]].each_with_index do |a,i|
  k,j=a; z=4200+(k-1)*3100; y=j*3600+600
  p=cg(bal,"SIDE_BALCONY_#{i}"); bx(p,'POT',17180,y,z,600,1500,450,stone); ell(p,'SHRUB',17480,y+750,z+800,400,700,530,green)
end
# Preserve neighbor volume and shop fronts. Correct only repeated upper windows.
nf=fg(fg(fg(root,'CONTEXT'),'RIGHT_NEIGHBOR'),'VISIBLE_FACADE')
8.times do |k|
  10.times do |j|
    w=fg(nf,"WINDOW_#{k}_#{j}"); bar=fg(nf,"WINDOW_BAR_#{k}_#{j}")
    if j==9
      clear_owned_contents.call(['CONTEXT','RIGHT_NEIGHBOR','VISIBLE_FACADE',w.name])
      clear_owned_contents.call(['CONTEXT','RIGHT_NEIGHBOR','VISIBLE_FACADE',bar.name])
    else
      newx=21800+j*2500
      old=w.bounds.min.x.to_mm
      w.transform!(Geom::Transformation.translation([(newx-old).mm,0,0]))
      scale_at(w,1.4,1,1,w.bounds.min)
      dx=newx+690-bar.bounds.min.x.to_mm
      bar.transform!(Geom::Transformation.translation([dx.mm,0,0]))
      w.entities.grep(Sketchup::Edge).each { |e| e.hidden=true }; bar.entities.grep(Sketchup::Edge).each { |e| e.hidden=true }
    end
  end
end
ivy=cg(nf,'GREEN_WALL_RELIEF')
8.times do |j|
  15.times do |k|
    y=9300+j*1950+(k%2)*200; z=700+k*1900
    ell(ivy,"IVY_#{j}_#{k}",44120+(j%3)*45,y,z,150+(k%3)*35,1050,1200,(j+k)%3==0 ? green2 : green)
  end
end
