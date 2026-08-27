# Design

新增 `/workspace/fa-knowledge` 管理路由和 repair API 客户端，使用已有 Workspace Knowledge 的页面构成和上传组件。后端暴露 repair-scoped 列表、预览导入、提交导入、删除和重建接口。开发 fixture 生成器受 `--synthetic` 显式参数保护，使用固定 RNG seed 将 370 行写入 `.xlsx`；每行含原始导入列，刻意分布不完整和不一致的人工记录模式。导入测试通过同一个上传 API 使用该文件，生成器与 UI 均以 `is_synthetic` 标识。
