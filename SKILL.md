---
name: dre-workflow
description: "Use when user says 搓个娃, 搓娃, 重建人偶, 跑DRE, or DRE workflow with an image. Doll Reconstruction Engineer — convert reference character images into standardized doll figures. v2.3: gpt-image-2 optimized prompt template with Job+Preserve/Change/Do NOT add+Constraints structure."
version: 2.3.0
platforms: [macos, linux]
repository: https://github.com/ashesxera/hermes-dre-workflow
---

# DRE 工作执行方案 v2.2

> 基于 Doll Reconstruction Workflow 制定
> 全局优先级：**Shape > Pose > Appearance**
> 视觉能力：主模型内部多模态视觉（图片加载至上下文直接分析）

---

## 核心变更（v2.2）

| 维度 | v2.1 | v2.2 |
|------|------|------|
| 流程阶段 | 6 Steps（含 Step 1-4 前置分析） | **2 Steps**：迭代生成 + 最终评比 |
| 前置分析 | Step 1-4 产出中间文件 | **全部移除**，分析内化到主模型视觉 |
| 目录结构 | 嵌套多层（step_1/ ~ step_6/） | **扁平化**（r1/ ~ r5/ + ranking.md） |
| 提示词 | Step 4 产出完整版备用 | **仅保留固定双图模板**，无中间文件 |

---

## 历史核心变更

### v2.1

| 维度 | v2.0 | v2.1 |
|------|------|------|
| 参考图策略 | 默认双图，可单图回退 | **固定双图策略** |
| 提示词模板 | 固定双图模板 | **R5 修订版正式模板**，显式加入材质强调层 |
| 鞋型/对称性 | 模板说明中已放宽 | **彻底移除固定约束**，全部交由参考图决定 |

### v2.0

| 维度 | v1.x | v2.0 |
|------|------|------|
| 阶段数 | 8 Stages | 6 Steps |
| 视觉工具 | `vision_analyze` 外部调用 | 主模型内部视觉能力 |
| 资产提取 | Stage 5 并行轨道 | **移除**（专注生产） |
| Step 2 验证 | 人工检查 checklist | **自动验证** |
| 评分权重 | Shape 40% | **Shape 45%** |

---

## 项目目录结构

```
~/DRE_Projects/{project_name}/
├── input/
│   └── reference.png              # 原始参考图（用户提供）
│
├── r1/
│   ├── output.png                 # R1 生成图
│   ├── prompt.md                  # R1 使用的提示词
│   └── inspection.md              # R1 视觉检验报告
├── r2/
│   ├── output.png
│   ├── prompt.md
│   └── inspection.md
├── r3/
├── r4/
├── r5/
│
├── ranking.md                     # 排名表
└── evaluation.md                  # 详细评估报告
```

### 默认模板

技能内置标准人偶模板：

```
~/.hermes/skills/doll-reconstruction/dre-workflow/assets/default_template.png
```

- ~1.8 头身 Q 版潮玩素体
- 暖米白 + 淡粉配色
- 纯白背景
- 100% 镜像对称
- 面部完全留白（无五官）

**用户无需提供模板**。如用户提供了自定义模板（`input/template.png`），则优先使用。

---

## 全局约束

```
优先级（高→低）：Shape > Pose > Appearance

Shape（人偶底座权威 — 绝对优先）：
  - 头部形状/大小/宽高比
  - 面部轮廓（必须完全留白）
  - 身体比例（头身比 ~1.8）
  - 躯干宽度
  - 四肢粗细
  - 脚部尺寸
  - 整体轮廓
  - 材质表现（哑光软胶 PVC）
  - 🔴 面部留白：绝对禁止五官。无眼睛、无眉毛、无鼻子、无嘴巴、无腮红。
    任何五官痕迹均视为 Shape 层违规，直接判定不合格。
  - 🔴 肢体数量：EXACTLY 两条手臂 + EXACTLY 两条腿。无额外肢体。

Pose（参考图权威）：
  - 关节旋转
  - 四肢位置
  - 躯干朝向
  - 重心分布

Appearance（参考图权威）：
  - 发型（塑料块状，无镂空）
  - 服装（颜色+形状，材质统一为塑料）
  - 鞋履
  - 配饰/道具
  - 色彩方案
```

---

## 视觉能力调用规范

**优先使用主模型内部多模态视觉能力。当主模型不具备多模态能力时，回退到 `vision_analyze` 工具。**

