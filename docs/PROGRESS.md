# 开发进展（Progress）

> 实时更新。每条记录格式：`- [日期] 阶段 / 内容`。每次里程碑结束更新"总览表"。

## 总览

| Phase | 内容 | 状态 |
| --- | --- | --- |
| P0 | 仓库与工具链骨架 | 完成 |
| P1 | Canonical Schema + Mock 生成器 | 完成 |
| P2 | 采集层（导入 + 推送 + 运行器抽象） | 完成 |
| P3 | 持久化与数据 API | 完成 |
| P4 | 评测引擎 + 断言 | 完成 |
| P5 | LLM-as-a-Judge | 完成 |
| P6 | 前端可视化 | 完成 |
| P7 | opencode CLI 运行抓 Trace（Run 页 + SSE） | 完成 |
| P8 | 打磨与收尾 | 未开始 |

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

## Phase 2 · 采集层（完成）

- `ingest/registry.py`：可插拔注册表（register/get/parse），默认注册 opencode + codex/claude-code/pi 骨架。
- `ingest/adapters/opencode.py`：v1 假设格式解析（session/agent/tool 事件配对、未配对标记 running、未知事件忽略并警告、结构错误 ParseError）。
- `ingest/adapters/skeletons.py`：骨架适配器统一抛 ParseError（pending 真实样例）。
- `runner/`：Runner 抽象（RunContext + available + run），opencode 运行器探测 CLI 可用性；POST /api/runner/run 错误路径 404/503/501。
- API：POST /api/ingest/import（适配器解析）、POST /api/ingest/push（校验并接收 Canonical Trace）。
- TDD 59 用例全绿。

## Phase 3 · 持久化与数据 API（完成）

- `store/`：SQLAlchemy 2 模型（traces / test_cases / eval_runs），JSON 列承载 Canonical Trace；Store 仓库（save/get/list 过滤分页/delete + upsert 去重）；内存 SQLite 供测试。
- 数据 API：GET/POST/PUT/DELETE /api/traces、/api/test-cases、/api/eval-runs；历史查询（agent/skill/status/trace_id/rule 过滤 + 分页）。
- ingest 接入持久化：import/push 均入库（响应含 saved）；CORS 放行前端 dev 端口。
- 已知说明：import 的响应结构不变，新增 saved/id 字段；push 契约含 saved。
- TDD 79 用例全绿。

## Phase 4 · 评测引擎 + 断言（完成）

- `eval/rules.py`：strict（序列全等+错位明细）/ unordered（多重集相等）/ subset（不得有期望外工具）/ superset（必须覆盖必需工具），输出 missing/unexpected/mismatches。
- `eval/sandbox.py`：受限 Python 断言（子进程 + 超时 + builtins 白名单），支持表达式或 `result=` 语句块；工具对象提供属性访问；异常/语法错误/超时均转化为失败信息。
- `eval/service.py`：rule + 断言综合评分 score=(规则通过+断言通过)/(1+断言数)。
- `eval/api.py`：POST /api/eval/run 评测并持久化 EvalRun（passed/failed/error），异常路径不阻塞。
- TDD 120 用例全绿（本轮揪出：沙箱作用域问题、Mock 工具名序列假设）。

## Phase 5 · LLM-as-a-Judge（完成）

- `judge/client.py`：OpenAI 兼容 chat/completions 客户端（base_url/api_key/model 可配置，默认读 SKILLEVAL_LLM_* 环境变量），错误映射 LLMError。
- `judge/analyzers.py`：JudgeReport 固定 JSON 结构（score/verdict/summary/findings + raw 兜底）；ResultJudge（结果级）+ ProcessAnalyzer（全过程级，Trace digest：工具序列/状态/错误/usage）。
- `judge/api.py`：POST /api/judge/result 与 /api/judge/process，结果以 eval-run 持久化（rule=llm-result/llm-process，verdict 映射 passed/failed/review）；未配置 503、无最终输出 400、未知 trace 404。
- DTO 扩展：RuleName 增加 llm-result/llm-process，EvalResult 增加 review。
- TDD 138 用例全绿（MockTransport 验证请求构造 + Fake LLM 驱动分析器/API）。

