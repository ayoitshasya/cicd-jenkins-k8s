# test_app.py
import pytest
from app import app, add

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello from CI/CD Pipeline" in response.data

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0