### 模式 A：主模型内部视觉（优先）

当主模型支持多模态（如 GPT-5、Claude Sonnet 等）时：

```
1. 将目标图片加载到当前对话上下文（作为附件/引用）
2. 向主模型发送结构化视觉分析指令
3. 主模型利用内部视觉能力直接输出分析结果
4. 将结果写入对应 markdown 文件归档
```

### 模式 B：vision_analyze 回退（当主模型非多模态时）

当主模型不支持直接看图（如 DeepSeek、纯文本模型等）时，**必须**使用 `vision_analyze`：

```
1. 调用 vision_analyze(image_url=生成图, question=检验指令)
2. 调用 vision_analyze(image_url=模板图, question=模板特征描述指令)
3. 调用 vision_analyze(image_url=参考图, question=参考特征描述指令)
4. 最后调用 vision_analyze(image_url=生成图, question=三图对比检验指令)
   — 在 question 中嵌入前两步获取的模板图和参考图特征描述
5. 将 vision_analyze 返回的分析结果整理写入报告
```

**重要**：回退模式下无法做到真正的"同时跨图对比"（`vision_analyze` 每次只看一张图），因此需要先分别获取模板图和参考图的特征描述，再将描述嵌入检验 question 中供辅助视觉模型做逻辑对比。这不是理想方案，但在主模型非多模态时是唯一可行路径。

**多图对比模式**（每轮检验、最终评比）：

```
1. 将多张图片同时加载到上下文（生成图、模板图、参考图）
2. 主模型一次性跨图对比，直接输出判定结果
3. 写入报告
```

> ⚠️ 多图对比模式仅在主模型支持多模态时可用。回退模式下需逐图分析后逻辑对比。

---

## 执行顺序

```
输入参考图 → 迭代生成（≤5轮） → 最终评比
```

- 迭代上限 **5 轮**，超过后强制进入最终评比
- 最终评比对全部迭代输出打分排序

### API 资源约束

- 每轮消耗 1 次 `image_gen` 调用
- 5 轮上限 = 最多 5 次 `image_gen`
- 视觉分析全部内化，**零外部视觉 API 消耗**

---

## Step 1 — 多轮迭代生成与视觉检验（最多5轮）

### 目的
利用 `image_gen` 的固定双图策略生成成品，每轮后主模型内部视觉检验，动态调整。

### 输入

| 项目 | 来源 |
|------|------|
| 双图提示词模板 | 固定模板（下文定义） |
| 标准模特模板 | `assets/default_template.png` 或 `input/template.png` |
| 原始参考图 | `input/reference.png` |

### 图片策略（固定双图）

**固定策略：每轮必须使用双图**（模板图 + 参考图）。双参考图策略是 DRE 生产轨道的唯一标准策略；参考图承担外观信息传递，提示词仅锁定 Shape 约束和材质气质。

**固定双图提示词模板**（v2.3 — 基于 gpt-image-2 最佳实践重构）：

> 模板遵循 wiki [[entities/gpt-image-2]] 的多图编辑规范：
> Job 头 + Image 编号角色 + Preserve/Change/Do NOT add 三段式 + Constraints 收尾。
> 三段式标签（`Preserve list` / `Change only` / `Do NOT add`）为 gpt-image-2 验证过的固定英文锚点，
> 中文 prompt 中也保留这三个英文词。

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

**模板说明**：
- 遵循 gpt-image-2 多图编辑的**完整生产模板**格式（Job + Image 角色 + 三段式 + Constraints）
- `Preserve list` 锁定 Shape 层所有硬约束（比例、面部留白、材质、肢体数、背景）
- `Change only` 明确允许替换的范围（发型、服装、鞋、道具、姿态），防止模型自行扩散变更
- `Do NOT add` 用否定句明确禁止项——gpt-image-2 对 `NO` 前缀的识别度高于模糊描述
- 外观信息（发型、服装、配饰、颜色、姿势）完全由参考图承担，提示词仅锁定 Shape + 材质 + 背景 + 面部留白
- 鞋子样式、对称性/非对称性由参考图决定，不固定约束
- 材质强调为强制项（`Preserve list` 第三条），防止参考图的布料/柔绒质感覆盖模板的塑料感

**单图回退（仅极端例外）**：仅在 `image_gen` 双图调用超时或参考图无法加载等极端情况下回退。回退时需在 prompt 中补全外观描述。

### 每轮操作流程