## Phase 6 · 前端可视化（完成）

- 依赖：tailwindcss + @tailwindcss/vite、@xyflow/react（React Flow）、react-router-dom、recharts；openapi-typescript + @playwright/test。
- 类型链路：FastAPI 导出 openapi.json（scripts/export_openapi.py）→ openapi-typescript 生成 src/api/types.generated.ts；src/api/client.ts fetch 封装（BASE 可经 VITE_API_BASE 覆盖）。
- 设计基础：Tailwind v4 @theme token（canvas/surface/line/ink/muted/faint/accent/accent-soft/ok/bad/wait/skip），Anthropic 风格侧边栏布局。
- 工具函数（TDD）：utils/trace.ts（flattenTree / buildTimeline / traceStats / nodeTitle / statusColor，traceStats 聚合节点级 llm usage 兜底 trace.usage）、utils/diff.ts（LCS 序列 diff + 参数 diff + projectTrace）。
- 页面与组件：/traces 列表（Agent/状态过滤）、/traces/:id 详情（React Flow DAG + Timeline + DetailPanel + CostPanel + LLM 结果级/全过程按钮）、/test-cases 用例管理（新建/评测/删除）、/eval-runs 评测记录、/diff 双 Trace 对比（?from= 预选基线）。
- 后端补充：opencode 适配器支持 llm.start/llm.end 事件（LLM_CALL 节点 + LlmUsage 聚合，未配对报错）——后端 140 用例全绿。
- 质量：前端 vitest 20 用例 + tsc --noEmit + vite build 全绿；Playwright E2E 5 用例全绿（chromium headless 用 channel=chromium，避免 headless-shell 下载）。
- 说明：Windows 下 Playwright 默认下载 headless-shell 常超时，playwright.config.ts 以 use.channel='chromium' 复用完整 chromium；e2e 使用独立 SQLite（data/e2e.db，启动时清理含 WAL）。
- [2026-08-09] 后端虚拟环境迁移至 uv 管理：依赖声明收敛到 pyproject.toml（dependencies + [dependency-groups] dev），删除 requirements*.txt 与旧 .venv，uv sync 生成 uv.lock；`uv run uvicorn ...` 启动、`uv run pytest` 140 用例全绿；README 启动说明同步更新。

## Phase 7 · opencode CLI 运行抓 Trace（完成）

- [2026-08-23] 用真实 `opencode run --format json` JSONL 事件流（`step_start`/`text`/`tool_use`/`step_finish`，epoch-ms 时间戳）回填 opencode 适配器，替换原虚构 v1 假设格式；新增 `TraceBuilder` 增量 API（`feed`/`finalize`），`finalize` 合并 `opencode export` 的权威 trace 级 metadata（title/agent/model/cost/tokens）。失败工具（`metadata.exit!=0`）标 `NodeStatus.ERROR`。
- [2026-08-23] 实现 `OpencodeRunner.run_stream`：spawn `opencode run --format json --auto [--agent] [--session] [--dir] [--model]`，逐行读 JSONL → 喂 `TraceBuilder` → emit 规范化事件 → 进程结束后 `opencode export` enrich → 返回 Trace；非零退出/超时标 `RunState.ERROR`。`RunContext` 新增 `skill_name/cwd/auto/timeout/agent_name/model`。
- [2026-08-23] 新增 SSE 端点 `POST /api/runner/run/stream`（`text/event-stream`，线程+队列：event/done/error 帧）与 `GET /api/runner/skills`（扫描 `~/.agents/skills` + superpowers skills，解析 SKILL.md frontmatter）。
- [2026-08-23] 前端新增 `/run` 页：skill 下拉 / agent 选择 / 工作目录 / `--auto` 开关 / prompt，提交后 fetch+ReadableStream 消费 SSE，实时渲染事件流，done 帧跳转 `/traces/:id`；选中的 skill 注入引导语到 prompt（opencode skill 由模型自动触发，无法强制）。
- [2026-08-23] OpenAPI/TS 类型重生成。后端 151 用例、前端 24 用例全绿。

## 下一步

Phase 8：打磨与收尾（其余 Agent Trace 样例回填、LLM 评测联调、性能/细节优化）。