# MVP PRD v0.1

## One-line definition

An AI architectural workspace that transforms a brief, site, reference cases, and user intent into an editable early-stage architectural model through AI discussion and professional-software execution.

## Jobs to be done

When I receive a new architecture task, I want to quickly understand the requirements, use relevant precedents, and turn my design intent into an editable first scheme so I can spend more time on design judgment and less time on repetitive production.

## Golden Path

Create Project  
→ Upload Brief / Site / References  
→ AI Analysis  
→ Design Discussion  
→ Confirm Scheme  
→ Send to SketchUp  
→ AI Builds Model  
→ User Reviews  
→ Conversational Model Editing  
→ Approve Model  
→ Output

## P0 capabilities

- persistent project context
- brief understanding
- reference-image understanding
- reference-URL understanding
- user design-intent input
- architectural design discussion
- SketchUp connection
- editable geometry generation
- continuous natural-language editing
- screenshot / model-state feedback
- model save / recover

## Later capabilities

- basic drawings / DXF
- rendering
- analysis diagrams
- presentation layout
- Rhino / Blender connectors

## Explicit non-goals for the current spike

- full website
- authentication
- payments
- Rhino
- Blender
- Revit
- full AutoCAD control
- full rendering pipeline
- automated presentation layout
- full code-compliance checking
- construction documentation
- complex multi-agent architecture

## North-star metric

**Time to First Usable Scheme**

Definition: elapsed time from project input to the first editable scheme the user considers worth continuing.

## Technical-risk priority

1. Stable professional-software control
2. Continuous editing of the same model
3. State consistency between Agent and SketchUp
4. Project-context understanding
5. Recovery after errors
6. Later: drawings / rendering / layout
