---
name: dre-workflow
description: "Doll Reconstruction Engineer (DRE) 工作流：将参考角色图转化为标准化人偶角色，同时提取外观资产构建训练数据集。"
version: 1.0.0
platforms: [macos, linux]
---

# DRE 工作执行方案

> 基于 Doll Reconstruction Workflow 制定
> 全局优先级：**Shape > Pose > Appearance**

## 项目目录结构

```
~/DRE_Projects/{project_name}/
├── input/
│   ├── reference.png              # 原始参考图（用户提供）
│   ├── reference_cleaned.png      # 清理后的参考图（Stage 0 产出）
│   └── template.png               # 标准人偶模板（可选，自动从技能资产复制）
├── stage_0_preprocess/
│   └── preprocess_report.md       # 预处理报告
├── stage_1_analysis/
│   └── appearance_report.md       # 结构化外观报告
├── stage_2_pose/
│   └── pose_prompt.md             # 姿势提示词
├── stage_3_base/
│   └── doll_base.png              # 标准人偶底座
├── stage_4_posed/
│   └── posed_doll_base.png        # 已摆姿势的人偶底座
├── stage_5_assets/                # ⚠️ 并行轨道，不阻塞 Stage 6
│   ├── hair_asset.png
│   ├── clothing_asset.png
│   ├── footwear_asset.png
│   ├── accessory_asset.png
│   └── asset_metadata.md
├── stage_6_reconstruction/
│   ├── iterations/                # 🆕 所有迭代输出（不覆盖）
│   │   ├── README.md              # 迭代总览
│   │   ├── r1/
│   │       ├── output.png
│   │       └── report.md
│   └── README.md                 # 迭代总览
│   │       ├── output.png
│   │       └── report.md
│   └── README.md                 # 迭代总览
│   │       ├── output.png
│   │       └── report.md
│   └── README.md                 # 迭代总览
│   │       ├── output.png
│   │       └── report.md
│   └── README.md                 # 迭代总览
│   │       ├── output.png
│   │       └── report.md
│   └── README.md                 # 迭代总览
    ├── ranking.md                  # 打分排名（Stage 7 产出）
    └── verification_report.md      # 详细验证报告
```

### 默认模板

技能内置标准人偶模板，路径：

```
~/.hermes/skills/doll-reconstruction/dre-workflow/assets/default_template.png
```

- 2.2 头身 Q 版潮玩素体
- 暖米白 + 淡粉配色
- 纯白背景
- 100% 镜像对称

**用户无需提供模板**。如用户提供了自定义模板，则优先使用自定义模板。

## 全局约束

```
优先级（高→低）：Shape > Pose > Appearance

Shape（人偶底座权威）：
  - 头部形状/大小/宽高比
  - 面部轮廓
  - 身体比例（头身比）
  - 躯干宽度
  - 四肢粗细
  - 脚部尺寸
  - 整体轮廓
  - 材质表现（聚乙烯塑料）
  - 🔴 面部留白：**绝对禁止五官**。标准模板为无脸设计（被刘海覆盖的光滑弧面），
    最终成品必须保持面部完全空白——无眼睛、无眉毛、无鼻子、无嘴巴、无腮红。
    任何五官痕迹均视为 Shape 层违规，直接判定不合格。

Pose（参考图权威）：
  - 关节旋转
  - 四肢位置
  - 躯干朝向
  - 重心分布

Appearance（参考图权威）：
  - 发型/发饰
  - 服装（颜色+形状，材质统一为塑料）
  - 鞋履
  - 配饰/道具
  - 色彩方案
```

## 执行顺序

```
Stage 0 → Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 6 (≤5轮) → Stage 7 (打分排序)
                                                          │                                            │
                                                          └──→ Stage 5（并行）─────────────────────────┘
```

- **Stage 0 必须最先执行**，清理参考图中的背景杂物和无关元素
- Stage 1 → 2 → 3 → 4 必须顺序执行
- Stage 5 可在 Stage 1 完成后随时启动，与 Stage 2-6 并行
- Stage 6 依赖 Stage 4 完成，不依赖 Stage 5
- **Stage 6 上限 5 轮**，超过后强制进入 Stage 7
- Stage 7 对所有 Stage 6 输出打分排序，产出 `ranking.md` + `verification_report.md`

### API 资源约束

