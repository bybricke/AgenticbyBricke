import os
import pytest
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def test_chat_without_api_key_returns_401():
    response = client.post(
        "/chat",
        json={"user_id": "test_user", "texto": "hola"}
    )
    assert response.status_code == 401
    assert "X-API-Key" in response.json().get("detail", "")

def test_chat_with_api_key_returns_200(monkeypatch):
    api_key = os.getenv("API_KEY")
    if not api_key:
        pytest.skip("No API_KEY in env, skipping test")

    def mock_invoke(*args, **kwargs):
        return {"ruta": "preventa", "motivo": "test", "respuesta": "test ok"}
    
    # Parcheamos el grafo para que no llame al LLM real
    monkeypatch.setattr("api.app.graph.invoke", mock_invoke)

    response = client.post(
        "/chat",
        json={"user_id": "test_user", "texto": "hola"},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ruta"] == "preventa"
    assert data["motivo"] == "test"
    assert data["respuesta"] == "test ok"

