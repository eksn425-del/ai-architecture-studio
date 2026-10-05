# frozen_string_literal: true
# Adapted from SAIE eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f, ops/wall.rb.
# Copyright (c) 2026 Ahsan Mehmood; MIT, see LICENSE.
# Only geometry helpers retained; no global model, lifecycle, or bridge code.
module KStudioSAIE
  MM_TO_IN = 1.0 / 25.4
      def self._read_centerline(params)
        if params["centerline"]
          cl = params["centerline"]
          x1 = cl[0][0].to_f * MM_TO_IN
          y1 = cl[0][1].to_f * MM_TO_IN
          x2 = cl[1][0].to_f * MM_TO_IN
          y2 = cl[1][1].to_f * MM_TO_IN
          thick = params["thickness_mm"].to_f * MM_TO_IN
          height = params["height_mm"].to_f * MM_TO_IN
        else
          x1 = params["start_x"].to_f
          y1 = params["start_y"].to_f
          x2 = params["end_x"].to_f
          y2 = params["end_y"].to_f
          thick = params["thickness"].to_f
          height = params["height"].to_f
        end

        dx = x2 - x1
        dy = y2 - y1
        len = Math.sqrt(dx*dx + dy*dy)

        {
          x1: x1, y1: y1, x2: x2, y2: y2,
          dx: dx, dy: dy,
          len: len,
          thick: thick, height: height
        }
      end

      # Build the 4 footprint corners + extrude.
      def self._build_wall_group(ents, c)
        # Perpendicular offset (proven v1 math): rotate (dx,dy)/len by +90deg.
        len = c[:len]
        px = (-c[:dy] / len) * (c[:thick] / 2.0)
        py = ( c[:dx] / len) * (c[:thick] / 2.0)

        p1 = Geom::Point3d.new(c[:x1] + px, c[:y1] + py, 0)
        p2 = Geom::Point3d.new(c[:x2] + px, c[:y2] + py, 0)
        p3 = Geom::Point3d.new(c[:x2] - px, c[:y2] - py, 0)
        p4 = Geom::Point3d.new(c[:x1] - px, c[:y1] - py, 0)

        group = ents.add_group
        face = group.entities.add_face(p1, p2, p3, p4)
        face.reverse! if face.normal.z < 0
        face.pushpull(c[:height])
        group
      end

end
