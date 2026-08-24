# 设计规格：前端重构 + 模型/提供商选择

- **状态**：待审阅
- **日期**：2026-08-24
- **范围**：`apps/web`（前端全量）+ `apps/api`（两个新端点）
- **关联**：本规格为「规格1」。规格2（文档机制 + CHANGELOG + AGENTS.md 规范化）独立于本规格。

## 1. 背景与问题

当前前端（`apps/web`）存在以下问题（经代码审查确认）：

1. **中英文混杂**：无 i18n 库，所有字符串为内联字面量，约 60% 中文、其余英文或句内混杂（如 `AI Agent / Skill 测试与 Trace 可视化`）。导航条 5 项中 4 英文 1 中文（`运行`）。
2. **无 UI 原语层**：`components/` 仅 4 个领域组件（TraceDag/Timeline/DetailPanel/CostPanel），无 Button/Input/Select/Badge/Card/Modal 等通用原语；每个页面内联重复 Tailwind 标记（按钮、输入、选择、徽章、卡片容器类串近乎逐字重复）。
3. **无深色模式**：`index.css` 硬编码 `color-scheme: light`；无 `@custom-variant dark`、无 `dark:` 工具类、无 `.dark` 类、无 `prefers-color-scheme` 查询、无切换控件。
4. **路径选取为纯文本输入**：`RunPage.tsx:181-189` 是无校验、无浏览、无自动补全的自由文本框。
5. **运行表单未暴露模型/提供商**：`RunPage` 表单仅 skill/agent/cwd/auto/prompt 五项；后端 `RunContext.model` 与 `StreamRunRequest.model` 已端到端存在并转发为 `--model`，但前端未接入。
6. **SSE 处理脆弱**：`RunPage.tsx:60-120` 内联 ~35 行 SSE 解析，无 `AbortController`（卸载/中途导航泄漏 reader），中途断流无错误提示。
7. **缺失交互状态**：无 Toast 反馈、空列表无 EmptyState、加载无 Spinner/骨架。

## 2. 目标与非目标

### 目标
- G1：全前端文案统一为中文（专有名词 Trace/Skill/Agent/DAG/Token/Cost/Prompt 作为产品术语保留原文）。
- G2：抽取 `components/ui/` 通用原语，6 页 + 4 组件迁移其上，消除内联重复。
- G3：新增深色模式（token 覆盖 + 三态切换 + 持久化 + 系统跟随）。
- G4：整体美化，采用方案2「冷色开发者工具」美学（slate + 靛蓝 accent），补齐 空/加载/错误/Toast 状态。
- G5：运行页新增 提供商→模型 级联下拉，提交时拼 `provider/model` 发给后端 `model` 字段。
- G6：运行页新增路径浏览模态（后端目录列举端点 + 前端模态目录树）。
- G7：SSE 加固（抽到 `client.ts` 的 `api.postStream`，加 `AbortController`，补断流错误）。
- G8：后端新增 `GET /api/runner/models` 与 `GET /api/fs/browse`，不改 `RunContext`/`StreamRunRequest` schema。

### 非目标
- 不做中英双语运行时切换（统一中文；双语若需另开规格）。
- 不引入 i18n 库（直接翻译内联字面量）。
- 不为 `RunContext`/`StreamRunRequest` 新增 `provider` 字段（CLI 用 `provider/model` 合并格式，单一 `model` 字段足够）。
- 不重写 React Flow DAG / 评测规则 / Diff 逻辑等领域功能，仅迁移其 UI 外壳与文案。
- 不改动后端存储 / 评测 / Judge 子系统。

## 3. 设计决策（已与用户确认）

| 决策点 | 选定 | 理由 |
|---|---|---|
| i18n 语言 | 统一中文，无库 | 与文档体系一致；最轻量；解决混杂问题 |
| 路径选取 | 后端浏览端点 + 模态选择器 | 浏览器原生 API 不返回真实绝对路径；需真实 cwd 传给 `--dir` |
| 模型/提供商 UI | 提供商→模型 级联下拉 | 模型多时体验最好；客户端过滤无需二次请求；提交拼 `provider/model` |
| 深色模式 | token 覆盖 + 三态切换 | 现有语义 token 已就位，覆盖整组 token 组件几乎不动；三态（浅/深/系统）为现代美观模式 |
| UI 美学 | 方案2 冷色开发者工具（slate + 靛蓝） | 用户比对 3 个静态 demo 后选定 |
| 实现策略 | 方案A 地基优先 | 原语/token/i18n 是基底，一次建好再迁页面最省返工 |