- Stage 6 每轮消耗 1 次 `image_gen` 调用 + 1 次 `vision_analyze` 验证
- 5 轮上限 = 最多 5 次 image_gen + 5 次 vision_analyze
- Stage 7 额外消耗 N 次 vision_analyze（N = 实际生成轮数）
- 如某轮提前全部通过，可提前终止，节省资源

## Stage 0 — 图片预处理（清理背景与无关元素）

> 🔴 必须最先执行。参考图可能包含复杂背景、九宫格参考线、悬空装饰物等，
> 必须先清理为干净的纯白背景 + 仅保留主体娃娃。

### 输入

| 项目 | 来源 | 格式 |
|------|------|------|
| 原始参考图 | 用户提供 | PNG/JPG |

### 操作方式

#### 0.1 识别需要清理的元素

使用 `vision_analyze` 加载原始参考图，识别以下类别：

| 类别 | 示例 | 处理方式 |
|------|------|----------|
| 背景杂色/纹理 | 渐变背景、纸张纹理 | 替换为纯白 |
| 参考线/网格 | 九宫格线、裁剪标记 | 移除 |
| 悬空装饰物 | 浮动的胡萝卜、蝴蝶结、星星、花朵 | 移除 |
| 边缘裁切元素 | 被画框裁断的物体残片 | 移除 |
| 文字/水印 | 签名、URL、版权标记 | 移除 |
| 主体娃娃 | 角色本体 + 附着物（头饰、手持物、头顶物） | ✅ 保留 |
| 娃娃的附着配件 | 头发上的蝴蝶结、头顶的宠物、怀中的道具 | ✅ 保留 |

**判断原则**：
- 与娃娃身体直接接触或附着的 → 保留
- 悬浮在空中、独立于娃娃之外的 → 移除
- 被画面边缘裁切的不完整物体 → 移除

#### 0.2 生成清理后的参考图

调用 `image_gen`，使用原始参考图作为参考：

```
Prompt 模板：
"[主体娃娃的完整外观描述 — 从 Stage 0.1 的 vision_analyze 结果中提取]。
🔴 外观描述中绝对不要包含任何五官描述（眼睛、眉毛、鼻子、嘴巴、腮红）。

Pure white background, NO grid lines, NO floating objects, 
NO extra decorations, NO text, NO watermarks. 
ONLY the main subject on a clean white background.

🔴 CRITICAL: The face is COMPLETELY BLANK — NO eyes, NO eyebrows, 
NO nose, NO mouth, NO blush. The face area is a smooth featureless 
surface, exactly like a blank vinyl art toy. Keep the face empty.
```

参考图：原始参考图
```

#### 0.3 验证清理结果

使用 `vision_analyze` 检查清理后的图片：

| # | 检查项 | 判定 |
|---|--------|------|
| 1 | 背景为纯白 | ✅/❌ |
| 2 | 无参考线/网格 | ✅/❌ |
| 3 | 无悬空装饰物 | ✅/❌ |
| 4 | 无边缘裁切残片 | ✅/❌ |
| 5 | 无文字/水印 | ✅/❌ |
| 6 | 主体娃娃完整保留 | ✅/❌ |
| 7 | 附着配件完整保留 | ✅/❌ |
| 🔴 8 | 面部完全留白（无五官） | ✅/❌ |

如任一检查不通过 → 调整 prompt 重新生成。

#### 0.4 面部留白处理

面部留白约束已嵌入 §0.2 的 prompt 模板和 §0.3 的验证清单（第 8 项）。
Stage 0 输出 `reference_cleaned.png` 直接就是无脸版本，
后续 Stage 6 不再需要处理五官泄漏问题。

### 输出

| 产物 | 路径 | 格式 |
|------|------|------|
| 清理后的参考图 | `input/reference_cleaned.png` | PNG（纯白背景） |
| 预处理报告 | `stage_0_preprocess/preprocess_report.md` | Markdown |

### 目录结构

```
stage_0_preprocess/
├── preprocess_report.md       # 清理报告（原始图分析 + 移除清单 + 验证结果）
└── (中间产物可选保留)
```

### 后续阶段引用

Stage 1 及之后所有阶段使用 `input/reference_cleaned.png` 作为参考图，
不再使用原始参考图。

### 输入

| 项目 | 来源 | 格式 |
|------|------|------|
| 清理后的参考图 | `input/reference_cleaned.png`（Stage 0 产出） | PNG |

### 操作方式

1. 使用 `vision_analyze` 加载清理后的参考图
2. 按以下维度逐一提取信息：

```
姿势信息：
  - 身体朝向（正面/侧面/背面/半侧）
  - 躯干旋转角度（定性：轻微/明显/大幅）
  - 头部方向（正视/侧视/仰视/俯视）
  - 手臂位置（左右分别描述）
  - 手部姿态
  - 腿部位置（左右分别描述）
  - 重心分布

