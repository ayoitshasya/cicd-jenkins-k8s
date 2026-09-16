# app.py
#
# This is the main application file for the demo web service used to
# showcase the CI/CD pipeline (Jenkins -> Docker -> Kubernetes) in this
# project. It is a tiny Flask app with just two HTTP endpoints and one
# plain helper function, kept intentionally simple so the pipeline
# stages (test, build, deploy) have something quick and reliable to
# exercise.
#
# Related files:
#   - test_app.py: unit tests that import and exercise this module.
#   - Dockerfile: packages this app into a container image and runs it
#     with gunicorn (a production WSGI server) instead of Flask's
#     built-in dev server.
#   - Jenkinsfile: CI/CD pipeline that installs dependencies, runs the
#     tests in test_app.py, builds the Docker image from this file, and
#     deploys it to Kubernetes.
from flask import Flask

# Create the Flask application instance. `__name__` tells Flask where to
# look for resources (templates, static files) relative to this module;
# we don't use those features here, but Flask still needs the reference.
app = Flask(__name__)

@app.route("/")
def home():
    """Root endpoint ("/").

    Returns a plain-text greeting confirming the app is up and which
    pipeline deployed it. Used as a simple smoke-test target: if this
    responds, the container, service, and networking are all working.

    Returns:
        str: A greeting message with HTTP 200 (Flask's default status
        code when a view function returns just a string).
    """
    return "Hello from CI/CD Pipeline - Jenkins + Docker + Kubernetes!"

@app.route("/health")
def health():
    """Health-check endpoint ("/health").

    Kubernetes (or any monitoring/load-balancer probe) can call this to
    determine whether the pod is alive and ready to serve traffic,
    without depending on the content of the "/" route.

    Returns:
        tuple[dict, int]: A JSON body ``{"status": "ok"}`` together with
        an explicit HTTP 200 status code.
    """
    return {"status": "ok"}, 200

def add(a, b):
    """Simple function so we have something meaningful to unit test.

    Args:
        a: First number to add.
        b: Second number to add.

    Returns:
        The sum of ``a`` and ``b``.
    """
    return a + b

if __name__ == "__main__":
    # This block only runs when the file is executed directly
    # (e.g. `python app.py`), not when it's imported by test_app.py or
    # run via gunicorn in the Docker image. Binding to 0.0.0.0 (rather
    # than the default 127.0.0.1) makes the server reachable from
    # outside the container, which is required for it to work inside
    # Docker/Kubernetes.
    app.run(host="0.0.0.0", port=5000)