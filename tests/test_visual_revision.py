"""Wire/bridge fixtures only: these do not certify architectural fidelity."""
import base64
from copy import deepcopy
from pathlib import Path

import pytest
from PIL import Image

from app.agent_tools import AgentToolSurface
from app.litellm_runtime import _current_visual_context, _tool_result_parts
from app.sketchup_mcp import MCPCallError


def readback(label):
    return {'role': 'user', 'content': [
        {'type': 'text', 'text': 'Visual readback from SketchUp tool capture.'},
        {'type': 'image_url', 'image_url': {'url': label}},
    ]}


@pytest.mark.parametrize('success', [True, False])
def test_only_committed_geometry_invalidates_prior_visual_evidence(success):
    source = readback('source')
    source['content'][0]['text'] = 'Source image 1: villa-six-view-sheet.png'
    messages = [source, readback('old-roof'),
        {'role': 'assistant', 'tool_calls': [{'id': 'edit', 'function': {'name': 'sketchup_run_workspace_ruby', 'arguments': '{}'}}]},
        {'role': 'tool', 'tool_call_id': 'edit', 'content': '{"success": ' + str(success).lower() + '}'},
        readback('current-roof')]
    original = deepcopy(messages)
    active = _current_visual_context(messages)
    assert messages == original
    images = [b['image_url']['url'] for m in active if isinstance(m.get('content'), list)
              for b in m['content'] if b['type'] == 'image_url']
    assert images == (['source', 'current-roof'] if success else ['source', 'old-roof', 'current-roof'])
    assert active[2:4] == messages[2:4]


class ExportBridge:
    def __init__(self, mode):
        self.mode = mode

    def call_for_agent(self, name, arguments):
        path = Path(arguments['output_path'])
        if self.mode == 'png':
            Image.new('RGB', (40, 24), 'white').save(path)
        elif self.mode == 'corrupt':
            path.write_bytes(b'not an image')
        return {'success': True, 'contentItems': [{'type': 'inputText', 'text': 'export accepted'}]}


@pytest.mark.parametrize('mode', ['missing', 'corrupt'])
def test_export_without_decodable_png_is_not_visual_success(tmp_path, mode):
    surface = AgentToolSurface(tmp_path, ExportBridge(mode), oss_backends={})
    with pytest.raises(MCPCallError, match='screenshot'):
        surface.dispatch('sketchup_export_view_image', {}, project_dir=tmp_path, project_ruby=None)


def test_export_supplies_actual_pixels_and_relative_receipt(tmp_path):
    surface = AgentToolSurface(tmp_path, ExportBridge('png'), oss_backends={})
    result = surface.dispatch('sketchup_export_view_image', {}, project_dir=tmp_path, project_ruby=None)
    text, images = _tool_result_parts(result)
    assert len(images) == 1
    assert base64.b64decode(images[0].split(',', 1)[1]).startswith(b'\x89PNG')
    assert result['visual_evidence']['width'] == 40
    assert result['visual_evidence']['height'] == 24
    assert result['visual_evidence']['path'].startswith('outputs/renders/')
    assert str(tmp_path) not in text
