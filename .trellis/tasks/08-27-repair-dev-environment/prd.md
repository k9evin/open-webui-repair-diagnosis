# 配置本地开发环境

## Goal

创建安全的本地环境变量，启动前后端并验证管理员测试流程。

## Requirements

- 从 `.env.example` 创建不提交的本地 `.env`；生成随机 `WEBUI_SECRET_KEY`，使用本地 SQLite 数据库和安全的开发 CORS 配置。
- 验证 Node/Python 依赖可用；前端用 Vite、后端用 `backend/dev.sh` 分别启动。
- 在本地数据库创建管理员并通过登录接口或浏览器会话验证。

## Acceptance Criteria

- [ ] `.env` 未被 Git 跟踪，且后端读取的密钥不是示例值。
- [ ] 后端健康接口和前端页面可访问。
- [ ] `admin` / `password` 能完成一次本地登录。
