# 纯文本生图策略 (Text-Only Generation)

> 适用场景：provider 不支持图生图（如 openapitoken gpt-image-2），
> 仅 `/v1/images/generations` 端点可用。
> 模板图和参考图**不被模型看到**，仅用于 agent 提取外观特征。

---

## 核心原则

模型没有视觉输入。所有信息必须通过文字传递。提示词必须**自包含**——不引用"Image 1/Image 2"等不存在的视觉锚点。

```
模型视角：一段文字 → 一张图
你的任务：把 Shape 约束 + Appearance 描述 + Pose 描述 全部塞进这段文字
```

---

## 提示词模板

```
Job: Vinyl art toy figure — 1.8-head super-deformed collectible designer
     toy, 3D render, product photography style.

SHAPE RULES (absolute, must not violate):
- Head is ~56% of total figure height, body is tiny and compact.
  If the output still looks too tall (head <50%), progressively
  strengthen: R2 → ~60% + "head width equals or exceeds shoulder
  width" + "body is a tiny pedestal for the head"; R3 → 65% +
  "bobblehead proportion" + "head height ALONE equals entire body
  from neck to feet". gpt-image-2 defaults to ~2.5 heads and
  resists extreme SD proportions — concrete metaphors (DOMINATES,
  MASSIVE, bobblehead, pedestal) work better than abstract numbers.
- Head width equals or exceeds shoulder width — classic SD proportion.
  Without this, the model makes the head tall but keeps it narrow,
  resulting in a normal-proportioned figure with a big forehead.
- Limbs are short, thick, cylindrical stubs — no fingers, no joints, no ankles
- Entire body silhouette is rounded with no sharp edges or angles
- Material is smooth glossy vinyl plastic throughout — no fabric texture,
  no fuzz, no matte softness, no skin texture, no metallic reflection
- Face is a completely blank smooth egg-shaped surface — NO eyes,
  NO eyebrows, NO nose, NO mouth, NO blush of any kind
- EXACTLY two arms and EXACTLY two legs — no extra limbs
- Pure white background, no objects, no text, no watermarks, no logos

APPEARANCE:
- Hairstyle: [精确描述：发型结构、发饰位置+颜色+数量、发色]
- Headwear: [精确描述：帽子/头饰的款式、颜色、纹理]
- Clothing: [精确描述：主服装款式、颜色、层次、领口、袖型、裙型]
- Apron/overlay: [精确描述：围裙/外搭的颜色、形状、边缘装饰]
- Footwear: [精确描述：袜子款式+长度+颜色+纹理，鞋子款式+颜色]
- Accessories: [精确描述：手持物、道具的名称+颜色+位置]
- Props: [精确描述：脚边/身边的道具，每个独立描述颜色+位置]

POSE:
- [精确描述：站姿、头部倾斜、左右手各自的动作和位置、腿部姿态]
- 如有不对称手势，用道具位置做空间锚点而非 left/right
  例："The arm on the WHITE bear side is raised near the cheek.
        The arm on the BROWN bear side holds the pillow."

DO NOT CHANGE:
- 发型结构、发饰颜色和数量
- 头饰款式和颜色
- 袜子款式和长度
- 鞋子款式和颜色
- 道具的颜色和位置
- 材质类型（始终为光滑塑料）
- 面部留白状态

CONSTRAINTS:
- NO watermark, NO extra text, NO duplicate or fake logo
- Smooth glossy vinyl plastic material, soft diffuse lighting,
  3D render style, pure white background
- Face remains completely blank — highest priority
```

---

## 各段填写规范

### SHAPE RULES

**头两条（头身比+头宽）可能需要动态调整**。gpt-image-2 默认倾向 ~2.5 头身，对极端 Q 版比例有天然抵抗力。首轮用模板默认值，若 S1 失败则按模板内注释的渐进策略加强。**其余条（四肢/轮廓/材质/面部/肢体数/背景）固定不变**，每轮直接复制。

### APPEARANCE

**首轮**：从参考图提取，逐项精确填写。每个元素独立一行，颜色+款式+位置缺一不可。

```
正确：
- Hairstyle: twin braids in cream-blonde, each tied with a small WHITE bow
  at the end, wispy bangs across forehead, THREE star-shaped hairpins
  in a row along the bangs — all WHITE

错误：
- Hairstyle: twin braids with bows and star clips
  （颜色、数量、位置全缺，模型自由发挥）
```

**后续轮次**：只修改需要调整的项，其余保持不变。

### POSE

**首轮**：从参考图提取，特别注意不对称手势。用道具做空间锚点。

```
正确（空间锚定法）：
- The arm on the WHITE bear side is raised near the cheek in a loose fist,
  as if sleepily rubbing the eye — does NOT touch the pillow
- The arm on the BROWN bear side holds the heart pillow against the chest

错误：
- Left hand raised near face, right hand holding pillow
  （left/right 容易被镜像反转）
```