```
1. 使用固定双图提示词模板
2. 调用 image_gen（模板图 + 参考图）
3. 保存 output.png 到 r{N}/
4. 保存本轮实际使用的 prompt 到 r{N}/prompt.md
5. 将 output.png + 模板图 + 参考图 加载到主模型上下文
6. 主模型内部视觉逐项判定检验清单（必须直接看图对比）
7. 写入检验报告 r{N}/inspection.md
8. 决策：全部通过 → 进入 Step 2；有失败 → 调整 prompt，进入下一轮
```

**强制存档检查（每轮必做）**：
- 如果未能成功写入 `prompt.md` 或 `inspection.md`，立即补写。

### 视觉检验清单（每轮必做）

**强制操作规范**：

1. 必须将**三张图片同时**加载到当前对话上下文：
   - 生成图：`r{N}/output.png`
   - 标准模板图：`assets/default_template.png`
   - 原始参考图：`input/reference.png`

2. 向主模型发送指令：
   ```
   请直接对比上面三张图片（生成图、模板图、参考图）。
   注意：我们不是在比较"生成图是否和参考图一模一样"，
   而是检验"参考图的角色身份是否被正确迁移到了 vinyl toy 形态中"。
   请逐层检验以下清单，不得依赖文本记忆描述参考图特征。
   ```

3. 主模型利用内部多模态视觉能力，**实时跨图对比**后输出判定结果。

4. **P2 强制分步检验（防对称化偏好）**：在整体检验之外，必须额外发送两条独立指令：
   ```
   请单独描述参考图中左手（画面左侧）在做什么？右手（画面右侧）在做什么？
   然后对比生成图中左手和右手分别是否匹配。
   禁止用"手臂位置大致对"通过——必须逐手确认。
   ```
   原因：agent 天然倾向对称化处理，容易把非对称手势（一手抬脸一手抱物）
   简化为双手对称。整体检验时这个细节极易被忽略，必须用独立问题强制关注。

---

**检验框架：三层气质控制**

> 核心原则：DRE 不是复刻参考图，而是将参考图的角色身份翻译成 vinyl toy 形态。
> 参考图可能是 9 头身手绘美少女、写实照片、2D 插画或棉花娃娃实物——这都不重要。
> 重要的是成品必须具备 vinyl toy 气质，且角色身份一眼可识。

---

#### 第一层 — 形态气质（Shape + Style）

**核心问题**：这张图看起来像一个标准的 vinyl art toy 手办吗？

| 检查维度 | 检验内容 | 通过标准 | 失败标准 |
|-----------|----------|-----------|-----------|
| **头身气质** | 大头是否大到有"压迫感"？身体是否小到像个底座？ | 头部占比明显超过半身，整体呈现"super deformed"感 | 头部比例接近正常人体，失去 Q 版夸张感 |
| **轮廓气质** | 所有边缘是否圆润无锋角？ | 圆头、圆身、圆手、圆脚，无尖角、无写实关节 | 出现尖下巴、细手指、写实肌肉线条 |
| **材质气质** | 是否看起来像一块实心塑料？ | 统一哑光软胶 PVC 质感，无布料飘动感、皮肤肉感、金属反光 | 出现布料纹理、皮肤细节、透明材质 |
| **面部气质** | 面部是否完全光滑的空白蛋形面？ | **绝对光滑无五官痕迹** | **任何眼睛/眉毛/鼻子/嘴巴/腮红痕迹 = 立即失败** |
| **肢体气质** | 手臂和腿是否短粗圆钝？ | 无手指、无膝盖结构、无脚踝，四肢像圆柱 | 出现手指、写实关节、过细四肢 |

**红线**：面部出现任何五官痕迹 → 立即失败，无需检查其他项。

---

#### 第二层 — 角色身份可识别性

**核心问题**：把参考图和生成图放在一起，能一眼认出是同一个角色吗？

| 检查维度 | 检验内容 | 通过标准 | 失败标准 |
|-----------|----------|-----------|-----------|
| **发型识别** | 发型结构+发饰+发色的组合是否让人联想到参考图？ | 核心发型元素在位 | 发型完全不同或遗漏核心发饰 |
| **服装识别** | 主服装款式+层次关系是否匹配？ | 主服装核心元素在位 | 主服装款式错误或层次关系丢失 |
| **配色识别** | 整体色调是否让人联想到参考图？ | 主色/辅色/点缀色与参考图一致 | 配色方案完全改变 |
| **姿态识别** | 站姿是否传递出参考图那种感觉？ | 姿态氛围匹配 | 姿态氛围完全相反 |

