# Toddler Fish Doll — 案例研究

> 项目: toddler_fish_doll
> 日期: 2026-06-15
> 模型: doubao-seedream-4-0-250828 (Volces Ark)
> 结果: R1 双参考图模式一次通过，综合得分 100

## 关键发现

### 1. Seedream 4.0 双参考图模式首次成功

这是 DRE 流程中首次 R1 双参考图模式一次性通过全部验证项。

**对比历史项目**：
- gothic_lolita_starry_night：R1-R3 均失败，需多次迭代
- bunny_chibi：R1 双图超时（Meshy），回退单图模式

**可能原因**：
- Seedream 4.0 对双参考图的融合能力优于 Meshy gpt-image-2
- 参考图外观复杂度适中（无复杂印花/纹理），双图模式未产生比例漂移
- prompt 中结构约束描述充分（"~56% of height" 等量化描述）

### 2. Provider 回退链

```
Meshy (gpt-image-2) → 超时 → Seedream 4.0 (Volces Ark) → 成功
```

Stage 4（姿势应用）和 Stage 6（外观重建）均使用 Seedream 4.0。

**建议优先顺序**：Seedream 4.0 > Meshy gpt-image-2

### 3. 模板参数修正

实际测量标准人偶模板 `default_template.png` 的关键参数：

| 参数 | 旧值（误） | 新值（实测） |
|------|-----------|-------------|
| 头身比 | ~2.2 | ~1.8 |
| 头部含发高度占比 | 62% | 56% |
| 头部最大宽度 | 0.73H | 0.64H |
| 肩宽 | 0.47H | 0.55H |

### 4. Shape 外观干扰（陷阱 #7 再次确认）

Stage 7 初检时，vision 模型将蓬松卷发体积误判为头部结构放大，
导致 S1/S2/S4 被标记为失败。

**复核方法**：第二次 vision_analyze 明确要求"区分外观层与结构层"后，
确认结构层尺寸完全匹配标准底座。

**教训**：对长发/卷发/大体积发型的角色，Shape 验证必须主动区分
"装饰体积"和"结构尺寸"，否则会产生误判。

### 5. 双图模式未产生比例漂移

与陷阱 #1（双参考图比例漂移）不同，本项目的 R1 双图模式
未出现头身比漂移。可能原因：
- Seedream 4.0 对 posed_doll_base 的结构参考权重更高
- 参考图角色本身也是 Q 版比例，与底座比例接近
- prompt 中使用了精确量化描述（"~56% of height"）

## Prompt 策略总结

### Stage 4 姿势应用

简洁版 prompt + 单参考图（doll_base.png）：
```
A chibi vinyl art toy doll figure, mid-hop/tiptoe pose, facing slightly left.
Torso rotated toward the left. Head facing forward.
Both arms bent at elbows, raised to chest height, hands together in front of the face.
Right leg straight down, weight-bearing. Left leg bent at knee, lifted backward.
Smooth matte vinyl plastic, soft diffuse lighting, pure white background.
Warm beige-white body color. Face completely BLANK.
```

**特点**：去除所有外观描述，仅保留姿势 + 材质 + 面部留白。简洁 prompt 减少了 Seedream 的超时概率。

### Stage 6 R1 双参考图

完整版 prompt + 双参考图（posed_doll_base + reference_cleaned）：
```
A chibi vinyl art toy doll figure with extreme deformed proportions
(oversized head ~56% of height, tiny compact body, short stubby rounded
arms with no fingers, very short straight legs, large round shoes).

🔴 CRITICAL: The face is COMPLETELY BLANK — no eyes, no eyebrows,
no nose, no mouth, no blush.

[详细外观描述：发型、发饰、服装、道具、姿势]

Smooth matte vinyl plastic material finish, soft diffuse lighting,
pure white background.

CRITICAL: Maintain the exact doll body proportions — oversized head,
tiny body, stubby limbs. DO NOT change the body structure.
```

**特点**：量化头身比（~56%）、明确的负面约束（DO NOT change）、
面部留白放在 prompt 开头位置（提高权重）。

## 资产提取

Stage 5 使用 Seedream 4.0 成功提取了头发、服装、道具三个资产。
鞋履资产跳过（角色赤脚）。

**超时处理**：首次头发资产生成超时（prompt 过长），缩短 prompt 后重试成功。
建议 Stage 5 的 prompt 保持简洁，不超过 50 词。
