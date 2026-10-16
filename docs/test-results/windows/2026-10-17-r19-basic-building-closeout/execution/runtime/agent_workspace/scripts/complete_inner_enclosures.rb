# Add only four explicitly scoped envelope leaves. All dimensions are mm.
# kstudio.custom_owned_ruby: transparent planar glazing/open leaves and slender
# profiles do not fit SAIE opaque solid-wall/opening constructors. ADAI disabled.
def ce_find(es,name)
  a=es.select{|e|e.respond_to?(:name)&&e.name==name}
  raise "Missing/duplicate #{name}" unless a.length==1
  a.first
end
def ce_es(g)
  g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities
end
def ce_group(es,name)
  g=es.add_group;g.name=name;g.set_attribute('KStudio','semantic_id',name);g
end
def ce_point(mode,u,n,z)
  (mode==:long ? [u,n,z] : [n,u,z]).map(&:mm)
end
def ce_box(es,name,mode,u0,u1,n0,n1,z0,z1,mat)
  raise 'Degenerate frame' unless u1-u0>0.01 && n1-n0>0.01 && z1-z0>0.01
  g=ce_group(es,name)
  f=g.entities.add_face([[u0,n0],[u1,n0],[u1,n1],[u0,n1]].map{|u,n|ce_point(mode,u,n,z0)})
  raise 'Frame face failed' unless f && f.valid?
  f.reverse! if f.normal.z<0;f.pushpull((z1-z0).mm);g.material=mat;g
end
def ce_glass(es,name,mode,lo,hi,z0,z1,mat)
  return if hi-lo<0.1 || z1-z0<0.1
  g=ce_group(es,name)
  f=g.entities.add_face([[lo,z0],[hi,z0],[hi,z1],[lo,z1]].map{|u,z|ce_point(mode,u,0,z)})
  raise 'Glass face failed' unless f && f.valid?
  f.material=mat;f.back_material=mat;g
end
def ce_open_leaf(es,name,mode,u,width,sign,zbase,mat,glass,hinge_side)
  g=ce_group(es,name)
  ua,ub=hinge_side==:left ? [u-24,u] : [u,u+24]
  na,nb=[0.0,sign*width].minmax
  ce_box(g.entities,'HINGE_STILE',mode,ua,ub,-12,12,zbase,zbase+2400,mat)
  ce_box(g.entities,'OPEN_EDGE_STILE',mode,ua,ub,nb-24,nb,zbase,zbase+2400,mat) if sign>0
  ce_box(g.entities,'OPEN_EDGE_STILE',mode,ua,ub,na,na+24,zbase,zbase+2400,mat) if sign<0
  ce_box(g.entities,'LEAF_TOP',mode,ua,ub,na,nb,zbase+2376,zbase+2400,mat)
  ce_box(g.entities,'LEAF_BOTTOM',mode,ua,ub,na,nb,zbase,zbase+24,mat)
  n0,n1=na+24,nb-24
  face=g.entities.add_face([ce_point(mode,(ua+ub)/2,n0,zbase+24),ce_point(mode,(ua+ub)/2,n1,zbase+24),ce_point(mode,(ua+ub)/2,n1,zbase+2376),ce_point(mode,(ua+ub)/2,n0,zbase+2376)])
  raise 'Open leaf glass failed' unless face
  face.material=glass;face.back_material=glass
  g.set_attribute('KStudio','opening_angle_deg',90);g
