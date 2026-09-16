# Dockerfile
#
# Builds the container image for the Flask app defined in app.py. This
# image is what the Jenkins pipeline (see Jenkinsfile, stages "Build
# Docker Image" / "Push Docker Image") builds and pushes to Docker Hub,
# and what Kubernetes (see k8s/deployment.yaml) ultimately runs as pods.

# python:3.11-slim is a minimal Debian-based Python image — much smaller
# than the full python:3.11 image, which keeps the final image size down
# and reduces the attack surface, at the cost of not having some OS
# packages preinstalled (not needed here).
FROM python:3.11-slim

# All subsequent instructions (COPY, RUN, CMD) execute relative to this
# directory inside the container.
WORKDIR /app

# Copy only requirements.txt first (before the rest of the source code)
# and install dependencies here. Docker caches each layer, so as long as
# requirements.txt doesn't change, this layer is reused on rebuilds even
# if app.py changes — this avoids reinstalling dependencies every build.
COPY requirements.txt .
# --no-cache-dir keeps pip from storing its download cache in the image,
# which would otherwise bloat the final image size unnecessarily.
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the project (app.py, etc.) into the image.
COPY . .

# Documents that the app listens on port 5000. This is metadata only —
# it doesn't actually publish the port; that's done separately via
# `docker run -p` or, in this project, via the Kubernetes Service
# (k8s/deployment.yaml).
EXPOSE 5000

# Run the app with gunicorn, a production-grade WSGI server, instead of
# Flask's built-in development server (which is single-threaded and not
# meant for production use). "app:app" means "import the `app` object
# from the `app` module (app.py)".
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]