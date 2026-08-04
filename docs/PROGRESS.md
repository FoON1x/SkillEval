# 开发进展（Progress）

> 实时更新。每条记录格式：`- [日期] 阶段 / 内容`。每次里程碑结束更新"总览表"。

## 总览

| Phase | 内容 | 状态 |
| --- | --- | --- |
| P0 | 仓库与工具链骨架 | 完成 |
| P1 | Canonical Schema + Mock 生成器 | 完成 |
| P2 | 采集层（导入 + 推送） | 未开始 |
| P3 | 持久化与 API | 未开始 |
| P4 | 评测引擎 + 断言 | 未开始 |
| P5 | LLM-as-a-Judge | 未开始 |
| P6 | 前端可视化 | 未开始 |
| P7 | 打磨与收尾 | 未开始 |

## 规划阶段记录

- [2026-08-04] 需求澄清问答完成，方案 B 拍板（见 docs/REQUIREMENTS.md D1-D14）。
- [2026-08-04] 落盘：README / REQUIREMENTS / PLAN / ADR / SCHEMA / PROGRESS。
- [2026-08-04] git init 完成（规划文档首提）。

## Phase 0 · 仓库与工具链骨架（完成）

- 后端：FastAPI + uvicorn，/health 与 / 路由，pytest 2 用例通过。
- 前端：Vite + React 19 + TS 严格模式 + Vitest，2 用例通过；tsc 与 vite build 均通过。
- .gitignore 覆盖 venv/node_modules/dist 等。
- 首次 git 提交（本 Phase 出口条件达成）。

## Phase 1 · Canonical Trace Schema + Mock 生成器（完成）

- `skill_eval/core/schema.py`：Trace / Node / ToolCall / LlmUsage / Usage / TraceError，枚举约束（AgentName / RunState / NodeStatus / NodeType），JSON round-trip 验证。
- `skill_eval/core/projection.py`：tool_projection 深度优先收集工具调用（默认过滤 skipped），评估输入标准化。
- `skill_eval/mock/generator.py`：5 种确定性形态（simple_ok / nested / error_mid / running / long_chain）。
- TDD 共 34 用例全绿；测试揪出 error_mid 状态未置 error 的实现 bug 并修复。
- 说明：TS 类型生成推迟到 Phase 3（届时 FastAPI 已有真实路由与响应模型，OpenAPI 完整）。

## 下一步

Phase 2：采集层（导入适配器框架 + opencode 适配器 + 推送端点）。