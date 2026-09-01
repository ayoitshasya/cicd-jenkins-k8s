# CI/CD Pipeline with Jenkins, Docker & Kubernetes

An end-to-end DevOps pipeline built to demonstrate how modern software delivery is automated — from a developer pushing code to GitHub, all the way to a running, healthy application on a Kubernetes cluster, with zero manual steps in between.

---

## Table of Contents

- [About This Project](#about-this-project)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [How the Pipeline Works](#how-the-pipeline-works)
- [What Was Built](#what-was-built)
- [Challenges Faced & How They Were Solved](#challenges-faced--how-they-were-solved)
- [Running the App Locally](#running-the-app-locally)
- [Running Tests](#running-tests)
- [Building & Running with Docker](#building--running-with-docker)
- [Deploying to Kubernetes](#deploying-to-kubernetes)
- [Setting Up Jenkins for This Project](#setting-up-jenkins-for-this-project)
- [Key Learnings](#key-learnings)
- [Author](#author)

---

## About This Project

The goal of this project was to build a **real, working CI/CD pipeline** — not just read about one. It answers a simple question: *what actually happens between "I pushed my code" and "my app is live"?*

To answer that, I built a small Flask web application, containerized it with Docker, wrote Kubernetes manifests to run it in a cluster, and wrote a Jenkins pipeline (`Jenkinsfile`) that ties all of it together. The result is a pipeline where a single `git push` to GitHub is enough to automatically:

1. Pull the latest code
2. Install dependencies
3. Run the automated test suite
4. Build a Docker image
5. Push that image to Docker Hub
6. Deploy the new image to a Kubernetes cluster
7. Archive a build artifact for traceability

No manual "click to deploy" step exists anywhere in this flow — Jenkins watches the repository and reacts on its own.

## Architecture

```
Developer                GitHub                    Jenkins                  Docker Hub          Kubernetes
    │                       │                          │                         │                    │
    │── git push ──────────►│                          │                         │                    │
    │                       │◄── Poll SCM (detects ────│                         │                    │
    │                       │     new commit) ─────────►                         │                    │
    │                       │                          │── checkout ─────────────│                    │
    │                       │                          │── pip install ──────────│                    │
    │                       │                          │── pytest (unit tests) ──│                    │
    │                       │                          │── docker build ─────────│                    │
    │                       │                          │── docker push ─────────►│                    │
    │                       │                          │── kubectl apply ────────┼───────────────────►│
    │                       │                          │── archive artifact ─────│                    │
    │                       │                          │                         │      2 pods Running │
```

## Tech Stack

| Layer | Technology |
|---|---|
| Application | Python 3 + Flask |
| Testing | Pytest |
| Containerization | Docker |
| CI/CD Orchestration | Jenkins (Declarative Pipeline) |
| Container Registry | Docker Hub |
| Deployment Target | Kubernetes (kubectl) |
| Environment | Killercoda (sandboxed Kubernetes + Docker playground) |

## Project Structure

```
cicd-jenkins-k8s/
├── app.py                # Flask application with two routes
├── test_app.py             # Unit tests (pytest)
├── requirements.txt        # Python dependencies
├── Dockerfile               # Instructions to containerize the app
├── Jenkinsfile               # Declarative pipeline definition
└── k8s/
    └── deployment.yaml       # Kubernetes Deployment + NodePort Service
```

### `app.py`
A minimal Flask app with two endpoints:
- `GET /` — returns a plain-text greeting confirming the deployed version is live
- `GET /health` — returns `{"status": "ok"}`, useful as a Kubernetes readiness/liveness check in a real-world setup

### `test_app.py`
Three unit tests using Flask's test client and pytest, verifying both routes respond correctly and a simple helper function behaves as expected. These tests run automatically inside the pipeline before any image is built — if they fail, the pipeline stops and nothing gets deployed.

### `Dockerfile`
Builds a lightweight image on top of `python:3.11-slim`, installs dependencies, copies the app, and runs it with `gunicorn` (a production-grade WSGI server) rather than Flask's built-in dev server.

### `k8s/deployment.yaml`
Defines a `Deployment` with 2 replicas (so the app has basic redundancy) and a `NodePort` `Service` exposing it on port `30080`.

### `Jenkinsfile`
The heart of the automation — a Declarative Pipeline with 7 stages (Checkout → Install Dependencies → Run Tests → Build Docker Image → Push Docker Image → Deploy to Kubernetes → Archive Artifact), plus a `post` block that always publishes test results regardless of success or failure.

## How the Pipeline Works

1. **Trigger** — Jenkins is configured with **Poll SCM**, checking the GitHub repository every minute for new commits. (A GitHub webhook would be faster and push-based, but Poll SCM was used here because the Jenkins instance runs inside a sandboxed environment without a publicly reachable URL.)
2. **Checkout** — Jenkins clones the latest commit from `main`.
3. **Install Dependencies** — `pip install` runs against `requirements.txt` inside the Jenkins container itself.
4. **Run Tests** — `pytest` runs the full test suite and generates a JUnit XML report, which Jenkins displays as a "Tests" trend.
5. **Build Docker Image** — the app is containerized and tagged with both the current Jenkins build number and `latest`.
6. **Push Docker Image** — the image is pushed to Docker Hub using credentials stored securely in Jenkins (never hardcoded in the pipeline).
7. **Deploy to Kubernetes** — `kubectl apply` updates the running Deployment with the freshly built image, and `kubectl rollout status` waits until the rollout is confirmed healthy.
8. **Archive Artifact** — `app.py` is saved as a build artifact, so the exact source file behind any given build can be downloaded later, independent of the current state of the repository.

## What Was Built

- A working Flask application with tests
- A Docker image, published to a public Docker Hub repository
- A Kubernetes Deployment and Service running that image, verified reachable and returning the expected response
- A fully automated Jenkins pipeline, triggered purely by `git push`
- Multiple successful pipeline runs, including both manually triggered builds ("Build Now") and automatically triggered builds (via Poll SCM detecting new commits)

## Challenges Faced & How They Were Solved

Building this pipeline surfaced a series of real, practical DevOps problems — the kind that don't show up when just reading tutorials. Each one was diagnosed from Jenkins' console output and fixed:

| Problem | Root Cause | Fix |
|---|---|---|
| `pip: not found` | Base `jenkins/jenkins:lts` image has no Python installed | Installed `python3` and `python3-pip` inside the running Jenkins container |
| `externally-managed-environment` error on `pip install` | Debian 12+ blocks system-wide pip installs by default (PEP 668) | Added `--break-system-packages` flag to the `pip install` command |
| `invalid reference format` on `docker build` | Left a literal `<YOUR_DOCKERHUB_USERNAME>` placeholder in the `Jenkinsfile` and `deployment.yaml` | Replaced the placeholder with the actual Docker Hub username |
| `permission denied` connecting to Docker socket | The `jenkins` user inside the container lacked permission to use the mounted `docker.sock` | Ran `chmod 666` on the Docker socket to grant access |
| `kubectl` returning Jenkins' own login page instead of cluster data | The kubeconfig was mounted to `/root/.kube`, but Jenkins pipeline steps run as the `jenkins` user (home directory `/var/jenkins_home`), so `kubectl` never found it | Copied the kubeconfig into `/var/jenkins_home/.kube/config` and fixed ownership |

After resolving these five issues, the pipeline ran end-to-end without errors, confirmed by a full green build and a live, reachable deployment.

## Running the App Locally

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`.

## Running Tests

```bash
pytest test_app.py
```

## Building & Running with Docker

```bash
docker build -t cicd-app .
docker run -p 5000:5000 cicd-app
```

## Deploying to Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods
kubectl get deployment cicd-app-deployment
kubectl get svc cicd-app-service
curl http://localhost:30080
```

## Setting Up Jenkins for This Project

1. Run Jenkins as a Docker container with access to the Docker socket and `kubectl`:
   ```bash
   docker run -d --name jenkins \
     -p 8080:8080 -p 50000:50000 \
     -v jenkins_home:/var/jenkins_home \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v $(which docker):/usr/bin/docker \
     -v $(which kubectl):/usr/bin/kubectl \
     -v $HOME/.kube:/root/.kube \
     jenkins/jenkins:lts
   ```
2. Unlock Jenkins, install suggested plugins, and create an admin user.
3. Add Docker Hub credentials under **Manage Jenkins → Credentials**, with ID `dockerhub-creds`.
4. Create a new **Pipeline** job pointing at this repository, with:
   - **Definition:** Pipeline script from SCM
   - **SCM:** Git → this repository's URL, branch `main`
   - **Script Path:** `Jenkinsfile`
   - **Build Trigger:** Poll SCM (schedule: `* * * * *`)
5. Click **Build Now** for the first run — subsequent builds trigger automatically on every push.

## Key Learnings

- CI/CD is as much about **environment setup and permissions** as it is about writing pipeline scripts — most of the real work here was fixing infrastructure issues (missing dependencies, socket permissions, config file locations), not the Jenkinsfile logic itself.
- Automated testing embedded directly in the pipeline (rather than as a separate manual step) genuinely prevents broken code from ever reaching the build/deploy stages.
- Build artifacts and container image tags provide traceability — a specific Jenkins build number maps directly to a specific Docker image tag, making rollbacks and audits possible.
- Poll SCM vs. webhooks is a real trade-off in constrained environments: webhooks are faster and more efficient, but require a publicly reachable Jenkins URL that isn't always available (e.g., in a sandboxed lab).

## Author

**Hasya Sahithya Abburi**
Final-year B.Tech IT (AI Honours), K. J. Somaiya School of Engineering