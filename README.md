# AI Architecture Studio

AI-native architecture workflow for design reasoning, SketchUp execution, and editable project generation.

## Product direction

The long-term workflow is:

Brief + Site + Reference Cases + User Intent  
→ AI Design Discussion  
→ Confirmed Scheme  
→ Editable 3D Model  
→ Drawings  
→ Rendering  
→ Presentation

The core product idea is not "AI image generation". The primary artifact should remain a real, editable architectural project.

## Current milestone

**SketchUp Agent Technical Spike**

Before building the full web product, this repository first validates the highest-risk technical loop:

Project Context  
→ Agent  
→ SketchUp Connector  
→ Editable Model  
→ Model State / Screenshot  
→ AI Review  
→ Continuous Modification

The current task is defined in [docs/CURRENT_TASK.md](docs/CURRENT_TASK.md).

## Collaboration model

- **Product planning / architecture / review:** ChatGPT GPT-5.6 Sol High
- **Implementation:** Codex GPT-6 Luna Max or another execution agent
- **GitHub:** single source of truth

Execution agents should read [AGENTS.md](AGENTS.md) and [docs/CURRENT_TASK.md](docs/CURRENT_TASK.md) before doing work, then update [docs/HANDOFF.md](docs/HANDOFF.md) when finished.

## Key docs

- [Product Vision](docs/PRODUCT_VISION.md)
- [MVP PRD v0.1](docs/MVP_PRD_v0.1.md)
- [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md)
- [Technical Spike v0.1](docs/TECHNICAL_SPIKE_v0.1.md)
- [Product & Architecture Decisions](docs/DECISIONS.md)
- [Current Task](docs/CURRENT_TASK.md)
- [Handoff](docs/HANDOFF.md)

## Repository safety

This is a public repository. Do **not** commit:

- API keys, tokens, credentials, or secrets
- private graduation-design files
- copyrighted reference packages that cannot be redistributed
- proprietary company data
- machine-specific private paths
- private SketchUp / DWG benchmark files

Use sanitized fixtures or local-only benchmark paths instead.
