# frozen_string_literal: true
# Adapted from Stultus bfb0c012c6a5c669dadb2725aa76980e8481e859 scene.rb.
# Copyright 2026 B&A community; Apache-2.0, see LICENSE and AUTHORS.
# Namespace changed; only bounds/unit functions retained. No active-model access.
module KStudioStultusBounds
  module_function
      def bounds_mm(b)
        return nil unless b && b.valid?
        # Размер считаем из углов: у BoundingBox height — это Y, а depth — Z,
        # и [width, depth, height] давал бы [X, Z, Y].
        {
          min:  pt_mm(b.min),
          max:  pt_mm(b.max),
          size: [mm(b.max.x - b.min.x), mm(b.max.y - b.min.y), mm(b.max.z - b.min.z)]
        }
      end

      def pt_mm(p)
        [mm(p.x), mm(p.y), mm(p.z)]
      end

      def mm(inches)
        (inches.to_f * 25.4).round(1)
      end
end
