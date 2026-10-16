b=root.entities.find{|e|e.respond_to?(:name)&&e.name=='ENVELOPE_OUTER'}.entities.find{|e|e.respond_to?(:name)&&e.name=='NORTH_BAY_0'}
g=b.definition.entities.find{|e|e.respond_to?(:name)&&e.name=='GLASS'}
g.transform!(Geom::Transformation.translation([0,0,100.mm]))
