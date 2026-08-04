"""Tool-call projection: the input for rule evaluation and diffing."""

from pydantic import BaseModel

from skill_eval.core.schema import Node, NodeStatus, NodeType, Trace


class ToolCallRef(BaseModel):
    node_id: str
    name: str
    args: object | None = None
    result: object | None = None


def tool_projection(trace: Trace, include_skipped: bool = False) -> list[ToolCallRef]:
    """Collect tool_call nodes depth-first, in execution order.

    Skipped nodes are excluded by default (they never executed).
    Falls back to node.name when ToolCall.name is missing.
    """

    def walk(n: Node) -> list[ToolCallRef]:
        refs: list[ToolCallRef] = []
        if n.type == NodeType.TOOL_CALL and (include_skipped or n.status != NodeStatus.SKIPPED):
            tool = n.tool
            refs.append(
                ToolCallRef(
                    node_id=n.id,
                    name=tool.name if tool else n.name,
                    args=tool.args if tool else None,
                    result=tool.result if tool else None,
                )
            )
        for child in n.children:
            refs.extend(walk(child))
        return refs

    return walk(trace.root)
