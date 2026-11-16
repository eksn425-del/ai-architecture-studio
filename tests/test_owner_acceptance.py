import hashlib
import os

from tests.test_reconstruction_integration import setup_project, send


def test_saved_plan_is_an_immutable_conversation_snapshot(tmp_path):
    client, _, _, project = setup_project(tmp_path)
    response = send(client, "plan")
    assert response.status_code == 200
    messages = response.json()["project"]["context"]["conversation"]
    metadata = messages[-1]["metadata"]
    original = metadata["plan_text"]
    assert hashlib.sha256(original.replace("\r\n", "\n").encode()).hexdigest() == metadata["plan_sha256"]
    (project / "runtime/agent_workspace/notes/reconstruction_card.md").write_text("changed future plan", encoding="utf-8")
    saved = client.get("/api/projects/demo-cultural-center").json()["context"]["conversation"]
    assert saved[-1]["metadata"]["plan_text"] == original
    from app.models import ProjectContext
    from app.reconstruction_runtime import reconstruction_context_payload
    context = ProjectContext.model_validate(client.get("/api/projects/demo-cultural-center").json()["context"])
    payload = reconstruction_context_payload(context)
    assert all("plan_text" not in m["metadata"] for m in payload["recent_conversation"])


def test_recent_projects_sort_by_saved_activity_instead_of_identifier(tmp_path):
    client, _, _, project = setup_project(tmp_path)
    client.post("/api/projects", json={"project_name": "A oldest"})
    latest = client.post("/api/projects", json={"project_name": "Z newest"}).json()["project_id"]
    newest = project.parent / latest / "state/project_context.json"
    os.utime(newest, (2000000000, 2000000000))
    rows = client.get("/api/projects").json()
    assert rows[0]["project_id"] == latest
    assert rows[0]["updated_at"] == 2000000000
