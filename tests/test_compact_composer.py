from html.parser import HTMLParser
from pathlib import Path


class Layout(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.parents = [], {}

    def handle_starttag(self, tag, attrs):
        identity = dict(attrs).get("id")
        if identity:
            self.parents[identity] = [i for _, i in self.stack if i]
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append((tag, identity))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                return


def test_all_phase_actions_and_errors_scroll_in_chat_outside_the_fixed_composer():
    layout = Layout()
    layout.feed((Path(__file__).parents[1] / "app/static/index.html").read_text(encoding="utf-8"))
    for control in ["reconstruction-state", "approve-reconstruction", "prepare-plan",
                    "clarification-shortcuts", "cancel-agent-turn", "agent-error", "operation-progress"]:
        assert "conversation-history" in layout.parents[control]
        assert "conversation-form" not in layout.parents[control]
    for control in ["conversation-input", "reference-file", "model-settings-toggle", "conversation-send"]:
        assert "conversation-form" in layout.parents[control]
