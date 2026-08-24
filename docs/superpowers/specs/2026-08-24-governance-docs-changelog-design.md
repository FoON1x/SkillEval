# 设计规格：文档机制 + CHANGELOG + AGENTS.md 规范化

- **状态**：待审阅
- **日期**：2026-08-24
- **范围**：根 + `docs/`（纯文档/治理，无代码改动）
- **关联**：本规格为「规格2」，独立于规格1（前端重构 + 模型/提供商选择）。规格1 的实现成果（0.3.0）将作为 CHANGELOG 首个完整版本节的重要来源。

## 1. 背景与问题

经文档与治理审查（`docs/`、`AGENTS.md`、git log）发现：

1. **无 CHANGELOG**：仓库无 `CHANGELOG.md`/`HISTORY.md`。`docs/PROGRESS.md` 是自由叙述的开发进展日志（按 Phase 的叙事），非结构化变更日志，无版本号、无 Added/Changed/Fixed 分节、无发布分组。
2. **文档机制未固化**：`AGENTS.md`「文档」节仅一句指针（"文档驱动开发，改动相关模块时对照对应文档"），未列出文档清单、未定义各文档的更新触发条件、未记录 superpowers 规格/计划工作流。`docs/superpowers/specs/` 此前不存在（规格1 首次创建）。
3. **提交约定与实际背离**：`AGENTS.md`「版本控制」节规定中文 conventional commits（`feat(<范围>): commend`），但 git 历史 18 条提交绝大多数为英文（仅 1 条中文）。约定与实际不一致，新协作者无所适从。
4. **关键决策分散**：i18n 语言、设计系统配色、深色模式策略、运行页 `model` 字段格式、UI 原语层等决策散落在规格1 与对话中，未沉淀到全局约定文件，后续易重复决策。
5. **代码审查无归档**：本次代码审查的结论（前端/后端问题清单）未落文档，后续审查会重复排查相同问题。
6. **PLAN.md 落后**：`docs/PLAN.md` 仅到 Phase 7，而 `docs/PROGRESS.md` 已有 Phase 8 规划，二者不同步。

## 2. 目标与非目标

### 目标
- G1：新建根 `CHANGELOG.md`，Keep-a-Changelog 格式 + semver，回填 0.1.0 / 0.2.0，并写入 0.3.0（本次重构）。
- G2：每节不只记"做了什么"，还记**决策原因**（避免后续重复决策）。
- G3：扩充 `AGENTS.md`：新增「文档机制」节（文档清单 + 更新触发 + superpowers 工作流）、「变更日志约定」节、关键技术约定（i18n/设计系统/运行页 model/新端点）。
- G4：调和提交约定：明确自 0.3.0 起严格执行中文提交，历史不重写。
- G5：新建 `docs/README.md` 文档索引导航。
- G6：新建 `docs/CODE_REVIEW.md` 归档代码审查结论（已处理清单 + 残留项）。
- G7：明确 `docs/PROGRESS.md`（开发进展叙述）与 `CHANGELOG.md`（发布变更日志）分工；同步 `docs/PLAN.md` 与 PROGRESS 的 Phase 进度。

### 非目标
- 不重写 git 历史（不 reword 过往英文提交）。
- 不引入文档生成工具（mkdocs/docsify 等）；纯 Markdown。
- 不改动代码（纯文档任务）。
- 不把 `docs/PROGRESS.md` 删除或合并入 CHANGELOG（二者分工保留）。

## 3. 设计决策（已与用户确认）

| 决策点 | 选定 | 理由 |
|---|---|---|
| CHANGELOG 形态 | Keep-a-Changelog + semver，根 `CHANGELOG.md` | 行业标准，便于审计；semver 表达破坏性/功能/修复 |
| 历史回填 | 回填 0.1.0（骨架）+ 0.2.0（opencode 运行+Trace）+ 0.3.0（本次重构） | 一处览全貌，审计完整 |
| 文档机制固化 | AGENTS.md 加节 + 新建 `docs/README.md` 索引 | 双管齐下：约定进 AGENTS，导航进 docs/README |
| 版本号 | 0.2.0 → 0.3.0（minor） | 新增功能、无破坏性 schema 改动 |

## 4. CHANGELOG.md 设计

根 `CHANGELOG.md`，顶部 Keep-a-Changelog 说明 + semver 链接，版本倒序（新在上）。

