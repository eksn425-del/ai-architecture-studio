# Source05 section hanging outward-down eave flap; source08 arrows are not solids.
# kstudio.custom_owned_ruby: SAIE opaque straight walls do not form transparent
# zero-thickness shared glazing cutouts or hinged/stayed glazed frames. ADAI disabled.
# Host has verified and approved ALL38 physical occurrences of this shared GLASS.
# Do not make a bay unique or edit a bay/frame; clear shared leaf exactly ONCE.
def ov_find(es,n)
  a=es.select{|e|(e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance))&&e.name==n}
  raise "Missing/duplicate #{n}" unless a.length==1;a.first
end
def ov_group(es,n)
  g=es.add_group;g.name=n;g.set_attribute('KStudio','semantic_id',n);g
end
def ov_bar(es,n,a,b,w,mat)
  v=Geom::Vector3d.new(*(0..2).map{|i|(b[i]-a[i]).mm});len=v.length
  raise 'Zero bar' if len<0.001
  g=ov_group(es,n);q=w/2.0
  f=g.entities.add_face([[-q,-q,0],[q,-q,0],[q,q,0],[-q,q,0]].map{|p|p.map(&:mm)})
  f.reverse! if f.normal.z<0;f.pushpull(len);g.material=mat
  zz=v.normalize;ref=zz.parallel?(Z_AXIS) ? X_AXIS : Z_AXIS
  xx=ref.cross(zz).normalize;yy=zz.cross(xx).normalize
  g.transformation=Geom::Transformation.axes(Geom::Point3d.new(*a.map(&:mm)),xx,yy,zz);g
end
raise 'Wrong owned root' unless root.persistent_id==20606
env=ov_find(root.entities,'ENVELOPE_OUTER')
raise 'Unexpected envelope' unless env.persistent_id==41319 && env.transformation.identity?
raise 'Vent leaf already exists' if env.entities.grep(Sketchup::Group).any?{|e|e.name=='OUTER_EAVE_VENTS'}
targets=[]
['NORTH','SOUTH'].each do |side|
  (1..19).each do |i|
    bay=ov_find(env.entities,"#{side}_BAY_#{i}");glass=ov_find(bay.definition.entities,'GLASS')
    raise 'Unexpected shared physical leaf' unless glass.persistent_id==41323
    raise 'Unexpected glass transform' unless glass.transformation.identity?
    p=bay.transformation*Geom::Point3d.new(0,0,0)
    raise 'Unexpected bay position' unless (p.x.to_mm-(-4000+i*2900)).abs<0.01 && (p.y.to_mm-(side=='NORTH' ? 24000 : -4000)).abs<0.01
    targets<<[side,i,bay,glass]
  end
end
raise 'Unexpected shared definition' unless targets.map{|a|a[2].definition}.uniq.length==1 && targets.first[2].definition.instances.length==38
glass=targets.first[3];old_mat=glass.entities.grep(Sketchup::Face).first.material||glass.material
steel=model.materials['KS_White_Steel'];raise 'Missing steel or glass' unless steel && old_mat
clear_owned_contents.call(['ENVELOPE_OUTER','NORTH_BAY_1','GLASS'])
# A single shared zero-thickness face with a true rectangular void. Lower glass
# remains complete, original shared mullions/transoms untouched. Container PID stable.
es=glass.entities
f=es.add_face([[0,0,7200],[2900,0,7200],[2900,0,13500],[0,0,13500]].map{|p|p.map(&:mm)})
hole=es.add_face([[90,0,12600],[2810,0,12600],[2810,0,13400],[90,0,13400]].map{|p|p.map(&:mm)})
raise 'Aperture failed' unless hole && hole.valid?
hole.erase!
es.grep(Sketchup::Face).each{|ff|ff.material=old_mat;ff.back_material=old_mat}
raise 'Shared leaf identity changed' unless glass.persistent_id==41323
remaining_area=es.grep(Sketchup::Face).sum{|ff|ff.area}*25.4*25.4
raise 'Wrong actual aperture area' unless (remaining_area-(2900*6300-2720*800)).abs<1
raise 'No real inner loop' unless es.grep(Sketchup::Face).any?{|ff|ff.loops.length==2}
vents=ov_group(env.entities,'OUTER_EAVE_VENTS')
mat=model.materials.add('OV_Clear_Vent_Glass_R17');mat.color=Sketchup::Color.new(222,242,245);mat.alpha=0.16
proto=ov_group(vents.entities,'OV_PROTOTYPE')
pe=proto.entities
# x local across bay; y local OUTWARD; z model elevation. Inboard canopy unchanged.
ov_bar(pe,'HINGE_HEADER',[0,25,13400],[2900,25,13400],24,steel)
[15,2885].each_with_index{|x,j|ov_bar(pe,"ROOF_FRAME_CLIP_#{j}",[x,15,13500],[x,25,13400],16,steel)}
corners=[[55,25,13400],[2845,25,13400],[2845,475,12500],[55,475,12500]]
4.times{|j|ov_bar(pe,"SASH_EDGE_#{j}",corners[j],corners[(j+1)%4],28,steel)}
ov_bar(pe,'SASH_CENTRE',[1450,25,13400],[1450,475,12500],20,steel)
pg=ov_group(pe,'TRANSPARENT_OUTWARD_DOWN_PANE');pf=pg.entities.add_face(corners.map{|p|p.map(&:mm)})
pf.material=mat;pf.back_material=mat
[[15,55],[2885,2845]].each_with_index do |xs,j|
  ov_bar(pe,"STAY_#{j}",[xs[0],0,12800],[xs[1],340,12770],16,steel)
  ov_bar(pe,"STAY_FRAME_FOOT_#{j}",[xs[0],-5,12800],[xs[0],20,12800],22,steel)
end
comp=proto.to_component;comp.definition.name='OV_2900_CLEAR_TOPHINGED_450x900'
definition=comp.definition
targets.each_with_index do |a,j|
  side,i,bay=a[0],a[1],a[2]
  inst=j==0 ? comp : vents.entities.add_instance(definition,Geom::Transformation.new)
  inst.name="#{side}_VENT_BAY_#{i}";inst.set_attribute('KStudio','semantic_id',inst.name)
  sg=side=='NORTH' ? 1 : -1
  inst.transformation=Geom::Transformation.translation([(-4000+i*2900).mm,(sg==1 ? 24000 : -4000).mm,0])*Geom::Transformation.scaling(1,sg,1)
  raise 'Inboard intrusion' unless sg==1 ? inst.bounds.min.y.to_mm>=23990 : inst.bounds.max.y.to_mm<=-3990
end
raise 'Wrong vent count' unless vents.entities.grep(Sketchup::ComponentInstance).length==38
# Probe each real high-level aperture from just outside the original glass plane.
tests=0
targets.each do |side,i,bay,gl|
  sg=side=='NORTH' ? 1 : -1;y=sg==1 ? 24000 : -4000
  [12700,13200].each do |z|
    a=Geom::Point3d.new((-4000+i*2900+1450).mm,(y+sg*5).mm,z.mm)
    hit=model.raytest([a,Geom::Vector3d.new(0,-sg,0)],true)
    raise 'Backing glass still blocks aperture' if hit && a.distance(hit[0]).to_mm<50
    tests+=1
  end
end
puts "38 outward-down clear vents; 38 real openings 2720x800mm; #{tests} short-ray tests passed; original glass container PID41323 retained."
