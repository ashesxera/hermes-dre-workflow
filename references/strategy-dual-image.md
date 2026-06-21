# 双图生图策略（meshy nano-banana）

> 适用 provider：`meshy`（nano-banana-pro / nano-banana-2 / nano-banana）
> 模式：text-to-image + image-to-image（双参考图）
> 参见：`references/provider-meshy.md`

## 核心事实

meshy 的 nano-banana 系列**支持真正的双图输入**：
- `POST /openapi/v1/text-to-image` — 文生图
- `POST /openapi/v1/image-to-image` — 图生图，接受 `reference_image_urls` 数组
- 插件已声明 `capabilities: {modalities: ["text", "image"], max_reference_images: 4}`

生图时模板图和参考图**都会被模型看到**。提示词只需锁定 Shape 约束和材质，外观由参考图承担。

## 提示词模板

双图条件下，提示词极简——外观信息由参考图传递，文字只负责 Shape 锁定。

```
Job: Vinyl art toy figure — transfer character identity from reference
     image onto a locked body template, producing a collectible designer
     toy in 3D render style.

Image 1 (template): Body structure authority — a 1.8-head chibi vinyl
     toy base with blank face, stubby limbs, and glossy plastic finish.
     This image defines the SHAPE only. Its proportions, head size,
     limb thickness, and body silhouette are LOCKED and must NOT change.

Image 2 (reference): Character identity source — provides hairstyle,
     hair accessories, hair color, clothing style/colors/layering,
     shoes, props, accessories, pose, stance, head tilt, foot angle,
     and symmetry/asymmetry. This image defines APPEARANCE and POSE only.

Preserve list:
- Image 1's body proportions exactly (head ~56% of total height,
  tiny compact body, short stubby limbs, large shoes)
- Image 1's blank face — completely smooth egg-shaped surface with
  NO eyes, NO eyebrows, NO nose, NO mouth, NO blush
- Image 1's glossy plastic material — smooth, solid molded vinyl
  with sharp highlights and rounded surfaces
- Image 1's limb count — EXACTLY two arms and EXACTLY two legs
- Pure white background with no objects, no floating props,
  no decorative elements suspended in the air

Change only:
- Replace Image 1's hairstyle with Image 2's hairstyle, hair
  accessories, and hair color (solid vinyl-like masses, rounded
  blunt tips, no wispy strands)
- Replace Image 1's clothing with Image 2's clothing style,
  colors, layering, and patterns (all rendered as glossy plastic)
- Replace Image 1's shoes with Image 2's shoe style and color
- Transfer Image 2's props and accessories
- Transfer Image 2's pose: stance, head tilt, arm positions,
  foot angle, symmetry or asymmetry

Do NOT add:
- Facial features of any kind (eyes, eyebrows, nose, mouth, blush)
- Extra limbs beyond two arms and two legs
- Fabric texture, fuzz, matte softness, or any non-plastic material
- Background objects, floating props, text, watermarks, logos
- Any elements not present in either Image 1 or Image 2

Constraints:
- Image numbering matches input order (Image 1 = template, Image 2 = reference)
- Face remains completely blank — this is the highest priority constraint
- NO watermark, NO extra text, NO duplicate or fake logo
- Smooth glossy vinyl plastic material, soft diffuse lighting,
  3D render style, pure white background
```

## 与纯文本模板的关键差异

| 维度 | 纯文本模板 | 双图模板 |
|------|-----------|---------|
| Image 编号 | 去掉（噪音） | **保留**（模型能看到图） |
| Appearance 描述 | 逐项精确文字 | **省略**（参考图承担） |
| Preserve list | 改为 `SHAPE RULES` | 保留 `Preserve list`（有锚点） |
| 提示词长度 | 长（自包含） | **短**（极简） |
| 适用 provider | gpt-image-2 | meshy nano-banana |

## 已知陷阱

### 材质偏移

参考图的布料/柔绒质感可能覆盖模板的塑料感。

**对策**：`Preserve list` 第三条显式锁定材质为 glossy plastic。

### 五官泄漏

参考图的五官可能泄漏到生成图。

**对策**：`Preserve list` 第二条 + `Do NOT add` 第一条双重锁定。

### 发型被模板抑制

模板的原始发型可能抑制参考图发型的替换。

**对策**：`Change only` 第一条写 "COMPLETELY different from the template's original hairstyle — replace it entirely"。