### DO NOT CHANGE

**每轮必填**。列出本轮**不允许改变**的所有元素。这是防止颜色扩散和意外变更的关键段。

R4 教训：仅写 `LIGHT BLUE dress` 导致蓝色扩散到发饰、抱枕、袜子、鞋子、材质。正确做法是在 `DO NOT CHANGE` 中显式锁定：

```
DO NOT CHANGE:
- Hair bow color (must stay WHITE)
- Star hairpin color and count (must stay WHITE, exactly THREE)
- Heart pillow color (must stay PINK)
- Sock style and length (must stay white over-knee with lace trim)
- Shoe style and color (must stay cream Mary Jane)
- Material (must stay glossy vinyl plastic)
```

---

## 动态调整规则

每轮 `vision_analyze` 检验后，根据失败项调整下一轮 prompt。

### Shape 层失败

| 失败项 | 调整 |
|--------|------|
| S1 头身比偏离 | gpt-image-2 默认倾向 ~2.5 头身（头部 ~40%），对极端 Q 版比例（~1:1，头部 ~50-60%）有天然抵抗力。**渐进式加强**：R1 用 `~56%`，若失败 → R2 用 `~60%` + `head width exceeds shoulder width` + `body is a tiny pedestal`，若仍失败 → R3 用 `65%` + `bobblehead proportion` + `head height ALONE equals entire body from neck to feet`。不要一次跳到极限——模型可能忽略过于夸张的数字。 |
| S2 头部变形 | 加 `Head shape: perfectly oval, slightly wider at top, no elongation` |
| S3 四肢过细/过长 | 加 `Limbs are THICK cylinders — diameter at least 1/3 of torso width` |
| S4 轮廓有锋角 | 加 `All edges rounded with minimum 5mm radius — no corners, no points` |
| S5 材质不对 | 加 `NO fabric weave visible. NO skin pores. NO metallic shine. ONLY smooth plastic.` |
| S6 面部有五官 | 🔴 红线。加 `FACE IS BLANK. Repeat: NO eyes NO eyebrows NO nose NO mouth NO blush. This is the #1 constraint.` |
| S7 多余肢体 | 加 `Count the limbs: 1 left arm, 1 right arm, 1 left leg, 1 right leg. That is ALL.` |

### Pose 层失败

| 失败项 | 调整 |
|--------|------|
| P1 头部朝向错 | 用空间化语言：`Head tilts slightly toward the WHITE bear side` |
| P2 手臂位置错 | 逐手重写，用道具锚点。如镜像反转：改用空间锚定法 |
| P3 腿部错 | `Feet together, toes pointing forward, weight evenly distributed` |
| P4 躯干错 | `Torso faces directly forward, no twist, no lean` |

### Appearance 层失败

| 失败项 | 调整 |
|--------|------|
| A1 发型遗漏/错误 | 逐元素编号：`HAIR ELEMENT 1: twin braids. HAIR ELEMENT 2: WHITE bow at each braid end. HAIR ELEMENT 3: THREE WHITE star clips on bangs.` |
| A2 服装错误 | 分层描述：`Layer 1 (base): peach dress. Layer 2 (overlay): white apron with heart-shaped hem. Layer 3 (detail): small peach bow at collar.` |
| A3 配饰遗漏 | 加 `DO NOT OMIT: [遗漏项]` 并放入 DO NOT CHANGE 段 |
| A4 鞋履错误 | 精确款式：`Cream Mary Jane shoes with single strap across instep, round toe, no bow on shoe` |
| A5 配色偏移 | 在 DO NOT CHANGE 中逐色锁定 |
| A6 附着面错误 | 加 `[元素] is attached to [表面] — NOT on [错误表面]` |

### 颜色扩散（特殊处理）

当仅改一个颜色但多个元素被污染时：

```
本轮 CHANGE ONLY:
- Dress color: peach → light blue

本轮 DO NOT CHANGE（必须逐项列出所有被污染的元素）:
- Hair bows: WHITE
- Star hairpins: WHITE, exactly THREE
- Bonnet: WHITE lace, no colored lining
- Heart pillow: PINK
- Apron: WHITE, no added decorations
- Socks: WHITE over-knee with lace trim
- Shoes: CREAM Mary Jane
- Teddy bears: left WHITE with BROWN bowtie, right BROWN with WHITE bowtie
- Material: glossy vinyl plastic (NOT porcelain/ceramic)
```

---

## 首轮 vs 后续轮次

### 首轮 (R1)

完整填写所有段。APPEARANCE 从参考图提取全部细节。POSE 从参考图提取。DO NOT CHANGE 列出所有元素（首轮没有"不变项"，但列出来作为后续基准）。

