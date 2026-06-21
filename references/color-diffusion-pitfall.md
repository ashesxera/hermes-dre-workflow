# gpt-image-2 颜色词语义扩散陷阱

> 来源：DRE 工作流 R4 轮（lolita_bonnet_girl 项目，2026-06-21）
> 后端：openapitoken.com gpt-image-2（generations 端点，text-only）

## 现象

R3 提示词中裙子颜色为 `soft peach`，R4 仅将 `soft peach` 改为 `LIGHT BLUE`，其余完全不变。

预期：只有裙子颜色从桃色变为浅蓝。

实际：gpt-image-2 将 "LIGHT BLUE" 理解为"做一个蓝色主题版本"，导致：

| 元素 | R3（桃色） | R4（浅蓝） | 是否预期 |
|------|-----------|-----------|---------|
| 裙色 | 桃粉 | 浅蓝 | ✅ |
| 辫尾蝴蝶结 | 白色 | 浅蓝 | ❌ 被蓝色污染 |
| 星形发夹 | 额前 3 颗一排 | 右侧 2 颗（一蓝一白） | ❌ 数量+位置+颜色全变 |
| 大蝴蝶结 | 粉+白 | 全白 | ❌ 粉色丢失 |
| Bonnet | 纯白镂空 | 白镂空+蓝色衬底透出 | ❌ 多了蓝色 |
| 心形抱枕 | 粉色 | 浅蓝+新增蓝色蝴蝶结 | ❌ 颜色变+多了装饰 |
| 围裙 | 白色素面 | 白色+新增蓝色小蝴蝶结 | ❌ 多了装饰 |
| 袜子 | 过膝荷叶边袜 | 及踝罗纹短袜 | ❌ 款式全变 |
| 鞋子 | 素面玛丽珍 | 玛丽珍+新增蝴蝶结 | ❌ 多了装饰 |
| 材质 | PVC 哑光 | 瓷器釉面 | ❌ 质感变了 |
| 泰迪熊 | 左白棕结/右棕白结 | 左白棕结/右棕白结 | ✅ 不变 |
| 左手姿势 | 抬脸握拳 | 抬脸握拳 | ✅ 不变 |

## 根因

gpt-image-2 对颜色词的语义扩散极强。`LIGHT BLUE dress` 被模型理解为"做一个蓝色系的版本"，而非"只改裙子颜色"。模型自行扩散到发饰、抱枕、围裙、袜子、鞋子、材质等所有元素。

## 对策

在 prompt 的 `Preserve list` 中显式锁定所有不该变的元素：

```
Preserve list:
- ... (existing items)
- Hair bow colors remain white (NOT blue)
- Star hairpins remain white, 3 in a row across forehead
- Heart pillow remains pink with white lace edge
- Apron remains plain white with no added decorations
- Socks remain white over-knee with frilled cuffs
- Shoes remain plain cream Mary Jane style with no added bows
- Material remains matte PVC/vinyl (NOT porcelain/ceramic)
```

在 `Change only` 中只写要改的元素：

```
Change only:
- Dress color changes from peach to light blue
```

## 与 gpt-image-2 三段式规范的关系

这个陷阱恰好验证了 wiki `entities/gpt-image-2` 中三段式规范的必要性：

- `Preserve list` 不是可选的——它是防止模型自行扩散的唯一防线
- `Change only` 必须精确到单元素级别，不能写 "change the color scheme to blue"
- `Do NOT add` 需要覆盖"不要新增装饰"这类隐性扩散
