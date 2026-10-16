# Five receiving rail gates only; root and every existing container retained.
# Method kstudio.custom_owned_ruby: existing slender rail cap deformation,
# not SAIE wall/opening geometry. ADAI unavailable.
def og_find(es,name)
  a=es.select{|e|e.respond_to?(:name) && e.name==name}
  raise "Nonunique #{name}" unless a.length==1
  a.first
end
def og_vertices(g)
  g.entities.grep(Sketchup::Edge).flat_map{|e|e.vertices}.uniq
end
raise 'Wrong owned root' unless root.persistent_id==20606
ext=og_find(root.entities,'CIRCULATION_EXTERNAL')
gallery=og_find(ext.entities,'GALLERIES')
specs=[{"name"=>"LONG_RAIL_SOUTH_Z3600","pid"=>28139,"posts"=>[["LONG_RAIL_SOUTH_Z3600_POST_0",28141],["LONG_RAIL_SOUTH_Z3600_POST_1",28173],["LONG_RAIL_SOUTH_Z3600_POST_2",28205]],"rails"=>[["LONG_RAIL_SOUTH_Z3600_RAIL_120",29421],["LONG_RAIL_SOUTH_Z3600_RAIL_550",29453],["LONG_RAIL_SOUTH_Z3600_RAIL_1100",29485]]},{"name"=>"LONG_RAIL_NORTH_Z3600","pid"=>29517,"posts"=>[["LONG_RAIL_NORTH_Z3600_POST_0",29519],["LONG_RAIL_NORTH_Z3600_POST_1",29551],["LONG_RAIL_NORTH_Z3600_POST_2",29583]],"rails"=>[["LONG_RAIL_NORTH_Z3600_RAIL_120",30799],["LONG_RAIL_NORTH_Z3600_RAIL_550",30831],["LONG_RAIL_NORTH_Z3600_RAIL_1100",30863]]},{"name"=>"LONG_RAIL_SOUTH_Z7200","pid"=>31023,"posts"=>[["LONG_RAIL_SOUTH_Z7200_POST_0",31025],["LONG_RAIL_SOUTH_Z7200_POST_1",31057],["LONG_RAIL_SOUTH_Z7200_POST_2",31089]],"rails"=>[["LONG_RAIL_SOUTH_Z7200_RAIL_120",32305],["LONG_RAIL_SOUTH_Z7200_RAIL_550",32337],["LONG_RAIL_SOUTH_Z7200_RAIL_1100",32369]]},{"name"=>"LONG_RAIL_NORTH_Z7200","pid"=>32401,"posts"=>[["LONG_RAIL_NORTH_Z7200_POST_0",32403],["LONG_RAIL_NORTH_Z7200_POST_1",32435],["LONG_RAIL_NORTH_Z7200_POST_2",32467]],"rails"=>[["LONG_RAIL_NORTH_Z7200_RAIL_120",33683],["LONG_RAIL_NORTH_Z7200_RAIL_550",33715],["LONG_RAIL_NORTH_Z7200_RAIL_1100",33747]]},{"name"=>"LONG_RAIL_NORTH_Z10800","pid"=>35285,"posts"=>[["LONG_RAIL_NORTH_Z10800_POST_0",35287],["LONG_RAIL_NORTH_Z10800_POST_1",35319],["LONG_RAIL_NORTH_Z10800_POST_2",35351]],"rails"=>[["LONG_RAIL_NORTH_Z10800_RAIL_120",36567],["LONG_RAIL_NORTH_Z10800_RAIL_550",36599],["LONG_RAIL_NORTH_Z10800_RAIL_1100",36631]]}]
specs.each do |s|
  guard=og_find(gallery.entities,s['name'])
  raise 'Parent PID mismatch' unless guard.persistent_id==s['pid']
  pt=ext.transformation*gallery.transformation*guard.transformation
  s['rails'].each do |name,pid|
    bar=og_find(guard.entities,name)
    raise 'Rail PID mismatch' unless bar.persistent_id==pid
    tr=pt*bar.transformation
    vv=og_vertices(bar)
    original=vv.map{|v|tr*v.position}
    xmin=original.map{|p|p.x.to_mm}.min
    raise 'Unexpected rail end' unless (xmin+4000).abs<0.01
    moving=vv.select{|v|((tr*v.position).x.to_mm+4000).abs<0.01}
    raise 'Unexpected cap' unless moving.length==4
    vec=Geom::Vector3d.new(4000.mm,0,0).transform(tr.inverse)
    bar.entities.transform_by_vectors(moving,moving.map{|v|vec})
    vv.each_with_index do |v,i|
      p=tr*v.position
      if original[i].x.to_mm>=0
        raise 'Distant rail changed' unless p.distance(original[i]).to_mm<0.001
      end
    end
    raise 'Rail still blocks gate' unless og_vertices(bar).map{|v|(tr*v.position).x.to_mm}.min.abs<0.01
  end
  s['posts'].each_with_index do |pair,i|
    name,pid=pair;post=og_find(guard.entities,name)
    raise 'Post PID mismatch' unless post.persistent_id==pid
    tr=pt*post.transformation
    pp=og_vertices(post).map{|v|tr*v.position}
    cx=(pp.map{|p|p.x.to_mm}.min+pp.map{|p|p.x.to_mm}.max)/2.0
    tx=i==0 ? -4035.0 : 17.5
    dy=i==2 ? 35.0 : 0.0
    delta=Geom::Transformation.translation([(tx-cx).mm,dy.mm,0])
    post.transform!(pt.inverse*delta*pt)
    xx=og_vertices(post).map{|v|(pt*post.transformation*v.position).x.to_mm}
    raise 'Post obstructs aperture' unless xx.max<=-4000.0 || xx.min>=-0.001
  end
end

