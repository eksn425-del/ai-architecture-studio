# encoding: UTF-8
# User-approved extraction of the connected building from its context.
# No new shell/profile/opening geometry. SAIE wall helpers are inapplicable
# to removing existing owned context; ADAI is disabled. Guarded custom Ruby.

def cleanup_named(parent, name, pid)
  found=parent.entities.grep(Sketchup::Group).select { |g| g.name==name }
  raise "Expected unique owned target #{name}" unless found.length==1
  g=found.first
  raise "Target identity changed #{name}" unless g.persistent_id==pid
  raise "Target is locked #{name}" if g.locked?
  raise "Shared target definition #{name}" unless g.definition.instances.length==1
  g
end

building=cleanup_named(root,'BUILDING',23)
cleanup_named(root,'MODULE_FRONT_WALL',732)
context=cleanup_named(root,'CONTEXT',283)
environment=cleanup_named(root,'ENVIRONMENT',138452)
vegetation=cleanup_named(root,'VEGETATION',101225)
street=cleanup_named(vegetation,'STREET_INSTANCES',101231)

# Prove the four connected building volumes and four attached planting domains
# exist before removing any surroundings. Their actual geometry is host KEEP.
[['TOWER',25],['STEPPED_WING',67],['LEFT_UPPER',203],['LEFT_STREET',243]].each do |name,pid|
  cleanup_named(building,name,pid)
end
[['ROOF_INSTANCES',101227],['TERRACE_INSTANCES',101229],
 ['BALCONY_INSTANCES',159038],['LEFT_POCKET_INSTANCES',200004]].each do |name,pid|
  g=cleanup_named(vegetation,name,pid)
  raise "Missing attached planting #{name}" if g.entities.length==0
end

# Physically remove all geometry in the exact approved paths, including
# neighbour windows/green endwall, pavement, curbs, rail bed, wires, street beds
# and street trees. Keep empty target container PIDs stable for scope checks.
# Do not hide geometry or edit any building/attached planting.
clear_owned_contents.call(['CONTEXT'])
clear_owned_contents.call(['ENVIRONMENT'])
clear_owned_contents.call(['VEGETATION','STREET_INSTANCES'])

[context,environment,street].each do |g|
  raise "External geometry remains in #{g.name}" unless g.entities.length==0
end
