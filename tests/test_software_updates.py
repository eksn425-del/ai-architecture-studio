import io
import json
from urllib.error import HTTPError

from app import software_updates as subject


def test_release_discovery_never_enables_automatic_install_or_trusts_asset_urls(tmp_path, monkeypatch):
    payload = {"draft": False, "prerelease": False, "tag_name": "v0.3", "html_url": "https://evil.invalid", "assets": [{"browser_download_url": "file:///secret"}]}
    monkeypatch.setattr(subject, "urlopen", lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
    result = subject.check_release(tmp_path)
    assert result["status"] == "release_available"
    assert result["automatic_install"] is False and result["skills_auto_update"] is False
    assert result["release_url"] == subject.REPOSITORY + "/releases"
    assert "evil" not in str(result) and "secret" not in str(result)


def test_no_release_and_network_failure_are_different(tmp_path, monkeypatch):
    def missing(*args, **kwargs):
        raise HTTPError(subject.RELEASE_API, 404, "missing", {}, None)
    monkeypatch.setattr(subject, "urlopen", missing)
    assert subject.check_release(tmp_path)["status"] == "no_release"
    monkeypatch.setattr(subject, "urlopen", lambda *a, **k: io.BytesIO(b"not json"))
    assert subject.check_release(tmp_path)["status"] == "check_failed"


def test_pre_release_cannot_be_offered_as_stable(tmp_path, monkeypatch):
    monkeypatch.setattr(subject, "urlopen", lambda *a, **k: io.BytesIO(b'{"draft":false,"prerelease":true,"tag_name":"candidate"}'))
    assert subject.check_release(tmp_path)["status"] == "check_failed"