外观信息：
  🔴 面部五官不提取 — 成品必须无脸（参考 Shape 层约束）
  头发：
    - 发型类型
    - 发量/长度
    - 刘海样式
    - 鬓发/侧发
    - 马尾/辫子
    - 发饰

  服装：
    - 上装
    - 下装
    - 外套
    - 袖型
    - 领型
    - 腰带/腰封

  鞋履：
    - 鞋型
    - 袜类

  配饰：
    - 头饰/发带
    - 帽子
    - 包袋
    - 首饰
    - 道具/武器
    - 其他装饰
```

3. 将结果写入结构化 markdown 报告

### 输出

| 产物 | 路径 | 格式 |
|------|------|------|
| 外观报告 | `stage_1_analysis/appearance_report.md` | Markdown |

### 检验方法

- 人工目视确认报告覆盖了参考图中所有可见的外观元素
- 确认报告未包含身体比例、解剖结构描述
- 确认报告为纯客观描述，无主观评价

## Stage 2 — 姿势提取

### 输入

| 项目 | 来源 | 格式 |
|------|------|------|
| 参考角色图 | `input/reference_cleaned.png` | PNG/JPG |
| Stage 1 姿势分析结果 | `stage_1_analysis/appearance_report.md`（姿势部分） | Markdown |

### 操作方式

1. 从 Stage 1 报告中提取姿势信息作为基础
2. 使用 `vision_analyze` 再次确认姿势细节（仅关注身体姿态，忽略外观）
3. 将姿势信息转化为**对生图模型友好的自然语言描述**

格式要求：
- 使用定性描述，不需要精确角度数值
- 使用生图模型容易理解的词汇（standing、sitting、arms crossed、looking left 等）
- 保持简洁，聚焦于关键关节和身体朝向

示例：
```
Standing pose, facing slightly left.
Torso gently rotated to the left.
Head turned to face forward.
Right arm raised to shoulder height, hand open.
Left arm relaxed at side.
Right leg forward, knee slightly bent.
Left leg straight, bearing weight.
```

### 输出

| 产物 | 路径 | 格式 |
|------|------|------|
| 姿势提示词 | `stage_2_pose/pose_prompt.md` | Markdown（纯文本描述） |

### 检验方法

- 阅读提示词，确认能在大脑中还原出与参考图一致的姿势
- 确认描述未包含任何外观信息（发型、服装等）
- 确认用词为生图模型常用词汇

## Stage 3 — 标准人偶底座锁定

### 输入

| 项目 | 来源 | 格式 |
|------|------|------|
| 标准人偶模板 | 默认：`~/.hermes/skills/doll-reconstruction/dre-workflow/assets/default_template.png` | PNG |
| 自定义模板（可选） | 用户提供时：`input/template.png` | PNG/JPG |

### 操作方式

1. 检查用户是否提供了自定义模板（`input/template.png` 是否存在）
2. 如未提供 → 使用技能内置默认模板 `assets/default_template.png`
3. 复制模板到 `stage_3_base/doll_base.png`
4. 使用 `vision_analyze` 确认模板的关键结构特征：
   - 头部形状与大小
   - 头身比
   - 四肢粗细
   - 整体轮廓
   - 材质表现（聚乙烯塑料光泽）
5. 记录关键结构参数供后续验证使用

### 输出

| 产物 | 路径 | 格式 |
|------|------|------|
| 标准人偶底座 | `stage_3_base/doll_base.png` | PNG（白色背景） |
| 结构参数报告 | `stage_3_base/base_structure_report.md` | Markdown |

### 默认模板参数

| 参数 | 数值 |
|------|------|
| 头身比 | ~2.2（头部含发占 62% 总高） |
| 头部最大宽度 | 0.73H |
| 肩宽 | 0.47H |
| 裙摆最大宽度 | 0.61H |
| 手臂 | 短粗圆钝，无手指 |
| 腿部 | 极短直筒 |
| 脚部 | 大圆头鞋 |
| 材质 | 哑光软胶塑料 |
| 配色 | 暖米白 + 淡粉 |
| 对称性 | 100% 镜像对称 |

## Stage 4 — 姿势应用

### 输入

| 项目 | 来源 | 格式 |
|------|------|------|
| 标准人偶底座 | `stage_3_base/doll_base.png` | PNG |
| 姿势提示词 | `stage_2_pose/pose_prompt.md` | Markdown |

### 操作方式

1. 读取姿势提示词文本
2. 调用 `image_gen` 进行图文生图：

```
请求参数：
  - 参考图：doll_base.png（作为结构基础）
  - 文本提示词：pose_prompt.md 中的姿势描述
  - 要求：保持人偶结构不变，仅改变姿势
