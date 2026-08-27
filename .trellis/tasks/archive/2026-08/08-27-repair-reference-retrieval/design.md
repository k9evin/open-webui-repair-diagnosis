# Design

将辅助文档存为 `repair_reference_document` 块，使用同一返修专用 vector collection 和全文索引。以现有 `Loader`/MinerU 提取内容、FA Documents 配置的 chunking 分块、配置指定的 Qwen3 embedding 生成向量、配置指定的 reranker 对融合候选重排。每块 metadata 包含 `document_type`、版本、适用产品范围和来源；检索函数先以这些字段产生 candidate IDs，再以 ID 约束全文和向量查询，最后与案例结果分开组装。`repair_index_version` 保存专用配置哈希，在 FA Documents 配置变化时要求专用重建。