```
# 变更日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.3.0] - 2026-08-24

### 新增
- 前端 UI 原语层 `components/ui/`（Button/Input/Select/Badge/Card/Field/Modal/Toast/EmptyState/Spinner）
- 深色模式三态切换（浅/深/系统）+ localStorage 持久化 + prefers-color-scheme 跟随
- 运行页提供商→模型级联下拉（提交 model=provider/model）
- 运行页路径浏览模态（后端 GET /api/fs/browse）
- 后端 GET /api/runner/models（shell `opencode models`）
- 根 CHANGELOG.md、docs/README.md、docs/CODE_REVIEW.md

### 变更
- 主题 token 由暖石色切换为 slate/靛蓝（@custom-variant dark + .dark token 覆盖）
- 全前端文案统一中文（保留产品术语 Trace/Skill/Agent/DAG/Token/Cost/Prompt）
- 6 页 + 4 组件迁移至 UI 原语
- SSE 抽离为 api.postStream + AbortController 加固
- AGENTS.md 扩充文档机制/变更日志/技术约定节

### 修复
- SSE 无 AbortController 导致卸载泄漏（已加固）
- 后端 --model 转发未测试（已补断言）

### 决策记录
- 选 slate/靛蓝：经 3 个静态 demo（暖石/冷色/暗色优先）比对，冷色开发者工具风最契合
- 不加 provider 字段：opencode CLI 用 provider/model 合并格式，单一 model 字段足够
- i18n 统一中文无库：与文档体系一致，最轻量；双语若需另开规格

## [0.2.0] - 2026-08-23

### 新增
- opencode CLI 运行 + 实时 SSE 流抓取 Trace（运行页 /run）
- opencode 真实 JSONL 格式适配器（_TraceBuilder.feed/finalize）
- OpencodeRunner.run_stream（subprocess + watchdog + opencode export enrich）
- GET /api/runner/run/stream（SSE）、GET /api/runner/skills（技能列举）
- 一键启停脚本 scripts/start-all.{ps1,sh}、stop-all.{ps1,sh}

### 变更
- 重写 opencode 适配器为真实 JSONL 事件流（step_start/text/tool_use/step_finish）

### 决策记录
- 采集方案 A（CLI subprocess + SSE）+ A2（适配器单一事实源）
- skill 注入引导语而非强制（opencode skill 由模型自动触发）

## [0.1.0] - 2026-08-04

### 新增
- 单仓骨架：apps/api（FastAPI）+ apps/web（Vite/React）
- 核心 Trace Schema（Pydantic 单一事实源，OpenAPI→TS 同步）
- 可插拔导入注册表 + opencode 适配器骨架 + Runner 抽象
- SQLite 持久化（JSON 列 + 索引投影）
- 四规则评测引擎 + 沙箱断言
- LLM-as-a-Judge（结果级 + 过程级）
- 前端可视化（DAG/时间线/详情/成本/Diff）
- Playwright E2E
```

> 注：0.3.0 节内容在规格1 实现完成后据实补充/校正；此处为预期草案。

## 5. AGENTS.md 扩充设计

在现有 AGENTS.md 基础上新增/修订以下节（保持中文、高信号风格）：

### 5.1 新增「文档机制」节（置于「文档」节之后或合并）
- **文档清单**：表格列 `README.md` / `AGENTS.md` / `CHANGELOG.md` / `docs/REQUIREMENTS.md` / `docs/PLAN.md` / `docs/PROGRESS.md` / `docs/ADR.md` / `docs/SCHEMA.md` / `docs/CODE_REVIEW.md` / `docs/README.md` / `docs/superpowers/specs/*` / `docs/superpowers/plans/*`，每个一行用途。
- **更新触发**：改 Schema 必更 `docs/SCHEMA.md` + 重新生成 OpenAPI 类型；改架构决策必更 `docs/ADR.md`（新增 ADR 或标记旧 ADR Superseded）；完成 Phase 必更 `docs/PROGRESS.md`；发布节点必更 `CHANGELOG.md`；改端点必更 `README.md` API 概览。
- **superpowers 工作流**：较大改动走「头脑风暴 → `specs/YYYY-MM-DD-<topic>-design.md` → `plans/YYYY-MM-DD-<topic>.md` → 执行」；规格与计划分开提交，便于审查与模型切换。

