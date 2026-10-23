# encoding: UTF-8
# Endpoint-only r9 correction, after current independent visual review.
# Guarded custom_owned_ruby: in-place transforms of existing unique wire leaves.
env=root.entities.grep(Sketchup::Group).find { |g| g.name=='ENVIRONMENT' }
raise 'Missing owned environment' unless env
wires=env.entities.grep(Sketchup::Group).find { |g| g.name=='CONTACT_WIRES' }
raise 'Wire container identity drift' unless wires && wires.persistent_id==138460
leaves=wires.entities.grep(Sketchup::Group)
raise 'Wire inventory drift' unless leaves.length==30
contact=leaves.find { |g| g.name=='CONTACT_0' }
raise 'Wrong wire starting revision' unless contact && (contact.bounds.min.x.to_mm+64200).abs<0.5 && (contact.bounds.max.x.to_mm-58200).abs<0.5

# 14m in from both physical site ends: also visibly inside the footprint in
# the user's orbit, canonical oblique and current street inspection cameras.
origin=Geom::Point3d.new((-64200).mm,0,0)
shrink=Geom::Transformation.scaling(origin,98000.0/122400.0,1,1)
shift=Geom::Transformation.translation([12200.mm,0,0])
leaves.each do |g|
  g.transform!(shift*shrink)
  # Existing 2mm dropper/messenger gap is closed while keeping its lower joint.
  if g.name.start_with?('DROPPER_')
    joint=Geom::Point3d.new(0,0,6018.mm)
    g.transform!(Geom::Transformation.scaling(joint,1,1,782.0/780.0))
  end
  bb=g.bounds
  raise 'Wire endpoint not inside final scope' unless bb.min.x.to_mm>=-52000.5 && bb.max.x.to_mm<=46000.5
end
