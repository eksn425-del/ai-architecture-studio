import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("release_licenses", Path(__file__).parents[1] / "scripts" / "collect_release_licenses.py")
licenses = importlib.util.module_from_spec(spec)
spec.loader.exec_module(licenses)


def test_actual_metadata_texts_and_unknowns_without_private_files(tmp_path):
    bundle = tmp_path / "bundle"
    package = bundle / "node_modules" / "example"
    package.mkdir(parents=True)
    (package / "package.json").write_text(json.dumps({"name": "example", "version": "1.2.3", "license": "MIT"}))
    (package / "LICENSE").write_text("Preserve this original license text.\n")
    (package / ".env").write_text("SECRET_TEST_MUST_NOT_COPY=hidden")
    nested = package / "node_modules" / "unknown"
    nested.mkdir(parents=True)
    (nested / "package.json").write_text(json.dumps({"name": "unknown", "version": "2.0"}))
    info = bundle / "example_python-1.0.dist-info"
    info.mkdir()
    (info / "METADATA").write_text("Name: example-python\nVersion: 1.0\nLicense: LGPL-3.0\n")
    (info / "LICENSE.txt").write_text("Python component license")
    output = tmp_path / "report"
    summary = licenses.collect(bundle, output)
    data = json.loads((output / "license-inventory.json").read_text())
    npm = next(c for c in data["components"] if c["name"] == "example")
    unknown = next(c for c in data["components"] if c["name"] == "unknown")
    assert len(npm["license_texts"]) == 1
    assert "LICENSE_TEXT_MISSING" in unknown["review_flags"]
    assert "LICENSE_DECLARATION_UNKNOWN" in unknown["review_flags"]
    assert summary["clearance"] == "REVIEW_REQUIRED"
    assert "example-python==1.0" in (output / "requirements-bundled.lock").read_text()
    assert not any("SECRET_TEST_MUST_NOT_COPY" in f.read_text(errors="ignore") for f in output.rglob("*") if f.is_file())
    with pytest.raises(ValueError, match="fresh output"):
        licenses.collect(bundle, output)


def test_toc_uses_literal_parser_and_finds_sources(tmp_path):
    toc = tmp_path / "Analysis-00.toc"
    source = tmp_path / "thing.py"
    toc.write_text(repr((["hello", ["nested"], []], [("thing", str(source), "PYMODULE")], {})), encoding="utf-8")
    assert str(source.resolve()).casefold() in licenses.toc_sources(toc)
    toc.write_text("__import__('os').getcwd()")
    with pytest.raises(ValueError):
        licenses.toc_sources(toc)


def test_binary_license_is_rejected_and_original_bytes_retained(tmp_path):
    src = tmp_path / "LICENSE"
    dst = tmp_path / "out.txt"
    src.write_bytes(b"copyright \xff\n")
    result = licenses.copy_text(src, dst, "fixture:LICENSE")
    assert result["sha256"] == licenses.digest(src)
    assert dst.read_bytes() == src.read_bytes()
    src.write_bytes(b"\x00secret")
    assert licenses.copy_text(src, tmp_path / "rejected", "fixture") is None


def test_supplement_requires_matching_component_and_content_digest(tmp_path):
    bundle=tmp_path/'bundle';info=bundle/'example-1.0.dist-info';info.mkdir(parents=True)
    (info/'METADATA').write_text('Name: example\nVersion: 1.0\n')
    license_file=tmp_path/'LICENSE';license_file.write_text('Exact original license text')
    supplement=tmp_path/'supplements.json'
    row={'ecosystem':'pypi','name':'example','version':'1.0','path':'LICENSE',
         'sha256':licenses.digest(license_file),'status':'FETCHED_OFFICIAL_VERSION_TAG',
         'source_url':'https://example.test/v1.0/LICENSE'}
    supplement.write_text(json.dumps({'components':[row]}))
    licenses.collect(bundle,tmp_path/'report',supplements=supplement)
    report=json.loads((tmp_path/'report'/'license-inventory.json').read_text())
    component=next(c for c in report['components'] if c['name']=='example')
    assert component['license_texts'] and component['evidence'][-1]['version_binding']=='FETCHED_OFFICIAL_VERSION_TAG'
    license_file.write_text('Changed bytes')
    with pytest.raises(ValueError,match='hash mismatch'):
        licenses.collect(bundle,tmp_path/'changed-report',supplements=supplement)
