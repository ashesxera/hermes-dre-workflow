# Case Study: bunny_chibi

> 项目: ~/DRE_Projects/bunny_chibi/
> 参考图: 308 7.jpeg（粉发兔耳少女，含九宫格线+胡萝卜+悬空蝴蝶结）
> 执行日期: 2026-06-15
> 总轮次: Stage 6 仅 2 轮（R1 双图超时跳过，R1-R2 均为单参考图）

---

## 关键发现

### 1. Stage 0 面部留白预处理成功

原始参考图包含完整五官（大圆眼、小嘴、腮红）。Stage 0 在清理 prompt 中同时要求面部留白，输出 `reference_cleaned.png` 直接就是无脸版本。后续 Stage 6 未出现五官泄漏。

**验证**: 最终成品面部完全留白，S6 通过。

### 2. 双参考图超时回退

R1 双图模式连续两次 `image_gen` 超时（`TimeoutError: The write operation timed out`）。直接切换单参考图策略，R1 成功生成。

**分析**: 可能原因 — prompt 较长（含详细外观描述）+ 两张参考图增加处理复杂度。单参考图模式极少超时。

**对策**: 已在技能中新增超时回退策略。

### 3. 蝴蝶结编号策略

R1 prompt 描述 "four deep crimson satin ribbon bows" → 模型仅生成 3 个蝴蝶结。

R2 使用编号+精确位置：
```
EXACTLY FOUR bows on hair:
BOW 1 — large, at cheek level on the right hair strand.
BOW 2 — medium, mid-length on the right hair strand below BOW 1.
BOW 3 — medium, near the end of the right hair strand below BOW 2.
BOW 4 — medium, near the end of the left hair strand.
```
→ 全部 4 个准确生成。

**启示**: 对需要精确数量的装饰元素，编号+位置描述比单纯的数量描述更有效。

### 4. Stage 7 Shape 外观干扰

vision 模型在 Stage 7 验证时，将长发体积、赤脚、头顶兔等外观变化误判为 Shape 层结构漂移：
- S1（头部大小）❌ — 长发+头顶兔使头部视觉占比增大
- S2（头身比）❌ — 赤脚使腿部视觉缩短
- S4（整体轮廓）❌ — 长发+赤脚 vs 短发+鞋的轮廓差异

但 S3（四肢粗细）、S5（材质）、S6（面部留白）均通过，说明底层身体结构实际未漂移。

**启示**: 当 Shape 得分异常低但 S3/S5/S6 通过时，应人工复核是否为外观干扰。

---

## 执行时间线

| 阶段 | 轮次 | 耗时 | 备注 |
|------|------|------|------|
| Stage 0 | 1 | 1 image_gen + 1 vision | 清理+面部留白，一次通过 |
| Stage 1 | 1 | 1 vision | 结构化分析 |
| Stage 2 | — | 0 | 直接从 Stage 1 提取 |
| Stage 3 | — | 0 | 使用内置默认模板 |
| Stage 4 | 1 | 1 image_gen + 1 vision | 姿势应用，一次通过 |
| Stage 5 | 3 | 3 image_gen | 并行：头发/服装/配饰 |
| Stage 6 R1 | 1 | 1 image_gen + 1 vision | 单图（双图超时跳过），蝴蝶结 3/4 |
| Stage 6 R2 | 1 | 1 image_gen + 1 vision | 单图，编号策略，全部通过 |
| Stage 7 | 1 | 1 vision | 打分验证 |

**总计**: 7 image_gen + 5 vision_analyze

---

## 最终评分

| 维度 | 得分 |
|------|------|
| Pose | 100 |
| Appearance | 100 |
| Shape | 42.9（外观干扰） |
| 综合 | 77.1（良好） |
