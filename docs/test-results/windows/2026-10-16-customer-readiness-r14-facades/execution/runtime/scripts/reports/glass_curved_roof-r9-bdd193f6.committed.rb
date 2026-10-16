# Same root, 13 exact slab leaves only. Real open grating; no solid backing.
# kstudio.custom_owned_ruby; SAIE wall/opening incompatible; ADAI unavailable.
def gg_find(es,n)
  a=es.select{|e|e.respond_to?(:name) && e.name==n};raise "Missing/duplicate #{n}" unless a.length==1;a.first
end
def gg_path(root,path)
  g=root;path.each{|n|g=gg_find(g.entities,n)};g
end
def gg_group(es,n)
  g=es.add_group;g.name=n;g.set_attribute('KStudio','semantic_id',n);g
end
def gg_box(es,n,x0,x1,y0,y1,z0,z1,mat,hide_edges=false)
  return if x1-x0<0.001 || y1-y0<0.001
  g=gg_group(es,n)
  f=g.entities.add_face([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0]].map{|p|p.map(&:mm)})
  f.reverse! if f.normal.z<0;f.pushpull((z1-z0).mm);g.material=mat
  g.entities.grep(Sketchup::Edge).each{|e|e.hidden=true} if hide_edges
  g
end
def gg_positions(length,step,width)
  a=[[0.0,width],[length-width,length]];k=step
  while k<length-width
    a<<[k,k+width];k+=step
  end
  a.sort
end
def gg_union_length(a)
  total=0.0;lo=nil;hi=nil
  a.each do |x,y|
    if lo.nil?;lo=x;hi=y
    elsif x<=hi;hi=[hi,y].max
    else;total+=hi-lo;lo=x;hi=y
    end
  end
  total+(hi-lo)
end
def gg_tile(es,uid,u,v,mat,cache)
  key=[u.round(3),v.round(3)]
  if cache[key]
    c=es.add_instance(cache[key],Geom::Transformation.new);c.name=uid;c.set_attribute('KStudio','semantic_id',uid);return c
  end
  g=gg_group(es,uid)
  aa=gg_positions(u,40,3);bb=gg_positions(v,80,3)
  openness=(u-gg_union_length(aa))*(v-gg_union_length(bb))/(u*v)
  raise 'Representative grating too opaque' unless openness>0.80
  aa.each_with_index{|ab,i|gg_box(g.entities,"GRID_#{u}_#{v}_BEARING_#{i}",ab[0],ab[1],0,v,-35,0,mat,true)}
  bb.each_with_index{|ab,i|gg_box(g.entities,"GRID_#{u}_#{v}_CROSS_#{i}",0,u,ab[0],ab[1],-10,0,mat,true)}
  # Each leaf is a narrow bar; there is no continuous panel-sized face.
  g.entities.grep(Sketchup::Group).each do |bar|
    raise 'Opaque grating backing' if bar.entities.grep(Sketchup::Face).any?{|f|f.area*25.4*25.4>u*v*0.5}
  end
  c=g.to_component;c.name=uid;c.definition.name="KS_GALLERY_OPEN_#{u.round}_#{v.round}"
  c.set_attribute('KStudio','semantic_id',uid)
  c.set_attribute('KStudio','estimated_open_fraction',openness)
  cache[key]=c.definition;c
