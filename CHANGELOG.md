# DRE Workflow Changelog

## v2.7.0 (2026-06-22)

- 新增双审图员模式（Alice+Bobo 交叉验证）
- 新增 Kanban 多代理编排支持
- 确认 delegate_task 子代理可加载 skill（已验证 systematic-debugging）
- 确认 image_gen 必须在主会话调用，Kanban worker 不可用
- 新增 `references/dual-reviewer-pattern.md`、`references/kanban-orchestration.md`
- 新增 `references/hermes-soul-md-loading-mechanism.md`

## v2.6.0

| 维度 | v2.5 | v2.6 |
|------|------|------|
| 检验方式 | `browser_vision` 双图并排 | **`vision_analyze` 单图 ×3 + agent 文字对比** |
| 检验次数 | 2 次 browser_vision | 3 次 vision_analyze + 1 次 agent 对比 |
| 每轮输出 | `shape_check.html` + `appearance_check.html` | **一个** `inspection.html`（三图+完整报告） |
| browser_vision | 承担检验职责 | **仅 UI 呈现**（三图并列） |
| 回退原因 | — | kimi-k2.6 双图并排严重幻觉（编造头部倾斜、躯干旋转、错误手势） |

## v2.5.0

| 维度 | v2.3 | v2.4 |
|------|------|------|
| 视觉检验 | 主模型内部视觉 / vision_analyze 回退 | **browser_vision 双图并排**（统一方案） |
| 跨图对比 | 文字描述→文字描述（间接） | **像素级并排对比**（直接） |
| 工具依赖 | 依赖主模型多模态能力 | **所有模型通用** |
| 生图策略 | 单一固定模板 | **策略文档分离**：纯文本 / 双图 各自建档 |
| 提示词 | 引用不存在的 Image 编号 | **自包含描述**，去掉 Image 锚点 |
| 动态调整 | 手动判断 | **规则化**：根据检验失败项精确调整对应段 |

## v2.3.0

| 维度 | v2.1 | v2.2 |
|------|------|------|
| 流程阶段 | 6 Steps（含 Step 1-4 前置分析） | **2 Steps**：迭代生成 + 最终评比 |
| 前置分析 | Step 1-4 产出中间文件 | **全部移除**，分析内化到主模型视觉 |
| 目录结构 | 嵌套多层（step_1/ ~ step_6/） | **扁平化**（r1/ ~ r5/ + ranking.md） |
| 提示词 | Step 4 产出完整版备用 | **仅保留固定双图模板**，无中间文件 |

## v2.1.0

| 维度 | v2.0 | v2.1 |
|------|------|------|
| 参考图策略 | 默认双图，可单图回退 | **固定双图策略** |
| 提示词模板 | 固定双图模板 | **R5 修订版正式模板**，显式加入材质强调层 |
| 鞋型/对称性 | 模板说明中已放宽 | **彻底移除固定约束**，全部交由参考图决定 |

## v2.0.0

| 维度 | v1.x | v2.0 |
|------|------|------|
| 阶段数 | 8 Stages | 6 Steps |
| 视觉工具 | `vision_analyze` 外部调用 | 主模型内部视觉能力 |
| 资产提取 | Stage 5 并行轨道 | **移除**（专注生产） |
| Step 2 验证 | 人工检查 checklist | **自动验证** |
| 评分权重 | Shape 40% | **Shape 45%** |
