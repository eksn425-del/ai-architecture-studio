# Three local receiving door apertures; all other bays and assemblies protected.
# kstudio.custom_owned_ruby: existing zero-thickness glazing and slender profile
# clipping cannot use root-level SAIE solid wall/opening. ADAI is unavailable.
def ud_find(es,n)
  aa=es.select{|e|e.respond_to?(:name) && e.name==n}
  raise "Missing/duplicate #{n}" unless aa.length==1
  aa.first
end
def ud_es(g)
  g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities
end
def ud_box(es,name,x0,x1,y0,y1,z0,z1,mat)
  g=es.add_group; g.name=name
  f=g.entities.add_face([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0]].map{|p|p.map{|v|v.mm}})
  f.reverse! if f.normal.z<0
  f.pushpull((z1-z0).mm)
  g.material=mat
end
raise 'Wrong root' unless root.persistent_id==20606
env=ud_find(root.entities,'ENVELOPE_OUTER')
raise 'Shared envelope' unless env.definition.instances.length==1
[['NORTH_BAY_0',41577,[7200,10800]],['SOUTH_BAY_00',41557,[7200]]].each do |name,pid,levels|
  bay=ud_find(env.entities,name)
  raise 'Bay PID changed' unless bay.persistent_id==pid
  bay.make_unique
  bes=ud_es(bay)
  holes=levels.map{|z|[350.0,2550.0,z.to_f,z+2400.0]}
  names=['GLASS']+[7200,8250,9300,10800,12000].map{|z|"TRANSOM_#{z}"}
  names.each do |leaf_name|
    leaf=ud_find(bes,leaf_name)
    les=ud_es(leaf)
    bb=Geom::BoundingBox.new
    les.grep(Sketchup::Edge).each{|e|e.vertices.each{|v|bb.add(v.position)}}
    xmin=bb.min.x.to_mm;xmax=bb.max.x.to_mm
    ymin=bb.min.y.to_mm;ymax=bb.max.y.to_mm
    zmin=bb.min.z.to_mm;zmax=bb.max.z.to_mm
    next unless holes.any?{|h|h[0]<xmax && h[1]>xmin && h[2]<zmax && h[3]>zmin}
    face=les.grep(Sketchup::Face).first
    mat=face.material || leaf.material
    back=face.back_material
    normal=face.normal
    oldpid=leaf.persistent_id
    leaf.make_unique
    clear_owned_contents.call(['ENVELOPE_OUTER',name,leaf_name])
    les=ud_es(leaf)
    xs=([xmin,xmax]+holes.flat_map{|h|[h[0],h[1]]}.select{|v|v>xmin && v<xmax}).uniq.sort
    zs=([zmin,zmax]+holes.flat_map{|h|[h[2],h[3]]}.select{|v|v>zmin && v<zmax}).uniq.sort
    count=0
    xs.each_cons(2) do |xa,xb|
      zs.each_cons(2) do |za,zb|
        cx=(xa+xb)/2;cz=(za+zb)/2
        next if holes.any?{|h|cx>h[0] && cx<h[1] && cz>h[2] && cz<h[3]}
        count+=1
        if leaf_name=='GLASS'
          f=les.add_face([[xa,0,za],[xb,0,za],[xb,0,zb],[xa,0,zb]].map{|p|p.map{|v|v.mm}})
          f.reverse! if f.normal.dot(normal)<0
          f.material=mat;f.back_material=back
        else
          ud_box(les,"#{name}_#{leaf_name}_RETAINED_#{count}",xa,xb,ymin,ymax,za,zb,mat)
        end
      end
    end
    raise 'Leaf identity lost' unless leaf.persistent_id==oldpid
    # Every resulting face vertex is outside or on the opening boundary.
    # Rectangles above are partitioned at every cut bound, so none crosses a hole.
    raise 'Unexpected empty retained leaf' unless count>0
  end
  raise 'Bay identity lost' unless bay.persistent_id==pid
end
