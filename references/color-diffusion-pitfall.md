# Color Diffusion Pitfall — gpt-image-2

> Discovered 2026-06-21 during DRE lolita_bonnet_girl R4 generation.
> Provider: openapitoken gpt-image-2 (text-only).

## The Bug

Prompt changed ONLY the dress color from `soft peach` to `LIGHT BLUE`.
All other text was identical to R3.

## What Happened

gpt-image-2 interpreted "LIGHT BLUE dress" as "make a blue-themed version"
and changed 10+ elements beyond the dress:

| Element | R3 (expected) | R4 (actual) | Correct? |
|---------|--------------|-------------|----------|
| Dress color | peach | light blue | ✅ |
| Braid-end bows | WHITE | light blue | ❌ |
| Star hairpins | 3 WHITE on forehead | 1 blue+white on side | ❌ |
| Head bows | pink+white | all white | ❌ |
| Bonnet | white lace | white+blue lining | ❌ |
| Heart pillow | PINK | light blue+added bow | ❌ |
| Apron | plain white | white+added blue bow | ❌ |
| Socks | white over-knee lace | white ankle ribbed | ❌ |
| Shoes | plain cream Mary Jane | cream Mary Jane+added bow | ❌ |
| Material | PVC matte | porcelain/ceramic glaze | ❌ |
| Teddy bears | correct | correct | ✅ |
| Left hand pose | correct | correct | ✅ |

## Root Cause

gpt-image-2 has extremely strong **color semantic diffusion**. A single
color word in one element's description is interpreted as a global theme
directive. The model doesn't understand "change ONLY the dress color" —
it understands "the user wants a blue version."

## Fix

Use the `DO NOT CHANGE` section to explicitly lock every element that
should stay the same. Be specific about colors, counts, styles, and materials:

```
DO NOT CHANGE:
- Hair bow color (must stay WHITE)
- Star hairpin color and count (must stay WHITE, exactly THREE)
- Bonnet color (WHITE lace, no colored lining)
- Heart pillow color (must stay PINK)
- Apron color and style (WHITE, heart-shaped hem, no added decorations)
- Sock style and length (WHITE over-knee with lace trim)
- Shoe style and color (cream Mary Jane, no added bow)
- Teddy bear colors and bowtie colors
- Material (glossy vinyl plastic — NOT porcelain/ceramic)
```

## Prevention

When changing ANY single element in a follow-up round:
1. List the change in `CHANGE ONLY`
2. List EVERY other element in `DO NOT CHANGE` with explicit color/style/material
3. Never assume the model will keep unchanged elements stable
