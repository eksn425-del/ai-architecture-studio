# Architecture Overview

## Product architecture hypothesis

Long term:

Web Workspace  
→ Agent / Orchestrator  
→ Local Design Connector  
→ SketchUp / Rhino / Blender / CAD

The first Technical Spike validates only the SketchUp portion.

## Current spike loop

Project Context  
→ Agent  
→ SketchUp Connector  
→ SketchUp Ruby API  
→ Editable Geometry  
→ Model Query + Screenshot  
→ Agent Review  
→ User Instruction  
→ Modify Existing Geometry

## Responsibility split

### AI / Agent

Responsible for:
- understanding project context
- interpreting design intent
- deciding which tool operation to call
- evaluating whether a requested design change was achieved
- proposing or executing recoverable corrections

### Deterministic connector / software layer

Responsible for:
- units
- coordinates
- stable object IDs
- entity references
- dimensions
- file state
- save / version / undo
- deterministic validation
- API error handling

## Core engineering principle

**Explore Loose, Produce Strict.**

AI handles uncertain interpretation.  
Software enforces deterministic correctness.

## Stable object identity

Continuous editing requires major building objects to have stable identities instead of being located only by screen position or free-form descriptions.

Example conceptual IDs:

- BUILDING_SPORTS
- BUILDING_LIBRARY
- BUILDING_CULTURE
- BUILDING_RECEPTION
- PUBLIC_STREET
- COURTYARD_01

The exact schema is intentionally deferred until the spike validates the minimum needed implementation.

## Security / privacy

This public repository stores product code and sanitized test fixtures only.

Real graduation-design assets and licensed reference materials remain local/private.
