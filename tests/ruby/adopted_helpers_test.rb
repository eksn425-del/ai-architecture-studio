# Cloud arithmetic/ownership test doubles, NOT the SketchUp geometry engine.
raise 'Run only in system Ruby, never inside SketchUp: this suite defines API doubles' if defined?(Sketchup)
require_relative '../../app/adopted_sketchup_helpers'

def check(value, message)
  raise message unless value
end

def rejected
  begin
    yield
  rescue ArgumentError, RuntimeError
    return
  end
  raise 'Expected invalid wall specification to be rejected'
end

module Geom
  Point3d = Struct.new(:x, :y, :z)
  module Transformation
    def self.translation(values); values; end
  end
end
Bounds = Struct.new(:min, :max) do
  def valid?; !min.nil? && !max.nil?; end
end
Face = Struct.new(:normal, :depth) do
  def reverse!; normal.z = -normal.z; end
  def pushpull(value); self.depth = value; end
end
class Entities
  include Enumerable
  attr_reader :list, :points, :face
  def initialize; @list=[]; end
  def each(&block); @list.each(&block); end
  def to_a; @list.dup; end
  def add_group
    group=Sketchup::Group.new; @list << group; group
  end
  def add_face(*points)
    @points=points;@face=Face.new(Geom::Point3d.new(0,0,-1),nil)
  end
end
module Sketchup
  class Group
    attr_accessor :name, :bounds
    attr_reader :entities, :translation
    def initialize
      @entities=Entities.new;@name='';@bounds=Bounds.new(nil,nil)
    end
    def persistent_id; object_id; end
    def locked?; false; end
    def transform!(value); @translation=value; end
  end
  class ComponentInstance < Group; end
end
root=Sketchup::Group.new
params={'name'=>'rear-wall','centerline'=>[[10000,8000],[0,8000]],'thickness_mm'=>200,'height_mm'=>3200,'elevation_mm'=>3200}
wall=KStudioProfessionalHelpers.wall(root,params)
check(root.entities.to_a==[wall], 'Only owned-root entities may receive geometry')
xs=wall.entities.points.map { |p| p.x*25.4 };ys=wall.entities.points.map { |p| p.y*25.4 }
check((xs.min-0).abs<0.001 && (xs.max-10000).abs<0.001, 'Wall x must retain metric origin')
check((ys.min-7900).abs<0.001 && (ys.max-8100).abs<0.001, 'Rear wall must stay at y=8m, not 8 inches')
check((wall.entities.face.depth*25.4-3200).abs<0.001, 'Height conversion incorrect')
check(wall.entities.face.normal.z>0, 'Extrusion normal must point up')
check((wall.translation[2]*25.4-3200).abs<0.001, 'Elevation conversion incorrect')
rejected { KStudioProfessionalHelpers.wall(root,params) }
rejected { KStudioProfessionalHelpers.wall(root,params.merge('name'=>'bad','height_mm'=>-1)) }
rejected { KStudioProfessionalHelpers.wall(root,params.merge('name'=>'bad','centerline'=>[[0,0],[0,0]])) }
rejected { KStudioProfessionalHelpers.wall(root,params.merge('name'=>'bad','centerline'=>[[Float::INFINITY,0],[0,0]])) }
wall.bounds=Bounds.new(Geom::Point3d.new(0,10,20),Geom::Point3d.new(40,60,80))
snap=KStudioProfessionalHelpers.owned_snapshot(root)
check(snap[:objects][0][:bounds_mm][:size]==[1016.0,1270.0,1524.0], 'Stultus XYZ must not swap SketchUp Y/Z bounding-box dimensions')
check(snap[:objects][0][:persistent_id]==wall.persistent_id, 'Readback must include actual persistent identity')
check(snap[:bounds_units]=='mm' && snap[:api_units]=='inch', 'Readback units must be explicit')
puts 'PASS: SAIE wall math/owned target, validation, Stultus XYZ bounds and identity (test doubles only)'