**关键原则**：不需要每个细节都对，需要"整体一眼认出"。

---

#### 第三层 — 关键特征完整性

**核心问题**：有没有遗漏"让人认不出这是谁"的关键元素？

| 优先级 | 特征类型 | 定义 | 判定标准 |
|--------|---------|------|----------|
| 🔴 **核心识别特征** | 丢了就认不出来 | 发型结构、主服装款式、标志性配色 | 必须全部在位 → 缺一 → 失败 |
| 🟡 **辅助识别特征** | 丢了还能猜 | 配饰、图案细节、小道具 | 允许缺 1-2 项 → 偏差 |
| 🟢 **氛围特征** | 有更好，没有也行 | 褶皱、倾斜角度、内八字、光影细节 | 完全不做硬性要求 → 不影响判定 |

**判定流程**：
1. 先检查第一层 — 如果形态气质不对（不像 vinyl toy），直接失败
2. 再检查第二层 — 如果身份不可识别，失败
3. 最后检查第三层 — 核心特征缺失 → 失败；辅助特征缺失 → 偏差

---

#### 补充：操作级逐项检查清单

| # | 检查维度 | 检验内容 | 对比源 | 属于层级 |
|---|----------|----------|--------|----------|
| S1 | **Shape** | 头身比是否接近标准模特（头部占高 50-60%） | 模板图 | 层一 |
| S2 | **Shape** | 头部大小/形状是否一致（圆-椭圆，无明显变形） | 模板图 | 层一 |
| S3 | **Shape** | 四肢粗细/长度是否一致（短粗圆钝无指） | 模板图 | 层一 |
| S4 | **Shape** | 整体轮廓/剪影是否一致（圆润无锋角） | 模板图 | 层一 |
| S5 | **Shape** | 材质是否为哑光塑料质感（统一 PVC 无其他质感） | 模板图 | 层一 |
| S6 | **Shape** | 面部是否完全留白（无五官痕迹） | 模板图 | 层一 |
| S7 | **Shape** | 是否存在额外肢体（恰好 2 臂 2 腿） | — | 层一 |
| P1 | **Pose** | 头部朝向/倾斜是否传递出参考图的氛围 | 参考图 | 层三 |
| P2 | **Pose** | 手臂位置/姿态是否传递出参考图的氛围（**必须逐手对比**：左手在参考图中做什么？右手在参考图中做什么？生成图是否分别匹配？禁止仅凭"手臂位置大致对"通过） | 参考图 | 层三 |
| P3 | **Pose** | 腿部位置/重心是否传递出参考图的氛围 | 参考图 | 层三 |
| P4 | **Pose** | 躯干旋转是否传递出参考图的氛围 | 参考图 | 层三 |
| A1 | **Appearance** | 发型是否迁移（样式+塑料化特征） | 参考图 | 层二 |
| A2 | **Appearance** | 服装款式/颜色是否迁移 | 参考图 | 层二 |
| A3 | **Appearance** | 配饰/道具是否迁移 | 参考图 | 层二 |
| A4 | **Appearance** | 鞋履是否迁移 | 参考图 | 层二 |
| A5 | **Appearance** | 整体配色是否匹配 | 参考图 | 层二 |
| A6 | **Appearance** | 装饰物/标记的物理附着面是否合理 | 参考图 | 层三 |
| A7 | **Appearance** | 面部标记（创可贴/贴纸等）是否在皮肤上而非头发上 | 参考图 | 层三 |

每项判定为 ✅ 通过 / ❌ 失败 / ⚠️ 偏差（可接受）。

**检验报告强制字段**：

```markdown
## 修正项对照（如本轮有新增修正目标）
| 修正项 | 参考图状态 | 生成图状态 | 判定 |
|---------|----------|----------|--------|
| 例：创可贴位置 | 前额皮肤上 | 头顶头发上 | ❌ 失败 |

## 三层检验结果
- 层一 形态气质：通过/失败/偏差
- 层二 身份可识别：通过/失败/偏差
- 层三 特征完整性：通过/失败/偏差

## 详细观察
### Shape 层
### Pose 层
### Appearance 层

## 迭代决策
```

---

### 迭代调整规则

