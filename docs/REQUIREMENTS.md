# 需求分析报告（v0.1 · 已确认）

> 状态：已确认（2026-08-04 与项目负责人澄清问答后拍板）。任何变更需先更新本文档并经确认。

## 1. 背景与目标

- 面向 AI Agent / Skill 开发者的测试与调试工具。
- 第一版目标：Skill Trace 的采集、可视化与评测。
- 目标使用者：本地单机的 Skill 开发者。

## 2. 确认决策一览

| # | 议题 | 决策 |
| --- | --- | --- |
| D1 | 技术栈 | 方案 B：Python FastAPI 后端 + React+TS 前端（ADR-001） |
| D2 | Trace 获取方式 | 双通道：本地文件导入 + 运行时 SDK/Hook 推送 |
| D3 | Trace 样例 | 暂无真实样例：以参考实现 + Mock 生成器驱动开发，Schema 预留扩展字段 |
| D4 | 使用形态 | 本地单机工具，无鉴权，SQLite |
| D5 | 评估粒度 | 规则（tool 序列）+ 自定义断言（可校验参数/输出） |
| D6 | LLM-as-a-Judge | 纳入 v1：结果级 + 全过程级两种分析，OpenAI 兼容 Provider |
| D7 | 成本/延迟 | 有 usage 元数据则展示，缺失自动跳过 |
| D8 | 运行方式 | 双通道：导入外部 Trace + 系统内 CLI 触发 Agent 运行（CLI 触发将成为主流） |
| D9 | 跨语言 Schema | Python Pydantic 为事实源，OpenAPI 生成 TS 类型（ADR-002） |
| D10 | 断言脚本语言 | Python 断言（与后端同语言） |
| D11 | CLI Runner v1 | 先实现 opencode CLI 运行器 + 抽象接口，其余 Agent 逐步适配 |
| D12 | LLM Provider v1 | 配置化，兼容 OpenAI / DeepSeek / 本地 Ollama 等 OpenAI 格式接口 |
| D13 | Mock 数据 | 提供一套参考 Trace 生成器用于开发与联调 |
| D14 | Diff 粒度 | 结构级对比（步骤存在性/顺序 + 关键参数），文本降级视图 |

## 3. 核心模块与验收标准

### 3.1 可插拔 Trace 采集

- 适配器接口：parse(raw) -> Trace；PushHandler(Trace) -> sink。按 agent_name 注册。
- v1 适配器：opencode（首个，含 CLI 运行器）、codex、claude code、pi（骨架 + 解析占位）。
- 导入：从各 Agent 本地日志目录读取/拖拽文件，也支持手贴 JSON。
- 推送：接收运行时事件流的 HTTP 端点。
- 验收：任意适配器可独立增减；解析失败有结构化错误；能导入真实/ Mock 文件并入库。

### 3.2 Trace 可视化

- 视图：Trace DAG（React Flow）+ 时间线 + 详情面板（L 面板）。
- 交互：缩放/平移/节点聚焦/状态着色/错误高亮。
- UI：现代、高级、简约（Figma / Anthropic 设计语言）：中性色板、留白、细边框、极简排版。
- 验收：100 节点以上平滑渲染；状态一眼可辨；错误可快速定位。

### 3.3 持久化与 Diff

- SQLite 存储 Trace、用例、评测结果。
- 历史列表查询（按 Agent / Skill / 时间 / 结果过滤）。
- Diff：任意两次 Trace 结构级对比；有 Details。
- 验收：两次运行可对比出 新增/缺失/顺序变化/参数变化。

### 3.4 测试用例与 Evaluator

- 用例：id、名称、描述、目标 Agent、输入上下文、期望 Trace 路径（tool 序列投影）、自定义断言列表。
- 规则评估器（作用于 Trace 的 tool 投影序列）：
  - strict：实际序列 === 期望序列（顺序、集合完全一致）。
  - unordered：实际集 === 期望集（顺序不限）。
  - subset：实际工具 ⊆ 期望工具（不得出现期望之外的工具）。
  - superset：期望工具 ⊆ 实际工具（至少覆盖所有必需工具）。
- 自定义断言：Python 片段，运行于受限沙箱，可访问 trace 投影与参数/输出，返回通过/失败 + 消息。
- 验收：四规则对构造样例全部通过；断言失败信息可定位；结果持久化并可重跑对比。

### 3.5 LLM-as-a-Judge

- Provider-agnostic OpenAI 兼容客户端（base_url / api_key / model 配置化）。
- 模式一 结果级：仅基于最终输出判定，产出 JSON 化评分与理由。
- 模式二 全过程级：基于完整 Trace（步骤 + 中间输出 + 工具行为）做整体评价。
- 密钥本地保存（不硬编码、不入库），失败不阻塞主流程。
- 验收：Mock LLM 服务可驱动单测；两种模式的输出 schema 稳定。

### 3.6 成本 / 延迟

- 由 Trace 中 usage/模型元数据驱动：估算代际、延迟、token 消耗。
- 缺失数据自动跳过，不影响其它功能。

### 3.7 运行触发（CLI Runner）

- 抽象 Runner 接口，v1 实现 opencode CLI：给定用例输入，headless 调起 opencode，捕获事件流并在运行中推送进系统。
- 后续扩展 codex / claude code / pi 的 CLI 调用。
- 验收：可通过 API 一键触发运行，运行 Trace 自动回填并可直接评测。

## 4. 非功能需求

- 单机内网使用，无鉴权；数据默认落在本地。
- 启动友好：一个脚本拉起后端（uvicorn）与前端（vite dev）。
- 跨语言 Schema 不漂移：前端类型由 OpenAPI 生成并纳入 CI 检查。
- 全部核心逻辑以 TDD 覆盖（规则、断言沙箱、解析器、Diff、LLM 客户端）。

## 5. 风险与开放项

| 风险 | 等级 | 应对 |
| --- | --- | --- |
| 各 Agent Trace 形态未确认 | 高 | Schema 扩展字段 + 适配器隔离 + Mock 先行；拿到样例后回补 |
| pi agent 资料少 | 中 | 先骨架 + 解析占位，确认能力后实现 |
| 自定义断言沙箱安全 | 中 | 受限进程 + 超时 + 资源限制，v1 允许用户单方执行 |

## 6. 待确认遗留项

- 各 Agent 真实日志样例（官方能力核实后回填 Schema 细节）。
- 前端是否需要暗色主题（默认浅色 + 预留 token）。
- 用例期望路径是否支持多分支（OR）与正则通配（v1 先不做，Schema 预留）。