# 实现 FA 知识库管理

## Goal

提供独立的 FA Knowledge Base，用于上传、导入和管理返修案例及辅助文档，且完全隔离于普通 Knowledge Base。

## Requirements

- 页面复用现有 Knowledge 页面布局、列表、上传、筛选和确认交互，但调用 repair API。
- 管理案例 XLSX、SOP、Work Requirements 与 debug 文档；展示类型、审核状态、适用范围、索引状态、版本及原始来源。
- 开发环境提供一份显式生成、可通过 API 上传的 XLSX fixture，使用固定种子生成 370 条 synthetic 案例；所有模拟数据带清晰标记且不在生产自动生成。
- XLSX 应模拟人工填写缺陷：故障/步骤文本长短不一、同义术语不一致、失效类型缺失、测量/预期值未记录、替换件或复测结果缺失、重复维修模式及少量矛盾/低质量记录。
- 支持导入预览、失败报告、删除/重建索引，并保留审计记录。

## Acceptance Criteria

- [ ] 与普通 Knowledge Base 的 API、数据和 collection 完全隔离。
- [ ] 管理员可导入、筛选和查看四类返修资料及其索引状态。
- [ ] XLSX fixture 稳定生成恰好 370 行可检索的 synthetic 案例，并保留模拟来源/行号。
- [ ] 上传 API 测试直接使用该 XLSX，验证原始字段保留、缺失值标识、清洗预览和导入计数。
- [ ] 非管理员无法访问或操作该页面。