- **第一层任一项失败** → 优先级最高。检查是否提示词中 Shape 约束被弱化或覆盖，加强 `"body structure LOCKED"` 重申。
- **第二层失败** → 检查参考图是否被正确传递。确保参考图清晰可见、关键元素无遮挡。
- **第三层核心特征缺失** → 在提示词中明确标注该元素为"核心识别特征，不可遗漏"。
- **某轮三层全部通过** → 可提前终止迭代，跳过剩余轮次直接进入 Step 2。
- **5 轮耗尽未全部通过** → 停止生成，进入 Step 2 评出最优。

### 关键 Prompt 技巧

**防止发型被模板抑制**：
```
The hair is COMPLETELY different from the template's original
hairstyle — replace it entirely with: [完整目标发型描述]
```

**防止额外肢体**：
```
CRITICAL: The figure has EXACTLY TWO ARMS and EXACTLY TWO LEGS.
No extra limbs. No third arm.
```

**精确数量装饰物**：
```
EXACTLY FOUR bows: BOW 1 — large at cheek level right side.
BOW 2 — medium below BOW 1. BOW 3 — medium near right end.
BOW 4 — medium near left end.
```

**精确面部标记定位**（防止附着面错误）：
```
A small pink band-aid sticker is placed diagonally on the
upper-right area of the FOREHEAD, above the bangs, on the skin
surface (NOT on the hair).
```

**防止单元素变更扩散为全局主题重设计**（gpt-image-2 颜色词语义扩散）：
```
gpt-image-2 对颜色词的语义扩散极强。仅写 "LIGHT BLUE dress"
会导致模型把蓝色扩散到发饰、抱枕、围裙、袜子、鞋子、材质
等所有元素，理解为"做一个蓝色主题版本"而非"只改裙子颜色"。

对策：在 Change only 段中只写要改的元素，在 Preserve list
中显式锁定所有不该变的元素（发饰颜色、抱枕颜色、袜子款式、
鞋子款式、材质类型等）。越具体越好。
```
**空间锚定法修正左右手镜像反转**（当左右手不对称姿态被反转时）：
```
用画面中已有的非对称道具作为空间锚点。例如：
- 参考图中白熊在左、棕熊在右
- 提示词中写："The arm on the SAME SIDE as the WHITE bear is raised
  near the cheek. The arm on the SAME SIDE as the BROWN bear holds
  the pillow."
- 避免使用 "left hand / right hand" 这种容易被镜像反转的术语，
  改用道具位置做绝对参照。
```

### 输出

| 产物 | 路径 | 格式 |
|------|------|------|
| R1-R5 生成图 | `r{N}/output.png` | PNG |
| R1-R5 提示词 | `r{N}/prompt.md` | Markdown |
| R1-R5 检验报告 | `r{N}/inspection.md` | Markdown |

---

## Step 2 — 最终评比、打分与报告

### 目的
对 Step 1 全部成品进行系统性视觉评比，量化打分，生成排名与报告。

### 输入

| 项目 | 来源 |
|------|------|
| 全部迭代成品 | `r{N}/output.png`（N ≤ 5） |
| 标准模特模板 | 模板图 |
| 参考图 | `input/reference.png` |

### 操作

#### 2.1 逐轮深度视觉分析

**强制操作规范**：

1. 将全部成品图（最多5张）+ 模板图 + 参考图 **同时加载到主模型上下文**。

2. 向主模型发送指令：
   ```
   请直接对比上面所有图片，按 Shape / Pose / Appearance 维度逐轮评分。
   必须基于实时视觉对比给出分数，禁止依赖之前轮次的检验报告文本。
   ```

3. 主模型利用内部多模态视觉能力，**实时跨图对比评分**。

**Shape 维度（权重 45%）**

| 子项 | 权重 | 判定标准 |
|------|------|----------|
| 头身比 | 4 | 与模板图差异 ≤5% 满分，>15% 0 分 |
| 头部大小 | 4 | 与模板图一致 |
| 四肢粗细 | 3 | 与模板图一致 |
| 整体轮廓 | 3 | 剪影匹配度 |
| 材质表现 | 2 | 塑料质感 |
| 面部留白 | 4 | 完全无五官（有则 0 分） |
| 肢体正确性 | 3 | 无额外肢体 |

**Pose 维度（权重 25%）**

| 子项 | 权重 | 判定标准 |
|------|------|----------|
| 头部方向 | 4 | 与参考图匹配 |
| 手臂位置 | 4 | 与参考图匹配 |
| 躯干朝向 | 3 | 与参考图匹配 |
| 腿部位置 | 2 | 与参考图匹配 |