```

### 输出

| 产物 | 路径 | 格式 |
|------|------|------|
| 已摆姿势的人偶底座 | `stage_4_posed/posed_doll_base.png` | PNG |

### 检验方法

1. 使用 `vision_analyze` 对比 `doll_base.png` 和 `posed_doll_base.png`：
   - ✅ 头部大小一致
   - ✅ 头身比一致
   - ✅ 四肢粗细一致
   - ✅ 整体轮廓一致
   - ✅ 材质表现一致
2. 使用 `vision_analyze` 对比 `reference.png` 和 `posed_doll_base.png`：
   - ✅ 姿势方向一致
   - ✅ 四肢位置大致匹配
3. 如任一检查不通过 → 调整 prompt 重新生成

### ⚠️ 关键陷阱：Q版模型抗拒头部不对称

**问题**：生图模型对 Q 版/Chibi 造型有强烈的对称性偏好。
当要求头部微倾斜时，模型倾向于忽略该指令并生成完全对称的头部。
在 gothic_lolita_starry_night 项目中，前 3 轮均未能实现头部倾斜。

**迭代策略**：
1. R1: 温和描述 "head tilted very slightly" → 通常失败
2. R2: 量化描述 "head tilted ~5 degrees" → 通常失败
3. R3: 强调不对称 "the head is NOT perfectly straight, it leans to one side" → 可能失败
4. R4: 空间化描述 "the left side of the head is higher than the right side" → 成功率较高

**关键技巧**：使用空间化/视觉化语言而非角度数值。
描述"左耳比右耳高"比"头部倾斜 5 度"更有效。
在 prompt 中加入 "the figure must NOT be perfectly symmetrical" 作为负面约束。

## Stage 5 — 外观资产提取 ⚠️ 并行轨道

> 此阶段与 Stage 6 并行，不阻塞最终人偶生成。
> 目的：构建长期训练数据集。

### 输入

| 项目 | 来源 | 格式 |
|------|------|------|
| 参考角色图 | `input/reference_cleaned.png` | PNG/JPG |

### 操作方式

#### 5.1 头发资产

1. 使用 `vision_analyze` 识别头发区域和样式
2. 使用 `image_gen` 生成仅包含发型的独立图片：
   - Prompt：描述发型特征 + "white background, isolated hair asset, no face, no body"
   - 参考图：reference.png（作为发型参考）

#### 5.2 服装资产

1. 使用 `vision_analyze` 识别服装部件
2. 使用 `image_gen` 生成服装独立图片：
   - Prompt：描述服装特征 + "white background, isolated clothing asset, flat lay"

#### 5.3 鞋履资产

1. 使用 `vision_analyze` 识别鞋履
2. 使用 `image_gen` 生成鞋履独立图片

#### 5.4 配饰资产

1. 使用 `vision_analyze` 识别所有配饰
2. 使用 `image_gen` 逐个生成配饰独立图片

#### 5.5 元数据报告

汇总所有资产信息，记录每个资产的描述、颜色、材质特征。

### 输出

| 产物 | 路径 | 格式 |
|------|------|------|
| 头发资产 | `stage_5_assets/hair_asset.png` | PNG（白色背景） |
| 服装资产 | `stage_5_assets/clothing_asset.png` | PNG（白色背景） |
| 鞋履资产 | `stage_5_assets/footwear_asset.png` | PNG（白色背景） |
| 配饰资产 | `stage_5_assets/accessory_asset.png` | PNG（白色背景） |
| 资产元数据 | `stage_5_assets/asset_metadata.md` | Markdown |

### 检验方法

- 每个资产图片中目标部件清晰可辨
- 背景为纯白或接近纯白
- 资产元数据描述准确
- ⚠️ 不要求达到 LoRA 训练级精度，作为视觉参考即可

## Stage 6 — 外观引导重建（迭代式，上限 5 轮）

> ⚠️ 硬限制：最多 5 轮迭代。超过 5 轮仍未达标 → 停止生成，进入 Stage 7 打分排序选出最优。

### 输入

| 项目 | 来源 | 格式 |
|------|------|------|
| 参考角色图 | `input/reference_cleaned.png` | PNG/JPG |
| 已摆姿势的人偶底座 | `stage_4_posed/posed_doll_base.png` | PNG |
| 外观报告 | `stage_1_analysis/appearance_report.md`（外观部分） | Markdown |

### 目录结构

```
stage_6_reconstruction/
├── iterations/
│   ├── r1/
│   │   ├── output.png           # R1 生成图
│   │   └── report.md            # R1 提示词 + 验证结果
│   ├── r2/
│   │   ├── output.png
│   │   └── report.md
│   ├── r3/
│   │   ├── output.png
│   │   └── report.md
│   ├── r4/
│   │   ├── output.png
│   │   └── report.md
│   ├── r5/
│   │   ├── output.png
│   │   └── report.md
│   └── README.md                 # 迭代总览
```

### 迭代策略：混合双图/单图（含超时回退）

采用 **2 轮双参考图 + 3 轮单参考图** 的固定混合策略：

| 轮次 | 策略 | 参考图 | 目的 |
|------|------|--------|------|
| R1 | 双参考图 | posed_doll_base + reference | 外观信息最大化，接受比例可能漂移 |
| R2 | 双参考图 | posed_doll_base + reference | 调整 prompt 修复 R1 缺陷 |
| R3 | 单参考图 | posed_doll_base only | 锁定结构，外观纯文本 |
| R4 | 单参考图 | posed_doll_base only | 调整外观描述修复 R3 缺陷 |
| R5 | 单参考图 | posed_doll_base only | 最终精修 |

**设计原理**：
- R1-R2（双图）：利用 reference.png 的图像通道传递复杂视觉特征（印花纹理、配色细节），
  即使比例漂移，外观信息密度最高。
- R3-R5（单图）：切换为结构锁定模式，用前两轮积累的外观描述经验进行文本迁移，
  确保最终输出比例正确。

**超时回退策略**：
双参考图模式可能因 prompt 过长或参考图复杂度高导致 `image_gen` 超时
（在 bunny_chibi 项目中 R1 双图连续两次超时）。
如双图轮次超时 → **直接跳过该轮，切换为单参考图模式继续**。
单参考图模式极少超时，外观质量损失可控。

### 每轮操作流程

#### 6.1 构建提示词

**双参考图轮次（R1, R2）**：

```
A chibi vinyl art toy doll figure with extreme deformed proportions 
(oversized head ~62% of height, tiny compact body, short stubby rounded 
arms with no fingers, very short straight legs, large round shoes).

