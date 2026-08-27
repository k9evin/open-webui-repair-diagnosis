# Design

在 `SettingsModal.svelte` 增加 `admin:fa-documents` Tab，并以现有 Documents 组件的 AdminSetting primitives 组装 `FADocuments.svelte`。后端添加 repair-scoped config API 和持久化配置；使用独立配置生成 loader、chunking、embedding 和 reranking 调用。验证器要求全文或向量至少一个开启，并把配置哈希写入 `repair_index_version`。重建端点只操作 `repair_documents` collection 和 repair 索引表。
