# Case Study: Band-Aid Placement — Physical Attachment Surface Misjudgment

## Session
- Date: 2026-06-17
- Project: bunny_buns_girl
- Reference: IMG_1448.PNG (cotton doll style character)

## Problem
The pink band-aid on the reference image was located on the **forehead skin** (above the bangs, near the hairline). However, the DRE pipeline initially described it as "on the top-right area of the head" without specifying the attachment surface. This ambiguity caused `image_gen` to place the band-aid on the **hair** rather than the skin in R1 and R2.

## Root Cause
1. **Step 1 analysis omitted attachment surface judgment**: The analysis dimension for "special facial marks" did not explicitly require determining whether the mark was on skin vs. hair.
2. **Vague prompt language**: "top-right area of the head" is ambiguous — it could mean hair, scalp, or forehead.
3. **Q-version structural limitation**: The Q-version vinyl toy's bangs are a solid plastic fringe covering the forehead. The available "forehead skin" surface is minimal. The model tends to treat decorative marks as "hair accessories" rather than "skin decals."

## Iteration History

| Round | Strategy | Band-aid Location | Tilt Direction | Notes |
|-------|----------|-------------------|----------------|-------|
| R1 | Dual (template + ref) | On hair, top-center-right | Left-high-right-low (wrong) | Completely wrong placement |
| R2 | Dual (template + ref) | On hair, top-center-right | Left-high-right-low (wrong) | Same as R1 |
| R3 | Single (template only) | On hair, above bangs right side | Left-low-right-high (correct) | Improved position but still on hair |
| R4 | Single (template only) | **On forehead skin**, upper-right blank face area | Left-low-right-high (correct) | **Breakthrough** — achieved skin attachment |

## Fix Applied

### Step 1 Analysis Fix
Explicitly report attachment surface:
```
A small pink band-aid sticker is placed diagonally on the
upper-right area of the FOREHEAD, above the bangs,
on the skin surface (NOT on the hair).
```

### Prompt Refinement
Added precise physical location constraints:
```
HEAD: Round head facing directly forward, no tilt.
A small pink band-aid sticker is placed diagonally on the
upper-right area of the FOREHEAD, above the bangs,
on the skin surface (NOT on the hair).
```

Also added in CRITICAL section:
```
The pink band-aid is on the FOREHEAD skin above the bangs,
NOT on the hair.
```

## Key Lessons

1. **Attachment surface is mandatory metadata for all facial marks**. Never describe a mark's location without specifying skin/hair/clothing/prop.
2. **"Head" is too vague — always disambiguate**. Use "forehead skin", "scalp hair", "left cheek skin", etc.
3. **Q-version bangs structure blocks forehead skin access**. To place a mark on forehead skin, you may need to either:
   - Lower the bangs height description to expose more forehead
   - Explicitly state the mark is "on the blank face surface above the bangs"
   - Accept that the model may place it on the hair unless the prompt is extremely precise
4. **Single-reference strategy (template only) helps for precise text-controlled placement**. After R1/R2 established the overall appearance, switching to single-reference in R3/R4 allowed fine-tuning specific details via pure text without reference image interference.

## Other Discoveries in This Session

### Head Tilt (Pose) — Omitted in Step 1
The reference figure had a slight leftward head tilt (dazed-cute expression). Step 1 initially reported "no tilt". This propagated to 3 rounds of prompts with `no tilt`, and the model never produced a tilted head because "100% mirror-symmetric" in the structure description overrode the pose cue.

**Lesson**: Head tilt must be reported in Step 1. If the user wants the tilt preserved, reduce the "symmetric" constraint strength in Step 4.

### Pigeon-Toed Feet (Pose) — Omitted in Step 1
Reference had slightly inward-turned feet. Step 1 reported "feet parallel, toes pointing forward". All 3 rounds generated parallel feet.

**Lesson**: Foot angle is a high-risk omission item. Always report toe direction explicitly.

### Pant Leg Folds (Appearance) — Omitted in Step 1
Reference had baggy pant legs with fabric folds/wrinkles. Step 1 did not mention this. The "smooth plastic surface" material constraint dominated, suppressing fold rendering.

**Lesson**: Clothing volume/fold details must be explicitly described in Step 1 and carefully reconciled with material constraints in Step 4.

### Blush Handling (Appearance)
Reference had natural pink blush on cheeks. User instruction: "blush can be ignored, don't process as stickers." The correct handling is to simply omit all blush/cheek references from the prompt and rely on `NO blush` in CRITICAL constraints.

**Lesson**: When a user says "ignore X", remove it entirely from the prompt rather than trying to convert it to a different representation.

## Methodology Improvements Driven by This Session

### 1. Dual-Reference Prompt Degradation Strategy

**Problem**: In R1/R2 (dual-reference mode), the full `prompt_final.md` (~3000+ chars) was passed along with both template and reference images. This caused:
- Text description conflicting with visual information from the reference image
- Model struggling to reconcile detailed text with direct image input
- Key details (like band-aid location) drifting due to text overriding image

**Solution**: When using dual-reference strategy (R1-R2), the prompt must be **degraded to a minimal version**. Appearance details should be carried by the reference image directly, not by verbose text.