## 4. 架构与分层

三层工作，依序推进（实现计划将细化为任务）：

```
地基层（Foundation）
├─ components/ui/      UI 原语
├─ index.css           slate/靛蓝 token + @custom-variant dark + .dark token 覆盖
├─ theme/ThemeProvider  三态切换 + localStorage + prefers-color-scheme
└─ 文案中文化          内联字面量翻译（无 i18n 库）

页面迁移（Migration）
├─ 6 页面 → 引用原语、套用新 token（自动）、文案中文化、补齐状态
└─ 4 领域组件 → 同上

运行页新功能（Run page features）
├─ 提供商→模型级联下拉（GET /api/runner/models）
├─ 路径浏览模态（GET /api/fs/browse）
└─ SSE 加固（client.ts api.postStream + AbortController）

后端新增（Backend）
├─ runner/models.py + GET /api/runner/models
├─ fs/api.py + GET /api/fs/browse
└─ 重新生成 openapi.json + types.generated.ts
```

## 5. 组件设计

### 5.1 UI 原语（`apps/web/src/components/ui/`）

每个原语为单文件、纯展示、受控，接受标准 React props + `className` 透传。

| 原语 | props | 用途 |
|---|---|---|
| `Button` | `variant: primary\|ghost\|danger`、`size: sm\|md`、`loading`、`icon` | 主/次/危险按钮，loading 态内置 Spinner |
| `Input` | 标准 input props | 文本输入 |
| `Textarea` | 标准 textarea props | 多行输入 |
| `Select` | 标准 select props | 原生 select styled（下拉箭头 SVG） |
| `Badge` | `tone: ok\|bad\|wait\|skip\|neutral`、`children` | 状态徽章，色映射走 token |
| `Card` | `title?`、`children`、`className` | 卡片容器（`rounded-lg border bg-surface p-*`） |
| `Field` | `label`、`hint?`、`optional?`、`children`、`htmlFor` | label+hint+控件包裹，统一表单结构 |
| `Modal` | `open`、`onClose`、`title`、`children`、`footer` | 遮罩 + 对话框，ESC/背板关闭，焦点约束 |
| `Toast` / `ToastContainer` | `useToast()` → `toast(msg, tone)` | 右上角通知，auto-dismiss 4s |
| `EmptyState` | `icon`、`title`、`description?`、`action?` | 空列表占位 |
| `Spinner` | `size` | 加载指示 |

### 5.2 主题（`apps/web/src/theme/`）

- `ThemeProvider`：挂载时读 `localStorage['skilleval-theme']`（默认 `system`），监听 `prefers-color-scheme` 变化（仅 system 模式），在 `<html>` 上 toggle `.dark` 类。提供 `useTheme()` → `{mode, setMode, resolved}`。
- `ThemeToggle`：三段开关（☀ 浅 / 🌙 深 / 💻 系统），放侧边栏底部。
- token 命名不变，仅换值；组件代码因走 `bg-surface` 等语义类无需改动。

### 5.3 主题 token（`apps/web/src/index.css`）

浅色（slate/靛蓝）：
```
--canvas:#f8fafc; --surface:#ffffff; --surface-2:#f1f5f9;
--line:#e2e8f0; --line-strong:#cbd5e1; --ink:#0f172a; --muted:#64748b; --faint:#94a3b8;
--accent:#6366f1; --accent-ink:#ffffff; --accent-soft:#eef2ff; --accent-border:#c7d2fe;
--ok:#16a34a; --bad:#dc2626; --wait:#0ea5e9; --skip:#94a3b8;
```
深色（`.dark` 下覆盖）：
```
--canvas:#0f172a; --surface:#1e293b; --surface-2:#0f172a;
--line:#334155; --line-strong:#475569; --ink:#f1f5f9; --muted:#94a3b8; --faint:#64748b;
--accent:#818cf8; --accent-ink:#0f172a; --accent-soft:#1e1b4b; --accent-border:#3730a3;
--ok:#4ade80; --bad:#f87171; --wait:#38bdf8; --skip:#64748b;
```
新增 `@custom-variant dark (&:where(.dark, .dark *));`（Tailwind v4 CSS 写法）。色值来自已验证的 `demo-cool.html`。

