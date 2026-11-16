# encoding: UTF-8
# Stage 1: source-anchored primary volumes; root is supplied by the host.
def cg(parent, name)
  g = parent.entities.add_group
  g.name = name
  g
end
def bx(parent, name, x, y, z, w, d, h, mat)
  g = cg(parent, name)
  pts = [[x,y,z],[x+w,y,z],[x+w,y+d,z],[x,y+d,z]].map { |p| p.map { |v| v.mm } }
  f = g.entities.add_face(pts)
  f.reverse! if f.normal.z < 0
  f.pushpull(h.mm)
  g.material = mat
  g.entities.grep(Sketchup::Face).each { |q| q.material=mat; q.back_material=mat }
  g
end
def mt(model, name, rgb)
  m = model.materials[name] || model.materials.add(name)
  m.color = Sketchup::Color.new(*rgb)
  m
end
mass = mt(model,'Envelope_bluegrey',[132,151,157])
stone = mt(model,'Warm_limestone',[207,191,162])
b = cg(root,'BUILDING')
t = cg(b,'TOWER')
bx(cg(t,'MASSING'),'ENVELOPE',0,0,0,18000,14400,56900,mass)
['FACADE','ROOF','MODULE_PROTOTYPE'].each { |n| cg(t,n) }
s = cg(b,'STEPPED_WING')
sm = cg(s,'MASSING')
[[-21600,6],[-16200,8],[-10800,10],[-5400,13]].each_with_index do |a,i|
  bx(sm,"STEP_#{i+1}",a[0],0,0,5400,14400,4200+(a[1]-1)*3100,mass)
end
['FACADE','TERRACES'].each { |n| cg(s,n) }
u = cg(b,'LEFT_UPPER')
bx(cg(u,'MASSING'),'ENVELOPE',-46800,3600,0,14400,18000,22800,mass)
['FACADE','ROOF'].each { |n| cg(u,n) }
l = cg(b,'LEFT_STREET')
bx(cg(l,'MASSING'),'ENVELOPE',-32400,0,0,10800,10800,13500,mass)
['FACADE','ROOF'].each { |n| cg(l,n) }
c=cg(root,'CONTEXT')
bx(cg(c,'RIGHT_NEIGHBOR'),'ENVELOPE',21000,8500,0,23000,16000,29000,stone)
e=cg(root,'ENVIRONMENT')
['INTERSECTION','CURBS','TRACKS','CONTACT_WIRES'].each { |n| cg(e,n) }
v=cg(root,'VEGETATION')
['ROOF_INSTANCES','TERRACE_INSTANCES','STREET_INSTANCES'].each { |n| cg(v,n) }
