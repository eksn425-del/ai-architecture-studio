# encoding: UTF-8
# Scoped street correction; retain every existing target container PID.
# This is the complete r8-to-r9 pass. Later endpoint-only refinement is retained
# as a separately scoped guarded script, street_wire_finish.rb.
# Method: kstudio.custom_owned_ruby. SAIE straight walls/rectangular apertures
# cannot make horizontal curved paving profiles or adjust rail/wire assemblies.
# ADAI is disabled by the verified project contract.

def street_named(parent, name)
  groups = parent.entities.grep(Sketchup::Group).select { |g| g.name == name }
  raise "Expected unique existing group #{name}" unless groups.length == 1
  groups.first
end

def street_prism(parent, name, points, z, height, material)
  g = parent.entities.add_group
  g.name = name
  face = g.entities.add_face(points.map { |x,y| [x.mm,y.mm,z.mm] })
  raise "Invalid street profile #{name}" unless face
  face.reverse! if face.normal.z < 0
  face.pushpull(height.mm)
  g.entities.grep(Sketchup::Face).each { |f| f.material = material; f.back_material = material }
  # Retain silhouettes while hiding only the vertical facet seams.
  g.entities.grep(Sketchup::Edge).each do |e|
    a=e.start.position; b=e.end.position
    if (a.x-b.x).abs < 0.001.mm && (a.y-b.y).abs < 0.001.mm
      e.soft = true; e.smooth = true
    end
  end
  g
end

def street_arc(cx,cy,r,a,b,n=36)
  (0..n).map do |i|
    t=(a+(b-a)*i.to_f/n)*Math::PI/180.0
    [cx+r*Math.cos(t),cy+r*Math.sin(t)]
  end
end

def street_rect(parent,name,x,y,w,d,z,h,material)
  street_prism(parent,name,[[x,y],[x+w,y],[x+w,y+d],[x,y+d]],z,h,material)
end

env=street_named(root,'ENVIRONMENT')
curbs=street_named(env,'CURBS')
targets={
  'BUILDING_SIDEWALK'=>138526,
  'FAR_CORNER_PAVEMENT'=>138558,
  'FOREGROUND_PAVEMENT'=>138590,
  'CURB_FRONT'=>138622
}
targets.each do |name,pid|
  raise "Curb identity drift #{name}" unless street_named(curbs,name).persistent_id == pid
end
tracks=street_named(env,'TRACKS')
wires=street_named(env,'CONTACT_WIRES')
raise 'Track identity drift' unless tracks.persistent_id == 138458
raise 'Wire identity drift' unless wires.persistent_id == 138460
raise 'Unexpected track inventory' unless tracks.entities.grep(Sketchup::Group).length == 187
raise 'Unexpected wire inventory' unless wires.entities.grep(Sketchup::Group).length == 30
rail=street_named(tracks,'RAIL_HEAD_0')
raise 'Already adjusted rail; refuse duplicate translation' unless (rail.bounds.max.z.to_mm-75).abs < 0.5

pave=model.materials['Paving']
stone=model.materials['Warm_limestone']
asphalt=model.materials['Asphalt']
raise 'Missing existing street materials' unless pave && stone && asphalt
targets.keys.each { |n| clear_owned_contents.call(['ENVIRONMENT','CURBS',n]) }

# First representative corner: 4.5 m radius, tangent to original street lines.
# Asphalt fills only the removed old square corner, preventing a white void.
near=street_named(curbs,'BUILDING_SIDEWALK')
street_rect(near,'SW_CORNER_ASPHALT',-46800,-6000,4500,4500,-380,200,asphalt)
near_curve=street_arc(-42300,-1500,4500,270,180)
near_outline=[[-46800,0],[60000,0],[60000,-6000]]+near_curve
street_prism(near,'ROUNDED_PAVING',near_outline,-180,180,pave)
raise 'Representative corner polygon failed' unless street_named(near,'ROUNDED_PAVING').manifold?

# Same curved paving module at the opposite street corner.
far=street_named(curbs,'FAR_CORNER_PAVEMENT')
street_rect(far,'SE_CORNER_ASPHALT',-62500,-6000,4500,4500,-380,200,asphalt)
far_curve=street_arc(-62500,-1500,4500,270,360)
far_outline=[[-66000,-6000]]+far_curve+[[-58000,21000],[-66000,21000]]
street_prism(far,'ROUNDED_PAVING',far_outline,-180,180,pave)
far_outer=street_arc(-62500,-1500,4650,270,360)
far_inner=[[-66000,-6000]]+far_curve+[[-58000,21000]]
far_out=[[-66000,-6150]]+far_outer+[[-57850,21000]]
street_prism(far,'CONTINUOUS_CURVED_CURB',far_inner+far_out.reverse,-180,180,stone)

# Foreground island nose: rounded NW corner; retain its other extents/height.
front=street_named(curbs,'FOREGROUND_PAVEMENT')
street_rect(front,'NW_CORNER_ASPHALT',-42000,-51000,5000,5000,-380,200,asphalt)
front_curve=street_arc(-37000,-51000,5000,90,180)
front_outline=[[-42000,-53000],[60000,-53000],[60000,-46000]]+front_curve
street_prism(front,'ROUNDED_PAVING',front_outline,-300,200,pave)
front_outer=street_arc(-37000,-51000,5150,90,180)
front_inner=[[60000,-46000]]+front_curve+[[-42000,-53000]]
front_out=[[60000,-45850]]+front_outer+[[-42150,-53000]]
street_prism(front,'CONTINUOUS_CURVED_CURB',front_inner+front_out.reverse,-300,200,stone)

# Original CURB_FRONT now follows both the straight approach and tangent arc.
curb=street_named(curbs,'CURB_FRONT')
near_outer=street_arc(-42300,-1500,4650,270,180)
inner=[[60000,-6000]]+near_curve+[[-46800,0]]
outer=[[60000,-6150]]+near_outer+[[-46950,0]]
street_prism(curb,'CONTINUOUS_CURVED_CURB',inner+outer.reverse,-180,180,stone)

# Preserve rail/sleeper/wire leaf PIDs: transform existing native groups in place.
# Main road native top is -180 mm; old rail head top +75 mm -> translate -255.
# Track bed keeps the site footprint. All metal, sleepers and wires inset 1800.
origin=Geom::Point3d.new((-66000).mm,0,0)
shrink=Geom::Transformation.scaling(origin,122400.0/126000.0,1,1)
inset=Geom::Transformation.translation([1800.mm,0,0])
lower=Geom::Transformation.translation([0,0,(-255).mm])
tracks.entities.grep(Sketchup::Group).each do |g|
  g.transform!(g.name=='TRACK_BED' ? lower : lower*inset*shrink)
end
wires.entities.grep(Sketchup::Group).each { |g| g.transform!(inset*shrink) }

raise 'Rail head not aligned to road plane' unless (rail.bounds.max.z.to_mm+180).abs < 0.5
['RAIL_HEAD_0','RAIL_HEAD_1'].each do |name|
  bb=street_named(tracks,name).bounds
  raise 'Rail endpoint outside approved inset' unless bb.min.x.to_mm >= -64200.5 && bb.max.x.to_mm <= 58200.5
end
wires.entities.grep(Sketchup::Group).each do |g|
  bb=g.bounds
  raise 'Wire outside site inset' unless bb.min.x.to_mm >= -64200.5 && bb.max.x.to_mm <= 58200.5
end
