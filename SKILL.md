---
name: dre-workflow
description: "Use when user says 搓个娃, 搓娃, 重建人偶, 跑DRE, or DRE workflow with an image. Doll Reconstruction Engineer — convert reference character images into standardized doll figures. v2.0: 6-step pipeline with internal vision, auto-validation, and iterative generation."
version: 2.0.0
platforms: [macos, linux]
repository: https://github.com/ashesxera/hermes-dre-workflow
---

# DRE 工作执行方案 v2.0

> 基于 Doll Reconstruction Workflow 制定
> 全局优先级：**Shape > Pose > Appearance**
> 视觉能力：主模型内部多模态视觉（图片加载至上下文直接分析）

---

## 核心变更（v2.0）

| 维度 | v1.x | v2.0 |
|------|------|------|
| 阶段数 | 8 Stages | 6 Steps |
| 视觉工具 | `vision_analyze` 外部调用 | 主模型内部视觉能力 |
| 预处理 | Stage 0 独立阶段 | 并入 Step 2 提示词增强 |
| 姿势处理 | Stage 4 独立"姿势底座" | 并入最终提示词一次性生成 |
| 资产提取 | Stage 5 并行轨道 | **移除**（专注生产） |
| Step 2 验证 | 人工检查 checklist | **自动验证**，无需人工介入 |
| 评分权重 | Shape 40% | **Shape 45%** |

---

## 项目目录结构

```
~/DRE_Projects/{project_name}/
├── input/
│   └── reference.png                              # 原始参考图（用户提供）
│
├── step_1_reference_analysis/
│   └── analysis_report.md                         # 参考图视觉分析报告
│
├── step_2_prompt_construction/
│   ├── prompt_raw.md                              # Step 1 原始外观提示词
│   ├── prompt_stage0_enhanced.md                  # Step 2 增强后提示词
│   ├── auto_validation_report.md                  # Step 2 自动验证报告
│   └── prompt_final.md                            # Step 4 最终融合提示词
│
├── step_3_template_analysis/
│   └── template_report.md                         # 标准模特视觉分析报告
│
├── step_5_iterations/
│   ├── r1/
│   │   ├── output.png                             # R1 生成图
│   │   ├── prompt.md                              # R1 使用的完整提示词
│   │   └── inspection_report.md                   # R1 视觉检验报告
│   ├── r2/
│   ├── r3/
│   ├── r4/
│   ├── r5/
│   └── README.md                                  # 迭代总览索引
│
└── step_6_final_evaluation/
    ├── ranking.md                                 # 排名表
    └── evaluation_report.md                       # 详细评估报告
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

## 视觉能力调用规范（v2.0 核心）

**本工作流所有视觉分析均使用主模型内部多模态视觉能力，不再调用 `vision_analyze` 工具。**

标准调用方式：

```
1. 将目标图片加载到当前对话上下文（作为附件/引用）
2. 向主模型发送结构化视觉分析指令
3. 主模型利用内部视觉能力直接输出分析结果
4. 将结果写入对应 markdown 文件归档
```

**多图对比模式**（Step 5 检验、Step 6 评比）：

```
1. 将多张图片同时加载到上下文（生成图、模板图、参考图）
2. 主模型一次性跨图对比，直接输出判定结果
3. 写入报告
```

---

## 执行顺序

```
Step 1 → Step 2 → Step 3 → Step 4 → Step 5 (≤5轮) → Step 6
```

- Step 1-4 必须顺序执行
- Step 5 上限 **5 轮**，超过后强制进入 Step 6
- Step 6 对 Step 5 全部输出打分排序

### API 资源约束

- Step 5 每轮消耗 1 次 `image_gen` 调用
- 5 轮上限 = 最多 5 次 `image_gen`
- 视觉分析全部内化，**零外部视觉 API 消耗**

---

## Step 1 — 参考图视觉分析与提示词提取

### 目的
用主模型内部视觉能力分析参考图，提取所有客观外观信息，写成英文绘图提示词。

### 输入
| 项目 | 来源 | 格式 |
|------|------|------|
| 原始参考图 | 用户提供 | PNG/JPG |

### 操作

1. 将 `input/reference.png` 加载到主模型上下文
2. 发送结构化分析指令，要求按以下维度输出：

```
分析维度：
  - 整体构图：人物在画面中的位置、朝向、重心脚
  - 头部：朝向（正视/侧视/俯视/仰视）、倾斜角度与方向
  - 发型：类型、长度、颜色、刘海形态、鬓发、发饰、特殊造型
  - 服装：上装、下装、外套、袖型、领型、腰带、层叠关系、颜色、纹样
  - 鞋履：鞋型、袜子、颜色
  - 配饰：头饰、包袋、首饰、手持道具、其他装饰物
  - 特殊面部标记：创可贴、伤疤、贴纸、面具等（⚠️ 明确区别于五官）
  - 姿势：双臂位置、双腿位置、躯干旋转、重心分布
  - 色彩方案：主色、辅色、点缀色
  - 氛围/风格：可爱、冷酷、复古等（仅作渲染风格参考，不改变材质）