### 5.2 新增「变更日志约定」节
- 何时更新：每次较大更新（新功能/破坏性改动/重要修复）必在 `CHANGELOG.md` 新增或更新版本节。
- semver：破坏性 → major；新功能 → minor；修复 → patch。
- 决策原因：每节附「决策记录」子节，记录关键选型理由（避免后续重复决策）。
- 发布可选打 git tag `v<版本>`。

### 5.3 修订「版本控制」节（调和）
- 保留：减少不必要 commit、commit 前请求用户审查、提交信息中文 `feat(<范围>): <描述>`。
- **新增**：自 0.3.0 起严格执行中文提交信息；历史英文提交不重写（rebase 风险 > 收益）。

### 5.4 新增「关键技术约定」节（保持全局统一）
- **i18n**：前端统一中文，保留产品术语（Trace/Skill/Agent/DAG/Token/Cost/Prompt/SSE/CLI）；不引入 i18n 库；双语若需另开规格。
- **设计系统**：slate/靛蓝语义 token（`index.css` `@theme`）；深色模式 = `@custom-variant dark` + `.dark` token 覆盖 + 三态切换；通用 UI 原语在 `apps/web/src/components/ui/`，页面禁内联重复按钮/输入/选择/徽章/卡片标记。
- **运行页 model 字段**：提交格式 `provider/model`（合并），无独立 provider 字段；对应 opencode CLI `--model provider/model`。
- **后端端点**：`GET /api/runner/models`（列举模型）、`GET /api/fs/browse?path=`（目录列举，供路径选择）。

## 6. docs/README.md 设计

文档索引导航页：分组列出所有文档，每项一行说明 + 相对链接。
- **根**：README.md（项目总览/快速开始）、AGENTS.md（会话约定）、CHANGELOG.md（变更日志）
- **docs/**：REQUIREMENTS / PLAN / PROGRESS / ADR / SCHEMA / CODE_REVIEW
- **docs/superpowers/**：specs/（设计规格）、plans/（实现计划）

## 7. docs/CODE_REVIEW.md 设计

代码审查归档：
- **审查范围**：`apps/web` + `apps/api`（runner/ingest 子系统重点）
- **已处理（在规格1 覆盖）**：前端无 UI 原语（重复标记）→ 已抽 `components/ui/`；无深色模式 → 已加三态；中英文混杂 → 已统一中文；SSE 无 AbortController → 已加固；后端 `--model` 转发未测 → 已补断言；`providerID` 丢弃 → 标注可选记入 Trace.extra；无模型列举 → 已加端点。
- **残留项**：`opencode models --verbose` 输出格式跨版本稳定性待观察；Tailwind v4 `@custom-variant dark` 写法在不同构建版本表现待验证。
- **避免重复**：后续审查先读本文件，跳过已处理项。

## 8. PROGRESS.md / PLAN.md 同步

- `docs/PROGRESS.md` 顶部加注：「本文件为开发进展叙述；正式发布变更日志见根 `CHANGELOG.md`」。Phase 进度继续入此。
- `docs/PLAN.md`：补 Phase 8 条目对齐 PROGRESS（概述本轮前端重构 + 治理工作，引用 specs/plans）。
- 二者分工：PROGRESS = 过程叙事（按 Phase / 日期），CHANGELOG = 发布快照（按版本 / Added/Changed/Fixed）。

## 9. 测试与验证

- 纯文档任务，无单测。
- 验证清单：
  - [ ] `CHANGELOG.md` 含 0.1.0/0.2.0/0.3.0 三节，每节有决策记录
  - [ ] `AGENTS.md` 含文档机制/变更日志/关键技术约定节，命令与测试计数与实际一致
  - [ ] `docs/README.md` 链接全部有效
  - [ ] `docs/CODE_REVIEW.md` 已处理/残留清单完整
  - [ ] `docs/PROGRESS.md` 顶部分工注记到位
  - [ ] `docs/PLAN.md` 与 PROGRESS 的 Phase 进度对齐
  - [ ] 提交信息中文

## 10. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 0.3.0 节为预期草案，实现后需校正 | 标注为草案；规格1 完成后据实更新（在规格1 Task 16 或本规格实现时校正） |
| AGENTS.md 测试计数/命令与实际漂移 | 验证步骤交叉比对实际 `uv run pytest`/`npm test` 计数与命令 |
| 文档链接失效 | docs/README.md 验证步骤逐一核对相对路径 |
| 历史回填遗漏 | 0.1.0/0.2.0 从 PROGRESS.md + git log 提炼，关键决策对照 ADR |
