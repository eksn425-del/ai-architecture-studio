from pathlib import Path

from app.agent_tools import AgentToolSurface
from app.oss_backends import DEFAULT_BLOCKED_TOOLS, SdkStdioMCPBackend


class FakeKongxing:
    def __init__(self):
        self.calls = []

    def list_tools(self):
        return [{
            "name": "sketchup_health",
            "description": "Read bridge health.",
            "inputSchema": {"type": "object", "properties": {}},
        }]

    def call_for_agent(self, name, arguments):
        self.calls.append((name, arguments))
        return {"success": True, "contentItems": []}


class FakeSaie:
    def __init__(self):
        self.calls = []

    def list_tools(self):
        return [
            {
                "name": "create_wall",
                "description": "Create a wall with stable AI identity.",
                "inputSchema": {
                    "type": "object",
                    "required": ["ai_id"],
                    "properties": {"ai_id": {"type": "string"}},
                },
            },
            {
                "name": "view_snapshot",
                "description": "Return a current SketchUp image.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def call_for_agent(self, name, arguments):
        self.calls.append((name, arguments))
        return {"success": True, "contentItems": [{"type": "inputText", "text": name}]}


def test_agent_surface_composes_namespaced_oss_tools(tmp_path: Path) -> None:
    kongxing = FakeKongxing()
    saie = FakeSaie()
    surface = AgentToolSurface(tmp_path, kongxing, oss_backends={"saie": saie})

    tools = surface.dynamic_tools(ruby_enabled=False)
    names = {tool["name"] for tool in tools}

    assert "sketchup_health" in names
    assert "saie__create_wall" in names
    assert "saie__view_snapshot" in names
    assert next(tool for tool in tools if tool["name"] == "saie__create_wall")["inputSchema"]["required"] == ["ai_id"]


def test_agent_surface_dispatches_oss_tool_without_reimplementing_it(tmp_path: Path) -> None:
    kongxing = FakeKongxing()
    saie = FakeSaie()
    surface = AgentToolSurface(tmp_path, kongxing, oss_backends={"saie": saie})

    result = surface.dispatch(
        "saie__create_wall",
        {"ai_id": "wall-a"},
        project_dir=tmp_path,
        project_ruby=None,
    )

    assert saie.calls == [("create_wall", {"ai_id": "wall-a"})]
    assert result["success"] is True
    assert kongxing.calls == []


def test_saie_lifecycle_and_raw_ruby_tools_are_blocked_by_default() -> None:
    assert {"execute_ruby", "clear_model", "open_file", "save_as"}.issubset(DEFAULT_BLOCKED_TOOLS)
    backend = SdkStdioMCPBackend("saie", "definitely-not-installed-saie-mcp")
    assert backend.available is False