```

3. 将分析结果转化为**详细的英文绘图提示词**。

### 约束
- **禁止**写入任何身体比例描述（如"头身比"、"Q版"、"大头"等）。这些属于 Step 3 的标准模特范畴。
- **禁止**写入背景描述（背景在 Step 2 统一处理）。
- 对五官的描述**暂时保留**（Step 2 会统一清除）。

### 输出
| 产物 | 路径 | 格式 |
|------|------|------|
| 视觉分析报告 | `step_1_reference_analysis/analysis_report.md` | Markdown |
| 原始外观提示词 | `step_2_prompt_construction/prompt_raw.md` | Markdown |

---

## Step 2 — 提示词增强 + 自动验证

### 目的
在原始提示词上叠加强制性约束层：清空背景、去除五官、发型塑料玩偶化。并**自动验证**，无需人工介入。

### 输入
| 项目 | 来源 |
|------|------|
| 原始外观提示词 | `step_2_prompt_construction/prompt_raw.md` |
| 原始参考图 | `input/reference.png` |

### 操作

#### 2.1 三要素增强

**要素 A — 清空背景与漂浮道具**
- 在提示词末尾追加：
  ```
  Pure white background, no background objects, no floating props,
  no decorative elements suspended in the air, no text, no watermarks.
  ```
- 如参考图中存在与主体无物理接触的悬空装饰（漂浮星星、散落花瓣等），在提示词中明确排除。

**要素 B — 去除五官，保留特殊面部标记**
- **绝对清除**：眼睛、眉毛、鼻子、嘴巴、腮红、睫毛、美瞳、唇色。
- **保留例外**：创可贴、伤疤、贴纸、面罩、眼罩、机械纹路等非五官类面部标记。
- 追加约束：
  ```
  The face is completely blank and smooth — no eyes, no eyebrows,
  no nose, no mouth, no blush. The facial area is a featureless
  vinyl surface.
  ```
- 如有合法例外：
  ```
  [Exception: A small band-aid on the left cheek is preserved.]
  ```

**要素 C — 发型塑料玩偶化**
- **禁止**：发丝镂空、空气感层次、飘逸碎发、尖锐发梢。
- **允许**：浮雕状线条表现发束走向、整体块状造型、圆润发梢。
- 追加约束：
  ```
  Hair is rendered as solid vinyl-like masses with embossed line
  details showing strand direction. No hollow or airy layered effects.
  Hair tips are rounded and blunt, not sharp or spiky. The hairstyle
  has a toy-like solid plastic appearance with soft molded edges.
  ```

#### 2.2 自动验证

Step 2 产出 `prompt_stage0_enhanced.md` 后，**立即触发自动验证**。

**验证流程**：

```
验证输入：
  - 原始参考图（加载到主模型上下文）
  - prompt_raw.md
  - prompt_stage0_enhanced.md

