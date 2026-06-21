# openapitoken.com gpt-image-2 Provider 参考

> 来源：2026-06-21 实际 API 测试 + 截图文档
> 参见：`references/strategy-text-only.md`

## API 端点

| 端点 | 状态 | 说明 |
|------|------|------|
| `POST /v1/images/generations` | ✅ 稳定 | 文生图，JSON body。不支持 `image` 参数（返回 400 "Parameter data type error"） |
| `POST /v1/images/edits` | ⚠️ 不稳定 | 图生图 multipart。存在但频繁 SSL 错误 / 524 超时，不可靠 |
| `POST /v1/chat/completions` | 📋 文档推荐 | stream=true，避免 CDN ~100s 超时。插件已实现但未充分测试 |

## 可用模型

nano-banana, nano-banana-2, nano-banana-pro, gpt-image-2, gpt-image-1.5, gpt-image-2-vip

## 响应特征

- 请求 `response_format: b64_json` → 实际返回 `url`（非 b64）
- 插件 `_extract_image()` 已处理 url fallback（自动下载缓存）
- 生成耗时：~50-120 秒

## 插件配置

```yaml
image_gen:
  provider: gpt-image-2
  base_url: https://openapitoken.com/v1
  api_key: sk-xxx
  model: gpt-image-2
```

## 结论

**纯文生图**。DRE 工作流在此 provider 上必须使用纯文本策略（`strategy-text-only.md`），不能依赖双图。
