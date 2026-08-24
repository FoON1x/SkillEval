# 文档机制 + CHANGELOG + AGENTS.md 规范化 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立结构化 CHANGELOG（Keep-a-Changelog + semver，回填历史）、文档索引导航、代码审查归档，并扩充 AGENTS.md 固化文档机制/变更日志/关键技术约定，调和提交约定。

**Architecture:** 纯文档任务，无代码改动。新建 3 个文档 + 扩充 AGENTS.md + 同步 PROGRESS/PLAN。各任务独立可审查。

**Tech Stack:** Markdown。

## Global Constraints

- 所有文档中文（与现有文档体系一致）；保留产品术语原文（Trace/Skill/Agent/DAG/Token/Cost/Prompt/SSE/CLI）。
- 提交信息中文，格式 `docs(<范围>): <描述>`；提交前请求用户审查（AGENTS.md 约定）。
- 测试计数/命令必须与执行时实际一致（运行命令取值，勿硬编码易漂移的数字）。
- 不重写 git 历史。
- 不改动任何代码。

---

### Task 1: 创建根 CHANGELOG.md（回填 + 0.3.0 草案）

**Files:**
- Create: `CHANGELOG.md`

- [ ] **Step 1: 写 `CHANGELOG.md`**

内容按规格2 §4。顶部 Keep a Changelog + semver 说明链接；版本倒序：0.3.0（2026-08-24，标注为"本次重构（实现中）"草案）、0.2.0（2026-08-23）、0.1.0（2026-08-04）。每节含 新增/变更/修复/决策记录 子节。0.3.0 节末加注："本节为规格1/规格2 实现完成后的据实校正前草案。" 0.1.0/0.2.0 从 `docs/PROGRESS.md` 与 git log 提炼关键条目（opencode CLI 运行+SSE+Trace 抓取、一键启停脚本、初始骨架与各子系统）。

- [ ] **Step 2: 校对版本节完整**

确认含 3 个版本节、每节有决策记录；0.2.0 含 opencode 运行/SSE/Trace/启停脚本；0.1.0 含骨架/Schema/采集/存储/评测/Judge/可视化/E2E。

- [ ] **Step 3: 提交**

```bash
git add CHANGELOG.md
git commit -m "docs: 新建 CHANGELOG（Keep-a-Changelog + semver，回填 0.1.0/0.2.0 + 0.3.0 草案）"
```

---

### Task 2: 创建 docs/README.md 文档索引

**Files:**
- Create: `docs/README.md`

- [ ] **Step 1: 写 `docs/README.md`**

按规格2 §6。分组列出：
- **根文档**：`../README.md`（项目总览/快速开始）、`../AGENTS.md`（OpenCode 会话约定）、`../CHANGELOG.md`（变更日志）
- **规划与进展**：`REQUIREMENTS.md`（需求分析 v0.1）、`PLAN.md`（执行计划 Phase 0-8）、`PROGRESS.md`（开发进展叙述）
- **架构与 Schema**：`ADR.md`（架构决策记录 ADR-001~006）、`SCHEMA.md`（Canonical Trace Schema v0.1）
- **审查**：`CODE_REVIEW.md`（代码审查归档）
- **superpowers 工作流**：`superpowers/specs/`（设计规格）、`superpowers/plans/`（实现计划）

每项一行说明 + 相对链接（从 `docs/README.md` 出发，根文档用 `../`）。

- [ ] **Step 2: 校对链接有效**

逐项核对相对路径存在（`Test-Path` 或目测 git 跟踪文件）。

- [ ] **Step 3: 提交**

```bash
git add docs/README.md
git commit -m "docs: 新建文档索引导航 docs/README.md"
```

---

### Task 3: 创建 docs/CODE_REVIEW.md 审查归档

**Files:**
- Create: `docs/CODE_REVIEW.md`

- [ ] **Step 1: 写 `docs/CODE_REVIEW.md`**