验证执行：
  1. 主模型对比三份材料，执行自动检查

  【检查项 A — 背景清除】
  - 增强后提示词是否包含 "pure white background" 或等效表述
  - 是否明确排除漂浮道具、文字、水印
  - 自动判定：✅ 通过 / ❌ 缺失

  【检查项 B — 五官清除】
  - 扫描增强后提示词全文，匹配禁用词库：
    eyes, eyebrows, nose, mouth, lips, blush, eyelashes, pupils,
    眼睛, 眉毛, 鼻子, 嘴巴, 唇, 腮红, 睫毛
  - 如存在 → 标记位置，判定 ❌
  - 如不存在 → 判定 ✅
  - 例外检查：确认是否保留了"创可贴、伤疤、面罩"等合法标记

  【检查项 C — 发型塑料化】
  - 扫描关键词：
    正向标记（应有）：solid, vinyl-like, embossed, rounded tips,
                      blunt tips, molded edges, toy-like plastic
    负向标记（应无）：hollow, airy, layered, flowing, wispy,
                      sharp tips, spiky, transparent strands
  - 正向标记 ≥2 个且负向标记 = 0 → ✅
  - 否则 → ❌，并指出缺失/多余项

  2. 输出自动验证报告
```

**自动修复规则**：

| 失败项 | 自动修复动作 |
|--------|-------------|
| 背景清除缺失 | 在提示词末尾追加标准背景清除语句 |
| 五官词汇残留 | 定位并删除对应词汇；如为合法例外，保留并加注释 |
| 发型塑料化不足 | 在发型描述段插入/替换为标准塑料化描述 |

修复后**重新执行自动验证**，直至全部通过或达到 **3 次修复上限**。

### 输出
| 产物 | 路径 | 格式 |
|------|------|------|
| 增强后提示词 | `step_2_prompt_construction/prompt_stage0_enhanced.md` | Markdown |
| 自动验证报告 | `step_2_prompt_construction/auto_validation_report.md` | Markdown |

### 自动验证报告格式
```markdown
# Step 2 自动验证报告

## 检查项 A：背景清除
- 状态: ✅ 通过
- 命中关键词: "pure white background", "no floating props"

## 检查项 B：五官清除
- 状态: ✅ 通过
- 禁用词扫描: 0 命中
- 例外保留: "a small band-aid on left cheek" (合法)

## 检查项 C：发型塑料化
- 状态: ⚠️ 偏差（已自动修复）
- 原始问题: 缺失正向标记 "solid", "molded edges"
- 修复动作: 在发型段插入 "solid vinyl-like hair with molded edges"
- 复验状态: ✅ 通过

## 最终判定
- 验证轮次: 2/3
- 结论: 通过，进入 Step 3
```

---

## Step 3 — 标准模特视觉分析

### 目的
独立分析标准模板图片，提取其外形比例和材质特征。**完全不涉及发型、穿着、姿势**。

### 输入
| 项目 | 来源 |
|------|------|
| 标准人偶模板 | 默认：`assets/default_template.png`；自定义：`input/template.png` |

### 操作

1. 将模板图加载到主模型上下文
2. 发送结构化指令，要求仅回答以下问题：

```
分析维度（仅限结构与材质）：
  - 头身比：头部高度占总身高的比例
  - 头部特征：形状（圆/椭圆）、大小、宽度与肩宽的关系
  - 身体：躯干长度、宽度、整体紧凑度
  - 四肢：手臂长度与粗细、腿部长度与粗细、手脚大小
  - 材质：表面光泽度（哑光/亮光）、质感（PVC/搪胶/软胶）、颜色
  - 对称性：是否完全镜像对称
  - 面部：是否为完全留白的光滑表面
