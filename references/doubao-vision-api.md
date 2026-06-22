# doubao-seed-2.0-pro 视觉描述 API

## 用途

作为 `vision_analyze` 的替代方案，直接调用火山引擎 doubao-seed-2.0-pro 的 vision 能力描述图片。
当 Hermes 配置的 auxiliary.vision 模型不可用或需要更精确的姿势分析时使用。

## 关键配置

| 项 | 值 |
|---|---|
| 模型 | `doubao-seed-2.0-pro` |
| Endpoint | `https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions` |
| API Key | `ark-8f7324a8-b8a5-47a6-8c1c-02f7f958e576-a19c0` |
| 图片格式 | base64 data URI（支持 PNG/JPG/WebP/GIF/BMP） |

## 重要发现

**正确的 endpoint 是 `/api/coding/v3/chat/completions`，不是 `/api/v3/chat/completions`。**

使用 `/api/v3/chat/completions` 会返回 404：
```
{"error":{"code":"InvalidEndpointOrModel.NotFound","message":"The model or endpoint doubao-seed-2.0-pro does not exist..."}}
```

## 姿势分析能力

doubao-seed-2.0-pro 在单图姿势分析上表现优秀，能准确区分：
- 左右手各自的动作和位置（以观众视角为准）
- 哪只眼睁开/闭合（wink 检测）
- 头部朝向、躯干朝向
- 道具的空间位置关系

与 kimi-k2.6 的对比：
- kimi-k2.6：双图并排时严重幻觉（编造头部倾斜、躯干旋转、错误手势）
- kimi-k2.6：单图分析准确
- doubao-seed-2.0-pro：单图分析准确，姿势细节描述更丰富

## 在 DRE 流程中的定位

当 `auxiliary.vision` 配置为 kimi-k2.6 时，检验流程使用 vision_analyze 单图分析 + agent 文字对比。
如果 kimi-k2.6 不可用，可回退到此脚本作为替代方案。

## 脚本

见 `scripts/doubao_describe.py`
