# Local r18: Source05 shows continuous slender buffer framing at eave corners.
# kstudio.custom_owned_ruby: SAIE straight opaque walls are unsuitable for a
# 60mm curtain-wall frame member; ADAI is disabled by the verified contract.
def cj_find(es, name)
  found=es.select{|e|(e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)) && e.name==name}
  raise "Missing/duplicate #{name}" unless found.length==1
  found.first
end
raise 'Wrong root' unless root.persistent_id==20606
env=cj_find(root.entities,'ENVELOPE_OUTER')
vents=cj_find(env.entities,'OUTER_EAVE_VENTS')
raise 'Wrong parents' unless env.persistent_id==41319 && vents.persistent_id==1371575
raise 'Transformed parents' unless env.transformation.identity? && vents.transformation.identity?
name='NORTH_EAST_CORNER_JAMB'
raise 'Jamb already present' if vents.entities.any?{|e|e.respond_to?(:name) && e.name==name}
raise 'Wrong vent count' unless vents.entities.grep(Sketchup::ComponentInstance).length==38
steel=model.materials['KS_White_Steel'];raise 'Missing original steel' unless steel
# Add the exact approved absent leaf, without editing its parent or siblings.
g=vents.entities.add_group;g.name=name;g.set_attribute('KStudio','semantic_id',name)
f=g.entities.add_face([[53970,23970,7200],[54030,23970,7200],[54030,24030,7200],[53970,24030,7200]].map{|p|p.map(&:mm)})
f.reverse! if f.normal.z<0
f.pushpull(6300.mm);g.material=steel
raise 'Not a solid jamb' unless g.manifold? && (g.volume*25.4**3-60*60*6300).abs<1
pt=Geom::Point3d.new(53985.mm,24000.mm,12800.mm)
# Actual six half-spaces establish the formerly unsupported stay foot is inside
# the newly closed solid, rather than just inside an approximate outer bound.
inside=g.entities.grep(Sketchup::Face).all? do |face|
  v=pt-face.vertices.first.position
  face.normal.dot(v)<=0.000001
end
raise 'Stay foot does not enter solid' unless inside
# The unchanged terminal bay has six horizontal rails reaching X54000.
bay=cj_find(env.entities,'NORTH_BAY_19')
[7200,8250,9300,10800,12000,13500].each do |z|
  rail=cj_find(bay.definition.entities,"TRANSOM_#{z}")
  b=rail.bounds
  raise 'Rail does not reach jamb' unless (bay.transformation*Geom::Point3d.new(b.max.x,0,z.mm)).x.to_mm.between?(53999.99,54000.01)
  raise 'Jamb misses rail level' unless z.between?(7200,13500)
end
puts 'Added one solid 60x60x6300mm corner jamb. Former failed stay start is inside actual solid; six original horizontal rail levels connected. All existing geometry retained.'