### 后续轮次 (R2-R5)

```
1. 读取上一轮 inspection.md，提取所有 ❌ 和 ⚠️ 项
2. 只修改失败项对应的段
3. DO NOT CHANGE 中锁定本轮不允许变的所有元素
4. 其余段保持与上一轮完全一致
```

**关键**：不要重写整个 prompt。只改失败项。gpt-image-2 对 prompt 稳定性敏感——大幅改写可能导致之前已通过的项漂移。

---

## 完整示例：lolita_bonnet_girl R3

```
Job: Vinyl art toy figure — 1.8-head super-deformed collectible designer
     toy, 3D render, product photography style.

SHAPE RULES (absolute, must not violate):
- Head is ~56% of total figure height, body is tiny and compact.
  If the output still looks too tall (head <50%), progressively
  strengthen: R2 → ~60% + "head width equals or exceeds shoulder
  width" + "body is a tiny pedestal for the head"; R3 → 65% +
  "bobblehead proportion" + "head height ALONE equals entire body
  from neck to feet". gpt-image-2 defaults to ~2.5 heads and
  resists extreme SD proportions — concrete metaphors (DOMINATES,
  MASSIVE, bobblehead, pedestal) work better than abstract numbers.
- Head width equals or exceeds shoulder width — classic SD proportion.
  Without this, the model makes the head tall but keeps it narrow,
  resulting in a normal-proportioned figure with a big forehead.
- Limbs are short, thick, cylindrical stubs — no fingers, no joints, no ankles
- Entire body silhouette is rounded with no sharp edges or angles
- Material is smooth glossy vinyl plastic throughout — no fabric texture,
  no fuzz, no matte softness, no skin texture, no metallic reflection
- Face is a completely blank smooth egg-shaped surface — NO eyes,
  NO eyebrows, NO nose, NO mouth, NO blush of any kind
- EXACTLY two arms and EXACTLY two legs — no extra limbs
- Pure white background, no objects, no text, no watermarks, no logos

APPEARANCE:
- Hairstyle: twin braids in cream-blonde, each tied with a small WHITE bow
  at the end, wispy bangs across forehead, THREE WHITE star-shaped hairpins
  in a row along the bangs
- Headwear: WHITE lace bonnet with crisscross lattice pattern and frilled
  edges, two large WHITE bows at ear level on each side
- Clothing: soft peach Lolita maid dress, high collar with small peach bow
  at neck, short puffy sleeves, tiered ruffled skirt with lace trim
- Apron: WHITE frilly apron tied at waist, heart-shaped hem
- Footwear: WHITE over-knee socks with lace trim at top, cream Mary Jane
  shoes with single strap, round toe
- Accessories: heart-shaped pillow in PINK, held against chest
- Props: two teddy bears at feet — WHITE bear with BROWN bowtie on
  viewer's LEFT, BROWN bear with WHITE bowtie on viewer's RIGHT

POSE:
- Standing upright facing forward, feet together
- The arm on the WHITE bear side is raised near the cheek in a loose fist,
  as if sleepily rubbing the eye — does NOT touch the pillow
- The arm on the BROWN bear side holds the PINK heart pillow against chest
- Two arms are ASYMMETRIC — one up near face, one holding pillow

DO NOT CHANGE:
- Hair bow color (WHITE)
- Star hairpin color and count (WHITE, exactly THREE)
- Bonnet color (WHITE lace, no colored lining)
- Heart pillow color (PINK)
- Apron color and style (WHITE, heart-shaped hem, no added decorations)
- Sock style and length (WHITE over-knee with lace trim)
- Shoe style and color (cream Mary Jane)
- Teddy bear colors and bowtie colors
- Material (glossy vinyl plastic)

CONSTRAINTS:
- NO watermark, NO extra text, NO duplicate or fake logo
- Smooth glossy vinyl plastic material, soft diffuse lighting,
  3D render style, pure white background
- Face remains completely blank — highest priority
```

---

## 常见陷阱

| 陷阱 | 原因 | 对策 |
|------|------|------|
| 颜色扩散 | 单个颜色词被理解为全局主题 | DO NOT CHANGE 逐项锁定所有颜色 |
| 左右手镜像反转 | left/right 无视觉锚点 | 空间锚定法：用道具位置做参照 |
| 细节逐轮漂移 | 每轮重写 prompt 引入新偏差 | 只改失败项，其余逐字复制 |
| 星形发夹数量变 | 未显式声明数量 | 写 `exactly THREE` 而非 `star hairpins` |
| 袜子款式变 | 未锁定长度+纹理 | 写 `WHITE over-knee socks with lace trim` 而非 `white socks` |
| 材质变瓷器 | 颜色词触发材质联想 | DO NOT CHANGE 中锁定 `glossy vinyl plastic (NOT porcelain)` |
