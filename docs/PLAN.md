# 执行计划（Execution Plan）

> 状态：Accepted（2026-08-04）。所有里程碑遵循 TDD：先测试、后实现、跑绿才收。
> 与 REQUIREMENTS.md 一一对应；开发进展实时更新至 PROGRESS.md。

## 1. 架构总览

```
用户 / 开发者
   │  (浏览器 → apps/web · Vite + React)
   ▼
apps/api (FastAPI)
 ├── ingest/      采集层：importers（导入解析）+ push endpoints（推送）
 ├── runner/      CLI 运行器抽象（v1: opencode）
 ├── core/        Canonical Schema（Pydantic，单一事实源）
 ├── store/       持久化（SQLAlchemy + SQLite：trace/test/eval）
 ├── eval/        评测引擎（strict/unordered/subset/superset + 断言沙箱）
 ├── diff/        结构级 Diff
 └── judge/       LLM-as-a-Judge（JudgeClient + ProcessAnalyzer）
        │
        └── OpenAI 兼容 Provider（OpenAI / DeepSeek / Ollama）
```

数据流：Trace 入库（导入或推送或 Runner 触发）→ 前端可视化 → 关联用例评测 → 结果与历史 Diff。

## 2. 里程碑规划

### Phase 0 · 仓库与工具链骨架（基础设施）

- 任务：git 基础提交规范；后端包结构 + 最小 FastAPI app（/health）；前端 Vite 骨架；两端最小测试跑通；文档落盘（本文档即产物之一）。
- TDD：/health 单测 + 前后端 smoke 测试先绿。
- 退出条件：`pytest` 与 `vitest` 全绿，git 提交规范生效。

### Phase 1 · Canonical Trace Schema + Mock 生成器

- 任务：定义 Pydantic Schema（见 SCHEMA.md）；编写参考 Mock Trace 生成器（构造多种形态：成功/失败/多层级/超长序列）。
- TDD：Schema 序列化/反序列化测试；Mock 生成器输出符合 Schema 与边界规则。
- 出口：Schema 稳定，前端可消费生成的 TS 类型（Phase 2 联调）。

### Phase 2 · 采集层（导入 + 推送 + 运行器抽象）

- 任务：导入适配器框架（注册表 + parse 接口）；opencode 导入适配器 + codex / claude code / pi 骨架；推送 HTTP 端点（增量事件 -> Trace 组装）；Runner 抽象 + opencode CLI 运行器（可用性探测，真实接线随 CLI 集成落地）。
- TDD：用 Mock 文件测各适配器解析；推送端点事件流到入库的集成测试；运行器不可用/未知 Agent 的错误路径。
- 出口：Mock/真实文件可一键入库；推送可实时入库。

### Phase 3 · 持久化与 API

- 任务：store 层 models + Repository；Trace/用例/评测 CRUD；历史查询（过滤/分页）；删除与导入去重。
- TDD：Repository 与 API 集成测试（内存 SQLite 或临时库）。
- 出口：前端可消费全部数据接口。

### Phase 4 · 评测引擎 + 断言

- 任务：tool 投影提取；四规则评估器；断言沙箱（受限运行 + 超时）；结果持久化。
- TDD：四规则边界用例（见 REQUIREMENTS 3.4）+ 断言命中/失败测试先行。
- 出口：规则与断言可独立单测全绿。

### Phase 5 · LLM-as-a-Judge

- 任务：OpenAI 兼容客户端（配置化）；Mock LLM 服务（测试用）；结果级 + 全过程级分析器；密钥本地配置。
- TDD：Mock 服务驱动单测；输出 JSON schema 测试。
- 出口：断网/无密钥不阻塞主流程；两种模式输出稳定。

### Phase 6 · 前端可视化

- 任务：UI 基础（Anthropic 风格 token：中性色板/排版）；Trace DAG（React Flow）+ 时间线 + 详情面板；用例管理 + 评测结果视图；Diff 视图；成本/延迟图表（有数据才显示）。
- TDD：组件逻辑 Vitest + Playwright E2E（关键流转：导入 → 可视化 → 评测）。
- 出口：E2E 覆盖主链路。

### Phase 7 · 打磨与收尾

- 一键启动脚本；.gitignore/环境样例；README 快速开始；PROGRESS 收尾；示例用例与示例 Trace。

### Phase 8 · 前端重构 + 文档治理

- 任务（规格 1）：全前端统一中文文案；slate/靛蓝主题 + 深色模式三态；UI 原语层（components/ui/）；运行页提供商→模型级联 + 路径浏览模态 + SSE 加固；后端 GET /api/runner/models 与 /api/fs/browse。
- 任务（规格 2）：根 CHANGELOG（Keep-a-Changelog + semver）；docs/README 文档索引；docs/CODE_REVIEW 归档；AGENTS.md 文档机制/变更日志/技术约定扩充。
- 设计规格：`docs/superpowers/specs/2026-08-24-frontend-overhaul-design.md`、`docs/superpowers/specs/2026-08-24-governance-docs-changelog-design.md`；执行计划：`docs/superpowers/plans/2026-08-24-frontend-overhaul.md`、`docs/superpowers/plans/2026-08-24-governance-docs-changelog.md`。
- 出口：后端 pytest、前端 vitest、`npx tsc -b` 全绿；E2E 覆盖运行页主链路。

## 3. 每阶段通用流程（DoD）

1. 更新 PLAN/PROGRESS。
2. 编写测试（先红）。
3. 最小实现（变绿）。
4. 重构 + 补齐边界。
5. 前端消费联调（涉及 API 时）。
6. 提交（约定式提交，见下）。

## 4. 规范

- 提交信息：`feat(scope): desc`（scope: api/web/eval/judge/ingest/docs）。
- 分支：默认主干开发；重大变更走 feature 分支。
- 文档驱动：REQUIREMENTS / PLAN / PROGRESS / ADR 为事实源，改需求必改文档。
- 禁止：绕过 Schema 直接增字段；提交密钥。