from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_homepage_loads() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Mock mode" in response.text


def test_example_contains_candidate_language() -> None:
    response = client.get("/api/example")
    assert response.status_code == 200
    assert "Possible candidate" in response.json()["source_text"]


def test_mock_analysis_has_panels_and_trace() -> None:
    text = "Possible candidate: Jordan Reed — 93% similarity. Identity unverified. Jordan Reed identified as suspect."
    response = client.post("/api/analyze", json={"source_text": text, "provider": "mock"})
    body = response.json()
    assert response.status_code == 200
    assert body["provider"] == "mock"
    assert all(layer in body for layer in ("pal", "pecan", "pea", "seed"))
    assert any(item["layer"] == "PAL" for item in body["trace"])
    assert "not an identification" in body["seed"]["findings"][0]["safer_wording"].lower()


def test_blank_text_is_rejected() -> None:
    response = client.post("/api/analyze", json={"source_text": "   "})
    assert response.status_code == 422


def test_provider_status_exposes_only_safe_booleans(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "present-for-test-only")
    response = client.get("/api/provider-status")
    body = response.json()
    assert response.status_code == 200
    assert body["openai_api_key_exists"] is True
    assert body["openai_api_key_nonempty"] is True
    assert body["environment_source"] == "process_environment"
