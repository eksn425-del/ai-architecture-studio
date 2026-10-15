r=root.entities.find{|e|e.respond_to?(:name)&&e.name=='RAMPS'}.entities.find{|e|e.respond_to?(:name)&&e.name=='RAMP_1'}
r.transform!(Geom::Transformation.translation([1.mm,0,0]))
g=root.entities.find{|e|e.respond_to?(:name)&&e.name=='ROOF_TIMBER'}
raise 'Missing roof' unless g
g.material=model.materials.find{|m|m.name!=''&&m!=g.material}
