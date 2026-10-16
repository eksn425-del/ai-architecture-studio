env=root.entities.find{|e|e.respond_to?(:name)&&e.name=='ENVELOPE_OUTER'}
b=env.entities.find{|e|e.respond_to?(:name)&&e.name=='NORTH_BAY_0'}
es=b.is_a?(Sketchup::Group) ? b.entities : b.definition.entities
g=es.find{|e|e.respond_to?(:name)&&e.name=='GLASS'};g.transform!(Geom::Transformation.translation([0,0,1.mm]))
p=es.find{|e|e.respond_to?(:name)&&e.name=='MULLION'}
p.material=model.materials.find{|m|m!=p.material}