**Minimal dual-reference prompt template**:
```
[Shape hard constraints]
A chibi vinyl art toy figure with extreme deformed proportions:
head ~56% of total height, tiny compact body, short stubby limbs,
large round-toe shoes, 100% mirror-symmetric silhouette.
The body structure is LOCKED and must NOT be altered.

[Minimal appearance directive]
Reference the attached character image for:
- hairstyle, hair accessories, hair color
- clothing style, colors, layering, patterns
- shoes, scarf, props, accessories
- pose, stance, head tilt, foot angle
- face decorations (band-aid location, stickers)

[Hard constraint closing]
Smooth matte vinyl plastic material, soft diffuse lighting,
3D render style, pure white background.
CRITICAL: The face remains completely blank with NO eyes,
NO eyebrows, NO nose, NO mouth, NO blush.
EXACTLY two arms and EXACTLY two legs. No extra limbs.
```

**Prohibition**: Never pass the full `prompt_final.md` in dual-reference rounds. The reference image should carry 80% of the appearance information.

### 2. Multi-Image Injection Inspection Protocol

**Problem**: Previous inspections loaded only the generated image and relied on the main model's text memory of the reference image. This caused:
- Band-aid location errors being missed (R1/R2 inspection falsely reported "all passed")
- Micro-features (head tilt, foot angle) not being detected as deviations
- Inability to do real-time visual cross-comparison

**Solution**: Every inspection round must **inject all three images simultaneously** into the context, and the main model must perform real-time cross-image visual comparison.

**Mandatory inspection procedure**:
```
1. Load all three images into the current conversation context:
   - Generated image: step_5_iterations/r{N}/output.png
   - Template image: assets/default_template.png
   - Reference image: input/reference.png

2. Send instruction to the main model:
   "Please directly compare the three images above (generated,
   template, reference). Check the following checklist item by
   item. Do NOT rely on text memory to describe reference image
   features — you MUST perform real-time cross-image visual
   comparison and judge directly."

3. The main model uses its internal multimodal vision capability
   to perform real-time cross-image comparison and output judgments.
```

**Key principle**: Inspection must be **image-to-image comparison**, not text-to-image comparison. The reference image must be physically present in the context alongside the generated image.

**Same protocol applies to Step 6 evaluation**: All generated images + template + reference must be loaded simultaneously for ranking and scoring.

### 3. Step 6 Scoring Enhancement

**Previous flaw**: Step 6 scoring relied on text reports from previous rounds. If a round's inspection report falsely claimed "all passed", the scoring would blindly accept it.

**Fix**: Step 6 must reload all images and perform fresh visual comparison. The instruction must explicitly state: "Scoring must be based on real-time visual comparison. Do NOT rely on previous round inspection report texts."

### 4. R5 — Dual-Reference with Material Emphasis (v2.1 Template Origin)

**Context**: R1-R4 iterated on band-aid placement and facial mark attachment. By R4, skin attachment was achieved using single-reference strategy. R5 tested whether dual-reference could work **with a minimal prompt + explicit material emphasis layer**.

**R5 Original (pre-revision)**:
```
...100% mirror-symmetric silhouette...
...round-toe enclosed shoes...
Smooth matte vinyl plastic material...
```

**Problems observed**:
- Material was "matte" instead of "glossy" — reference image's soft cotton texture overrode the plastic constraint
- Shoes were forced to round-toe, overriding reference image's sneaker style
- Symmetry was forced to 100% mirror, overriding reference image's natural asymmetry (uneven bangs)

**R5 Revised (v2.1 official template)**:
```
...large shoes... [removed round-toe constraint]
...symmetry/asymmetry... [removed 100% mirror constraint]
The entire figure must have a smooth, glossy plastic texture
— no fabric, no fuzz, no matte softness.
Everything is solid molded vinyl with sharp highlights
and smooth rounded surfaces.
```

**Results of revision**:
- ✅ Material shifted from matte/cotton to **glossy PVC with sharp highlights**
- ✅ Shoes became **reference-matching sneakers** with laces
- ✅ Symmetry became **reference-driven** (uneven bangs preserved)
- ✅ Band-aid remained correctly on forehead skin

**Key lesson**: In dual-reference strategy, the reference image carries appearance information so strongly that any fixed constraint in the prompt (shoe type, symmetry level) will either be overridden or cause conflict. The prompt should only lock **Shape** (proportions, limb count, face blankness) and **material class** (plastic vs. fabric), leaving all stylistic details to the reference image.

**v2.1 skill upgrade driven by this R5 revision**:
- Dual-reference strategy promoted from "default" to **"fixed strategy"** — single-reference is now an extreme fallback only
- R5 revised template became the **official fixed dual-reference prompt template**
- `prompt_final.md` downgraded from "default iteration input" to **"extreme fallback only"**

---

## v2.1 Changelog Summary

| Change | From | To |
|--------|------|-----|
| Image strategy | Default dual, single fallback | **Fixed dual**; single only on timeout/load failure |
| Prompt template | Original dual minimal | **R5 revised** with explicit `smooth, glossy plastic — no fabric, no fuzz` |
| Shoe style | Fixed "round-toe enclosed" | **Reference-driven**, no fixed constraint |
| Symmetry | Fixed "100% mirror-symmetric" | **Reference-driven**, no fixed constraint |
| Step 4 `prompt_final.md` | Default iteration input | **Extreme fallback only** |

## Files
- `~/DRE_Projects/bunny_buns_girl/step_5_iterations/r{1..5}/output.png` — iteration outputs
- `~/DRE_Projects/bunny_buns_girl/step_5_iterations/r{1..5}/prompt.md` — prompt evolution
- `~/DRE_Projects/bunny_buns_girl/step_5_iterations/r{1..5}/inspection_report.md` — inspection records