🔴 CRITICAL: The face is COMPLETELY BLANK — no eyes, no eyebrows, 
no nose, no mouth, no blush. The face area is a smooth featureless 
surface, exactly like a blank vinyl art toy. The bangs/hair cover 
the forehead, and the lower face is an empty smooth surface.

[完整外观描述：发型、发饰、服装、配饰、鞋履、配色]
⚠️ 外观描述中绝对不要包含任何五官描述（眼睛、眉毛、鼻子、嘴巴、腮红）

Smooth matte vinyl plastic material finish, soft diffuse lighting, 
pure white background.

CRITICAL: Maintain the exact doll body proportions — oversized head, 
tiny body, stubby limbs, large round shoes. DO NOT change the body 
structure. The face must remain BLANK with NO facial features.
```

**单参考图轮次（R3, R4, R5）**：

```
This is a chibi vinyl art toy doll. The body structure, proportions, 
head size, and limb thickness are EXACTLY as shown in the reference 
image — DO NOT modify any proportions. The head-to-body ratio is locked.
🔴 The face is BLANK — a smooth featureless surface with NO eyes, 
NO eyebrows, NO nose, NO mouth, NO blush. Keep the face exactly as 
blank as the reference image.

🔴 The hair must be COMPLETELY replaced — the original short bob 
hairstyle in the reference image must be entirely removed and 
replaced with: [完整发型描述，包括刘海形态、鬓发延伸、马尾起始位置、卷度、长度、发饰].
Explicitly describe side-swept bangs that extend past the cheeks 
as framing strands, and pigtails starting from below ear level.

Now recolor and retexture the surface only: [完整外观描述].
⚠️ 外观描述中绝对不要包含任何五官描述（眼睛、眉毛、鼻子、嘴巴、腮红）

