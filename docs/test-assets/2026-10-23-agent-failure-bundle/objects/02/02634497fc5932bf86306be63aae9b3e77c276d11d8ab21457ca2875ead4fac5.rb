# encoding: UTF-8
def findg(parent, name)
  parent.entities.grep(Sketchup::Group).find { |g| g.name == name }
end
def cg(parent, name)
  g=parent.entities.add_group; g.name=name; g
end
def bx(parent,name,x,y,z,w,d,h,mat)
  g=cg(parent,name)
  f=g.entities.add_face([[x,y,z],[x+w,y,z],[x+w,y+d,z],[x,y+d,z]].map { |p| p.map { |v| v.mm } })
  f.reverse! if f.normal.z<0
  f.pushpull(h.mm)
  g.entities.grep(Sketchup::Face).each { |q| q.material=mat; q.back_material=mat }
  g
end
def mt(model,name,rgb)
  m=model.materials[name] || model.materials.add(name); m.color=Sketchup::Color.new(*rgb); m
end
stone=mt(model,'Warm_limestone',[207,191,162])
glass=mt(model,'Glazing_cool',[128,157,170])
dark=mt(model,'Bronze_mullion',[72,77,74])
floor=mt(model,'Slab_interior',[170,164,149])
b=findg(root,'BUILDING'); t=findg(b,'TOWER'); mass=findg(t,'MASSING')
clear_owned_contents.call(['BUILDING','TOWER','MASSING'])
bx(mass,'TEMP_INSET_ENVELOPE',200,1000,0,16600,13200,56900,glass)
p=cg(t,'MODULE_PROTOTYPE')
bx(p,'SLAB',50,50,4200-220,17900,14300,220,floor)
fr=cg(p,'FRAME')
bx(fr,'FRONT_COLUMN',14400-120,-300,4200,240,500,3100,stone)
bx(fr,'CORNER_COLUMN',18000-120,-300,4200,420,500,3100,stone)
bx(fr,'FRONT_BEAM',14280,-300,7080,4020,500,220,stone)
bx(fr,'SIDE_BEAM',17800,200,7080,500,3400,220,stone)
gl=cg(p,'GLAZING')
bx(gl,'FRONT_GLASS',14650,100,4420,3100,24,2600,glass)
bx(gl,'SIDE_GLASS',17900,200,4420,24,3150,2600,glass)
bx(gl,'FRONT_MULLION',16200,70,4420,48,80,2600,dark)
bx(gl,'SIDE_MULLION',17870,1800,4420,80,48,2600,dark)
saie_wall_with_openings.call({'name'=>'MODULE_FRONT_WALL','centerline'=>[[14400,100],[18000,100]],'thickness_mm'=>200,'height_mm'=>3100,'elevation_mm'=>4200,'openings'=>[{'offset_mm'=>250,'width_mm'=>3100,'height_mm'=>2600,'sill_mm'=>220}]})