```

3. 将结果写成**纯结构+材质描述文本**，禁止出现任何服装/发型/姿势词汇。

### 默认模板参数（基准值）

| 参数 | 数值 |
|------|------|
| 头身比 | ~1.8（头部含发占 56% 总高） |
| 头部最大宽度 | 0.64H |
| 肩宽 | 0.55H |
| 手臂 | 短粗圆钝，无手指，长径比 ~1.57 |
| 腿部 | 极短敦实，长径比 ~0.92 |
| 脚部 | 大圆头包头鞋 |
| 材质 | 哑光软胶 PVC（搪胶） |
| 配色 | 暖米白 + 淡粉 |
| 对称性 | 100% 镜像对称 |
| 面部 | 完全留白光滑表面 |

### 输出
| 产物 | 路径 | 格式 |
|------|------|------|
| 标准模特分析报告 | `step_3_template_analysis/template_report.md` | Markdown |

---

## Step 4 — 提示词融合与优化

### 目的
将 Step 2 的外观提示词与 Step 3 的标准模特结构参数融合，生成最终绘图提示词。

### 输入
| 项目 | 来源 |
|------|------|
| 增强后外观提示词 | `step_2_prompt_construction/prompt_stage0_enhanced.md` |
| 标准模特结构报告 | `step_3_template_analysis/template_report.md` |

### 操作

1. 读取两个文件内容
2. 按以下优先级拼接为最终提示词：

```
[标准模特结构前置描述 — 高权重锚点]
A chibi vinyl art toy figure with extreme deformed proportions:
[Step 3 的结构参数，用自然语言重写].
The body structure, head size, and limb proportions are locked
and must not be altered.

[外观描述 — 来自参考图]
[Step 2 增强后的完整外观描述：姿势、发型、服装、配饰、道具、色彩]

[材质与渲染收尾]
Smooth matte vinyl plastic material, soft diffuse lighting,
3D render style, pure white background.