The body stays EXACTLY the same size and shape — only colors and 
surface details change. The face must remain completely BLANK.
```

#### 6.2 调用 image_gen

```
双参考图轮次：
  - reference_images: [posed_doll_base.png, reference.png]
  - prompt: 上述双图提示词

单参考图轮次：
  - reference_images: [posed_doll_base.png]
  - prompt: 上述单图提示词
```

#### 6.3 保存输出

每轮生成后**立即保存**到对应目录，**绝不覆盖**：

```bash
cp <生成图> stage_6_reconstruction/iterations/r{N}/output.png
```

#### 6.4 快速验证

每轮生成后用 `vision_analyze` 快速检查 4 个核心项：

| # | 检查项 | 对比源 |
|---|--------|--------|
| 1 | 头身比是否保持 ~2.2 | vs doll_base.png |
| 2 | 头部倾斜/手臂位置是否正确 | vs reference.png |
| 3 | 核心外观元素是否齐全 | vs reference.png |
| 🔴 4 | 面部是否完全留白（无五官） | vs doll_base.png |

#### 6.5 写入本轮报告

每轮报告格式：

```markdown
# Stage 6 — 迭代 R{N}

> 策略: [双参考图 / 单参考图]
> 参考图: [列出]

## 提示词
[完整 prompt]

## 快速验证
| # | 检查项 | 结果 |
|---|--------|------|
| 1 | 头身比 | ✅/❌ |
| 2 | 姿势 | ✅/❌ |
| 3 | 外观 | ✅/❌ |

