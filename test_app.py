# test_app.py
#
# Unit tests for app.py, run with pytest. These are executed by the
# Jenkins pipeline (see Jenkinsfile, stage "Run Tests") before the
# Docker image is built, so that a broken app never gets packaged or
# deployed to Kubernetes.
import pytest
from app import app, add

@pytest.fixture
def client():
    """Provides a Flask test client for use in the test functions below.

    pytest fixtures let multiple tests share the same setup code without
    repeating it. Any test function that takes ``client`` as an argument
    automatically receives the value this fixture yields.

    Yields:
        flask.testing.FlaskClient: A client that can make fake HTTP
        requests (GET/POST/etc.) directly against the app in-process,
        without needing a real running server or network connection.
    """
    # TESTING mode disables error catching during request handling, so
    # exceptions raised inside routes propagate to the test instead of
    # being turned into a generic 500 response — this makes failures
    # easier to diagnose.
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    """Verifies the "/" route responds successfully with the expected greeting text."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello from CI/CD Pipeline" in response.data

def test_health(client):
    """Verifies the "/health" route responds with HTTP 200 and a JSON status of "ok",
    confirming the endpoint Kubernetes uses for health checks behaves correctly."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"

def test_add():
    """Verifies the add() helper handles both a normal case and a case involving a negative number."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0