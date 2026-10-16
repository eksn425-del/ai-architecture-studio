# Local additive edit only: two source4 fine white cylindrical mesh guards.
# Custom owned Ruby: SAIE straight walls/openings cannot express open cylindrical mesh.
def sc_group(es,name)
  g=es.add_group;g.name=name;g.set_attribute('KStudio','semantic_id',name);g
end
def sc_find(es,name)
  a=es.select{|e|e.respond_to?(:name) && e.name==name}
  raise "Missing/duplicate #{name}" unless a.length==1
  a.first
end
def sc_ring(es,name,r,w,z,h,mat)
  g=sc_group(es,name);n=144
  n.times do |i|
    a=2*Math::PI*i/n;b=2*Math::PI*(i+1)/n
    p=[]
    [z,z+h].each{|zz|[r-w/2,r+w/2].each{|rr|[a,b].each{|t|p<<[rr*Math.cos(t),rr*Math.sin(t),zz].map(&:mm)}}}
    [[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6]].each do |ids|
      f=g.entities.add_face(ids.map{|k|p[k]});raise 'Ring face failed' unless f
    end
  end
  g.material=mat;g.entities.grep(Sketchup::Edge).each{|e|e.hidden=true};g
end
def sc_vertical(es,name,r,a,z,height,width,mat)
  g=sc_group(es,name);c=Math.cos(a);s=Math.sin(a);w=width/2
  p=[[-w,-w],[w,-w],[w,w],[-w,w]].map{|u,v|[(r+u)*c-v*s,(r+u)*s+v*c,z].map(&:mm)}
  f=g.entities.add_face(p);raise 'Post face failed' unless f
  f.reverse! if f.normal.z<0;f.pushpull(height.mm)
  g.material=mat;g.entities.grep(Sketchup::Edge).each{|e|e.hidden=true};g
end
raise 'Wrong root' unless root.persistent_id==20606
parent=sc_find(root.entities,'CIRCULATION_INTERNAL')
raise 'Wrong parent' unless parent.persistent_id==45400 && parent.definition.instances.length==1
raise 'Unexpected parent transform' unless parent.transformation.identity?
raise 'Target already exists' if parent.entities.any?{|e|e.respond_to?(:name) && e.name=='SMALL_CIRCULAR_VOID_GUARDS'}
floor=sc_find(sc_find(root.entities,'FLOORS').entities,'L3')
raise 'Wrong floor' unless floor.persistent_id==76979
centers=[[12000.0,10500.0],[22500.0,10500.0]]
centers.each do |cx,cy|
  match=floor.entities.grep(Sketchup::Face).flat_map{|f|f.loops.reject(&:outer?)}.any? do |loop|
    vv=loop.vertices.map{|v|v.position}
    vv.length==48 && vv.all?{|p|(p.z.to_mm-10800).abs<0.1 && (Math.sqrt((p.x.to_mm-cx)**2+(p.y.to_mm-cy)**2)-1100).abs<0.1}
  end
  raise 'Registered floor hole mismatch' unless match
end
mat=model.materials['KS_White_Steel'];raise 'Missing existing white finish' unless mat
leaf=sc_group(parent.entities,'SMALL_CIRCULAR_VOID_GUARDS')
first=sc_group(leaf.entities,'SMALL_HOLE_01_FINE_WHITE_MESH')
sc_ring(first.entities,'H01_TOP_RING',1125,24,1080,20,mat)
sc_ring(first.entities,'H01_BASE_RING',1125,18,0,18,mat)
144.times{|i|sc_vertical(first.entities,"H01_MESH_VERTICAL_#{i}",1125,2*Math::PI*i/144,18,1062,3,mat)}
(1..21).each{|i|sc_ring(first.entities,"H01_MESH_HORIZONTAL_#{i}",1125,3,i*50,3,mat)}
8.times{|i|sc_vertical(first.entities,"H01_POST_#{i}",1125,2*Math::PI*i/8,0,1100,18,mat)}
first.transform!(Geom::Transformation.translation([12000.mm,10500.mm,10800.mm]))
first.set_attribute('KStudio','mesh_pitch_mm',50)
first.set_attribute('KStudio','height_mm',1100)
second=leaf.entities.add_instance(first.definition,Geom::Transformation.translation([22500.mm,10500.mm,10800.mm]))
second.name='SMALL_HOLE_02_FINE_WHITE_MESH';second.set_attribute('KStudio','semantic_id','SMALL_HOLE_02_FINE_WHITE_MESH')
raise 'Guard count mismatch' unless leaf.entities.length==2
puts 'TWO_SMALL_CIRCLE_GUARDS: centers retained; base10800 top11900; floor loops validated; continuous real open mesh; all existing geometry untouched'
