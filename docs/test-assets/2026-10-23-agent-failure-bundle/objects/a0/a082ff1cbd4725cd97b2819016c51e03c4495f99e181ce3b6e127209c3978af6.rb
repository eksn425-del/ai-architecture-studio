# encoding: UTF-8
# Local revision: preserve existing leaf containers and structural grid.
# kstudio.custom_owned_ruby: connected multi-plane loggia assembly; SAIE straight-wall
# cutters do not replace these existing leaves; ADAI is disabled in this session.
def named(parent, name)
  matches = parent.entities.grep(Sketchup::Group).select { |g| g.name == name }
  raise "Expected unique existing group #{name}" unless matches.length == 1
  matches.first
end
def box_in(parent, name, x, y, z, w, d, h, material)
  raise 'Nonpositive box' unless [w,d,h].all? { |v| v > 0 }
  g = parent.entities.add_group
  g.name = name
  f = g.entities.add_face([[x,y,z],[x+w,y,z],[x+w,y+d,z],[x,y+d,z]].map { |p| p.map { |v| v.mm } })
  f.reverse! if f.normal.z < 0
  f.pushpull(h.mm)
  g.entities.grep(Sketchup::Face).each { |q| q.material = material; q.back_material = material }
  g.entities.grep(Sketchup::Edge).each { |e| e.hidden = true }
  g
end
facade = named(named(named(root,'BUILDING'),'TOWER'),'FACADE')
light = model.materials['Light_opaque_panel']
dark = model.materials['Bronze_mullion']
glass = model.materials['Glass_2']
guard = model.materials['Balustrade_glass']
paving = model.materials['Terrace_paving']
# Sample first; the same durable script is revised for the confirmed peer after review.
locations = [[11,4]]
locations.each do |k,j|
  row_name = "TOWER_L#{k.to_s.rjust(2,'0')}"
  row = named(facade,row_name)
  base = ['BUILDING','TOWER','FACADE',row_name]
  infill = named(row,"FRONT_GLAZING_#{j}")
  mullion = named(row,"FRONT_MULLION_#{j}")
  balustrade = named(row,"FRONT_BALUSTRADE_#{j}")
  handrail = named(row,"FRONT_RAIL_#{j}")
  [infill,mullion,balustrade,handrail].each { |g| clear_owned_contents.call(base+[g.name]) }
  x = j*3600 + 165
  z = 4200 + (k-1)*3100
  width = 3270
  deck_top = z + 80
  ceiling = z + 2792
  # Deck sits on the retained structural slab (its top is z); Y50 is the measured slab edge.
  box_in(infill,'LOGGIA_DECK',x,50,z,width,1980,80,paving)
  box_in(infill,'RETURN_LEFT',x,50,deck_top,200,1980,ceiling-deck_top,light)
  box_in(infill,'RETURN_RIGHT',x+width-200,50,deck_top,200,1980,ceiling-deck_top,light)
  # Upper surface meets the underside of the next retained 220mm structural slab.
  box_in(infill,'LOGGIA_SOFFIT',x,50,ceiling,width,1980,88,light)
  box_in(infill,'RECESSED_DOOR_GLASS',x+200,2000,deck_top,width-400,26,ceiling-deck_top,glass)
  [x+200,x+width/2-25,x+width-250].each_with_index do |xx,i|
    box_in(mullion,"DOOR_STILE_#{i}",xx,1960,deck_top,50,70,ceiling-deck_top,dark)
  end
  box_in(mullion,'DOOR_THRESHOLD',x+200,1960,deck_top,width-400,70,45,dark)
  box_in(mullion,'DOOR_HEAD',x+200,1960,ceiling-45,width-400,70,45,dark)
  box_in(balustrade,'GLASS_GUARD',x,65,deck_top,width,24,1050,guard)
  box_in(handrail,'TOP_RAIL',x,50,deck_top+1050,width,55,50,dark)
  [x+10,x+width-55].each_with_index do |xx,i|
    box_in(handrail,"GUARD_END_POST_#{i}",xx,50,deck_top,45,55,1050,dark)
  end
  box_in(handrail,'BASE_CHANNEL',x,60,deck_top,width,35,35,dark)
end
