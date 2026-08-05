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

## 下一步

Phase 5：LLM-as-a-Judge（OpenAI 兼容 Provider + 结果级/全过程级分析器 + Mock 驱动测试）。