# Only the newly added west L2 entry leaves: avoid narrowing the 1650mm return.
# Sliding leaf detail is inferred. Existing door aperture/frame/glass unchanged.
def cs_find(es,name)
  a=es.select{|e|e.respond_to?(:name)&&e.name==name}
  raise "Missing/duplicate #{name}" unless a.length==1
  a.first
end
def cs_box(es,name,u0,u1,x0,x1,z0,z1,mat)
  g=es.add_group;g.name=name;g.set_attribute('KStudio','semantic_id',name)
  f=g.entities.add_face([[x0,u0,z0],[x1,u0,z0],[x1,u1,z0],[x0,u1,z0]].map{|p|p.map(&:mm)})
  raise 'Frame face failed' unless f
  f.reverse! if f.normal.z<0;f.pushpull((z1-z0).mm);g.material=mat
end
raise 'Wrong root' unless root.persistent_id==20606
path=['ENVELOPE_OUTER','LOWER_END_WEST_ADDITION','LEVEL_7200_BAY_6']
g=root;path.each{|n|g=cs_find(g.entities,n)}
raise 'Shared doorway' unless g.definition.instances.length==1
mat=model.materials['KS_White_Steel'];glass=model.materials['KS_Clear_Glass']
raise 'Missing finishes' unless mat && glass
[['DOOR_LEFT_OPEN_90','DOOR_LEFT_SLID_OPEN',14100.0,15200.0],['DOOR_RIGHT_OPEN_90','DOOR_RIGHT_SLID_OPEN',17400.0,18500.0]].each do |oldname,newname,lo,hi|
  leaf=cs_find(g.entities,oldname)
  raise 'Unexpected leaf transform' unless leaf.transformation.identity?
  clear_owned_contents.call(path+[oldname])
  es=leaf.entities
  # Door is parked 60mm outside the facade, beyond 20/25mm frame profiles.
  cs_box(es,'BOTTOM',lo,hi,-72,-48,7200,7224,mat)
  cs_box(es,'TOP',lo,hi,-72,-48,9576,9600,mat)
  cs_box(es,'STILE_A',lo,lo+24,-72,-48,7224,9576,mat)
  cs_box(es,'STILE_B',hi-24,hi,-72,-48,7224,9576,mat)
  f=es.add_face([[-60,lo+24,7224],[-60,hi-24,7224],[-60,hi-24,9576],[-60,lo+24,9576]].map{|p|p.map(&:mm)})
  raise 'Sliding glass failed' unless f
  f.material=glass;f.back_material=glass
  leaf.name=newname;leaf.set_attribute('KStudio','semantic_id',newname)
  leaf.set_attribute('KStudio','opening_angle_deg',0)
  leaf.set_attribute('KStudio','opening_style','fully slid aside, empty 2200mm passage')
  b=leaf.bounds
  raise 'Sliding leaf blocks approach' if b.min.x.to_mm < -73 || b.max.x.to_mm > -47
end
g.set_attribute('KStudio','entry_return_clearance_mm_estimated',1578)
g.set_attribute('KStudio','opening_style','sliding instead of projecting into narrow return')
puts 'WEST_L2_ENTRY: clear aperture2200x2400 retained; leaf projection reduced1100 to72mm; return approx1578mm clear. Entire route not certified.'
