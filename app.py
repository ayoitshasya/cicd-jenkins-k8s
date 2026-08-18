# app.py
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello from CI/CD Pipeline - Jenkins + Docker + Kubernetes!"

@app.route("/health")
def health():
    return {"status": "ok"}, 200

def add(a, b):
    """Simple function so we have something meaningful to unit test."""
    return a + b

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)