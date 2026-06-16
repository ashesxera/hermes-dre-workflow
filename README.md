# Hermes DRE Workflow v2.0

Doll Reconstruction Engineer (DRE) — Hermes Agent skill that converts reference character images into standardized doll figures.

## Overview

DRE is a strict structured workflow following **Shape > Pose > Appearance** priority:

- **Shape (Absolute Authority)**: Head size, head-to-body ratio, limb thickness, overall silhouette — never modified
- **Pose (Reference Authority)**: Joint rotation, limb positioning, torso orientation
- **Appearance (Reference Authority)**: Hairstyle, clothing, accessories, color scheme

## What's New in v2.0

- **6-Step Pipeline**: Reduced from 8 stages for leaner execution
- **Internal Vision**: All visual analysis uses the main model's built-in multimodal capability — no external `vision_analyze` tool calls
- **Auto-Validation**: Step 2 validation runs automatically without human intervention
- **Structure-First Generation**: Pose and appearance fused into a single prompt, no separate "posed base" stage
- **Shape Weight 45%**: Increased from 40% to further emphasize structural fidelity

## Installation

```bash
# Install into Hermes skills directory
cp -r dre-workflow ~/.hermes/skills/doll-reconstruction/
hermes skills list  # confirm loaded
```

## Usage

In a Hermes session, provide a reference character image and say "跑 DRE 流程" or "重建这个人偶".

The workflow automatically executes 6 steps:

```
Step 1 (Reference Analysis)
  → Step 2 (Prompt Enhancement + Auto-Validation)
  → Step 3 (Template Analysis)
  → Step 4 (Prompt Fusion)
  → Step 5 (Iterative Generation, ≤5 rounds)
  → Step 6 (Scoring & Ranking)
```

## File Structure

```
dre-workflow/
├── SKILL.md                                    # Skill definition + full workflow (v2.0)
├── README.md                                   # This file
├── assets/
│   └── default_template.png                    # Standard doll template (~1.8 head-body ratio)
└── references/
    ├── gothic-lolita-starry-night-case-study.md  # Case 1
    ├── bunny-chibi-case-study.md                 # Case 2
    ├── toddler-fish-case-study.md                # Case 3
    └── lolita-bonnet-girl-case-study.md          # Case 4
```

## Dependencies

- Hermes Agent
- `image_gen` tool (the only external API call — up to 5 times per run)
- Main model with built-in vision capability (for all visual analysis)

## License

MIT
