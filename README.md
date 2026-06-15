# Hermes DRE Workflow

Doll Reconstruction Engineer (DRE) — Hermes Agent 技能，将参考角色图转化为标准化人偶角色，同时提取外观资产构建训练数据集。

## 概述

DRE 是一个严格的结构化工作流，遵循 **Shape > Pose > Appearance** 的优先级体系：

- **Shape（人偶底座权威）**：头部大小、头身比、四肢粗细、整体轮廓 — 永不修改
- **Pose（参考图权威）**：关节旋转、四肢位置、躯干朝向
- **Appearance（参考图权威）**：发型、服装、配饰、色彩方案

## 安装

```bash
# 直接安装到 Hermes skills 目录
cp -r dre-workflow ~/.hermes/skills/doll-reconstruction/
hermes skills list  # 确认已加载
```

或通过 Hermes skills hub 安装（待发布）。

## 使用

在 Hermes 会话中，提供参考角色图并说「跑 DRE 流程」即可。

工作流自动执行 8 个阶段：

```
Stage 0 (预处理) → Stage 1 (分析) → Stage 2 (姿势提取) → Stage 3 (底座锁定)
→ Stage 4 (姿势应用) → Stage 6 (外观重建, ≤5轮) → Stage 7 (打分排序)
                                    ↘ Stage 5 (资产提取, 并行)
```

## 文件结构

```
dre-workflow/
├── SKILL.md                                    # 技能定义 + 完整工作流
├── assets/
│   └── default_template.png                    # 标准人偶模板 (2.2头身 Q版)
└── references/
    ├── gothic-lolita-starry-night-case-study.md  # 案例 1
    └── bunny-chibi-case-study.md                 # 案例 2
```

## 依赖

- Hermes Agent
- `vision_analyze` 工具（视觉分析）
- `image_gen` 工具（图像生成）

## License

MIT
