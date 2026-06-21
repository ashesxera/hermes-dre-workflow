# Asymmetric Pose + Spatial Anchor Case Study

Date: 2026-06-21
Project: lolita_bonnet_girl

## Problem

Reference image had an asymmetric hand pose:
- Left hand (viewer's left): raised near cheek in loose fist (sleepy eye-rubbing gesture)
- Right hand (viewer's right): holding heart pillow against chest

R1 output: both hands symmetrically holding the pillow. The asymmetric narrative pose was completely lost.

## Root Cause

Agent's natural symmetry bias. When processing "figure holding a heart pillow", the model defaults to both hands on the pillow — the asymmetric detail (one hand near face) is easily overlooked during initial generation and even during inspection.

## Iteration History

| Round | Left Hand | Right Hand | Issue |
|-------|-----------|------------|-------|
| R1 | Holding pillow ❌ | Holding pillow ❌ | Symmetry bias — both hands on pillow |
| R2 | Holding pillow ❌ | Near cheek ❌ | Mirror flip — correct asymmetry but wrong sides |
| R3 | Near cheek ✅ | Holding pillow ✅ | Correct |

## Solution: Spatial Anchor Method

R2 failed because "left hand / right hand" is ambiguous — AI models often mirror-flip these. R3 succeeded by using **existing asymmetric props as spatial anchors**:

```
The arm on the SAME SIDE as the WHITE teddy bear (viewer's LEFT) is raised
near the cheek. The arm on the SAME SIDE as the BROWN teddy bear (viewer's
RIGHT) holds the heart pillow.
```

This works because:
1. Teddy bears are visually prominent and asymmetric (white vs brown)
2. Their positions are stable across generations
3. "Same side as X" is harder to mirror-flip than "left/right"

## Prevention: Mandatory Per-Hand Inspection

Added to dre-workflow SKILL.md Step 1 inspection rules:

After the standard three-layer check, send a separate focused query:
```
Describe what the LEFT hand (viewer's left) is doing in the reference image.
Describe what the RIGHT hand (viewer's right) is doing in the reference image.
Now check the generated image — does each hand match?
```

This forces the vision model to examine each hand individually rather than
making a holistic "arms look about right" judgment.

## Key Takeaway

Asymmetric hand poses carry narrative information (sleepiness, shyness, etc.).
Losing them through symmetry bias is a structural Pose-layer failure, not a
minor detail. Always inspect hands independently.
