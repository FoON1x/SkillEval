# SkillEval

面向 AI Agent / Skill 开发者的测试与调试平台。第一版聚焦 **Skill Trace 的采集、可视化与评测**：
可插拔接入 opencode / codex / claude code / pi 的运行时 Trace，统一建模、持久化、可视化，
并支持规则评估（strict / unordered / subset / superset + 自定义断言）与 LLM-as-a-Judge。

> 状态：规划阶段（Phase 0 待启动）——需求与技术栈已确认，尚未编写业务代码。

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 可插拔 Trace 采集 | 文件导入 + 运行时 Hook/推送 双通道；各 Agent 经适配器归一为 Canonical Schema（见 `docs/SCHEMA.md`） |
| Trace 可视化 | Trace DAG / 时间线渲染，现代极简 UI（参考 Figma / Anthropic 设计语言） |
| 持久化与 Diff | SQLite 持久化历史 Trace，前后版本结构级对比 |
| 测试用例 + Evaluator | 创建/导入用例（输入 + 期望 Trace 路径）；strict / unordered / subset / superset + 自定义断言 |
| LLM-as-a-Judge | OpenAI 兼容 Provider，结果级 + 全过程级两种分析 |
| 成本 / 延迟 | 有 usage 元数据则展示，缺失自动跳过 |

## 技术栈（已确认 · 方案 B）

- 后端：Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy + SQLite
- 前端：React 19 + TypeScript + Vite + Tailwind CSS + React Flow
- 跨语言 Schema：以 Python Pydantic 为单一事实源，经 OpenAPI 自动生成 TS 类型
- 测试：pytest（后端）/ Vitest + Playwright（前端与 E2E）

## 目录结构

```
skilleval/
├── docs/            # 需求、计划、进展、Schema、架构决策 — 文档驱动
│   ├── REQUIREMENTS.md
│   ├── PLAN.md
│   ├── PROGRESS.md
│   ├── SCHEMA.md
│   └── ADR.md
├── apps/
│   ├── api/         # FastAPI 后端（采集 / 持久化 / 评测 / LLM Judge）
│   └── web/         # React 前端（可视化 / 用例管理 / Diff）
└── packages/        # 预留共享产物（如生成的 TS 类型）
```

## 文档索引

| 文档 | 内容 |
| --- | --- |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | 需求分析（已确认项 + 风险 + 验收标准） |
| [docs/PLAN.md](docs/PLAN.md) | 执行计划（里程碑 / 任务 / TDD 规范） |
| [docs/PROGRESS.md](docs/PROGRESS.md) | 开发进展与变更日志 |
| [docs/SCHEMA.md](docs/SCHEMA.md) | Canonical Trace Schema（v0.1 草案 + 示例） |
| [docs/ADR.md](docs/ADR.md) | 架构决策记录 |

## 快速开始（开发模式）

```powershell
# 后端（Python 3.12）
cd apps/api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn skill_eval.main:app --reload --port 8000
# 冒烟：curl http://127.0.0.1:8000/health

# 前端（Node 20+）
cd apps/web
npm install
npm run dev   # http://localhost:5173
```

测试：后端 `cd apps/api && .\.venv\Scripts\python.exe -m pytest`；前端 `cd apps/web && npm test`。