## 6. 数据流

### 6.1 模型列举（运行页加载）
```
RunPage mount → GET /api/runner/models → {models:[{provider,model,id,context_window?,input_cost?,output_cost?}]}
  → 前端按 provider 去重得提供商列表；选 provider 后客户端过滤模型列表
  → 提交时 model = chosen ? `${provider}/${model}` : null
```

### 6.2 路径浏览（点击"浏览"）
```
Modal 打开 → GET /api/fs/browse?path=<当前cwd或空> → {path:resolved, entries:[{name,type,path}]}
  → 目录与文件都返回；前端文件灰显不可选，目录可点击进入
  → 点击目录 → 再 GET /api/fs/browse?path=<子目录path>（逐层进入）
  → 面包屑点击任意段 → 跳到该层
  → "选择此目录" → 写回 cwd 输入框并关模态
```

### 6.3 SSE 运行流（加固后）
```
点击"运行" → api.postStream('/api/runner/run/stream', body, {signal})
  → fetch + ReadableStream + 帧解析（\n\n 分帧、data: 前缀、JSON.parse）
  → 逐事件回调 onEvent(node) / onDone(trace_id) / onError(msg)
  → AbortController.signal 传入 fetch；卸载或"停止"按钮 → controller.abort()
  → done → navigate(/traces/:id)；error → Toast + 停止运行态
```

## 7. 后端新增端点

### 7.1 `GET /api/runner/models`
- 新文件 `apps/api/skill_eval/runner/models.py`，函数 `list_models()`：shell `opencode models --verbose`，`capture_output=True, text=True, timeout=30`；解析 stdout 行（`provider/model` 格式，`--verbose` 带成本列）；返回 `[{"provider":str, "model":str, "id":"provider/model", "context_window":int|None, "input_cost":float|None, "output_cost":float|None}]`。
- 守卫：`shutil.which("opencode") is None` → `[]`；`OSError`/超时/非零退出 → `[]`。
- 路由 `api.py` 加 `@router.get("/models")` → `return {"models": list_models()}`（镜像 `get_skills`，`api.py:114-116`）。
- 测试：`test_runner.py` 加 `TestModelsApi`，monkeypatch subprocess 返回样例 stdout，断言解析；monkeypatch `shutil.which → None` 断言返回 `[]`。

### 7.2 `GET /api/fs/browse?path=`
- 新文件 `apps/api/skill_eval/fs.py`：含 `browse_directory(path: str | None) -> dict` 与 `router = APIRouter(prefix="/api/fs", tags=["fs"])`（`@router.get("/browse")`），在 `app.py` 与其他领域路由一同挂载（与 ingest/runner/store/eval/judge 同模式）。
  - 空 path → `Path.home()`；展开 `~`；`Path(path).expanduser().resolve()`。
  - 安全校验：resolve 后若不存在或非目录 → 404；权限不足 → 跳过该条目。
  - 列举子条目：`sorted(dir.iterdir())`，跳过隐藏（`.` 开头）与 Windows 系统目录；**目录与文件都返回**（`type:"dir"|"file"`），前端模态中文件灰显不可选（仅作上下文参考），目录可点击进入。
  - 容错：`PermissionError` 跳过该条目；整体 `OSError` → 返回空 entries。
- 测试：新 `apps/api/tests/test_fs.py`，用 `tmp_path` 造目录结构，断言列举、隐藏跳过、空 path → home、文件 type 正确、不存在目录报 404。

### 7.3 schema 与类型同步
- **不改** `RunContext`/`StreamRunRequest`（`model` 已存在）。
- 重新生成：`cd apps/api && uv run python scripts/export_openapi.py ../web/openapi.json` → `cd apps/web && npx openapi-typescript openapi.json -o src/api/types.generated.ts`（按 AGENTS.md 流程）。
- 补后端测试：`test_runner.py` 加一条断言 `--model` 进入 `cmd` argv（填补已知测试缺口——当前 `_FakeProc` 未捕获 argv）。

