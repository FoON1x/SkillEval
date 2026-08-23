# AGENTS.md

面向在 SkillEval 仓库中工作的 OpenCode 会话。仅收录从配置/脚本推断出的高价值事实，省略可从文件名直接看出或通用常识。

## 项目概览

SkillEval：AI Agent / Skill 的 Trace 采集、可视化、评测（规则 + LLM-as-a-Judge）平台。单机本地、无鉴权、数据落 SQLite。详见 `README.md`。

## 仓库边界

- **两个独立应用，无根级 workspace**：`apps/api`（Python 3.12 / FastAPI / Pydantic v2 / SQLAlchemy / SQLite，由 `uv` 管理）与 `apps/web`（React 19 / TS / Vite / Tailwind v4 / React Flow）。仓库根没有 `package.json`，也没有 `uv` workspace 配置——两边各自独立构建/测试。
- `packages/` 当前为空，忽略。
- 后端入口：`skill_eval.main:app`（由 `skill_eval/app.py` 的 `create_app()` 组装）。路由按领域分：`ingest` / `runner` / `store` / `eval` / `judge`；`app.state.store` 与 `app.state.judge_client` 在工厂中注入。包版本在 `app.py` 为 `0.2.0`（README 的 "v1" 指交付里程碑，非包版本）。

## 开发命令

```powershell
# 后端（在 apps/api 下；pytest 的 pythonpath=["."]，必须在该目录运行）
uv sync
uv run uvicorn skill_eval.main:app --reload --port 8000

# 前端（在 apps/web 下）
npm install
npm run dev          # http://localhost:5173
```

## 测试与验证

```powershell
# 后端（apps/api）—— 140 例
uv run pytest
uv run pytest tests/test_rules.py            # 单文件
uv run pytest tests/test_rules.py::test_xxx  # 单用例

# 前端（apps/web）
npm test              # vitest run，20 例
npm run test:watch    # 监听
npm run test:e2e      # Playwright E2E，5 例

# 前端类型检查（无独立 typecheck 脚本，build 含 tsc）
npx tsc -b
```

- **未配置 lint 脚本**：`apps/api/pyproject.toml` 有 `[tool.ruff]`（line-length 100，py312）但 ruff 不在依赖中；需要时用 `uvx ruff check apps/api`。前端无 lint 脚本。
- **E2E 自动拉起前后端**（见 `apps/web/playwright.config.ts`）：
  - 用 `apps/api/.venv/Scripts/python.exe`（Windows venv 布局）起后端——**必须先在 `apps/api` 跑过 `uv sync`**，否则 E2E 失败。
  - `reuseExistingServer: false`，不会复用你正在运行的服务；运行前清空 `apps/api/data/e2e.db*`，并以 `SKILLEVAL_DB_URL=sqlite:///data/e2e.db` 启动。
  - `channel: 'chromium'` 复用完整 Chromium，规避 Windows 下 headless-shell 下载超时。

## 架构约束（改动前必读）

- **Schema 单一事实源**（ADR-002）：Canonical Trace 只在 `apps/api/skill_eval/core/schema.py` 用 Pydantic 定义。新增/改字段必须先改 Python，再同步前端类型——**不要手改 `apps/web/src/api/types.generated.ts`**，它是生成产物。
- **OpenAPI → TS 类型同步流程**（无 npm 脚本，手动执行）：
  1. `cd apps/api && uv run python scripts/export_openapi.py ../web/openapi.json`（用 in-memory store 导出 JSON）
  2. `cd apps/web && npx openapi-typescript openapi.json -o src/api/types.generated.ts`
  - `apps/web/openapi.json` 与 `src/api/types.generated.ts` 均为提交的构建产物。
- **`skill_eval/eval/` 保持纯逻辑、无 I/O**（ADR-004）：规则评估与自定义断言可单测、可离线。自定义断言在受限沙箱运行（subprocess + 超时 + 资源限制，禁止文件/网络）。
- **存储模型**（ADR-003）：Trace 本体存 JSON 列，索引列仅存查询投影（agent/skill/session/time/status）。Diff 在内存中基于 Schema 对象计算。
- **采集双通道 + Runner 抽象**（ADR-005）：导入适配器 `parse(raw) -> Trace` 按 agent 注册；推送端点组装增量事件；Runner 抽象 `run(context) -> run_id + events`。**目前仅 opencode 适配器/运行器已实现**，codex / claude code / pi 为骨架（导入返回未实现错误）。

## 环境变量

| 变量 | 作用 | 默认 |
| --- | --- | --- |
| `SKILLEVAL_DB_URL` | 后端数据库 URL（`sqlite:///path`） | `sqlite:///data/skilleval.db`（相对 `apps/api` cwd） |
| `SKILLEVAL_LLM_BASE_URL` | LLM Judge 的 OpenAI 兼容接口 | `https://api.openai.com/v1` |
| `SKILLEVAL_LLM_API_KEY` | LLM 密钥；未配置时 judge 端点返回 503，不影响其他功能 | 无 |
| `SKILLEVAL_LLM_MODEL` | LLM 模型名 | `gpt-4o-mini` |
| `VITE_API_BASE` | 前端请求的后端地址 | `http://127.0.0.1:8000` |

- LLM 密钥仅存环境变量，不入库。
- 后端 CORS 仅放行 `http://localhost:5173` 与 `http://127.0.0.1:5173`。
- `data/`、`*.db`、`.env*` 均在 `.gitignore`。

## 文档

架构决策与 Schema 细节见 `docs/ADR.md`、`docs/SCHEMA.md`；需求/计划/进展见 `docs/REQUIREMENTS.md`、`docs/PLAN.md`、`docs/PROGRESS.md`。文档驱动开发，改动相关模块时对照对应文档。