end
def ce_panel(es,name,mode,lo,hi,base,top,door,sign,mat,glass,vertical_edges)
  g=ce_group(es,name)
  raise 'Panel too low' unless top-base>2500
  bottom=base+30;transom=base+2400
  if door
    a,b=door
    raise 'Door outside panel' unless a-40>lo && b+40<hi && b-a>=1999
    ce_glass(g.entities,'LOWER_FIXED_LEFT',mode,lo,a-40,bottom,transom,glass)
    ce_glass(g.entities,'LOWER_FIXED_RIGHT',mode,b+40,hi,bottom,transom,glass)
    [[lo,a-40],[b+40,hi]].each_with_index{|ab,i|ce_box(g.entities,"SILL_#{i}",mode,ab[0],ab[1],-20,20,base,bottom,mat)}
    ce_box(g.entities,'DOOR_LEFT_JAMB',mode,a-40,a,-25,25,base,transom,mat)
    ce_box(g.entities,'DOOR_RIGHT_JAMB',mode,b,b+40,-25,25,base,transom,mat)
    ce_open_leaf(g.entities,'DOOR_LEFT_OPEN_90',mode,a,(b-a)/2,sign,base,mat,glass,:left)
    ce_open_leaf(g.entities,'DOOR_RIGHT_OPEN_90',mode,b,(b-a)/2,sign,base,mat,glass,:right)
    g.set_attribute('KStudio','clear_portal_mm',[a,b,base,transom])
    g.set_attribute('KStudio','threshold','no raised sill or glass across portal')
  else
    ce_glass(g.entities,'LOWER_FIXED_GLASS',mode,lo,hi,bottom,transom,glass)
    ce_box(g.entities,'SILL',mode,lo,hi,-20,20,base,bottom,mat)
  end
  ce_box(g.entities,'TRANSOM_AT_DOOR_HEAD',mode,lo,hi,-20,20,transom,transom+40,mat)
  ce_glass(g.entities,'UPPER_FIXED_GLASS',mode,lo,hi,transom+40,top-20,glass)
  ce_box(g.entities,'TOP_RAIL',mode,lo,hi,-20,20,top-20,top,mat)
  if vertical_edges
    ce_box(g.entities,'EDGE_LEFT',mode,lo-20,lo+20,-20,20,base,top,mat)
    ce_box(g.entities,'EDGE_RIGHT',mode,hi-20,hi+20,-20,20,base,top,mat)
  end
  g
end
def ce_floor_support(floors,x,y,z)
  pt=Geom::Point3d.new(x.mm,y.mm,z.mm)
  floors.entities.select{|g|g.respond_to?(:name)}.any? do |g|
    next false unless g.is_a?(Sketchup::Group)||g.is_a?(Sketchup::ComponentInstance)
    local=g.transformation.inverse*pt
    ce_es(g).grep(Sketchup::Face).any? do |f|
      next false unless f.vertices.all?{|v|(v.position.z-local.z).abs<0.01.mm}
      [Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(local))
    end
  end
