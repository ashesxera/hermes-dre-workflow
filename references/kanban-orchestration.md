# Kanban 多代理编排 — DRE 审图派发

> 创建日期: 2026-06-22
> 适用于: DRE 工作流 v2.7+

## 概念

用 Hermes Kanban + Profiles 实现 DRE 审图的持久化并行派发。Alice 和 Bob 并行看图，Cris 对比判定，全部通过 Kanban 任务板自动编排。

## 架构

```
用户: kanban create "DRE: {project}" --assignee cris
         │
         ▼
    ┌──────────────────────────┐
    │  Cris (编排 + 决策)       │
    │                          │
    │  Step 0: 预处理           │
    │  Step 1: 迭代生成(≤5轮)   │
    │    每轮:                  │
    │    ① image_gen           │
    │    ② kanban_create alice │
    │    ③ kanban_create bob   │
    │    ④ kanban_create cris  │
    │       (parents=[A, B])   │
    │    ⑤ 读对比 → 决策       │
    │  Step 2: 最终评比        │
    └──────────────────────────┘
```

## 前置条件

1. Gateway 运行中：`hermes gateway start`
2. Kanban 已初始化：`hermes kanban init`
3. Profile 已创建：alice, bob, cris
4. 每个 profile 有 `plugins/` 目录（符号链接到 `~/.hermes/plugins/`）
5. Alice/Bob 有 `auxiliary.vision` 配置
6. Cris 有 `toolsets: hermes-cli,kanban`

## 硬约束

- **image_gen 只能在主会话调用**。Kanban worker 和 delegate_task 子代理均无法访问 image_gen 插件。
- 如果 Cris 需要生成图片，必须创建 `assignee=default` 的子任务，由主会话捡起执行。

## Protocol Violation 根因与修复

### 现象
Worker 正常完成任务，输出文本后直接退出，未调用 `kanban_complete()`。调度器标记为 `protocol_violation` → `crashed`。

### 根因
chat 范式与 task queue 范式的冲突：
```
模型默认: 收到消息 → 思考 → 输出文本 → 结束
Kanban:   kanban_show → 干活 → 输出文本 → kanban_complete → 结束
```
模型输出文本后 agent loop 终止，不知道还需要调一个工具。SOUL.md 和 task body 写"必须调用"无效——模型会在文本中确认"好的"，但文本本身就是终止信号。

### 修复（按优先级）

| 方案 | 做法 | 适用 |
|------|------|------|
| 🥇 SOUL.md 重定义"完成" | 写"你的流程是 kanban_show→干活→kanban_complete，文本只是中间产物" | 所有 worker |
| 🥈 `--goal` 模式 | `hermes kanban create ... --goal "..."` | 改变 agent loop 终止条件 |
| 🥉 提高 failure_limit | `kanban.failure_limit: 3` | 临时容错 |
| 兜底 | 手动 `unblock` + `complete` | 任何时候 |

### 已验证
SOUL.md 重写后，cris/alice/bob 三人组连续 4 个任务零 protocol violation。

## 依赖链机制

```
kanban_create("对比", assignee=cris, parents=[alice_task, bob_task])
```

- 对比任务创建时状态为 `todo`
- Alice 和 Bob 都 `done` 后，调度器自动 `promoted` 为 `ready`
- Cris 被调度器唤醒，`kanban_show()` 中自动包含 Alice 和 Bob 的 summary

## 轮询等待

主会话创建 DRE 任务后，轮询等待完成：

```bash
TASK_ID=$(hermes kanban create "DRE: xxx" --assignee cris --json | jq -r .task_id)

while true; do
  STATUS=$(hermes kanban show "$TASK_ID" --json | jq -r .status)
  case "$STATUS" in
    done) break ;;
    blocked) echo "需要人工介入"; break ;;
  esac
  sleep 30
done

hermes kanban show "$TASK_ID"
```

## 已知限制

- 调度器 tick 60 秒，每轮审图约 5-7 分钟（含 tick 延迟）
- 5 轮迭代约 25-35 分钟
- image_gen 不在 Kanban worker 中可用，需主会话配合