[强制性约束收尾]
CRITICAL: The face remains completely blank with NO eyes,
NO eyebrows, NO nose, NO mouth, NO blush. EXACTLY two arms
and EXACTLY two legs. No extra limbs.
```

3. **冲突消解**：
   - 如外观描述中意外包含比例词汇（如"slender body"），删除或替换为符合标准模特的描述（"tiny compact body"）。
   - 如外观描述中包含材质冲突（如"silky dress"），保留塑料质感描述，将"silky"降级为视觉纹理描述（"smooth plastic surface with embossed fabric texture"）。

### 输出
| 产物 | 路径 | 格式 |
|------|------|------|
| 最终融合提示词 | `step_2_prompt_construction/prompt_final.md` | Markdown |

---

## Step 5 — 多轮迭代生成与视觉检验（最多5轮）

### 目的
利用 `image_gen` 的单/双图策略生成成品，每轮后主模型内部视觉检验，动态调整。

### 输入
| 项目 | 来源 |
|------|------|
| 最终融合提示词 | `step_2_prompt_construction/prompt_final.md` |
| 标准模特模板 | `assets/default_template.png` 或 `input/template.png` |
| 原始参考图 | `input/reference.png`（双图策略时使用） |

### 单/双图策略

| 轮次 | 策略 | 参考图 | 目的 |
|------|------|--------|------|
| R1 | **双图** | 模板图 + 参考图 | 最大化外观信息输入，测试融合能力 |
| R2 | **双图** | 模板图 + 参考图 | 基于 R1 检验修复缺陷 |
| R3 | **单图** | 模板图 | 锁定结构，纯文本传递外观，纠正比例漂移 |
| R4 | **单图** | 模板图 | 精修外观细节 |
| R5 | **单图** | 模板图 | 最终精修或兜底 |

**超时回退**：任何轮次如 `image_gen` 超时 → 自动切换为单图模式继续。

### 每轮操作流程

```
1. 读取当前版本 prompt_final.md
2. 根据轮次选择策略，调用 image_gen
3. 保存 output.png 到 step_5_iterations/r{N}/
4. 保存本轮实际使用的 prompt 到 step_5_iterations/r{N}/prompt.md
5. 将 output.png + 模板图 + 参考图 加载到主模型上下文
6. 主模型内部视觉逐项判定检验清单
7. 写入检验报告 step_5_iterations/r{N}/inspection_report.md
8. 决策：全部通过 → 进入 Step 6；有失败 → 调整 prompt，进入下一轮
```

### 视觉检验清单（每轮必做）

将三张图（生成图、模板图、参考图）同时加载到主模型上下文，要求逐项判定：

| # | 检查维度 | 检验内容 | 对比源 |
|---|----------|----------|--------|
| S1 | **Shape** | 头身比是否接近标准模特 | 模板图 |
| S2 | **Shape** | 头部大小/形状是否一致 | 模板图 |
| S3 | **Shape** | 四肢粗细/长度是否一致 | 模板图 |
| S4 | **Shape** | 整体轮廓/剪影是否一致 | 模板图 |
| S5 | **Shape** | 材质是否为哑光塑料质感 | 模板图 |
| S6 | **Shape** | 面部是否完全留白（无五官） | 模板图 |
| S7 | **Shape** | 是否存在额外肢体 | — |
| P1 | **Pose** | 头部朝向/倾斜是否匹配 | 参考图 |
| P2 | **Pose** | 手臂位置/姿态是否匹配 | 参考图 |
| P3 | **Pose** | 腿部位置/重心是否匹配 | 参考图 |
| P4 | **Pose** | 躯干旋转是否匹配 | 参考图 |
| A1 | **Appearance** | 发型是否迁移（含塑料化） | 参考图 |
| A2 | **Appearance** | 服装款式/颜色是否迁移 | 参考图 |
| A3 | **Appearance** | 配饰/道具是否迁移 | 参考图 |
| A4 | **Appearance** | 鞋履是否迁移 | 参考图 |
| A5 | **Appearance** | 整体配色是否匹配 | 参考图 |

每项判定为 ✅ 通过 / ❌ 失败 / ⚠️ 偏差（可接受）。

### 迭代调整规则

- **Shape 项（S1-S7）任一失败** → 优先级最高。在 prompt 中加重结构约束，单图轮次强化"DO NOT change body proportions"。
- **Pose 项失败** → 调整姿势描述用语，使用空间化语言（"left side of head is higher than right"）替代角度数值。
- **Appearance 项失败** → 补充细粒度描述（编号定位法处理装饰物数量）。
- **5 轮耗尽仍未全部通过** → 停止生成，进入 Step 6 评分选出最优。

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

### 输出
| 产物 | 路径 | 格式 |
|------|------|------|
| R1-R5 生成图 | `step_5_iterations/r{N}/output.png` | PNG |
| R1-R5 提示词 | `step_5_iterations/r{N}/prompt.md` | Markdown |
| R1-R5 检验报告 | `step_5_iterations/r{N}/inspection_report.md` | Markdown |
| 迭代总览 | `step_5_iterations/README.md` | Markdown |

---

## Step 6 — 最终评比、打分与报告

### 目的
对 Step 5 全部成品进行系统性视觉评比，量化打分，生成排名与报告。

### 输入
| 项目 | 来源 |
|------|------|
| 全部迭代成品 | `step_5_iterations/r{N}/output.png`（N ≤ 5） |
| 标准模特模板 | 模板图 |
| 参考图 | `input/reference.png` |

### 操作

#### 6.1 逐轮深度视觉分析

将全部成品图（最多5张）+ 模板图 + 参考图 **同时加载到主模型上下文**，一次性跨图对比评分。

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

#### 6.2 评分公式

```
Shape_score   = Σ(Shape_pass × weight) / Σ(weight) × 100
Pose_score    = Σ(Pose_pass × weight) / Σ(weight) × 100
Appearance_score = Σ(App_pass × weight) / Σ(weight) × 100

