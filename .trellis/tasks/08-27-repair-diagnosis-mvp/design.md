# Technical Design

## Boundaries

- 新增 `repair` 后端模型、路由和 Alembic 迁移；路由在 `main.py` 以 `/api/v1/repair` 注册。
- 返修数据使用独立表，不触碰 Open WebUI 的 collection、RAG 或普通聊天检索代码。
- 前端新增独立 `/repair-diagnosis` 路由、API 客户端和小型页面组件；优先复用现有 Svelte 页面、输入、按钮、卡片和 modal 组件。
- 新增管理员 `FA Documents` Tab，复用 `Documents.svelte` 的 `AdminSettingSection`/`AdminSettingRow`/`AdminSettingField` 布局与保存交互，但持久化到 repair 专用配置。默认值为 MinerU、`Qwen/Qwen3-Embedding-8B` 和 `Qwen/Qwen3-Reranker-4B`，不会覆盖普通 Documents 设置。
- 新增管理员 `FA Knowledge Base` 页面，复用 Workspace Knowledge 的列表、上传和确认交互，但连接 repair 专用 API、表和 collection。它展示数据类型、审核状态、适用 metadata、索引版本与来源，而不是普通 Knowledge Base 条目。

## Data Flow

1. 操作员在页面提交固定诊断字段。
2. `POST /api/v1/repair/retrieve` 在自有案例表中仅查询 `approved` 记录：精确 PN 优先；无命中时按产品族、产品类型受控回退，并返回显式 `scope` 和 SOP。
3. 导入时通过 Open WebUI 的 `Loader`/MinerU 实现提取内容，并使用 FA Documents 的 chunking、embedding 与 reranker 配置。服务将候选 ID 及其 metadata 作为硬过滤条件，同时送入返修专用全文索引和 vector collection。全文检索使用 PostgreSQL `tsvector`/GIN（SQLite 开发环境用 FTS5 等价表）；向量通过 VectorDB 抽象写入独立 `repair_documents` collection。两路结果以 reciprocal-rank fusion 合并，并用 Qwen3 reranker 对融合后的受控候选重排序；精确 PN 命中有明确优先级；不查询 Open WebUI collection endpoint 或普通 collection。
4. Work Requirements/debug/SOP 文档在各自适用范围 metadata 内同样经过预过滤和混合检索。它们单独返回为 `references`，且系统提示明确其是辅助指引，不是已验证案例。
5. 页面在结构化卡片中展示 API 返回的案例、SOP 与辅助材料，单独展示证据限制；普通聊天保持不变。
6. 操作员提交反馈时，API 保存完整原始输入和最小反馈，状态固定为 `pending`。
7. 工程师审核后，只有 `approved` 反馈可进入检索；每次导入、索引、查询、反馈和审核写入最小审计记录。

## Storage

最小表集合：`repair_case`、`repair_sop`、`repair_reference_document`、`repair_index_version`、`repair_audit_log`。案例表同时保存原始 JSON、来源文件与行号及所需规范化字段；文档表保存原文件、分块文本、类型（`sop`、`work_requirement`、`debug_guide`）、版本和适用范围。专用 vector collection 只保存 repair 文档 ID、embedding 与 metadata；事实文本留在自有表。`repair_index_version` 保存有效提取/分块/embedding/reranking 配置快照，避免混用不同 embedding 空间。全文索引与 vector collection 都在导入/审核时同步更新，失败时事务回滚并记录失败审计。

开发 fixture 由固定伪随机种子生成 370 条 `is_synthetic=true` 的案例，并写为可上传的 `synthetic_repair_cases.xlsx`。它包含有意的同 PN、产品族回退、缺失测量和 pending/approved 组合；保留真实人工记录常见的短/长故障描述、词汇不一致、遗漏失效类型、仅“更换某器件”的步骤、没有预期值的测量、空/矛盾复测及重复维修模式。它是显式 CLI/管理员开发操作，不在生产启动时自动执行；每条记录保留 `source_file=synthetic_repair_cases.xlsx` 和稳定的 `source_row_id`。所有 PN、SN、工厂和人员相关值均为虚构。

## Retrieval Contract

- 固定 metadata 过滤项：`review_status=approved`、`document_type`、`product_type`，以及已知的 PN、产品族、失效类型和分厂。
- 候选范围：`exact_pn` → `same_product_family_reference` → `same_product_type_reference` → `no_reliable_case`；后一个范围仅在前一个没有可用案例时执行，绝不静默扩大到全库。
- 输出分别携带全文、向量和融合排名，以及最终 `scope`；审计保存候选范围和每一路返回的文档 ID。
- 若 embedding 不可用，全文检索仍工作并在结果中显式标记 vector 状态；不可静默把辅助材料升级为确定维修建议。
- FA Documents 提供：启用状态、全文检索开关、向量检索开关、reranking 开关、混合权重、候选/最终 Top K、内容提取引擎、chunk size/overlap、embedding/reranker 引擎和模型。至少启用全文或向量之一；reranking 只有在存在候选时可用。配置变更会使返修索引显示“需要重建”；独立重建操作只重建 `repair_documents`，不会触及普通知识库或 memory vectors。开发环境默认使用 Chroma；生产 PostgreSQL/pgvector 必须将维度设为 Qwen3-Embedding-8B 实际输出维度并使用相应 HNSW/halfvec 配置。

## Compatibility and Rollback

- 所有新数据表和路由均为增量增加；回滚时移除页面导航/路由和 repair router，不影响现有业务表。
- 本地 `.env` 不提交；真实密钥仅存在开发机。
- 测试管理员仅在本地开发数据库创建。