**Appearance 维度（权重 30%）**

| 子项 | 权重 | 判定标准 |
|------|------|----------|
| 发型迁移 | 4 | 样式 + 塑料化特征 |
| 服装迁移 | 4 | 款式 + 颜色 |
| 配饰迁移 | 3 | 数量 + 位置 |
| 鞋履迁移 | 2 | 款式 + 颜色 |
| 配色方案 | 3 | 整体协调度 |
| 物理合理性 | 2 | 装饰物/标记附着面是否符合逻辑 |

#### 2.2 评分公式

```
Shape_score   = Σ(Shape_pass × weight) / Σ(weight) × 100
Pose_score    = Σ(Pose_pass × weight) / Σ(weight) × 100
Appearance_score = Σ(App_pass × weight) / Σ(weight) × 100

Composite = Shape_score × 0.45 + Pose_score × 0.25 + Appearance_score × 0.30
```

每项检查：✅ 通过 = 满分，❌ 失败 = 0 分，⚠️ 偏差 = 50% 权重分。

#### 2.3 排名规则

1. 按 `Composite` 降序排列
2. 并列时：优先 `Shape_score` 更高者
3. 仍并列：优先轮次更晚者

#### 2.4 生成 ranking.md

```markdown
| 排名 | 轮次 | Shape | Pose | Appearance | Composite | 推荐 |
|------|------|-------|------|------------|-----------|------|
| 1 | R3 | 92.3 | 88.9 | 95.5 | 92.5 | 🥇 |
| 2 | R1 | 78.6 | 94.4 | 97.0 | 88.2 | 🥈 |
```

#### 2.5 生成 evaluation.md

包含：项目概况、逐轮详细评分、关键发现、偏差记录、结论与建议。

### 判定标准

| Composite | 判定 |
|-----------|------|
| ≥ 90 | 优秀，可直接交付 |
| 75-89 | 良好，建议交付 |
| 60-74 | 及格，需人工复核 |
| < 60 | 不合格，建议重新执行 |

**硬性红线**：`Shape_score < 70` 或 `S6（面部留白）= 0` → 标记为"结构违规，不可交付"。

### 输出

| 产物 | 路径 | 格式 |
|------|------|------|
| 排名表 | `ranking.md` | Markdown |
| 详细评估报告 | `evaluation.md` | Markdown |

> 排名第一的 `r{X}/output.png` 即为最终成品。

---

## 关键陷阱与对策

| 陷阱 | 发生阶段 | 对策 |
|------|----------|------|
| 双图模式下参考图比例污染输出 | Step 1 R1-R2 | 双图极简提示词中加强 Shape 结构前置描述，确保模板结构不被覆盖 |
| **双图策略材质偏移**：参考图的布料/柔绒质感覆盖模板的塑料感 | Step 1 | 双图极简提示词中必须显式加入 `"smooth, glossy plastic texture — no fabric, no fuzz, no matte softness"` 材质强调 |
| 五官从参考图泄漏 | Step 1 | 检验清单 S6 + 评分 0 分红线 |
| 发型被模板原始发型抑制 | Step 1 | Prompt 中显式声明"COMPLETELY replace the hair" |
| 装饰物数量偏差 | Step 1 | 编号 + 精确定位法写入 prompt |
| 视觉模型将外观体积误判为结构漂移 | Step 1/2 | 检验时要求区分"外观层"与"结构层"；Shape 异常时人工复核 |
| 额外肢体（多手/多脚） | Step 1 | Prompt 强制声明"EXACTLY two arms/legs" |
| 发型镂空/尖锐发梢 | Step 1/2 | 提示词中写入"solid vinyl-like masses, rounded blunt tips" |
| Q版对称性偏好导致头部倾斜丢失 | Step 1 | 空间化语言替代角度数值 |
| 面部标记（创可贴/贴纸）被错误放置在头发而非皮肤上 | Step 1 | Prompt 中用 "on the FOREHEAD skin above the bangs, NOT on the hair" 精确定位 |
| 条纹/针织纹理平面化 | Step 1 | 用 "thick wide knit stripes" / "chunky ribbed knit texture" 替代笼统描述 |
| 腮红被错误处理成面部贴纸 | Step 1 | 默认忽略参考图中的自然腮红 |
| 迭代轮次遗漏存档 prompt.md / inspection.md | Step 1 | 每轮结束后必须确认两个文件已写入，未写入则立即补写 |
| **image_gen edits 端点不稳定**：代理的 `/v1/images/edits` 可能 SSL 错误或超时 | Step 1 | 遇到 edits 失败时自动回退到 generations（text-only），在 prompt 中补全外观描述；双图策略降级为单图 |
| **对称性偏好导致非对称姿态丢失**：agent 天然倾向对称化处理，容易将参考图的非对称手势（如一手抬脸一手抱物）简化为双手对称 | Step 1 检验 | P2 检验时必须**逐手对比**：左手（画面左侧）在参考图中做什么？右手（画面右侧）在参考图中做什么？生成图是否分别匹配？禁止仅凭"手臂位置大致对"通过 |

