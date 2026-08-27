# 实现返修诊断后端

## Goal

实现返修数据、受控检索、反馈和审核 API，保持普通 RAG 独立。

## Requirements

- 独立表保留案例原文、来源和规范化检索字段；初始导入记录为 `approved`，现场反馈为 `pending`。
- API 先执行 metadata 预过滤，再在候选集内执行全文与向量检索，并融合排序后返回明确范围、SOP、案例和证据限制。
- 向量使用独立 repair collection，全文使用返修自有索引；不读取 Open WebUI collection 数据或调用其 collection endpoint。
- 所有写操作需登录；工程师/管理员审核；写入最小审计记录。

## Acceptance Criteria

- [ ] 定向 API 测试证明同 PN 优先、受控回退、无可靠案例和 pending 隔离。
- [ ] 定向 API 测试证明 metadata 预过滤发生在全文/向量查询之前，并且混合排名不包含候选范围外的记录。
- [ ] 反馈被保存为 pending，批准后才进入查询结果。
- [ ] 普通检索端点未被调用或改动。
