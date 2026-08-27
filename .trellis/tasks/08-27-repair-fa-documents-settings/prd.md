# 配置 FA Documents 管理页

## Goal

在管理员设置中新增独立 FA Documents Tab，以现有 Documents 页为基准管理返修专用文档提取、索引和混合检索，而不影响普通 RAG。

## Requirements

- 复用 Documents 页的分区、字段、保存反馈和可访问性样式。
- 配置仅作用于 repair 数据域，包含启用状态、MinerU/提取设置、chunk size/overlap、embedding/reranker 引擎和模型、全文/向量/reranking 开关、融合权重与 Top K。
- 默认模型为 `Qwen/Qwen3-Embedding-8B`、`Qwen/Qwen3-Reranker-4B`；至少需要启用全文或向量检索。
- 展示索引版本和过期状态，允许只重建返修索引。

## Acceptance Criteria

- [ ] Tab 在管理员设置中可发现且非管理员无法访问。
- [ ] 保存 FA 设置不改变普通 Documents/RAG 配置。
- [ ] 无效组合被前后端拒绝；配置修改能标记返修索引过期。
- [ ] 独立重建不影响普通 RAG collection、知识库或 memory vectors。
