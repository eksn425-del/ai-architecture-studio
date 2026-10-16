# r15 local defect correction: only the new supports of three relocated tables.
# Shared unit bar definition is retained unmodified; change instance transforms.
raise 'Wrong owned model root' unless root.persistent_id==20606
interior=root.entities.grep(Sketchup::Group).find{|g|g.name=='INTERIOR'}
furniture=interior.entities.grep(Sketchup::Group).find{|g|g.name=='FURNITURE_SIMPLIFIED'}
[0,3600,10800].each do |z|
  g=furniture.entities.grep(Sketchup::Group).find{|e|e.name=="TABLE_Z#{z}_5"}
  raise 'Missing existing table' unless g
  top_edges=g.entities.grep(Sketchup::Edge)
  shape=top_edges.map{|e|[e.persistent_id,e.vertices.map{|v|v.position.to_a}]}
  parts=g.entities.grep(Sketchup::ComponentInstance)
  raise 'Unexpected new support count' unless parts.length==12 && parts.all?{|e|e.name.start_with?("TABLE_#{z}_5_")}
  dy=Geom::Transformation.translation([0,-2500.mm,0])
  parts.each do |e|
    raise 'Support already corrected or unexpected transform' unless e.bounds.min.y.to_mm>3900
    e.transform!(dy)
  end
  raise 'Tabletop geometry changed' unless shape==top_edges.map{|e|[e.persistent_id,e.vertices.map{|v|v.position.to_a}]}
  parts.each do |e|
    b=e.bounds
    raise 'Frame not under moved top' unless b.min.y.to_mm>=1500 && b.max.y.to_mm<=2500
  end
  legs=parts.select{|e|e.name.include?('_LEG_')}
  raise 'Legs not bearing on floor and tabletop' unless legs.length==4 && legs.all?{|e|(e.bounds.min.z.to_mm-z).abs<0.01 && (e.bounds.max.z.to_mm-z-720).abs<0.01}
end
puts 'Three relocated table frames aligned with existing tops. All other geometry unchanged.'
