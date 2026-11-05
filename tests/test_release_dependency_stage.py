import json
from pathlib import Path
import pytest
from scripts.prepare_release_dependency_stage import prepare


def fixture(tmp_path):
    stage = tmp_path / 'harness-stage'
    package = stage / 'node_modules/fast-uri'
    (package / 'benchmark').mkdir(parents=True)
    (package / 'package.json').write_text(json.dumps({'name': 'fast-uri', 'version': '3.1.9', 'main': 'index.js'}))
    (package / 'index.js').write_text('module.exports = {}')
    (package / 'LICENSE').write_text('original notice')
    (package / 'benchmark/package.json').write_text('{"private":true,"license":"ISC"}')
    return stage, package


def test_only_reviewed_benchmark_removed(tmp_path):
    stage, package = fixture(tmp_path)
    result = prepare(stage)
    assert len(result['removed']) == 1
    assert not (package / 'benchmark').exists()
    assert (package / 'index.js').read_text() == 'module.exports = {}'
    assert (package / 'LICENSE').read_text() == 'original notice'


def test_unreviewed_version_not_removed(tmp_path):
    stage, package = fixture(tmp_path)
    data = json.loads((package / 'package.json').read_text()); data['version'] = '4.0.0'
    (package / 'package.json').write_text(json.dumps(data))
    with pytest.raises(ValueError, match='Review exclusion'): prepare(stage)
    assert (package / 'benchmark/package.json').exists()


def test_reject_installed_or_source_root(tmp_path):
    with pytest.raises(ValueError, match='new harness-stage'): prepare(tmp_path)
