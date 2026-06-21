# Color Diffusion Pitfall (gpt-image-2)

> Discovered 2026-06-21 during DRE R4 generation.
> Changing a single color word in the prompt caused gpt-image-2 to
> reinterpret the entire design as a new color theme.

## The Incident

R3 prompt: `soft peach Lolita maid dress` → correct result (peach dress, white accessories)

R4 prompt: changed ONLY `soft peach` → `LIGHT BLUE` in the dress description.
Everything else in the prompt was identical.

## What Actually Happened

| Element | R3 (peach) | R4 (light blue) | Expected? |
|---------|-----------|-----------------|-----------|
| Dress color | Peach ✅ | Light blue ✅ | ✅ Yes |
| Braid-end bows | White | **Light blue** | ❌ Should stay white |
| Star hairpins | 3 white, forehead row | **1 blue+white, right side** | ❌ Count, position, color all changed |
| Head bows | Pink+white | **All white** | ❌ Pink lost |
| Bonnet | White lace | White lace + **blue lining** | ❌ Added blue |
| Heart pillow | Pink | Light blue + **added blue bow** | ❌ Color + extra decoration |
| Apron | White plain | White + **added blue bow** | ❌ Extra decoration |
| Socks | White over-knee lace | **Ankle-length ribbed** | ❌ Style completely changed |
| Shoes | Cream Mary Jane | Mary Jane + **added bow** | ❌ Extra decoration |
| Material | PVC matte | **Porcelain glaze** | ❌ Material changed |

## Root Cause

gpt-image-2 interprets color words as **theme directives**, not isolated
property changes. `LIGHT BLUE dress` is read as "make a blue-themed version"
rather than "change only the dress color to blue."

## Fix: DO NOT CHANGE Section

The solution is to explicitly lock every element that should NOT change:

```
DO NOT CHANGE:
- Hair bow color (must stay WHITE)
- Star hairpin color and count (must stay WHITE, exactly THREE, on forehead)
- Head bow colors (must stay PINK and WHITE)
- Bonnet (must stay WHITE lace, no colored lining)
- Heart pillow color (must stay PINK, no added decorations)
- Apron (must stay WHITE, no added bows)
- Sock style and length (must stay WHITE over-knee with lace trim)
- Shoe style and color (must stay cream Mary Jane, no added bows)
- Material (must stay glossy vinyl plastic, NOT porcelain)
```

This is now encoded in `references/strategy-text-only.md` as a mandatory
section in every prompt.