## 本轮分析
[失败原因 / 改进方向]
```

#### 6.6 迭代决策

- 如当前轮全部通过 → 可提前终止，直接进入 Stage 7
- 如当前轮有失败 → 分析原因，调整 prompt，进入下一轮
- 如 R5 完成仍未完美 → 停止生成，进入 Stage 7 打分排序

### ⚠️ 关键陷阱

1. **双参考图比例漂移**：双图模式下 reference.png 的比例会通过图像通道污染输出，
   头身比可能从 2.2 漂移至 ~2.0。这是预期行为，R3 切换单图后会修复。

2. **单参考图外观丢失**：单图模式下复杂视觉特征（如特定印花）可能丢失。
   需要在文本 prompt 中极其详细地描述外观。

3. **Q 版对称性偏好**：模型抗拒头部不对称。使用空间化语言
   （"left side of head is lower"）而非角度数值。

4. 🔴 **五官泄漏**：参考图中的人脸五官（眼睛、嘴巴、腮红）极易通过外观描述
   泄漏到最终输出。必须在 prompt 中明确禁止五官，且外观描述中完全剔除
   面部特征词汇。在快速验证中作为独立检查项。

5. 🔴 **发型结构被模板抑制**：单参考图模式下，posed_doll_base 的原始发型
   （波波头短发、圆润轮廓）会抑制目标发型的细节迁移。常见问题：
   - 刘海被"截断"为模板的齐刘海长度，无法延伸为斜刘海+鬓发
   - 侧边鬓发（framing strands）完全丢失
   - 双马尾起始位置被模板的短发轮廓限制
   
   **对策**：在 prompt 中显式描述发型与模板的差异：
   ```
   "The hair is COMPLETELY different from the reference image's original 
   short bob — replace it entirely: long side-swept bangs that extend 
   past the cheeks as framing strands, and two long drill pigtails 
   starting from below the ears."
   ```
   明确告诉模型"替换原有发型"而非"修改原有发型"。

6. 🔴 **装饰元素数量偏差**：当 prompt 中仅描述数量（如"4 个蝴蝶结"），
   模型可能生成错误数量（如 3 个）。在 bunny_chibi 项目中，R1 仅生成 3 个蝴蝶结。
   
   **对策**：对需要精确数量的装饰元素，使用编号+位置描述：
   ```
   "EXACTLY FOUR bows on hair: BOW 1 — large, at cheek level right side.
   BOW 2 — medium, mid-length right side below BOW 1.
   BOW 3 — medium, near end of right side below BOW 2.
   BOW 4 — medium, near end of left side."
   ```
   编号+精确位置比单纯的数量描述更有效。R2 采用此策略后一次性通过。

7. 🔴 **Stage 7 Shape 评分受外观干扰**：vision 模型在 Stage 7 验证时，
   可能将长发体积、赤脚、头顶装饰物等外观变化误判为 Shape 层结构漂移，
   导致 S1（头部大小）、S2（头身比）、S4（整体轮廓）被错误标记为失败。
   
   **对策**：当 Shape 得分异常低（<70）但 S3（四肢粗细）、S5（材质）、
   S6（面部留白）均通过时，应人工复核确认是否为外观干扰而非真实结构漂移。
   在验证报告中标注"可能为外观干扰"。

### 输出

| 产物 | 路径 | 格式 |
|------|------|------|
| R1-R5 生成图 | `stage_6_reconstruction/iterations/r{N}/output.png` | PNG |
| R1-R5 报告 | `stage_6_reconstruction/iterations/r{N}/report.md` | Markdown |
| 迭代总览 | `stage_6_reconstruction/iterations/README.md` | Markdown |

> ⚠️ Stage 6 不产生 `final_doll.png`。最终选择由 Stage 7 打分排名决定。

## Stage 7 — 质量验证与打分排序

> Stage 7 对 Stage 6 产生的所有迭代作品（N 个 output.png，N ≤ 5）逐一打分排序。
> 输出两份报告：`ranking.md`（排名）和 `verification_report.md`（详细验证）。

### 输入

| 项目 | 来源 | 格式 |
|------|------|------|
| Stage 6 全部输出 | `stage_6_reconstruction/iterations/r{1..N}/output.png` | PNG |
| 标准人偶底座 | `stage_3_base/doll_base.png` | PNG |
| 已摆姿势的人偶底座 | `stage_4_posed/posed_doll_base.png` | PNG |
| 参考角色图 | `input/reference_cleaned.png` | PNG/JPG |

### 操作方式

#### 7.1 逐轮验证

对 Stage 6 的**每一轮**输出（R1-R5 中实际生成的轮次），使用 `vision_analyze` 逐项对比验证。

**Shape 验证**（对比 doll_base.png）：

| # | 检查项 | 权重 | 方法 |
|---|--------|------|------|
| S1 | 头部大小一致 | 3 | vision 对比头部尺寸 |
| S2 | 头身比一致 | 3 | vision 对比整体比例 |
| S3 | 四肢粗细一致 | 2 | vision 对比肢体粗细 |
| S4 | 整体轮廓一致 | 2 | vision 对比剪影 |
| S5 | 材质为塑料质感 | 1 | vision 判断材质 |
| 🔴 S6 | 面部完全留白（无五官） | 3 | vision 检查是否有眼睛/眉毛/鼻子/嘴巴/腮红 |

**Pose 验证**（对比 reference.png）：

| # | 检查项 | 权重 | 方法 |
|---|--------|------|------|
| P1 | 手臂位置匹配 | 3 | vision 对比左右手臂 |
| P2 | 头部方向匹配 | 3 | vision 对比头部朝向 |
| P3 | 躯干朝向匹配 | 2 | vision 对比身体方向 |
| P4 | 腿部位置匹配 | 1 | vision 对比左右腿 |

**Appearance 验证**（对比 reference.png）：

| # | 检查项 | 权重 | 方法 |
|---|--------|------|------|
| A1 | 发型已迁移 | 3 | vision 对比发型样式 |
| A2 | 服装已迁移 | 3 | vision 对比服装款式和颜色 |
| A3 | 配饰已迁移 | 2 | vision 对比配饰 |
| A4 | 鞋履已迁移 | 1 | vision 对比鞋履 |
| A5 | 色彩已迁移 | 2 | vision 对比整体配色 |

#### 7.2 打分规则

每项检查：
- ✅ 通过 = 满分
- ❌ 失败 = 0 分

**加权总分公式**：

```
Shape 得分 = (S1×3 + S2×3 + S3×2 + S4×2 + S5×1 + S6×3) / 14 × 100
Pose 得分  = (P1×3 + P2×3 + P3×2 + P4×1) / 9 × 100
Appearance = (A1×3 + A2×3 + A3×2 + A4×1 + A5×2) / 11 × 100

综合得分 = Shape×0.40 + Pose×0.30 + Appearance×0.30
```

**权重设计原理**：
- Shape 权重最高（40%）：结构一致性是 DRE 的最高优先级
- Pose 和 Appearance 各 30%：两者同等重要
- 子项中头身比、头部方向、发型、服装权重最高（各 3 分）

#### 7.3 排名

1. 计算每轮的 Shape / Pose / Appearance / 综合得分
2. 按综合得分降序排列
3. 如最高分并列 → 优先选 Shape 得分更高者
4. 如 Shape 也并列 → 优先选轮次更晚者（后期 prompt 更成熟）

#### 7.4 生成 ranking.md

对全部迭代作品打分排序，输出排名表：

```markdown
# Stage 7 — 打分排名

