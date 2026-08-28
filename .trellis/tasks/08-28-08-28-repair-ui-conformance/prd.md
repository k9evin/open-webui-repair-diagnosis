# 返修页面 UI 一致性

## Goal

让返修诊断、FA Knowledge Base 和审核页沿用 Open WebUI 现有页面布局、组件和视觉语言。

## Requirements

- 诊断页复用现有 workspace 页面容器、输入样式、Badge、Spinner、Modal 和按钮规范。
- FA Knowledge Base 复用 Knowledge 页面列表/卡片布局和文件上传交互。
- 审核页复用现有列表、状态筛选、Badge、确认交互。
- 不改变返修 API 和普通聊天、普通 Knowledge Base 行为。

## Acceptance Criteria

- [ ] 新增页面不再定义独立视觉系统或大段重复样式。
- [ ] 页面在 Vite 下可编译并保持现有深色模式与响应式布局。
- [ ] 关键表单、加载、错误和空状态沿用现有组件风格。