Composite = Shape_score × 0.45 + Pose_score × 0.25 + Appearance_score × 0.30
```

每项检查：✅ 通过 = 满分，❌ 失败 = 0 分，⚠️ 偏差 = 50% 权重分。

#### 6.3 排名规则

1. 按 `Composite` 降序排列
2. 并列时：优先 `Shape_score` 更高者
3. 仍并列：优先轮次更晚者

#### 6.4 生成 ranking.md

```markdown
| 排名 | 轮次 | 策略 | Shape | Pose | Appearance | Composite | 推荐 |
|------|------|------|-------|------|------------|-----------|------|
| 1 | R3 | 单图 | 92.3 | 88.9 | 95.5 | 92.5 | 🥇 |
| 2 | R1 | 双图 | 78.6 | 94.4 | 97.0 | 88.2 | 🥈 |
```

#### 6.5 生成 evaluation_report.md

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
| 排名表 | `step_6_final_evaluation/ranking.md` | Markdown |
| 详细评估报告 | `step_6_final_evaluation/evaluation_report.md` | Markdown |

> 排名第一的 `step_5_iterations/r{X}/output.png` 即为最终成品。

---

## 关键陷阱与对策

| 陷阱 | 发生阶段 | 对策 |
|------|----------|------|
| 双图模式下参考图比例污染输出 | Step 5 R1-R2 | 结构描述前置 + 单图轮次兜底修复 |
| 五官从参考图泄漏 | Step 5 | Step 2 强制清除 + 检验清单 S6 + 评分 0 分红线 |
| 发型被模板原始发型抑制 | Step 5 | Prompt 中显式声明"COMPLETELY replace the hair" |
| 装饰物数量偏差 | Step 5 | 编号 + 精确定位法写入 prompt |
| 视觉模型将外观体积误判为结构漂移 | Step 5/6 | 检验时要求区分"外观层"与"结构层"；Shape 异常时人工复核 |
| 额外肢体（多手/多脚） | Step 5 | Prompt 强制声明"EXACTLY two arms/legs" |
| 发型镂空/尖锐发梢 | Step 5/6 | Step 2 已写入"solid vinyl-like masses, rounded blunt tips" |
| Q版对称性偏好导致头部倾斜丢失 | Step 5 | 空间化语言替代角度数值 |

---

## 工具依赖

| Step | 方式 | 用途 |
|------|------|------|
| 1 | 主模型内部视觉 | 参考图分析 |
| 2 | 文本规则 + 主模型内部视觉 | 提示词增强 + 自动验证 |
| 3 | 主模型内部视觉 | 模板结构分析 |
| 4 | 文本处理 | 提示词融合 |
| 5 | `image_gen` + 主模型内部视觉 | 生成 + 每轮检验 |
| 6 | 主模型内部视觉 | 深度评比打分 |

**完全移除 `vision_analyze` 调用。**

---

## API 资源预算

| 步骤 | 消耗 | 说明 |
|------|------|------|
| Step 1 | 主模型 1 轮看图 | 零外部 API |
| Step 2 | 主模型 1 轮看图 + 文本处理 | 零外部 API |
| Step 3 | 主模型 1 轮看图 | 零外部 API |
| Step 5（5轮） | 5× `image_gen` + 主模型 5 轮看图 | 唯一外部调用 |
| Step 6 | 主模型 1 轮看多图 | 零外部 API |
| **总计上限** | **5× `image_gen`** | 视觉分析全部内化 |

---

## 使用方式

### 标准流程

用户提供参考角色图，说「跑 DRE 流程」或「重建这个人偶」即可。

1. 保存参考图为 `~/DRE_Projects/{project_name}/input/reference.png`
2. 自动执行 Step 1 → 2 → 3 → 4 → 5 → 6
3. 模板自动使用内置默认模板
4. 最终成品路径：`step_5_iterations/r{rank1}/output.png`

### 自定义模板（可选）

用户提供自定义模板，放置于 `input/template.png`，Step 3 优先使用。

---

## 参考案例

- `references/gothic-lolita-starry-night-case-study.md` — v1.x 案例，包含头部倾斜迭代策略
- `references/bunny-chibi-case-study.md` — v1.x 案例，包含面部留白预处理、蝴蝶结编号策略
- `references/toddler-fish-case-study.md` — v1.x 案例，包含 Provider 回退链、Shape 外观干扰分析
- `references/lolita-bonnet-girl-case-study.md` — v1.x 案例，包含多肢体缺陷修复

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
git commit -m "v2.0: 6-step pipeline with internal vision and auto-validation"
git push
```
