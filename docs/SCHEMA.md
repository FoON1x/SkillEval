# Canonical Trace Schema（v0.1 草案）

> 状态：Draft。这是数据真相之处——跨后端（Pydantic）与前端（OpenAPI 生成 TS）。
> 真实样例到位后回填各 Agent 字段映射（见下 "扩展与映射"）。

## 1. 设计原则

- 递归树形节点，覆盖 Agent 运行时的所有可观测事件（类 OTel Span）。
- 结构尽量精简，未确认的字段走 `extra` 保留原始信息，不阻塞开发。
- 以"工具调用序列投影"支撑四规则评估；以树支撑可视化与全过程级 LLM 分析。

## 2. 顶层：Trace

```
Trace
  id: str (uuid)
  agent: "opencode" | "codex" | "claude-code" | "pi"
  tool_version: str | None        # agent 版本
  skill_name: str | None          # 关联的 Skill 名
  session_id: str | None
  status: run_state               # completed | running | error | cancelled
  started_at / ended_at: datetime | None
  usage: Usage | None             # 成本/延迟元数据（可选）
  error: TraceError | None
  root: Node                      # 根节点（整棵树）
  extra: dict                     # 适配器保留的原始字段/还原信息
```

run_state = "completed" | "running" | "error" | "cancelled"

## 3. 节点：Node（递归）

```
Node
  id: str (unique within trace)
  parent_id: str | None
  type: node_type
  name: str
  summary: str | None             # 单行描述（时间线/压缩视图用）
  status: node_status             # completed | running | error | skipped
  started_at / ended_at: datetime | None
  duration_ms: int | None
  input: unknown | None           # 序列化入参
  output: unknown | None          # 序列化出参
  tool: ToolCall | None           # type=tool_call 时填充
  llm: LlmUsage | None            # type=llm_call 时填充（成本/延迟来源）
  error: TraceError | None
  children: list[Node]            # 顺序保持调用顺序
  extra: dict
```

node_type = "skill_start" | "skill_end" | "agent_step" | "tool_call" | "llm_call" | "sub_agent" | "message" | "error" | "custom"

## 4. 附属结构

ToolCall:
```
name: str            # 工具名（评估投影的主键）
args: dict | None
result: unknown | None
meta: dict | None    # adapter 特有（exit code 等）
```

LlmUsage:
```
model: str | None
input_tokens: int | None
output_tokens: int | None
total_tokens: int | None
cost_usd: float | None   # 有定价表才估算，否则 None
latency_ms: int | None
```

Usage（Trace 级汇总）:
```
input_tokens / output_tokens / total_tokens: int | None
cost_usd: float | None
latency_ms: int | None
models: list[str]
```

TraceError:
```
message: str
kind: str | None   # adapter 提供的错误类别
trace: str | None  # 栈信息
```

## 5. 工具调用投影（评估输入）

```
tool_projection(trace) -> list[ToolCallRef]
ToolCallRef: { node_id, name, args, result }
```

四规则针对此列表（可先过滤掉被 skip 的节点，规则定义见 REQUIREMENTS 3.4）。

## 6. Diff 语义（v0.1）

- 结构级：对比两条 Trace 的 projection 序列与树形结构。
- 输出项：新增/缺失/顺序变化/同名参数差异/状态差异。
- 文本降级：无法结构对齐时提供逐字段文本对比。

## 7. 扩展与映射（opencode 已回填真实格式）

opencode 适配器消费 `opencode run --format json` 的 JSONL 输出（CLI ≥ 1.18）。每行一个 JSON：
`{"type","timestamp"(epoch ms),"sessionID","part":{...}}`。

| opencode 事件 | Canonical 节点 | 说明 |
| --- | --- | --- |
| `step_start` | `AGENT_STEP`（root 子节点，status=running） | 一次模型推理步 |
| `text` | `MESSAGE`（挂当前 step） | `part.text` → `node.output` |
| `tool_use` | `TOOL_CALL`（挂当前 step） | `part.state.{input,output,metadata.exit,time}` → args/result/状态/时序；`metadata.exit!=0` 标 `ERROR` |
| `step_finish` | 关闭当前 step；`reason=="stop"` 触发 `SKILL_END` | `part.tokens`/`cost` 聚合到 step 的 `LlmUsage` |
| 其它（`reasoning` 等） | 忽略（ParseWarning） | `--thinking` 或 export 才有 reasoning |

`opencode export <sessionID>` 的 `info`（title/agent/model/cost/tokens/time）比实时流更权威，`finalize(export_info)` 时合并填入 trace 级 `usage`/`tool_version`。导入端点 `/api/ingest/import` 接受 `{session_id?, skill_name?, events:[...], export_info?}`。

| Agent | 期望来源 | 映射清单 |
| --- | --- | --- |
| opencode | `opencode run --format json` JSONL + `opencode export` | 已实现（见上表） |
| claude code | ~/.claude/projects/*.jsonl | 待回填 |
| codex | codex log 目录 | 待回填 |
| pi | 待确认 | 待回填 |

未定字段一律落 `extra`，保证向后兼容。

## 8. JSON 示例

```json
{
  "id": "t-001",
  "agent": "opencode",
  "skill_name": "demo-skill",
  "status": "completed",
  "started_at": "2026-08-04T10:00:00Z",
  "ended_at": "2026-08-04T10:01:12Z",
  "usage": {"total_tokens": 8120, "cost_usd": 0.0321},
  "root": {
    "id": "n0", "type": "skill_start", "name": "demo-skill", "status": "completed",
    "children": [
      {"id": "n1", "type": "agent_step", "name": "parse input", "status": "completed",
       "children": [
         {"id": "n2", "type": "tool_call", "name": "read_file",
          "tool": {"name": "read_file", "args": {"path": "/a.txt"}, "result": "..."}}
       ]}
    ]
  }
}
```