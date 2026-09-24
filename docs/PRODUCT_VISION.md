# Product Vision

## Product

**AI Architecture Studio**

A lightweight AI-native workspace for architecture students and junior designers.

## Target users

Initial MVP:
- architecture students
- 0–3 year junior architectural designers

## Core user problem

Two parts of architectural design consume disproportionate effort:

1. **Concept formation is difficult.**  
   Users may already have a brief, site, reference case, and personal preferences, but turning those inputs into a coherent scheme requires substantial reasoning and iteration.

2. **Modeling and drawing are time-consuming.**  
   Once a direction is chosen, producing and repeatedly modifying editable models and drawings can consume weeks of repetitive work.

## Core value proposition

**Help users think through the design, then help them build it.**

The product should compress the path from:

Brief + Site + Reference Cases + User Intent

to:

A usable, editable scheme that the user wants to continue developing.

## Long-term workflow

Brief + Site + Reference Cases + User Intent  
→ Design Copilot  
→ Confirmed Scheme  
→ Design Executor  
→ Editable Model  
→ Drawings  
→ Render  
→ Diagram  
→ Layout

## Product principles

- **Project, not chat, is the core object.**
- AI handles ambiguity, reasoning, precedent interpretation, and design discussion.
- Deterministic software handles units, coordinates, stable IDs, geometry state, files, versions, saving, and validation.
- Major design decisions remain human-approved.
- Generated models must remain editable and recoverable.
- The product should support continuous modification of the same project, not repeatedly regenerate from scratch.
- Early versions do not claim full building-code compliance, BIM completeness, or automatic construction documentation.

## Important differentiation hypothesis

The product should move beyond image-only architectural AI.

A key differentiator is:

**Reference → Scheme → Editable Model**

The system should help translate precedent logic into a new project rather than simply imitate images.
