# 架构决策记录（ADR）

> 状态约定：Proposed / Accepted / Superseded。Accepted 后仅在明确变更时更新并标记旧 ADR 为 Superseded。

## ADR-001 · 技术栈：方案 B（Python 后端 + React 前端）

- 状态：Accepted（2026-08-04）
- 背景：Trace 解析/清洗、LLM 评测等后端逻辑用 Python 生态更顺手；项目负责人拍板方案 B。
- 决策：
  - 后端：Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2（SQLite）
  - 前端：React 19 + TypeScript + Vite + Tailwind CSS + React Flow
  - 工程：单仓库（apps/api + apps/web），Python 用 `uv` 或 venv+pip，Node 侧沿用 npm workspaces（pnpm 未安装）
- 后果：[ADR-002] 通过 OpenAPI 同步 Schema；前后端独立跑测试。

## ADR-002 · 跨语言 Schema 同步：Pydantic 为单一事实源

- 状态：Accepted
- 背景：方案 B 下后端 Pydantic 与前端 TS 会各写一份，容易漂移。
- 决策：Canonical Trace Schema 只在 Python 定义（`apps/api/skill_eval/core/schema.py`）；FastAPI 暴露 OpenAPI；前端用 `openapi-typescript` 生成 TS 类型（`apps/web/src/api/generated.ts`）并纳入构建前检查。
- 后果：新增字段不得绕过 Python Schema；生成类型作为编译产物提交，CI 校验一致。

## ADR-003 · Trace 存储：SQLite + JSON 列

- 状态：Accepted
- 背景：本地单机、痕量级数据，需支持历史查询与 Diff。
- 决策：SQLAlchemy + SQLite；Trace 本体存 JSON 列（保留结构树），索引列仅存查询所需投影（agent/skill/session/time/status）。
- 后果：Diff 在内存中基于 Schema 对象计算；数据量增长后迁移 Postgres 代价可控。

## ADR-004 · 评估核心：纯 Python 包 + 沙箱断言

- 状态：Accepted
- 背景：规则评估器与自定义断言必须可单测、可离线。
- 决策：`skill_eval/eval/` 保持无 I/O 纯逻辑，输入 Trace 投影 + 期望，输出评测结果结构。自定义断言为受限 Python 运行（subprocess + 超时 + 资源限制，v1 单用户模型可接受），禁止文件/网络访问。
- 后果：规则与断言可完全覆盖单元测试；日后可换语言无需动评估接口。

## ADR-005 · 采集双通道 + CLI Runner 抽象

- 状态：Accepted
- 背景：需求确认导入与推送都要，且 CLI 触发运行将成为主流。
- 决策：
  - 通道一 导入适配器：`parse(raw_bytes or path) -> Trace`，按 agent_name 注册。
  - 通道二 推送适配器：接收事件流端点，组装增量事件为 Trace。
  - 运行器（Runner）抽象：`run(context) -> run_id + event stream`，v1 实现 opencode CLI（headless，事件驱动旁路推送）。
- 后果：新增 Agent 只需补适配器/运行器，主流程不动。

## ADR-006 · LLM-as-a-Judge Provider 抽象

- 状态：Accepted
- 背景：需求要求 OpenAI 兼容 Provider 且密钥本地管理。
- 决策：客户端仅依赖 OpenAI 兼容 REST 协议（base_url/model/api_key 配置化）。提供 JudgeClient（结果级）+ ProcessAnalyzer（全过程级）两个分析器，输出固定 JSON 结构。密钥经环境变量/本地配置文件读取，不硬编码、不入库。
- 后果：可无缝对接 OpenAI / DeepSeek / Ollama 等；Mock 服务用于测试。