# 变更日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.3.0] - 2026-08-24

> 本次重构（实现中）。

### 新增
- 前端 UI 原语层 `components/ui/`（Button/Input/Select/Badge/Card/Field/Modal/Toast/EmptyState/Spinner）
- 深色模式三态切换（浅/深/系统）+ localStorage 持久化 + prefers-color-scheme 跟随
- 运行页提供商→模型级联下拉（提交 model=provider/model）
- 运行页路径浏览模态（后端 GET /api/fs/browse）
- 后端 GET /api/runner/models（shell `opencode models`）
- 根 CHANGELOG.md、docs/README.md、docs/CODE_REVIEW.md

### 变更
- 主题 token 由暖石色切换为 slate/靛蓝（@custom-variant dark + .dark token 覆盖）
- 全前端文案统一中文（保留产品术语 Trace/Skill/Agent/DAG/Token/Cost/Prompt）
- 6 页 + 4 组件迁移至 UI 原语
- SSE 抽离为 api.postStream + AbortController 加固
- AGENTS.md 扩充文档机制/变更日志/技术约定节

### 修复
- SSE 无 AbortController 导致卸载泄漏（已加固）
- 后端 --model 转发未测试（已补断言）

### 决策记录
- 选 slate/靛蓝：经 3 个静态 demo（暖石/冷色/暗色优先）比对，冷色开发者工具风最契合
- 不加 provider 字段：opencode CLI 用 provider/model 合并格式，单一 model 字段足够
- i18n 统一中文无库：与文档体系一致，最轻量；双语若需另开规格

> 本节为规格1/规格2 实现完成后的据实校正前草案。

## [0.2.0] - 2026-08-23

### 新增
- opencode CLI 运行 + 实时 SSE 流抓取 Trace（运行页 /run）
- opencode 真实 JSONL 格式适配器（TraceBuilder feed/finalize）
- OpencodeRunner.run_stream（subprocess + watchdog + opencode export enrich）
- POST /api/runner/run/stream（SSE）、GET /api/runner/skills（技能列举）
- 一键启停脚本 scripts/start-all.{ps1,sh}、stop-all.{ps1,sh}

### 变更
- 重写 opencode 适配器为真实 JSONL 事件流（step_start/text/tool_use/step_finish，epoch-ms 时间戳），替换原虚构 v1 假设格式
- finalize 阶段合并 `opencode export` 的权威 metadata（title/agent/model/cost/tokens）；失败工具（metadata.exit != 0）标 NodeStatus.ERROR

### 修复
- 运行器健壮性：watchdog 超时、null-token 崩溃、SSE 断开处理

### 决策记录
- 采集方案 A（CLI subprocess + SSE）+ A2（适配器单一事实源）
- skill 注入引导语而非强制（opencode skill 由模型自动触发，无法强制）

## [0.1.0] - 2026-08-04

### 新增
- 单仓骨架：apps/api（FastAPI）+ apps/web（Vite/React）
- 核心 Trace Schema（Pydantic 单一事实源，OpenAPI→TS 同步）
- 可插拔导入注册表 + opencode 适配器骨架 + Runner 抽象
- SQLite 持久化（JSON 列 + 索引投影）
- 四规则评测引擎 + 沙箱断言
- LLM-as-a-Judge（结果级 + 过程级）
- 前端可视化（DAG/时间线/详情/成本/Diff）
- Playwright E2E

### 变更
- 后端依赖管理迁移至 uv（pyproject.toml + uv.lock，删除 requirements*.txt）

### 修复
- error_mid 形态运行时状态未置 error（TDD 揪出）
- 沙箱作用域与 Mock 工具名序列假设（TDD 揪出）

### 决策记录
- 技术栈方案 B：Python 3.12 + FastAPI + React 19 + Vite（ADR-001）
- Pydantic 为 Schema 单一事实源，OpenAPI→TS 同步前端类型（ADR-002）
- SQLite + JSON 列存储，索引列仅存查询投影（ADR-003）
- eval 无 I/O 纯逻辑，自定义断言受限沙箱运行（ADR-004）
- 采集双通道（导入/推送）+ CLI Runner 抽象（ADR-005）
- LLM-as-a-Judge 仅依赖 OpenAI 兼容协议，密钥不入库（ADR-006）
