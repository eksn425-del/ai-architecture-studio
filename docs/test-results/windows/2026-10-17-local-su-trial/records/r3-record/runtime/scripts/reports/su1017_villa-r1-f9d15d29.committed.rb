# SU-1017. Dimensions in millimetres. Only the injected owned root is edited.
def villa_group(entities, name)
  g = entities.add_group
  g.name = name
  g
end

def villa_box(entities, name, x, y, z, w, d, h, material)
  g = villa_group(entities, name)
  pts = [[x,y,z],[x+w,y,z],[x+w,y+d,z],[x,y+d,z]].map { |a| a.map { |v| v.mm } }
  f = g.entities.add_face(pts)
  f.reverse! if f.normal.z < 0
  f.pushpull(h.mm)
  g.material = material
  g
end

def villa_opening(entities, name, x, z, width, height, frame, glass)
  g = villa_group(entities, name)
  e = g.entities
  villa_box(e,'JAMB_LEFT',0,80,0,60,65,height,frame)
  villa_box(e,'JAMB_RIGHT',width-60,80,0,60,65,height,frame)
  villa_box(e,'HEAD',60,80,height-60,width-120,65,60,frame)
  villa_box(e,'SILL',60,70,0,width-120,85,60,frame)
  villa_box(e,'MEETING_STILE',width/2.0-30,65,60,60,80,height-120,frame)
  villa_box(e,'GLASS_LEFT',60,112,60,width/2.0-90,8,height-120,glass)
  villa_box(e,'GLASS_RIGHT',width/2.0+30,105,60,width/2.0-90,8,height-120,glass)
  g.transform!(Geom::Transformation.translation([x.mm,0,z.mm]))
  g
end

white = model.materials.add('VILLA_White_stucco')
white.color = Sketchup::Color.new(240,238,231)
cap = model.materials.add('VILLA_Thin_light_coping')
cap.color = Sketchup::Color.new(215,215,209)
stone = model.materials.add('VILLA_Grey_plinth')
stone.color = Sketchup::Color.new(178,179,178)
frame = model.materials.add('VILLA_Charcoal_frames')
frame.color = Sketchup::Color.new(47,49,50)
metal = model.materials.add('VILLA_Slim_guard_metal')
metal.color = Sketchup::Color.new(125,132,133)
glass = model.materials.add('VILLA_Door_glass')
glass.color = Sketchup::Color.new(128,147,163)
glass.alpha = 0.42
guardglass = model.materials.add('VILLA_Guard_glass')
guardglass.color = Sketchup::Color.new(177,206,215)
guardglass.alpha = 0.24
wood = model.materials.add('VILLA_Warm_vertical_timber')
wood.color = Sketchup::Color.new(189,128,53)
darkwood = model.materials.add('VILLA_Timber_shadow_backing')
darkwood.color = Sketchup::Color.new(78,56,34)

# Stage 1: continuous wall solids with true openings, then floor/roof silhouette.
saie_wall_with_openings.call({'name'=>'SHELL_FRONT','centerline'=>[[0,100],[8000,100]],'thickness_mm'=>200,'height_mm'=>6000,'elevation_mm'=>0,'openings'=>[
 {'offset_mm'=>1700,'width_mm'=>4200,'height_mm'=>2400,'sill_mm'=>0},
 {'offset_mm'=>1300,'width_mm'=>2200,'height_mm'=>2400,'sill_mm'=>3000},
 {'offset_mm'=>4900,'width_mm'=>1800,'height_mm'=>2400,'sill_mm'=>3000}]})
saie_wall_with_openings.call({'name'=>'SHELL_LEFT','centerline'=>[[100,200],[100,6800]],'thickness_mm'=>200,'height_mm'=>6000,'elevation_mm'=>0,'openings'=>[
 {'offset_mm'=>3800,'width_mm'=>600,'height_mm'=>1800,'sill_mm'=>700},
 {'offset_mm'=>3800,'width_mm'=>600,'height_mm'=>1800,'sill_mm'=>3700}]})