### 7.4 可选小增强
- `ingest/adapters/opencode.py:230` 当前仅取 `info.model.id`，丢弃 `providerID`。可把 `providerID` 记入 `Trace.extra`（如 `extra["provider"]`），便于 Trace 详情显示所用提供商。标注为**可选**，实现时定。

## 8. 文案中文化约定

- 直接翻译内联字面量为中文，不引入 strings map / i18n 库。
- 保留原文的产品术语：Trace、Skill、Agent、DAG、Token(s)、Cost、Prompt、SSE、CLI。
- 状态词统一：completed→已完成、running→运行中、error→错误、skipped→已跳过、pending→待定。
- 导航条统一中文：运行记录 / 运行 Skill / 测试用例 / 评测记录 / Trace 对比。
- 空状态、Toast、按钮、表单标签、列名、提示全部中文化。

## 9. 错误处理

- 运行 SSE：fetch 失败 → Toast 错非致命；中途 abort → 静默（用户主动停止）；done → 跳转。
- 模型列举失败 → 提供商/模型下拉退化为禁用 + "无法获取模型列表"提示，但仍可提交（model=null）。
- 路径浏览失败 → 模态内显示"无法读取该目录"，保留当前路径。
- 表单校验：prompt 为空时禁用"运行"按钮；cwd 留空允许（= 后端 cwd）。

## 10. 测试策略

### 前端（vitest）
- 更新 `RunPage.test.tsx`：新增 provider/model 级联字段、路径模态打开/选择、SSE abort。
- 新增 `components/ui/` 原语测试：Button（variant/loading）、Modal（open/close/ESC/背板）、ThemeToggle（三态）、Toast（auto-dismiss）。
- 新增级联过滤纯逻辑测试（提取 `filterModelsByProvider` 到 utils 可单测）。
- `npx tsc -b` 退出 0；`npm test` 全绿（预计 24 → ~32+）。

### 后端（pytest）
- `test_runner.py`：`TestModelsApi`（解析 + CLI 缺失降级）、`--model` 进 argv 断言。
- `test_fs.py`（新）：`browse_directory` 列举、隐藏跳过、空 path→home、不存在目录报错。
- `uv run pytest` 全绿（预计 156 → ~162+）。

### E2E（Playwright）
- 现有 5 例保持绿；若运行页 E2E 覆盖表单提交，同步更新字段。

## 11. 验证清单（DoD）

- [ ] 全前端无英文/混杂用户可见文案（专有名词除外）
- [ ] `components/ui/` 原语全部落地，6 页 + 4 组件已迁移
- [ ] 深色模式三态切换可用、localStorage 持久化、system 模式跟随 OS
- [ ] 运行页提供商→模型级联可用，提交 `provider/model`
- [ ] 运行页路径浏览模态可逐层进入/面包屑/选择返回
- [ ] SSE 卸载/停止不泄漏，断流有错误提示
- [ ] `GET /api/runner/models` 与 `GET /api/fs/browse` 可用且测试覆盖
- [ ] `openapi.json` + `types.generated.ts` 已重新生成
- [ ] `npx tsc -b` 退出 0；`npm test`、`uv run pytest` 全绿
- [ ] 前端整体观感对齐 demo-cool.html（slate + 靛蓝）

## 12. 风险与缓解

| 风险 | 缓解 |
|---|---|
| `opencode models` 输出格式跨版本变化 | 解析容错（按行 split、`/` 拆 provider/model，失败行跳过）；CLI 缺失降级 `[]` |
| 路径列举在 Windows 遇权限/系统目录 | `PermissionError` 跳过；隐藏/系统目录过滤；resolve 容错 |
| Tailwind v4 `@custom-variant dark` 写法差异 | 以 demo-cool.html 已验证写法为准（CSS-first） |
| 原语抽取后样式回归 | 原语先行单测 + 逐页迁移后人工对照 demo 截图 |
| SSE 抽离引入回归 | `api.postStream` 单测 + RunPage 集成测试覆盖 abort/done/error |