end
raise 'Wrong root' unless root.persistent_id==20606
env=ce_find(root.entities,'ENVELOPE_OUTER')
raise 'Unexpected envelope' unless env.persistent_id==41319 && env.transformation.identity? && env.definition.instances.length==1
roof=ce_find(root.entities,'ROOF_TIMBER')
shell=ce_find(roof.entities,'CURVED_SHELL')
support=ce_find(roof.entities,'ROOF_SUPPORTS')
floors=ce_find(root.entities,'FLOORS')
structure=ce_find(root.entities,'STRUCTURE_EXISTING')
raise 'Transformed structure/floors' unless floors.transformation.identity? && structure.transformation.identity?
mat=model.materials['KS_White_Steel'];glass=model.materials['KS_Clear_Glass']
raise 'Missing existing finishes' unless mat && glass
names=['HALL_LONG_SOUTH_ADDITION','HALL_LONG_NORTH_ADDITION','LOWER_END_WEST_ADDITION','LOWER_END_EAST_ADDITION']
names.each{|name|raise "Target already exists #{name}" if env.entities.any?{|e|e.respond_to?(:name)&&e.name==name}}
st=roof.transformation*shell.transformation
world=ce_es(shell).grep(Sketchup::Edge).flat_map(&:vertices).uniq.map{|v|st*v.position}
raise 'Missing roof edge geometry' if world.empty?
door_checks=[]
# Actual world edges include the previously accepted handedness and clearance.
[['HALL_LONG_SOUTH_ADDITION',0.0,-1],['HALL_LONG_NORTH_ADDITION',20000.0,1]].each do |name,y,sign|
  edge=world.select{|p|(p.y.to_mm-y).abs<0.1}
  raise 'Roof edge not found' if edge.empty?
  underside=edge.map{|p|p.z.to_mm}.min
  top=underside-90.0 # existing 180mm edge beam underside; no roof edit
  leaf=ce_group(env.entities,name)
  leaf.set_attribute('KStudio','source','SOURCE2/4/5/7/8; detailed subdivisions inferred')
  leaf.set_attribute('KStudio','actual_roof_edge_underside_mm',underside)
  leaf.set_attribute('KStudio','glass_top_below_edge_beam_mm',90)
  definitions={}
  (0...20).each do |bay|
    door=[0,10,19].include?(bay)
    key=door ? 'DOOR' : 'FIXED'
    instance_name="BAY_#{bay.to_s.rjust(2,'0')}_#{key}"
    if definitions[key]
      module_instance=leaf.entities.add_instance(definitions[key],Geom::Transformation.translation([(bay*2500).mm,y.mm,0]))
      module_instance.name=instance_name;module_instance.set_attribute('KStudio','semantic_id',instance_name)
    else
      g=ce_panel(leaf.entities,instance_name,:long,55,2445,10800,top,door ? [200,2300] : nil,sign,mat,glass,false)
      raise 'Representative module dimensions' unless (g.bounds.width.to_mm-2390).abs<0.1
      module_instance=g.to_component;module_instance.name=instance_name;module_instance.definition.name="KS_#{name}_#{key}_2500"
      module_instance.set_attribute('KStudio','semantic_id',instance_name);definitions[key]=module_instance.definition
      module_instance.transform!(Geom::Transformation.translation([(bay*2500).mm,y.mm,0]))
    end
    if door
      x=bay*2500+1250
      raise 'Hall doorway lacks inside floor' unless ce_floor_support(floors,x,y-sign*100,10800)
      door_checks<<[name,bay,2100,2400,10800]
    end
  end
end
# Lower end glass stops under the existing cross beam and starts on each slab.
# At west L2 the Y<11000 region is a void: continuous glass, no invented door/floor.
[['LOWER_END_WEST_ADDITION',0.0,-1,0],['LOWER_END_EAST_ADDITION',50000.0,1,10]].each do |name,x,sign,column|
  leaf=ce_group(env.entities,name)
  leaf.set_attribute('KStudio','source','SOURCE1/3/5/7/8; remote end subdivision inferred')
  [0,3600,7200].each do |base|
    beam=ce_find(structure.entities,"CROSS_BEAM_Z#{base+3600}_X#{column}")
    top=beam.bounds.min.z.to_mm
    intervals=[[200,2500],[2500,5000],[5000,7500],[7500,9800],[10200,12500],[12500,15000],[15000,17500],[17500,19800]]
    intervals.each_with_index do |ab,i|
      lo,hi=ab.map(&:to_f)
      if x>0 && base==0
        next if lo>=13500
        hi=[hi,13500.0].min # existing opaque service core encloses the rest
      end
      door=nil
      if x==0
        door=[5200.0,7400.0] if i==2 && base<7200
        door=[15200.0,17400.0] if i==6
      else
        door=[7600.0,9600.0] if i==3
        door=[15200.0,17400.0] if i==6 && base>0
      end
      g=ce_panel(leaf.entities,"LEVEL_#{base}_BAY_#{i}",:end,lo,hi,base,top,door,sign,mat,glass,true)
      g.transform!(Geom::Transformation.translation([x.mm,0,0]))
      if door
        center=(door[0]+door[1])/2
        raise 'End door lacks occupied floor inside' unless ce_floor_support(floors,x-sign*100,center,base)
        door_checks<<[name,base,door[1]-door[0],2400,base]
      end
    end
  end
end
raise 'Door schedule failed' unless door_checks.length==16
raise 'Missing addition' unless names.all?{|n|env.entities.count{|g|g.respond_to?(:name)&&g.name==n}==1}
puts "ENCLOSURE_ADDITIONS_VERIFIED: four additive leaves; 40 upper hall bays; 16 empty portals with open leaves; inside floor classified; roof/frame/slabs/existing glass untouched"
puts door_checks.inspect
