import json
import os

import pytest

from tests.test_novice_flow import workspace


@pytest.mark.parametrize("migration", [False, True])
def test_reading_old_project_cannot_overtake_a_new_project(tmp_path, monkeypatch, migration):
    app, client, old, *_ = workspace(tmp_path)
    newest = client.post("/api/projects", json={"project_name": "Newest"}).json()["project_id"]
    path = app.state.store.project_dir(old) / "state/project_context.json"
    os.utime(path, ns=(1_000_000_000, 1_000_000_000))
    original = path.read_bytes()
    if migration:
        def normalize(context, _):
            context.user_intent = "read-migration-fixture"
        monkeypatch.setattr("app.main._reference_attachments", normalize)
    for _ in range(2):
        assert client.get(f"/api/projects/{old}").status_code == 200
        assert path.stat().st_mtime_ns == 1_000_000_000
        assert client.get("/api/projects").json()[0]["project_id"] == newest
    if migration:
        assert json.loads(path.read_text(encoding="utf-8"))["user_intent"] == "read-migration-fixture"
    else:
        assert path.read_bytes() == original
