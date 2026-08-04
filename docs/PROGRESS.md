# 开发进展（Progress）

> 实时更新。每条记录格式：`- [日期] 阶段 / 内容`。每次里程碑结束更新"总览表"。

## 总览

| Phase | 内容 | 状态 |
| --- | --- | --- |
| P0 | 仓库与工具链骨架 | 完成 |
| P1 | Canonical Schema + Mock 生成器 | 未开始 |
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

## 下一步

Phase 1：Canonical Trace Schema（Pydantic）+ 参考 Mock 生成器（TDD）。