> 项目: {project_name}
> 日期: {date}
> 总轮次: {N}

## 排名

| 排名 | 轮次 | 策略 | Shape | Pose | Appearance | 综合 | 判定 |
|------|------|------|-------|------|------------|------|------|
| 1 | R2 | 单图 | 85.7 | 100 | 100 | 94.3 | 🥇 最优 |
| 2 | R1 | 单图 | 78.6 | 100 | 90.9 | 88.7 | 🥈 |
| 3 | R3 | 单图 | 71.4 | 88.9 | 81.8 | 79.6 | 🥉 |

## 得分明细

### R1
| 维度 | 通过项 | 失败项 | 得分 |
|------|--------|--------|------|
| Shape | S3,S5,S6 | S1,S2,S4 | 42.9 |
| Pose | P1,P2,P3,P4 | — | 100 |
| Appearance | A1,A2,A3,A4,A5 | — | 100 |

### R2
...
```

#### 7.5 生成 verification_report.md

对排名第一的作品，生成详细验证报告（格式同原 Stage 7 报告）。

### 输出

| 产物 | 路径 | 格式 |
|------|------|------|
| 打分排名 | `stage_7_verification/ranking.md` | Markdown |
| 详细验证报告 | `stage_7_verification/verification_report.md` | Markdown |

> ⚠️ Stage 7 不产生 `final_doll.png`。排名第一的 `output.png` 即为最终成品，
> 用户可直接从 `stage_6_reconstruction/iterations/r{N}/output.png` 获取。

### 判定标准

- **综合得分 ≥ 90** → 优秀
- **综合得分 75-89** → 良好，可交付
- **综合得分 60-74** → 一般，需人工审核
- **综合得分 < 60** → 不合格，需重新执行 DRE 流程
- **Shape 得分 < 70** → 无论综合得分如何，必须标记为结构风险

### 偏差记录

对排名第一的输出，记录所有非满分的检查项：

| 偏差项 | 严重性 | 说明 |
|--------|--------|------|
| ... | 高/中/低 | ... |

偏差分级：
- **高**：Shape 项失败 → 结构风险
- **中**：Pose 或关键 Appearance 项失败 → 可用但不完美
- **低**：次要 Appearance 项失败 → 可接受

## 工具依赖

| 阶段 | 工具 | 用途 |
|------|------|------|
| Stage 0 | `vision_analyze` + `image_gen` | 图片预处理：识别杂物 + 清理生成 |
| Stage 1 | `vision_analyze` | 参考图全面分析 |
| Stage 2 | `vision_analyze` | 姿势确认 |
| Stage 3 | `vision_analyze` | 模板结构确认 |
| Stage 4 | `image_gen` | 图文生图（姿势应用） |
| Stage 5 | `vision_analyze` + `image_gen` | 资产识别与生成 |
| Stage 6 | `image_gen` | 图文生图（外观迁移） |
| Stage 7 | `vision_analyze` | 逐项对比验证 |

## 使用方式

### 标准流程（仅需参考图）

用户提供参考角色图，说「跑 DRE 流程」或「重建这个人偶」即可。

1. 用户提供参考图 → 保存为 `~/DRE_Projects/{project_name}/input/reference.png`
2. **Stage 0 自动执行**：清理背景杂物、移除悬空元素、面部留白 → 产出 `reference_cleaned.png`
3. 模板自动使用技能内置默认模板（`assets/default_template.png`）
4. 按 Stage 0 → 1 → 2 → 3 → 4 → 6 → 7 顺序执行，Stage 5 在 Stage 1 完成后并行启动

### 自定义模板（可选）

如用户提供了自定义人偶模板，放置于 `input/template.png`，Stage 3 会优先使用。

## 参考案例

- `references/gothic-lolita-starry-night-case-study.md` — 完整执行案例，
  包含 Stage 4 和 Stage 6 的迭代日志、关键陷阱和解决方案。
- `references/bunny-chibi-case-study.md` — 第二个完整案例，
  包含 Stage 0 面部留白预处理、双参考图超时回退、蝴蝶结编号策略、
  Stage 7 Shape 外观干扰分析。
