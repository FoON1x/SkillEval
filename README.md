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
- 测试：pytest（后端 151 例）· Vitest（前端 24 例）· Playwright（E2E 5 例）

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

opencode 真实事件流格式（`docs/SCHEMA.md §7`，每行为 JSONL 的一个事件）：

```powershell
curl -X POST http://127.0.0.1:8000/api/ingest/import -H "Content-Type: application/json" -d '{
  "agent": "opencode",
  "raw": {
    "session_id": "ses-1",
    "skill_name": "demo-skill",
    "events": [
      {"type": "step_start", "timestamp": 1787496800000, "sessionID": "ses-1",
       "part": {"id": "p1", "messageID": "m1", "sessionID": "ses-1", "type": "step-start"}},
      {"type": "tool_use", "timestamp": 1787496802000, "sessionID": "ses-1",
       "part": {"type": "tool", "tool": "bash", "callID": "c1",
                "state": {"status": "completed", "input": {"command": "ls"}, "output": "a.txt",
                          "metadata": {"exit": 0}, "title": "ls",
                          "time": {"start": 1787496802000, "end": 1787496805000}},
                "id": "p2", "sessionID": "ses-1", "messageID": "m1"}},
      {"type": "step_finish", "timestamp": 1787496805000, "sessionID": "ses-1",
       "part": {"id": "p3", "reason": "stop", "messageID": "m1", "sessionID": "ses-1",
                "type": "step-finish", "tokens": {"total": 100, "input": 80, "output": 20}, "cost": 0.001}}
    ]
  }
}'
```

开发联调也可直接生成 Mock Trace（`skill_eval.mock.generator`，5 种确定性形态）或调
`POST /api/ingest/push` 推送完整 Canonical Trace。

### 运行 opencode CLI 并抓取 Trace

在 `http://localhost:5173/run` 选择 Skill（下拉来自已安装的 opencode skill）、Agent、工作目录，
输入 prompt 后点「运行」。后端 spawn `opencode run --format json --auto`，通过 SSE 实时推送事件到
前端，运行结束自动入库并跳转到 Trace 详情页——便于快速调试 skill。opencode skill 由模型按需自动
触发，所选 skill 的引导语会注入 prompt 以提高命中（无法强制触发）。

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
- **CLI 触发运行**：`POST /api/runner/run`（同步）或 `/api/runner/run/stream`（SSE 实时流）；前端 `/run` 页直接运行，opencode CLI 未安装时返回 503。

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/ingest/import` | 按 Agent 适配器解析并入库原始事件流 |
| POST | `/api/ingest/push` | 接收 Canonical Trace 并入库 |
| POST | `/api/runner/run` | 触发 Agent CLI 运行（同步） |
| POST | `/api/runner/run/stream` | 触发 Agent CLI 运行（SSE 实时事件流，结束返回 trace_id） |
| GET | `/api/runner/skills` | 列出已安装的 opencode skill（name/description） |
| GET/POST/PUT/DELETE | `/api/traces` `/api/test-cases` `/api/eval-runs` | 数据 CRUD（列表支持过滤 + 分页） |
| POST | `/api/eval/run` | 对指定 Trace 运行指定用例评测 |
| POST | `/api/judge/result` `/api/judge/process` | LLM 结果级 / 全过程级评测 |

完整 OpenAPI 文档：后端启动后访问 `http://127.0.0.1:8000/docs`；前端类型由 `apps/api/scripts/export_openapi.py` 生成。

## 测试

```powershell
cd apps/api && uv run pytest          # 后端 151 例
cd apps/web && npm test               # 前端 24 例
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

- **opencode Trace 格式已回填真实样例**：适配器消费 `opencode run --format json` 的 JSONL 事件流（详见 `docs/SCHEMA.md §7`）
- codex / claude code / pi：仅骨架适配器（导入会返回未实现错误），待样例确认后实现
- 无鉴权的本地单机工具；LLM 密钥仅存环境变量，不入库
- 路线图：100+ 节点性能优化、OpenAPI 漂移 CI 检查、一键启动脚本