end
raise 'Wrong root' unless root.persistent_id==20606
mat=model.materials['KS_White_Steel'];raise 'Missing material' unless mat
cache={}
specs=[[["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z3600_SIDE0"], 28011], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z3600_SIDE1"], 28043], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z3600_SIDE2"], 28075], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z3600_SIDE3"], 28107], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z7200_SIDE0", "GALLERY_Z7200_SIDE0_RETURN_STRIP"], 88317], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z7200_SIDE1", "GALLERY_Z7200_SIDE1_RETURN_STRIP"], 88607], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z7200_SIDE2", "GALLERY_Z7200_SIDE2_RETURN_STRIP"], 88897], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z7200_SIDE3"], 30991], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z10800_SIDE0", "GALLERY_Z10800_SIDE0_RETURN_STRIP"], 89603], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z10800_SIDE0", "GALLERY_Z10800_SIDE0_SOUTH_FLAT"], 89635], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z10800_SIDE1", "GALLERY_Z10800_SIDE1_RETURN_STRIP"], 89925], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z10800_SIDE2", "GALLERY_Z10800_SIDE2_RETURN_STRIP"], 90215], [["CIRCULATION_EXTERNAL", "GALLERIES", "GALLERY_Z10800_SIDE3"], 33875]]
specs.each_with_index do |spec,idx|
  path,pid=spec;g=gg_path(root,path)
  raise 'Unexpected target identity' unless g.persistent_id==pid
  raise 'Shared target' unless g.definition.instances.length==1
  verts=g.entities.grep(Sketchup::Edge).flat_map{|e|e.vertices}.uniq
  raise 'Target is not old flat slab' unless verts.length==8
  bb=Geom::BoundingBox.new;verts.each{|v|bb.add(v.position)}
  x0=bb.min.x.to_mm;x1=bb.max.x.to_mm;y0=bb.min.y.to_mm;y1=bb.max.y.to_mm;z=bb.max.z.to_mm
  raise 'Unexpected slab thickness' unless ((z-bb.min.z.to_mm)-150).abs<0.01
  clear_owned_contents.call(path)
  field=gg_group(g.entities,"#{path.last}_OPEN_GRID")
  beams=gg_group(g.entities,"#{path.last}_DISCRETE_BEAMS")
  along_x=(x1-x0)>=(y1-y0);ulen=along_x ? x1-x0 : y1-y0;vlen=along_x ? y1-y0 : x1-x0
  u0=0.0;iu=0
  while u0<ulen-0.01
    du=[1000.0,ulen-u0].min;v0=0.0;iv=0
    while v0<vlen-0.01
      dv=[1000.0,vlen-v0].min
      c=gg_tile(field.entities,"GAL#{idx}_PANEL_U#{iu}_V#{iv}",du,dv,mat,cache)
      origin=along_x ? [x0+u0,y0+v0,z] : [x1-v0,y0+u0,z]
      ux=along_x ? X_AXIS : Y_AXIS;vy=along_x ? Y_AXIS : Geom::Vector3d.new(-1,0,0)
      c.transform!(Geom::Transformation.axes(Geom::Point3d.new(*origin.map(&:mm)),ux,vy,Z_AXIS))
      v0+=dv;iv+=1
    end
    u0+=du;iu+=1
  end
  # Edge/support beams fit within original 150mm depth; no solid underside.
  if along_x
    gg_box(beams.entities,"GAL#{idx}_EDGE_A",x0,x1,y0,y0+50,z-150,z-35,mat)
    gg_box(beams.entities,"GAL#{idx}_EDGE_B",x0,x1,y1-50,y1,z-150,z-35,mat)
  else
    gg_box(beams.entities,"GAL#{idx}_EDGE_A",x0,x0+50,y0,y1,z-150,z-35,mat)
    gg_box(beams.entities,"GAL#{idx}_EDGE_B",x1-50,x1,y0,y1,z-150,z-35,mat)
  end
  count=(ulen/2500.0).ceil
  (0..count).each do |i|
    q=ulen*i.to_f/count;lo=[[q-30,0].max,ulen-60].min;hi=lo+60
    if along_x
      gg_box(beams.entities,"GAL#{idx}_CROSS_BEAM_#{i}",x0+lo,x0+hi,y0,y1,z-150,z-35,mat)
    else
      gg_box(beams.entities,"GAL#{idx}_CROSS_BEAM_#{i}",x0,x1,y0+lo,y0+hi,z-150,z-35,mat)
    end
  end
  raise 'Target PID lost' unless g.persistent_id==pid
  b=g.bounds
  # Existing targets have identity transforms; preserve original XY/top/bottom.
  [[b.min.x.to_mm,x0],[b.max.x.to_mm,x1],[b.min.y.to_mm,y0],[b.max.y.to_mm,y1],[b.min.z.to_mm,z-150],[b.max.z.to_mm,z]].each{|a,bv|raise 'Deck outline/height changed' if (a-bv).abs>0.01}
  raise 'Retained opaque face' unless g.entities.grep(Sketchup::Face).empty?
end
