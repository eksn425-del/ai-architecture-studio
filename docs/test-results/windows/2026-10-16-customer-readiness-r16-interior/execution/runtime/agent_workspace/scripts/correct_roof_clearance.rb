# Scoped native r3 correction: retain asymmetric edge elevations and concavity.
# Source sections 5/8, exterior 1/2, interior 4; 1000mm lift is estimated.
# kstudio.custom_owned_ruby: preserve existing mesh, not a new SAIE/ADAI extrusion.
direct=lambda do |entities,name,pid|
  list=entities.select{|e| (e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance)) && e.name==name}
  raise "Nonunique target #{name}" unless list.length==1
  g=list.first
  raise "Target identity/lock changed #{name}" unless g.persistent_id==pid && !g.locked?
  g
end
entities_for=lambda{|g| g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities}
vertices_for=lambda{|entities|entities.grep(Sketchup::Edge).flat_map{|e|e.vertices}.uniq}
raise 'Unexpected root' unless root.persistent_id==20606
roof=direct.call(root.entities,'ROOF_TIMBER',77872)
shell=direct.call(roof.entities,'CURVED_SHELL',77873)
supports=direct.call(roof.entities,'ROOF_SUPPORTS',78849)
raise 'Clearance edit already applied' if shell.get_attribute('KStudio','clearance_lift_mm',0)!=0
raise 'Expected existing right-high reflection' unless roof.get_attribute('KStudio','roof_right_high',false)
shell.make_unique if shell.definition.instances.length>1
se=entities_for.call(shell)
raise 'Unexpected nested roof mesh' if se.any?{|e|e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)}
sv=vertices_for.call(se)
st=roof.transformation*shell.transformation
samples={}
sv.each do |v|
  p=st*v.position
  y=p.y.to_mm.round(5)
  z=p.z.to_mm
  samples[y]=z if !samples.key?(y) || z<samples[y]
end
ys=samples.keys.sort
raise 'Unexpected roof span' unless ys.first.abs<0.1 && (ys.last-20000).abs<0.1 && ys.length>=41
lift=lambda do |y|
  t=[[y/20000.0,0.0].max,1.0].min
  1000.0*4.0*t*(1.0-t)
end
new_samples=ys.map{|y|[y,samples[y]+lift.call(y)]}
profile=lambda do |y|
  if y<=ys.first
    a,b=new_samples[0],new_samples[1]
  elsif y>=ys.last
    a,b=new_samples[-2],new_samples[-1]
  else
    i=ys.bsearch_index{|value|value>=y}
    a,b=new_samples[i-1],new_samples[i]
  end
  a[1]+(b[1]-a[1])*(y-a[0])/(b[0]-a[0])
end
new_samples.each_cons(3) do |a,b,c|
  raise 'Roof lost continuous concavity' unless (c[1]-b[1])/(c[0]-b[0]) > (b[1]-a[1])/(b[0]-a[0])-0.000001
end
raise 'Right-high edge relation lost' unless profile.call(0)>profile.call(20000)+900
old_min=samples.values.min
new_min=new_samples.map{|p|p[1]}.min
raise 'Clearance out of source-estimated range' unless (new_min-10800).between?(3900,4100)
# Move existing shell vertices in root Z; preserve every XY and thickness.
vectors=sv.map do |v|
  p=st*v.position
  st.inverse*Geom::Vector3d.new(0,0,lift.call(p.y.to_mm).mm)
end
se.transform_by_vectors(sv,vectors)
raise 'Invalid shell faces' unless se.grep(Sketchup::Face).all?{|f|f.valid? && f.area>0}

support_entities=entities_for.call(supports)
targets=support_entities.select{|g|(g.is_a?(Sketchup::Group)||g.is_a?(Sketchup::ComponentInstance)) && g.name.match?(/\AEND_(GLASS|MULLION)_[01]_\d+\z/)}
raise 'Unexpected end targets' unless targets.length==102
glass_targets=targets.select{|g|g.name.start_with?('END_GLASS_')}
max_gap=0.0
max_overlap=0.0
targets.each do |g|
  # Endpoint mullions are KEEP; the two unequal high edges do not move.
  next if g.name.match?(/\AEND_MULLION_[01]_(0|10)\z/)
  g.make_unique if g.definition.instances.length>1
  ge=entities_for.call(g)
  raise "Unexpected nested target #{g.name}" if ge.any?{|e|e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)}
  gt=roof.transformation*supports.transformation*g.transformation
  vv=vertices_for.call(ge)
  bottom_before=vv.select{|v|(gt*v.position).z.to_mm<10800.1}.map{|v|[v,(gt*v.position)]}
  top=vv.select{|v|(gt*v.position).z.to_mm>12000}
  raise "Missing roof-joint vertices #{g.name}" if top.empty?
  shifts=top.map do |v|
    p=gt*v.position
    dz=profile.call(p.y.to_mm)-p.z.to_mm
    gt.inverse*Geom::Vector3d.new(0,0,dz.mm)
  end
  ge.transform_by_vectors(top,shifts)
  bottom_before.each{|v,p|raise "Moved fixed bottom #{g.name}" if (gt*v.position).distance(p)>0.000001}
  top.each{|v|p=gt*v.position;raise "Open joint #{g.name}" if (p.z.to_mm-profile.call(p.y.to_mm)).abs>0.001}
  raise "Invalid target face #{g.name}" unless ge.grep(Sketchup::Face).all?{|f|f.valid? && f.area>0}
  # Glass straight top edges span 500mm; evaluate roof's 250mm breakpoints too.
  if g.name.start_with?('END_GLASS_')
    points=top.map{|v|gt*v.position}.sort_by{|p|p.y}
    a,b=points.first,points.last
    ya,yb=a.y.to_mm,b.y.to_mm
    ys.select{|y|y>=ya-0.001 && y<=yb+0.001}.each do |y|
      z=a.z.to_mm+(b.z.to_mm-a.z.to_mm)*(y-ya)/(yb-ya)
      residual=profile.call(y)-z
      max_gap=[max_gap,residual].max
      max_overlap=[max_overlap,-residual].max
    end
  end
end
raise 'Roof/glass separation exceeds 0.01mm' if max_gap>0.01
raise 'Glass/roof sampling overlap exceeds 2mm' if max_overlap>2.0
actual_min=vertices_for.call(se).map{|v|(st*v.position).z.to_mm}.min
raise 'Roof minimum readback mismatch' if (actual_min-new_min).abs>0.001
shell.set_attribute('KStudio','clearance_lift_mm',1000)
shell.set_attribute('KStudio','soffit_min_before_mm',old_min)
shell.set_attribute('KStudio','soffit_min_after_mm',actual_min)
shell.set_attribute('KStudio','min_clearance_after_mm',actual_min-10800)
shell.set_attribute('KStudio','glass_joint_max_gap_mm',max_gap)
shell.set_attribute('KStudio','glass_joint_max_overlap_mm',max_overlap)
shell.set_attribute('KStudio','clearance_joint_check','passed')
