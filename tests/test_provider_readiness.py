"""Do not advertise a documented API model as an implemented K Studio builder."""
from fastapi.testclient import TestClient
from app.provider_readiness import CAPABILITY_MATRIX, readiness_matrix, standalone_premium_ready
from app.litellm_runtime import requires_responses_tools


def test_official_sol_astra_are_api_candidates_not_live_product_builders():
    assert requires_responses_tools("gpt-6.1-sol")
    assert requires_responses_tools("openai/gpt-6-astra")
    assert standalone_premium_ready() is False
    matrix = readiness_matrix()
    assert len(matrix) == len(CAPABILITY_MATRIX)
    for row in matrix:
        if row["model_id"] in {"gpt-6.1-sol", "gpt-6-astra"} and row["route"] != "codex_app_server":
            assert row["product_status"] != "native_product_verified"
            assert row["product_status"] != "release_ready"
    assert all("api_key" not in row for row in matrix)


def test_provider_readiness_api_does_not_expose_or_infer_credentials(tmp_path, monkeypatch):
    from app.main import create_app
    # Construct a fresh local test server, avoid real provider/network.
    app = create_app(runtime_root=tmp_path)
    with TestClient(app) as client:
        response = client.get("/api/provider-readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["independent_sol_astra_responses_modeling"] == "implemented_offline_verified_live_not_run"
    assert body["standalone_public_beta"] == "not_certified"
    assert len(body["models"]) >= 4
    assert "sk-" not in response.text
