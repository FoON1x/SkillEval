# 代码审查归档（CODE_REVIEW）

> 目的：归档代码审查结论（已处理清单 + 残留项），避免后续审查重复排查相同问题。

## 审查范围

- **对象**：`apps/web`（前端全量）+ `apps/api`（runner/ingest 子系统重点）
- **日期**：2026-08-24
- **关联**：已处理项主要落在规格1（前端重构 + 模型/提供商选择）及其后续修复波

## 已处理（规格1 覆盖 + 后续修复波，2026-08-24）

逐条列出原审查发现 → 对应规格1 任务 / 修复提交。以下项已处理，后续审查跳过。

### 前端

| 原问题 | 处理 |
| --- | --- |
| 无 UI 原语层（按钮/输入/选择等重复标记） | 规格1 Task 2-3：抽取 `components/ui/` 12 组件 |
| 无深色模式 | 规格1 Task 1：slate/靛蓝 token + 浅/深/系统三态切换 |
| 中英文混杂 | 规格1 Task 8-12：导航 / 6 页 / 4 组件中文化 |
| 路径选取纯文本（无目录浏览） | 规格1 Task 5（后端 `GET /api/fs/browse`）+ Task 14（路径浏览模态） |
| 运行表单未暴露模型 | 规格1 Task 4（后端 `GET /api/runner/models`）+ Task 13（提供商→模型级联） |
| SSE 脆弱（无 AbortController） | 规格1 Task 15：`api.postStream` + abort |
| 缺失交互状态（无 Toast/EmptyState/Spinner） | 规格1 Task 2-3 |
| 状态词未中文化（Badge 文本 / 筛选选项） | 规格1 修复波 `020b182`：`utils/labels.ts`，6 站点 |
| 深色模式 FOUC（首帧闪白） | 规格1 修复波 `d14f6d9`：ThemeProvider 首帧读已存模式 + index.html 内联脚本 |
| SSE 异常断开无反馈 | 规格1 修复波 `fced952`：postStream terminated 标志 + 兜底 onError |
| 模型列举失败无提示 | 规格1 修复波 `7a2dcc2`：modelsError + 提示 |

### 后端

| 原问题 | 处理 |
| --- | --- |
| `--model` 转发未测试 | 规格1 Task 6：补断言 |
| 无模型列举端点 | 规格1 Task 4：`GET /api/runner/models` |
| C1：models 端点 Windows 失效（.CMD shim + `--verbose` 垃圾解析） | 规格1 修复波 `0d3d018`：跨平台 `_build_cmd` + 去 `--verbose` + 收紧正则 + 回归测试 |

## 残留项 / 已知限制（未处理）

- opencode models 输出格式跨版本稳定性待观察（规格1 已去掉 `--verbose`，现为无 verbose 干净输出）
- Tailwind v4 `@custom-variant dark` 写法在不同构建版本表现待验证
- I1：运行页「停止」按钮仅断开客户端 SSE，worker 线程仍会跑完并保存 Trace（服务端取消需后续实现）
- UNC 路径面包屑父级回溯失效（Windows 边缘场景）
- Modal 缺焦点约束（a11y，规格提过）
- fs.py 任意目录列举无根域白名单（本地无鉴权场景可接受）
- loadDir 快速点击竞态（低频）

## 使用说明

后续审查先读本文件：跳过「已处理」清单，仅排查「残留项」与新增代码；残留项若被后续提交处理，移入「已处理」并标注对应提交。