按规格2 §7。结构：
- **审查范围**：`apps/web`（前端全量）+ `apps/api`（runner/ingest 重点），审查日期 2026-08-24
- **已处理（在规格1 覆盖）**：逐条列前端/后端问题 → 对应规格1 任务（如"无 UI 原语 → Task 2-3"、"无深色模式 → Task 1"、"中英文混杂 → Task 8-12"、"SSE 无 AbortController → Task 15"、"后端 --model 转发未测 → Task 6"、"providerID 丢弃 → 标注可选"、"无模型列举 → Task 4"）
- **残留项**：`opencode models --verbose` 输出格式跨版本稳定性待观察；Tailwind v4 `@custom-variant dark` 写法在不同构建版本表现待验证
- **使用说明**：后续审查先读本文件，跳过已处理项，仅查残留与新代码

- [ ] **Step 2: 提交**

```bash
git add docs/CODE_REVIEW.md
git commit -m "docs: 归档代码审查结论 docs/CODE_REVIEW.md"
```

---

### Task 4: 扩充 AGENTS.md（文档机制 + 变更日志 + 关键技术约定 + 提交调和）

**Files:**
- Modify: `E:\playground\skilleval\AGENTS.md`

- [ ] **Step 1: 读现有 AGENTS.md**

`read E:\playground\skilleval\AGENTS.md`，定位「文档」「版本控制」节位置。

- [ ] **Step 2: 新增「文档机制」节**（置于「文档」节之后）

内容按规格2 §5.1：文档清单表（README/AGENTS/CHANGELOG/REQUIREMENTS/PLAN/PROGRESS/ADR/SCHEMA/CODE_REVIEW/docs-README/superpowers-specs/superpowers-plans，每个一行用途）、更新触发（改 Schema 必更 SCHEMA+重生成 OpenAPI；改架构决策必更 ADR；完成 Phase 必更 PROGRESS；发布节点必更 CHANGELOG；改端点必更 README API 概览）、superpowers 工作流（头脑风暴→specs→plans→执行，规格与计划分开提交）。

- [ ] **Step 3: 新增「变更日志约定」节**（置于「文档机制」后）

按规格2 §5.2：何时更新 CHANGELOG、semver 规则（破坏性 major/功能 minor/修复 patch）、每节附「决策记录」、发布可选打 tag `v<版本>`。

- [ ] **Step 4: 修订「版本控制」节**

保留原有三条（减少不必要 commit、commit 前请求用户审查、提交信息中文 `feat(<范围>): <描述>`），新增一条："自 0.3.0 起严格执行中文提交信息；历史英文提交不重写（rebase 风险 > 收益）。"

- [ ] **Step 5: 新增「关键技术约定」节**（置于「架构约束」后或文末）

按规格2 §5.4：
- i18n：前端统一中文，保留产品术语；不引入 i18n 库；双语若需另开规格
- 设计系统：slate/靛蓝语义 token（`apps/web/src/index.css` `@theme`）；深色模式 = `@custom-variant dark` + `.dark` token 覆盖 + 三态切换（浅/深/系统）；通用 UI 原语在 `apps/web/src/components/ui/`，页面禁内联重复按钮/输入/选择/徽章/卡片标记
- 运行页 model 字段：提交格式 `provider/model`（合并），无独立 provider 字段；对应 opencode CLI `--model provider/model`
- 后端端点：`GET /api/runner/models`（列举模型，shell `opencode models`）、`GET /api/fs/browse?path=`（目录列举，供路径选择模态）

- [ ] **Step 6: 校对测试计数/命令一致**

运行 `cd apps/api; uv run pytest` 取末行计数；`cd apps/web; npm test` 取计数。更新 AGENTS.md「测试与验证」节的计数为实际值（当前文档可能为 151/24，实际可能为 156+/24——以运行结果为准）。

- [ ] **Step 7: 提交**