saie_wall.call({'name'=>'SHELL_REAR','centerline'=>[[0,6900],[8000,6900]],'thickness_mm'=>200,'height_mm'=>6000,'elevation_mm'=>0})
saie_wall.call({'name'=>'SHELL_RIGHT','centerline'=>[[7900,200],[7900,6800]],'thickness_mm'=>200,'height_mm'=>6000,'elevation_mm'=>0})
root.entities.grep(Sketchup::Group).each { |g| g.material = white }
villa_box(root.entities,'SLAB_GROUND',0,0,-180,8000,7000,180,stone)
villa_box(root.entities,'SLAB_LEVEL_2',200,200,2820,7600,6600,180,white)
villa_box(root.entities,'ROOF_FLAT',0,0,5820,8000,7000,180,white)
villa_box(root.entities,'ROOF_CAP',-15,-20,6000,8030,7035,50,cap)
villa_box(root.entities,'BALCONY_SLAB',600,-1200,2700,7200,1400,300,white)

# Stage 2: representative two-leaf recessed door; validate before replication.
prototype = villa_opening(root.entities,'DOOR_FRONT_L2_01',1300,3000,2200,2400,frame,glass)
raise 'Invalid representative door' unless prototype.valid? && prototype.entities.grep(Sketchup::Group).length == 7
# Stage 3: unique semantic assemblies using the verified profile dimensions.
villa_opening(root.entities,'DOOR_FRONT_L1_01',1700,0,4200,2400,frame,glass)
villa_opening(root.entities,'DOOR_FRONT_L2_02',4900,3000,1800,2400,frame,glass)
[700,3700].each_with_index do |z,i|
  g = villa_opening(root.entities,"WINDOW_LEFT_L#{i+1}_01",0,0,600,1800,frame,glass)
  rotation = Geom::Transformation.rotation(ORIGIN,Z_AXIS,-90.degrees)
  g.transform!(Geom::Transformation.translation([0,4600.mm,z.mm]) * rotation)
end
screen = villa_group(root.entities,'SCREEN_FRONT_RIGHT')
villa_box(screen.entities,'RECESSED_BACKING',7100,-20,60,900,20,5920,darkwood)
12.times do |i|
  villa_box(screen.entities,format('SLAT_%02d',i+1),7100+i*(855.0/11),-100,60,45,80,5920,wood)
end

# Stage 4: front glass guard with short side returns and slender metal edges.
front = villa_group(root.entities,'BALCONY_GUARD_FRONT')
6.times do |i|
  x = 620+i*1190
  villa_box(front.entities,format('PANE_%02d',i+1),x+12,-1170,3020,1166,12,1060,guardglass)
end
7.times do |i|
  villa_box(front.entities,format('POST_%02d',i+1),620+i*1190,-1180,3000,25,30,1100,metal)
end
villa_box(front.entities,'TOP_RAIL',620,-1180,4080,7165,30,25,metal)
villa_box(front.entities,'BOTTOM_CHANNEL',620,-1180,3000,7165,30,22,metal)
[['LEFT',620],['RIGHT',7760]].each do |side,x|
  g = villa_group(root.entities,'BALCONY_GUARD_'+side)
  villa_box(g.entities,'RETURN_GLASS',x,-1140,3020,12,1100,1060,guardglass)
  villa_box(g.entities,'WALL_POST',x-6,-40,3000,25,30,1100,metal)
  villa_box(g.entities,'RETURN_TOP_RAIL',x-6,-1170,4080,25,1160,25,metal)
end
# Stage 5: source-observed low grey plinth, interrupted by the ground doorway.
plinth = villa_group(root.entities,'FINISH_PLINTH')
villa_box(plinth.entities,'FRONT_LEFT',0,-5,0,1700,8,220,stone)
villa_box(plinth.entities,'FRONT_RIGHT',5900,-5,0,1200,8,220,stone)
villa_box(plinth.entities,'LEFT',-5,0,0,8,7000,220,stone)
villa_box(plinth.entities,'REAR',0,6997,0,8000,8,220,stone)
villa_box(plinth.entities,'RIGHT',7997,0,0,8,7000,220,stone)
