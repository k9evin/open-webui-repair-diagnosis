# Implementation Plan

1. 完成 `repair-dev-environment`：生成本地 `.env`，验证依赖，分别运行后端与 Vite，注册并登录管理员。
2. 完成 `repair-diagnosis-backend`：先写迁移/模型和最小 API 测试，再增加 router 注册、metadata 预过滤、全文/向量融合检索、反馈/审核和审计。
3. 完成 `repair-diagnosis-frontend`：复用现有组件实现独立输入、结果卡片和反馈弹窗，并以 API 客户端连接后端。
4. 完成 `repair-diagnosis-admin`：实现 XLSX 上传预览/导入、SOP 维护和审核入口；验证原始记录保留。
5. 完成 `repair-reference-retrieval`：经 MinerU/FA Documents 配置导入 Work Requirements/debug 文档，验证分块、metadata 预过滤、全文/向量融合、Qwen3 reranking 和受控回答上下文。
6. 完成 `repair-fa-documents-settings`：复用 Documents 页样式实现专用配置、开关、模型参数和返修索引重建状态。
7. 完成 `repair-fa-knowledge-base`：复用现有知识库页面模式实现返修专用导入/管理，生成 370 行带人工填写缺陷的 XLSX fixture，并用上传 API 导入它。
8. 对每个子任务运行定向检查和手工流程；最后运行前后端回归检查并完成父任务集成验收。

## Validation

- 后端：定向 pytest、MinerU loader 适配测试、配置快照/重建测试、metadata 预过滤/全文/向量融合/reranking 测试、鉴权 API 测试和普通健康接口。
- 前端：`npm run check`、定向 Vitest（新增逻辑时）和浏览器表单流程。
- 集成：管理员登录、查询、反馈、审核、再次查询、普通聊天/知识库冒烟测试。
