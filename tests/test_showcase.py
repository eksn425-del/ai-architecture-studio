import re

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import FakeBrain, FakeSketchUp


def test_case_study_route_and_curated_images_are_served(tmp_path):
    app = create_app(tmp_path / "runtime", brain=FakeBrain(), sketchup=FakeSketchUp())
    client = TestClient(app)

    page = client.get("/showcase")
    assert page.status_code == 200
    assert "GPT-6 ASTRA" in page.text
    assert "20,900" in page.text
    assert "非施工图" in page.text
    assert re.search(r"\b[A-Z]:[\\/]", page.text, re.IGNORECASE) is None

    for asset in ("massing-current.webp", "site-plan.webp", "ground-floor.webp", "seventh-floor.webp"):
        response = client.get(f"/static/showcase/assets/{asset}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/webp")
        assert response.content.startswith(b"RIFF")