```bash
git add AGENTS.md
git commit -m "docs(agents): 扩充文档机制/变更日志/关键技术约定 + 提交约定调和"
```

---

### Task 5: 同步 PROGRESS.md 与 PLAN.md

**Files:**
- Modify: `docs/PROGRESS.md`
- Modify: `docs/PLAN.md`

- [ ] **Step 1: PROGRESS.md 加分工注记**

在 `docs/PROGRESS.md` 顶部标题下加一行："本文件为开发进展叙述；正式发布变更日志见根 `CHANGELOG.md`。"

- [ ] **Step 2: PROGRESS.md 加 Phase 8 进度条目**

在总览表补 Phase 8（前端重构 + 治理）行；在末尾加 Phase 8 叙述段（本轮工作概述，引用 `docs/superpowers/specs/2026-08-24-*.md` 与 `plans/2026-08-24-*.md`）。若 Phase 8 已存在则对齐内容。

- [ ] **Step 3: PLAN.md 补 Phase 8 条目**

在 `docs/PLAN.md` §2 里程碑补 Phase 8 概述条目（前端重构 + 文档治理，引用 specs/plans），与 PROGRESS 对齐。

- [ ] **Step 4: 提交**

```bash
git add docs/PROGRESS.md docs/PLAN.md
git commit -m "docs: PROGRESS/PLAN 同步 Phase 8 + 分工注记"
```

---

### Task 6: 全量验证

**Files:** Verify only

- [ ] **Step 1: 校对 CHANGELOG 三节与决策记录**

确认 0.1.0/0.2.0/0.3.0 节齐全，0.3.0 标注草案，每节有决策记录。

- [ ] **Step 2: 校对 docs/README 链接**

逐项确认相对路径指向的文件存在（`git ls-files docs/` + 根文件）。

- [ ] **Step 3: 校对 AGENTS.md 一致性**

确认：文档清单列出的文件全部存在；测试计数与 `uv run pytest`/`npm test` 实际一致；命令（`uv run uvicorn`/`npm run dev`/pytest 路径要求）与实际一致。

- [ ] **Step 4: 校对 CODE_REVIEW 已处理/残留清单完整**

确认已处理项均映射到规格1 任务；残留项 2 条。

- [ ] **Step 5: 校对提交信息中文**

`git log --oneline -6` 确认本规格各提交信息为中文。

- [ ] **Step 6: 最终提交（若有验证中发现的小修）**

若 Step 1-5 发现需修正，修后提交：
```bash
git commit -am "docs: 校正文档一致性"
```

---

## Self-Review

**1. Spec coverage:** G1 CHANGELOG → Task 1；G2 决策原因 → Task 1（决策记录子节）；G3 AGENTS.md 扩充 → Task 4；G4 提交调和 → Task 4 Step 4；G5 docs/README → Task 2；G6 CODE_REVIEW → Task 3；G7 PROGRESS/PLAN 分工同步 → Task 5。全覆盖。

**2. Placeholder scan:** 无 TBD/TODO；Task 1 的 0.3.0 标注为草案是规格明确决定（非占位）；Task 4 Step 6 测试计数"以运行结果为准"是刻意避免硬编码漂移。

**3. Type consistency:** 纯文档，无类型/签名。文档清单在 Task 2（docs/README）与 Task 4（AGENTS.md 文档机制）列出的文件集一致（README/AGENTS/CHANGELOG/REQUIREMENTS/PLAN/PROGRESS/ADR/SCHEMA/CODE_REVIEW/docs-README/superpowers-specs/plans）。

**4. 依赖顺序:** Task 1-3 可并行（独立新文件）；Task 4 依赖 Task 1-3 文件已存在（文档清单需列 CHANGELOG/README/CODE_REVIEW）；Task 5 独立；Task 6 依赖全部。建议顺序 1→2→3→4→5→6。

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-24-governance-docs-changelog.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
