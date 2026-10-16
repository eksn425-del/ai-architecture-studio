# Final owner-authorized site-only addition. All coordinates in millimetres.
def sc_group(es,name)
  g=es.add_group;g.name=name;g.set_attribute('KStudio','semantic_id',name);g
end
def sc_face(es,pts,mat)
  f=es.add_face(pts.map{|p|p.map(&:mm)});raise 'Site face failed' unless f
  f.material=mat;f.back_material=mat;f
end
def sc_slab(es,name,x1,x2,y1,y2,z1,z2,mat)
  g=sc_group(es,name)
  f=sc_face(g.entities,[[x1,y1,z1],[x2,y1,z1],[x2,y2,z1],[x1,y2,z1]],mat)
  f.reverse! if f.normal.z<0;f.pushpull((z2-z1).mm);g.material=mat;g
end
def sc_rise(es,name,pts,mat)
  g=sc_group(es,name);sc_face(g.entities,pts,mat)
  pts.each_with_index do |p,i|
    q=pts[(i+1)%pts.length]
    sc_face(g.entities,[p,[p[0],p[1],-350],[q[0],q[1],-350],q],mat)
  end
  sc_face(g.entities,pts.reverse.map{|p|[p[0],p[1],-350]},mat);g
end
site=root.entities.grep(Sketchup::Group).find{|g|g.name=='SITE_GROUND'}
raise 'Verified site missing' unless site && site.persistent_id==76256
raise 'Site transformed' unless site.transformation.identity?
raise 'Site leaf already present' if site.entities.any?{|g|g.respond_to?(:name)&&g.name=='SIMPLE_SURROUNDINGS'}
leaf=sc_group(site.entities,'SIMPLE_SURROUNDINGS')
leaf.set_attribute('KStudio','provenance','Owner requested simple context; source1/3/5 greenery principle, exact layout inferred')
paving=model.materials.add('SC_Final_Pale_Paving');paving.color=Sketchup::Color.new(218,213,200)
grass=model.materials.add('SC_Final_Low_Green');grass.color=Sketchup::Color.new(134,157,108)
bark=model.materials.add('SC_Final_Tree_Trunk');bark.color=Sketchup::Color.new(142,127,108)
foliage=model.materials.add('SC_Final_Tree_Crown');foliage.color=Sketchup::Color.new(154,177,129)
paths=sc_group(leaf.entities,'ENTRY_WALKS')
sc_slab(paths.entities,'SOUTH_MAIN_WALK',-11000,57500,-8500,-6500,-350,-280,paving)
sc_slab(paths.entities,'WEST_ENTRY_LINK',-5500,-4200,-6500,18000,-350,-280,paving)
sc_slab(paths.entities,'EAST_STAIR_LINK',51000,54000,-6500,-2600,-350,-280,paving)
# Flush connection to existing zero-level ramp landing. No edit to landing.
sc_rise(paths.entities,'WEST_RAMP_APPROACH',[[-8500,-8500,-280],[-6300,-8500,-280],[-6300,-6200,0],[-8500,-6200,0]],paving)
[5500,15500].each_with_index do |y,i|
  sc_rise(paths.entities,"WEST_DOOR_APPROACH_#{i+1}",[[-4200,y,-280],[0,y,0],[0,y+1500,0],[-4200,y+1500,-280]],paving)
end
beds=sc_group(leaf.entities,'LOW_GREEN_BEDS')
bed_specs=[[14000,-5200,4500,900],[37000,-5200,4500,900],[13000,29200,6500,2100],[39000,29200,6500,2100]]
bed_specs.each_with_index do |(cx,cy,rx,ry),i|
  g=sc_group(beds.entities,"GREEN_BED_#{i+1}")
  pts=24.times.map{|j|a=2*Math::PI*j/24;[cx+rx*Math.cos(a),cy+ry*Math.sin(a),-280]}
  f=sc_face(g.entities,pts,grass);f.reverse! if f.normal.z<0;f.pushpull(45.mm);g.material=grass
end
trees=sc_group(leaf.entities,'SCHEMATIC_TREES')
[[14000,-5200,1200],[37000,-5200,1200],[13000,29200,1800],[39000,29200,1800]].each_with_index do |(cx,cy,r),i|
  tree=sc_group(trees.entities,"TREE_#{i+1}")
  trunk=sc_group(tree.entities,"TREE_#{i+1}_TRUNK")
  edges=trunk.entities.add_circle([cx.mm,cy.mm,-235.mm],[0,0,1],110.mm,8)
  f=trunk.entities.add_face(edges);f.reverse! if f.normal.z<0;f.pushpull(2900.mm);trunk.material=bark
  crown=sc_group(tree.entities,"TREE_#{i+1}_CROWN")
  rings=[[2200,0.35],[2900,0.85],[4200,1.0],[5400,0.55],[5900,0.06]].map do |z,scale|
    8.times.map{|j|a=2*Math::PI*j/8;[cx+r*scale*Math.cos(a),cy+r*scale*Math.sin(a),z]}
  end
  (0...4).each do |k|
    8.times do |j|
      n=(j+1)%8;sc_face(crown.entities,[rings[k][j],rings[k][n],rings[k+1][n]],foliage)
      sc_face(crown.entities,[rings[k][j],rings[k+1][n],rings[k+1][j]],foliage)
    end
  end
  sc_face(crown.entities,rings.first.reverse,foliage);sc_face(crown.entities,rings.last,foliage)
end
raise 'Site child inventory mismatch' unless leaf.entities.grep(Sketchup::Group).size==3
puts 'SITE_CLOSEOUT: 6 path pieces, 4 green beds, 4 schematic trees; old ground and building untouched.'
