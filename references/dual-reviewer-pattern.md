# 双审图员模式 — Alice + Bob 交叉验证

> 创建日期: 2026-06-22
> 适用于: DRE 工作流 v2.7+

## 概念

用两个不同模型的 agent 分别独立审图，然后交叉验证，避免单一模型幻觉。

```
生成图
  ├── Alice (doubao-seed-2.0-pro) → 描述 Shape + Pose
  ├── Bob   (kimi-k2-250905)      → 描述 Appearance
  └── Cris  (deepseek-v4-pro)     → 对比 Alice vs Bob，判定通过/失败
```

## 为什么需要双审图员

- 单一 vision 模型存在幻觉风险（kimi-k2.6 双图并排时编造头部倾斜、躯干旋转）
- 不同模型对不同细节敏感度不同（doubao 擅长结构化描述，kimi 擅长整体气质）
- 交叉验证暴露歧义点（如 Alice 报告 7 人、Bob 报告 6 人）

## Profile 配置

### Alice
```yaml
model:
  provider: custom:ark.cn-beijing.volces.com
  default: doubao-seed-2.0-pro
custom_providers:
- api_key: ark-...
  base_url: https://ark.cn-beijing.volces.com/api/coding/v3
  model: doubao-seed-2.0-pro
auxiliary:
  vision:
    provider: custom:ark.cn-beijing.volces.com
    model: doubao-seed-2.0-pro
    base_url: https://ark.cn-beijing.volces.com/api/coding/v3
    api_key: ark-...
```

### Bob
```yaml
model:
  provider: custom:ark.cn-beijing.volces.com
  default: kimi-k2-250905
custom_providers:
- api_key: ark-...
  base_url: https://ark.cn-beijing.volces.com/api/coding/v3
  model: kimi-k2-250905
auxiliary:
  vision:
    provider: custom:ark.cn-beijing.volces.com
    model: kimi-k2-250905
    base_url: https://ark.cn-beijing.volces.com/api/coding/v3
    api_key: ark-...
```

### Cris
```yaml
model:
  provider: custom:ark.cn-beijing.volces.com
  default: deepseek-v4-pro-260425
toolsets: hermes-cli,kanban
```

## SOUL.md 关键写法

Alice 和 Bob 是纯眼睛，不做判断：

```
如实描述图片内容，不做评判，不预设关注范围。具体看什么由任务分派者指定。
```

**关键**：对于 Kanban worker，必须重定义"完成"：

```
你的工作流程不是"输出文本 → 结束"。
你的工作流程是"kanban_show → 干活 → kanban_complete"。
在你调用 kanban_complete() 之前，你的任务不算完成。
文本回复只是中间产物，不是终点。
```

## 两种调用方式

### 方式 A：直接子进程（即时）
```bash
alice chat -q "描述图片" --image /path/to/img.png --max-turns 3 --quiet
bob chat -q "描述图片" --image /path/to/img.png --max-turns 3 --quiet
```

### 方式 B：Kanban 派发（持久化、可恢复）
```bash
hermes kanban create "审图" --assignee alice --body "用 vision_analyze 查看 {路径}..."
hermes kanban create "审图" --assignee bob --body "用 vision_analyze 查看 {路径}..."
```

## 常见问题

### vision_analyze 不可用
新 profile 默认没有 `auxiliary.vision` 配置。需在 config.yaml 中手动添加。

### 主模型原生视觉 vs vision_analyze
doubao-seed-2.0-pro 和 kimi-k2 都有原生视觉能力。用 `--image` 标志直接注入图片比 vision_analyze 更可靠（不经过 auxiliary provider 中转）。

### 插件目录
每个 profile 需要自己的 `plugins/` 目录。创建符号链接：
```bash
ln -s ~/.hermes/plugins ~/.hermes/profiles/alice/plugins
ln -s ~/.hermes/plugins ~/.hermes/profiles/bob/plugins
ln -s ~/.hermes/plugins ~/.hermes/profiles/cris/plugins
```
