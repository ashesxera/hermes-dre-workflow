# Step 0 — 参考图预处理

> 在 DRE 迭代生成之前，对原始参考图进行标准化清理。
> 使用 Meshy gpt-image-2 的 image-to-image 接口完成。

---

## 为什么需要 Step 0

原始参考图通常包含不适合 DRE 管线的元素：

| 问题 | 影响 | 示例 |
|------|------|------|
| 复杂背景 | 干扰外观提取，背景元素被误判为配饰 | 星星背景 → agent 以为角色头上有星形发饰 |
| 面部五官 | 泄漏到生成图，违反 Shape 层 S6 红线 | 参考图有眼睛 → 生成图出现眼睛 |
| 漂浮道具 | 被误认为角色配饰 | 空中爱心 → agent 以为角色手持爱心 |
| 头发卷曲/镂空/翘起 | 不适合 3D 打印/vinyl toy 生产 | 透明发丝 → 无法用塑料块表达 |
| 尖锐发梢 | 违反 Shape 层 S4 圆润轮廓约束 | 尖角发梢 → 生成图出现锋角 |

预处理后，参考图变为干净的"角色设计稿"，agent 提取外观特征时不会被干扰。

---

## 操作

### 触发

**按需触发**。首轮（R1）直接使用原始参考图生成。R1 检验后，若发现以下问题，触发 Step 0 清理参考图，后续轮次使用 `reference_clean.png`：

| 问题 | 表现 |
|------|------|
| 五官泄漏 | 生成图出现眼睛/眉毛/鼻子/嘴巴/腮红 |
| 背景干扰 | 背景元素被误判为配饰 |
| 漂浮物误判 | 空中元素被当作角色道具 |
| 头发问题 | 卷曲/镂空/翘起/尖锐发梢影响生成 |

若 R1 无上述问题，跳过 Step 0。

### 执行

```bash
python3 scripts/step0_preprocess.py \
  ~/DRE_Projects/{project}/input/reference.png \
  ~/DRE_Projects/{project}/input/
```

### 输出

| 产物 | 路径 | 说明 |
|------|------|------|
| 预处理参考图 | `input/reference_clean.png` | 清理后的参考图，替换原始 `reference.png` 使用 |
| 提示词 | `input/step0_prompt.md` | 预处理使用的 prompt |
| API 响应 | `input/step0_result.json` | Meshy 原始返回 |

### 后续流程

预处理完成后，DRE 流程使用 `reference_clean.png` 替代原始 `reference.png`：
- 纯文本策略下 agent 从 `reference_clean.png` 提取外观特征
- 双图策略下 `reference_clean.png` 作为 Image 2 传入

---

## 预处理内容

### 背景 → 纯白

```
Replace the entire background with pure white (#FFFFFF).
Remove ALL background elements: patterns, gradients, sparkles,
stars, hearts, text, decorative frames, scenery, floors, shadows.
```

### 面部 → 留白

```
Remove ALL facial features completely: eyes, eyebrows, nose,
mouth, blush, freckles, beauty marks.
The face becomes a completely blank smooth surface.
```

### 漂浮物 → 移除

```
Remove ALL objects floating in the air: sparkles, stars, hearts,
petals, ribbons, magical effects, dust particles.
Objects HELD by the character or WORN on the body are KEPT.
```

### 头发 → 塑料化

```
Simplify overly curly, wispy, or flyaway hair into solid,
smooth, rounded masses — like molded vinyl plastic.
Remove translucent/see-through hair effects. Hair must be opaque.
Round off sharp or pointed hair tips into blunt rounded ends.
Remove individual hair strands — replace with solid sculpted blocks.
Keep the overall hairstyle silhouette and color.
```

### 角色本体 → 保留

```
Keep the character's body, pose, clothing, accessories, and props
exactly as they are — do NOT change proportions, colors, or design.
The character should remain fully recognizable.
```

---

## 资源消耗

| 项目 | 消耗 |
|------|------|
| API 调用 | 1× Meshy image-to-image (gpt-image-2, 9-12 credits) |
| 耗时 | ~40-120s（提交 + 轮询） |
| 执行时机 | 每项目一次，Step 1 之前 |

---

## 容错

- 如果 Meshy API 不可用（key 缺失/网络错误）：跳过 Step 0，使用原始参考图，打印警告
- 如果预处理结果明显损坏（角色变形/颜色丢失）：保留原始参考图，标记为"预处理失败，使用原始图"
- 预处理不改变原始 `reference.png`，结果写入 `reference_clean.png`，原始文件始终保留

---

## 与纯文本策略的关系

纯文本策略下模型看不到图，但 **agent 需要看图来提取外观特征**。预处理后的干净参考图让 agent 提取的特征更准确：

| 预处理前 | 预处理后 |
|---------|---------|
| agent 看到"星星背景+角色" → 可能把背景星星写入发型描述 | agent 看到"纯白背景+角色" → 只提取角色特征 |
| agent 看到"闭眼微笑脸" → 可能把眼睛写入外观描述 | agent 看到"留白脸" → 不会描述五官 |
| agent 看到"透明发丝" → 可能描述为"半透明头发" | agent 看到"实心塑料块头发" → 描述为"solid hair mass" |
