import os
from pathlib import Path
import shutil
import subprocess

import pytest


def test_adopted_ruby_geometry_and_bounds_arithmetic():
    ruby = os.environ.get('ARCH_STUDIO_TEST_RUBY') or shutil.which('ruby')
    if not ruby:
        pytest.skip('System Ruby optional; real SketchUp smoke is a separate Windows gate')
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([ruby, '--disable=gems', str(root/'tests/ruby/adopted_helpers_test.rb')], cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr+result.stdout
    assert 'PASS: SAIE' in result.stdout


def test_agent_uses_injected_helpers_not_global_vendor_entrypoints():
    from app.project_ruby import validate_project_ruby_source
    source='saie_wall.call({"name"=>"rear", "centerline"=>[[10000,8000],[0,8000]], "height_mm"=>3200, "thickness_mm"=>200})'
    assert validate_project_ruby_source('villa',source)==source
    with pytest.raises(ValueError,match='blocked'):
        validate_project_ruby_source('villa','KStudioProfessionalHelpers.wall(model, {})')
