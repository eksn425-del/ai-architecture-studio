# Source4: slim central spiral support, pale upper floor/timber soffit.
# Custom owned Ruby: SAIE opaque straight walls cannot form stair brackets.
raise 'Wrong root' unless root.persistent_id==20606
find=lambda{|es,n| a=es.grep(Sketchup::Group).select{|g|g.name==n};raise "Missing #{n}" unless a.length==1;a.first}
cir=find.call(root.entities,'CIRCULATION_INTERNAL')
steel=model.materials['KS_White_Steel']
3.times do |k|
  stair=find.call(cir.entities,"SPIRAL_L#{k}_L#{k+1}")
  core=find.call(stair.entities,"S#{k}_CONTINUOUS_CORE")
  collar=find.call(stair.entities,"S#{k}_CORE_BASE_COLLAR")
  raise 'Shared target' unless [core,collar].all?{|g|g.definition.instances.length==1}
  clear_owned_contents.call(['CIRCULATION_INTERNAL',stair.name,core.name])
  z=k*3600
  f=core.entities.add_face(core.entities.add_circle([37000.mm,6500.mm,z.mm],Z_AXIS,180.mm,64))
  f.reverse! if f.normal.z<0;f.pushpull(3600.mm);core.material=steel
  # Short radial brackets connect the retained tread roots to the slim shaft.
  24.times do |i|
    a=(45+330.0*(i+0.5)/24)*Math::PI/180
    h=z+(i+1)*150-100
    g=core.entities.add_group;g.name="S#{k}_ROOT_BRACKET_#{i}";g.set_attribute('KStudio','semantic_id',g.name)
    pts=[[165,-32.5,h-65],[390,-32.5,h-65],[390,32.5,h-65],[165,32.5,h-65]]
    ff=g.entities.add_face(pts.map{|p|p.map(&:mm)});ff.reverse! if ff.normal.z<0;ff.pushpull(65.mm)
    g.material=steel
    g.transform!(Geom::Transformation.translation([37000.mm,6500.mm,0])*Geom::Transformation.rotation(ORIGIN,Z_AXIS,a))
  end
  # Landing short roots meet the retained under-landing radial support.
  [Math::PI/9,Math::PI/4].each_with_index do |a,i|
    g=core.entities.add_group;g.name="S#{k}_LANDING_ROOT_#{i}";g.set_attribute('KStudio','semantic_id',g.name)
    ff=g.entities.add_face([[165,-32.5,z+3417.5],[425,-32.5,z+3417.5],[425,32.5,z+3417.5],[165,32.5,z+3417.5]].map{|p|p.map(&:mm)})
    ff.reverse! if ff.normal.z<0;ff.pushpull(65.mm);g.material=steel
    g.transform!(Geom::Transformation.translation([37000.mm,6500.mm,0])*Geom::Transformation.rotation(ORIGIN,Z_AXIS,a))
  end
  clear_owned_contents.call(['CIRCULATION_INTERNAL',stair.name,collar.name])
  f=collar.entities.add_face(collar.entities.add_circle([37000.mm,6500.mm,z.mm],Z_AXIS,235.mm,64))
  f.reverse! if f.normal.z<0;f.pushpull(35.mm);collar.material=steel
end
floors=find.call(root.entities,'FLOORS');roof=find.call(root.entities,'ROOF_TIMBER')
l3=find.call(floors.entities,'L3');shell=find.call(roof.entities,'CURVED_SHELL')
shape=lambda{|g|g.entities.grep(Sketchup::Edge).map{|e|[e.persistent_id,e.vertices.map{|v|v.position.to_a}]}}
before=[shape.call(l3),shape.call(shell)]
floor_mat=model.materials.add('IC_Pale_Upper_Floor_R17');floor_mat.color=Sketchup::Color.new(248,246,236)
wood_mat=model.materials.add('IC_Light_Birch_R17');wood_mat.color=Sketchup::Color.new(253,240,216)
l3.entities.grep(Sketchup::Face).each{|f|if f.normal.z.abs>0.99;f.material=floor_mat;f.back_material=floor_mat;end}
shell.entities.grep(Sketchup::Face).each{|f|f.material=wood_mat;f.back_material=wood_mat}
raise 'Changed roof/floor geometry' unless before==[shape.call(l3),shape.call(shell)]
puts 'Slim 360mm core, rooted stair brackets, brighter pale finishes; retained roof/floor coordinates unchanged.'