---

## 工具依赖

| Step | 方式 | 用途 |
|------|------|------|
| Step 1（迭代生成） | `image_gen` + 主模型内部视觉（或 `vision_analyze` 回退） | 生成 + 每轮检验 |
| Step 2（最终评比） | 主模型内部视觉（或 `vision_analyze` 回退） | 深度评比打分 |

**视觉分析优先使用主模型内部能力，非多模态模型回退到 `vision_analyze`。**

### ⚠️ 重要：image_gen 必须在主会话中直接调用

`delegate_task` 子代理**无法正确调用 `image_gen` 插件**。DRE 工作流中所有 `image_gen` 生成操作必须在**主会话**中直接执行，切不可通过 `delegate_task` 委托。

如需并行处理多个生成任务，应在主会话中逐个调用 `image_gen`，而非使用子代理。

### ⚠️ 重要：image_gen 插件启动机制

Hermes 插件为**进程级缓存**：
- 插件需在 Hermes 启动前通过 `hermes plugins enable <name>` 启用
- 会话内 `/reset` **不刷新**插件缓存
- 如更新了插件代码，必须**重新启动 Hermes** 才能生效

---

## API 资源预算

| 步骤 | 消耗 | 说明 |
|------|------|------|
| Step 1（≤5轮） | ≤5× `image_gen` + 主模型 ≤5 轮看图 | 唯一外部调用 |
| Step 2 | 主模型 1 轮看多图 | 零外部 API（主模型多模态时） |
| Step 2（回退） | ≤N× `vision_analyze` | 非多模态模型回退时额外消耗 |
| **总计上限** | **≤5× `image_gen` + ≤N× `vision_analyze`** | 视觉分析优先内化 |

---

## 使用方式

### 标准流程

用户提供参考角色图，说「跑 DRE 流程」或「重建这个人偶」即可。

1. 保存参考图为 `~/DRE_Projects/{project_name}/input/reference.png`
2. 自动执行迭代生成 → 最终评比
3. 模板自动使用内置默认模板
4. 最终成品路径：`r{rank1}/output.png`

### 自定义模板（可选）

用户提供自定义模板，放置于 `input/template.png`，优先使用。

---

## 参考案例

- `references/v2.2-simplification-rationale.md` — v2.2 简化原理：为什么从 6-step 简化为 2-step，为什么移除 Step 1-4 的中间文件，以及 R5 迭代驱动的模板进化证据
- `references/gothic-lolita-starry-night-case-study.md` — v1.x 案例，头部倾斜迭代策略
- `references/bunny-chibi-case-study.md` — v1.x 案例，面部留白预处理、蝴蝶结编号策略
- `references/toddler-fish-case-study.md` — v1.x 案例，Provider 回退链、Shape 外观干扰分析
- `references/lolita-bonnet-girl-case-study.md` — v1.x 案例，多肢体缺陷修复
- `references/band-aid-placement-case-study.md` — v2.x 案例，创可贴物理附着面判断失误与修复，双图策略优化与三图注入检验法
- `references/asymmetric-pose-spatial-anchor-case-study.md` — v2.2 案例，非对称姿态被对称化 + 左右手镜像反转，空间锚定法修正

---

## 版本管理

本技能通过 Git 管理，托管于 GitHub：

```
仓库: https://github.com/ashesxera/hermes-dre-workflow
路径: ~/.hermes/skills/doll-reconstruction/dre-workflow/
```

### 更新流程

```bash
cd ~/.hermes/skills/doll-reconstruction/dre-workflow
git add -A
git commit -m "v2.2: simplified pipeline, removed Step 1-4, flat directory"
git push
```
