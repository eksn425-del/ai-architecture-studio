# Adopted runtime guidance (MIT excerpts)

SketchUp API Skill: validate geometry. The host already owns the Undo transaction; do not nest it.

SketchUp raises `TypeError: Zero length vector` and similar errors when you pass degenerate geometry. Guard every geometric operation:

```ruby
# ✅ Safe face normal
def safe_normal(face)
  return nil unless face.is_a?(Sketchup::Face)
  normal = face.normal
  return nil if normal.length < 0.001
  normal
end
```

SketchUp Agent Harness: project-memory guardrails. Our parameter card and persistent Ruby retain project facts; no mandatory design_model schema.

- Do not treat dynamic skills as canonical truth.
- Do not rely on dynamic-skill prose alone for source fidelity when a
  machine-checkable constraint can be recorded.
- Do not use dynamic skills to hide schema or MCP tool gaps.
- Do not use dynamic skills or hand-authored constraints to fake automatic
  source recognition during validation.
