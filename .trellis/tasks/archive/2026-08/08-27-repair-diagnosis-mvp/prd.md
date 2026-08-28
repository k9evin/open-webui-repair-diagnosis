# 返修诊断智能体 MVP

## Goal

在不影响 Open WebUI 既有普通聊天和文档问答链路的前提下，为返修操作员提供一个独立的返修诊断入口：基于受控范围内的已审核案例和 SOP 提供可追溯的参考建议，并将现场反馈以 `pending` 状态提交给工程师审核。

## Confirmed Facts

- 项目是 Open WebUI：SvelteKit 前端和 FastAPI 后端，前端开发命令为 `npm run dev`，后端以 `open-webui serve` 启动。
- 当前仓库没有本地 `.env`，仅有 `.env.example`；本任务需要生成仅供本地开发使用的随机密钥配置。
- 现有后端路由统一在 `backend/open_webui/main.py` 注册，并使用 `/api/v1/*` 前缀；前端已有独立页面路由和共享布局/侧栏组件。
- 用户要求使用本地管理员测试账号 `admin` / `password`，并在开发期间持续验证前后端未被破坏。
- PRD 要求新增独立返修诊断页面，不得改用或替换普通 Open WebUI RAG/聊天路径。

## In Scope

- 配置可启动的本地开发环境变量，随机生成本地密钥且不提交实际密钥。
- 分别启动并验证前端和后端；创建并使用指定管理员账号进行本地测试。
- 返修诊断独立入口与页面：固定收集 PN、SN、产品类型、分厂、故障描述；可选失效类型和已执行步骤；复用现有表单、布局、卡片和弹窗组件。
- 返修检索 API：只查询返修数据，不调用 Open WebUI collection endpoint；优先同 PN、同产品类型且 `approved` 的案例；不足时按 PRD 的受控回退顺序返回明确的匹配范围。
- 返修检索 API 先做 metadata 预过滤，再在候选范围内执行全文检索和向量检索，并以可配置权重混合排序；该过程使用独立返修数据表和 vector collection。
- SOP 与案例结构化展示；模型上下文和回答明确证据等级、范围、缺失信息及是否需要工程师升级。
- 管理员可导入 Work Requirements 和 debug 文档，作为带适用范围的辅助性材料；它们不会被视为已验证维修案例。
- 管理员新增专用 FA Documents Tab，复用 Documents 页布局和交互，但配置只作用于返修索引：内容提取、chunking、embedding、reranker、全文/向量检索开关和混合排序参数；默认使用 MinerU、Qwen3-Embedding-8B 与 Qwen3-Reranker-4B。
- 管理员新增独立 FA Knowledge Base，管理返修案例、SOP、Work Requirements 与 debug 文档的上传、导入、筛选和索引状态；不得使用普通 Knowledge Base 的 collection。
- 开发环境提供一份可上传的 XLSX fixture，其中有可重复生成的 370 条 `synthetic` 返修案例，仅用于测试，不得表现或导出为公司真实历史数据；其填写质量需模拟人工历史记录的不完整性与不一致性。
- 返修反馈 API 与弹窗：自动带入查询信息，最小反馈提交为 `pending`，不会进入正式检索。
- 工程师审核 `pending` 案例的最小能力，审核通过后进入正式返修检索。
- 管理员初始 XLSX 导入、保留原始字段/行号、最小清洗预览和结果报告。

## Constraints

- 最小化改动：不重构现有普通聊天、知识库或 RAG 流程；不新增与 MVP 无关的抽象。
- 历史案例、SOP 和产品规则是模型回答的唯一依据；证据不足时不得编造测试标准、根因或替换件。
- 初始历史 XLSX 数据为 `approved`；运营反馈为 `pending`。
- 原始记录必须保留 `source_file`、`source_row_id` 与 `raw_record_json`，清洗不得覆盖原文。
- SN 默认脱敏展示，除非已有权限模型明确允许完整展示。

## Out of Scope

- 模型微调、自动根因判定、自动批准换件。
- 从零散历史案例推导产品级测试标准。
- 修改 embedding、Hybrid Search 权重、阈值或 Top K 以替代受控检索。
- 替换 Open WebUI 原有普通知识库或普通文档问答链路。

## Acceptance Criteria

- [ ] 本地 `.env` 可供开发启动使用，包含随机安全密钥且不被 Git 跟踪。
- [ ] 前端和后端可分别启动，健康/页面访问验证通过；现有基础检查可运行且结果如实记录。
- [ ] 能以 `admin` / `password` 登录并完成返修诊断的查询、结构化结果查看、反馈提交与审核流程测试。
- [ ] 新页面必填校验 PN、SN、产品类型、分厂和故障描述；使用现有组件和路由惯例。
- [ ] 检索结果只包含 `approved` 案例，按 PRD 受控范围返回 `exact_pn`、同产品族参考、同产品类型参考或 `no_reliable_case`，并展示范围和证据限制。
- [ ] 每次返修检索均先执行 metadata 预过滤；全文和向量搜索只在候选范围内执行，混合排序和各检索来源可审计。
- [ ] Work Requirements 和 debug 文档只作为结构化辅助指引返回，不会被表现为历史验证证据或确定换件依据。
- [ ] 返修导入实际调用管理员 Documents 页的 MinerU/content-extraction、chunking、embedding 与 reranking 配置；索引记录配置快照，模型或 chunking 变更后能对返修数据单独重建索引。
- [ ] FA Knowledge Base 仅显示和管理返修数据域；XLSX fixture 含恰好 370 条带来源/行号的 synthetic 案例，且界面可识别其模拟性质。
- [ ] 上传该 XLSX 后，API 保留每行原始字段与来源行号；测试覆盖短/长文本、缺失字段、未记录测量、术语不一致和重复维修模式。
- [ ] 反馈默认不会进入正式检索；工程师批准后才可被检索。
- [ ] XLSX 导入保留原始字段与来源行号，并呈现最小可用的映射/异常/统计结果。
- [ ] 现有普通聊天和知识库 API/界面回归验证未受影响。

## Delivery Tasks

- `08-27-repair-dev-environment`：本地环境变量、前后端启动和管理员测试账号。
- `08-27-repair-diagnosis-backend`：返修数据结构、受控检索、反馈、审核与审计 API。
- `08-27-repair-diagnosis-frontend`：独立诊断页面、案例/SOP 结构化展示和反馈弹窗。
- `08-27-repair-diagnosis-admin`：XLSX 导入、SOP 管理与工程师审核管理页面。
- `08-27-repair-reference-retrieval`：Work Requirements/debug 文档导入、分块、索引和辅助材料检索。
- `08-27-repair-fa-documents-settings`：FA Documents 专用索引与检索配置 Tab。
- `08-27-repair-fa-knowledge-base`：返修资料上传、导入、管理及开发模拟案例初始化。

各子任务在自己的验收、质量检查和 `finish` 后归档；父任务仅在集成回归完成后结束。
