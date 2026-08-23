# SkillEval

面向 AI Agent / Skill 开发者的**测试与调试平台**：采集 Agent 运行 Trace，统一建模、持久化与可视化，并用
**规则评估 + LLM-as-a-Judge** 自动评测一次运行是否达到预期。

> 状态：**v1 可交付（2026-08）**。单机本地使用，无鉴权，数据落在本地 SQLite。

![Tech: FastAPI · React · SQLite](https://img.shields.io/badge/tech-FastAPI%20·%20React%20·%20SQLite-blue)

## 核心特性

- **Trace 采集（双通道）** — 本地文件/JSON 导入 + 运行时推送；Agent 经适配器归一为 Canonical Schema
  （opencode 已实现，codex / claude code / pi 骨架预留，见 `docs/SCHEMA.md`）
- **Trace 可视化** — Trace DAG（React Flow）+ 时间线 + 节点详情面板，状态着色、错误高亮、缩放平移；
  成本 / Token / 延迟有 usage 数据则展示，缺失自动跳过
- **持久化** — SQLite 存储 Trace / 测试用例 / 评测结果，支持按 Agent、Skill、状态、时间过滤查询
- **评测引擎** — 4 种规则（`strict` / `unordered` / `subset` / `superset`）+ 自定义 Python 断言（受限沙箱），
  综合评分并持久化，可重跑对比
- **LLM-as-a-Judge** — OpenAI 兼容 Provider（OpenAI / DeepSeek / 本地 Ollama 均可），
  结果级（只看最终输出）与全过程级（看完整 Trace）两种分析，输出结构化评分与理由
- **Trace Diff** — 任意两次运行的结构级对比：工具新增 / 缺失 / 顺序变化 / 参数变化
- **CLI 触发运行** — 抽象 Runner 接口 + opencode CLI 运行器（其余 Agent 逐步适配）

## 技术栈

- 后端：Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy + SQLite（依赖由 [uv](https://docs.astral.sh/uv/) 管理）
- 前端：React 19 + TypeScript + Vite + Tailwind CSS v4 + React Flow
- 跨语言 Schema：Pydantic 为单一事实源，OpenAPI 自动生成 TS 类型（`src/api/types.generated.ts`）
- 测试：pytest（后端 140 例）· Vitest（前端 20 例）· Playwright（E2E 5 例）

## 快速开始

前置：Python ≥ 3.12、[uv](https://docs.astral.sh/uv/)、Node ≥ 20。

```powershell
# 1. 启动后端（首次自动创建虚拟环境）
cd apps/api
uv sync
uv run uvicorn skill_eval.main:app --reload --port 8000

# 2. 启动前端
cd apps/web
npm install
npm run dev

# 3. 打开 http://localhost:5173
```

## 使用指南

### 导入一条 Trace

opencode v1 事件流格式（`docs/SCHEMA.md §7`）：

```powershell
curl -X POST http://127.0.0.1:8000/api/ingest/import -H "Content-Type: application/json" -d '{
  "agent": "opencode",
  "raw": {
    "version": "0.1",
    "session_id": "sess-1",
    "skill_name": "demo-skill",
    "events": [
      {"type": "session.start", "ts": "2026-08-04T10:00:00Z"},
      {"type": "agent.start",   "ts": "2026-08-04T10:00:01Z"},
      {"type": "tool.start", "tool": "read_file", "args": {"path": "/a"}, "ts": "2026-08-04T10:00:02Z"},
      {"type": "tool.end",   "tool": "read_file", "result": {"ok": true}, "ts": "2026-08-04T10:00:07Z"},
      {"type": "llm.start",  "model": "claude-sonnet", "input_tokens": 100, "ts": "2026-08-04T10:00:07Z"},
      {"type": "llm.end",    "output_tokens": 50, "cost_usd": 0.001, "latency_ms": 900, "ts": "2026-08-04T10:00:08Z"},
      {"type": "agent.end",  "ts": "2026-08-04T10:00:13Z"},
      {"type": "session.end", "ts": "2026-08-04T10:00:15Z"}
    ]
  }
}'
```

开发联调也可直接生成 Mock Trace（`skill_eval.mock.generator`，5 种确定性形态）或调
`POST /api/ingest/push` 推送完整 Canonical Trace。

### 创建测试用例并评测

在 `http://localhost:5173/test-cases` 新建用例（目标 Agent、期望工具序列、可选 Python 断言），
点击「运行评测」选择一条 Trace 即可；规则通过 + 断言通过合成 `score`，结果记录在「Eval Runs」。

### LLM-as-a-Judge

配置环境变量后，在 Trace 详情页点「LLM 结果级 / LLM 全过程」：

| 变量 | 说明 | 默认 |
| --- | --- | --- |
| `SKILLEVAL_LLM_BASE_URL` | OpenAI 兼容接口地址 | `https://api.openai.com/v1` |
| `SKILLEVAL_LLM_API_KEY` | API 密钥（未配置则返回 503，不影响其他功能） | 无 |
| `SKILLEVAL_LLM_MODEL` | 模型名 | `gpt-4o-mini` |

```powershell
$env:SKILLEVAL_LLM_BASE_URL = "https://api.deepseek.com/v1"
$env:SKILLEVAL_LLM_API_KEY  = "sk-..."
$env:SKILLEVAL_LLM_MODEL    = "deepseek-chat"
```

### Diff 与 CLI 触发

- **Diff**：任一 Trace 详情页点「Diff 对比」，或直接访问 `/diff?from=<trace_id>`，再选另一条 Trace。
- **CLI 触发运行**：`POST /api/runner/run`（body：`agent` / `task` / 可选 `session_id`），由 Runner 调起 Agent CLI
  并回填 Trace；opencode CLI 未安装时返回 503。

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/ingest/import` | 按 Agent 适配器解析并入库原始事件流 |
| POST | `/api/ingest/push` | 接收 Canonical Trace 并入库 |
| POST | `/api/runner/run` | 触发 Agent CLI 运行 |
| GET/POST/PUT/DELETE | `/api/traces` `/api/test-cases` `/api/eval-runs` | 数据 CRUD（列表支持过滤 + 分页） |
| POST | `/api/eval/run` | 对指定 Trace 运行指定用例评测 |
| POST | `/api/judge/result` `/api/judge/process` | LLM 结果级 / 全过程级评测 |

完整 OpenAPI 文档：后端启动后访问 `http://127.0.0.1:8000/docs`；前端类型由 `apps/api/scripts/export_openapi.py` 生成。

## 测试

```powershell
cd apps/api && uv run pytest          # 后端 140 例
cd apps/web && npm test               # 前端 20 例
cd apps/web && npm run test:e2e       # Playwright E2E 5 例（自动拉起前后端）
```

> Windows 提示：Playwright 默认下载 headless-shell 常超时，配置已用 `channel: 'chromium'`
> 复用完整 Chromium（见 `apps/web/playwright.config.ts`）。

## 目录结构

```
skilleval/
├── docs/            # 文档驱动：需求 / 计划 / 进展 / Schema / 架构决策
├── apps/
│   ├── api/         # FastAPI 后端：ingest / runner / store / eval / judge / mock
│   │   └── skill_eval/
│   └── web/         # React 前端：可视化 / 用例管理 / Diff / E2E
```

## 文档索引

| 文档 | 内容 |
| --- | --- |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | 需求分析与验收标准 |
| [docs/PLAN.md](docs/PLAN.md) | 执行计划与 TDD 规范 |
| [docs/SCHEMA.md](docs/SCHEMA.md) | Canonical Trace Schema（v0.1 草案） |
| [docs/PROGRESS.md](docs/PROGRESS.md) | 开发进展与变更日志 |
| [docs/ADR.md](docs/ADR.md) | 架构决策记录 |

## 已知限制与路线图

- **opencode Trace 格式为 v1 假设**：尚未拿到真实样例回填（`docs/SCHEMA.md §7`），真实日志落地后可能调整
- codex / claude code / pi：仅骨架适配器（导入会返回未实现错误），待样例确认后实现
- 无鉴权的本地单机工具；LLM 密钥仅存环境变量，不入库
- 路线图：Trace 导入 UI、100+ 节点性能优化、OpenAPI 漂移 CI 检查、一键启动脚本
