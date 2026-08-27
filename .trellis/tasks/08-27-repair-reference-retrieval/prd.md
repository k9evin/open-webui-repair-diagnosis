# 实现返修辅助文档检索

## Goal

将 Work Requirements 和 debug 文档作为带受控适用范围的辅助材料，纳入返修专用混合检索而不污染案例证据。

## Requirements

- 管理员可上传 PDF、DOCX、Markdown 或文本，选择 `work_requirement` 或 `debug_guide`，并填写可选 PN、产品族、产品类型、失效类型和分厂范围。
- 文档按语义完整段落分块，原文件、版本、来源和每块 metadata 均可追溯。
- 内容提取、chunking、embedding 和 reranking 使用 FA Documents 专用配置；页面样式与保存交互复用管理员 Documents 页；首选 MinerU、Qwen3-Embedding-8B 和 Qwen3-Reranker-4B。
- 查询先执行 metadata 预过滤，再在候选块内执行全文和向量检索，与案例检索采用相同的融合规则。
- 返回内容明确标为“辅助指引”，不作为同 PN 已验证案例、根因或换件依据。

## Acceptance Criteria

- [ ] 支持的文件类型能导入、预览、分块并保留来源信息。
- [ ] 单元/集成测试证明不匹配 metadata 的文档不会进入全文、向量或最终结果。
- [ ] 结果和审计能区分案例、SOP、Work Requirements 与 debug 文档。
- [ ] 索引保存配置快照；Documents 页的相关配置变更会标记返修索引过期，独立重建只处理返修 collection。
