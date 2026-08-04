from skill_eval.core.projection import ToolCallRef, tool_projection
from skill_eval.core.schema import Node, Trace


def node(**kw: object) -> Node:
    base: dict[str, object] = {"id": "x", "type": "custom", "name": "n"}
    base.update(kw)
    return Node(**base)


def trace(root: Node) -> Trace:
    return Trace(id="t", agent="opencode", root=root)


class TestToolProjection:
    def test_empty_when_no_tool_calls(self) -> None:
        root = node(children=[node(id="a", type="message")])
        assert tool_projection(trace(root)) == []

    def test_flat_tool_sequence_in_order(self) -> None:
        root = node(
            children=[
                node(id="t1", type="tool_call", name="read_file",
                     tool={"name": "read_file", "args": {"p": "a"}}),
                node(id="t2", type="tool_call", name="grep",
                     tool={"name": "grep", "args": {"q": "x"}}),
            ]
        )
        refs = tool_projection(trace(root))
        assert [r.name for r in refs] == ["read_file", "grep"]
        assert refs[0].node_id == "t1"

    def test_depth_first_nested_order(self) -> None:
        root = node(
            children=[
                node(
                    id="s1",
                    type="agent_step",
                    children=[
                        node(id="t1", type="tool_call", name="first",
                             tool={"name": "first"}),
                    ],
                ),
                node(id="t2", type="tool_call", name="second", tool={"name": "second"}),
            ]
        )
        assert [r.name for r in tool_projection(trace(root))] == ["first", "second"]

    def test_tool_result_carried(self) -> None:
        root = node(
            children=[
                node(id="t1", type="tool_call", name="read_file",
                     tool={"name": "read_file", "result": {"lines": 3}}),
            ]
        )
        ref = tool_projection(trace(root))[0]
        assert ref.result == {"lines": 3}  # type: ignore[union-attr]

    def test_missing_tool_name_uses_node_name(self) -> None:
        root = node(
            children=[node(id="t1", type="tool_call", name="legacy_tool")]
        )
        refs = tool_projection(trace(root))
        assert refs[0].name == "legacy_tool"

    def test_skipped_filtered_by_default(self) -> None:
        root = node(
            children=[
                node(id="ok", type="tool_call", name="keep", tool={"name": "keep"}),
                node(id="sk", type="tool_call", name="skipme",
                     tool={"name": "skipme"}, status="skipped"),
            ]
        )
        assert [r.name for r in tool_projection(trace(root))] == ["keep"]

    def test_include_skipped(self) -> None:
        root = node(
            children=[
                node(id="ok", type="tool_call", name="keep", tool={"name": "keep"}),
                node(id="sk", type="tool_call", name="skipme",
                     tool={"name": "skipme"}, status="skipped"),
            ]
        )
        refs = tool_projection(trace(root), include_skipped=True)
        assert [r.name for r in refs] == ["keep", "skipme"]


class TestToolCallRef:
    def test_fields(self) -> None:
        ref = ToolCallRef(node_id="a", name="b", args={"x": 1}, result=None)
        assert ref.args == {"x": 1}
        assert ref.result is None
