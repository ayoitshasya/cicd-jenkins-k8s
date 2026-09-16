// Jenkinsfile
//
// Declarative Jenkins pipeline definition for this project's CI/CD
// process. This is the orchestrator that ties everything else in the
// repo together: it tests app.py (using test_app.py), builds the
// container image described in Dockerfile, pushes it to Docker Hub, and
// deploys it to Kubernetes using k8s/deployment.yaml. Jenkins runs this
// file automatically (e.g. on each commit/PR, depending on job
// configuration) rather than a human running these steps by hand.
pipeline {
    // "any" means Jenkins can run this pipeline on any available agent
    // (build machine) — there's no requirement for a specific label,
    // e.g. a particular OS or set of pre-installed tools.
    agent any

    // Environment variables available to every stage below.
    environment {
        // Pulls the Docker Hub username/password from a Jenkins
        // credential named "dockerhub-creds" (configured in Jenkins,
        // not in this repo). This automatically exposes both the
        // combined value and the split
        // DOCKERHUB_CREDENTIALS_USR / DOCKERHUB_CREDENTIALS_PSW
        // variables used later in the "Push Docker Image" stage.
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-creds')
        // Docker Hub repository the built image gets pushed to.
        IMAGE_NAME = "ayoitshasya/cicd-app"
        // Tags each image build with Jenkins' own incrementing build
        // number, so every pipeline run produces a uniquely
        // identifiable image (in addition to a shared "latest" tag).
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitHub...'
                // "checkout scm" pulls the exact revision that
                // triggered this pipeline run, using whatever source
                // control configuration (repo URL, branch, credentials)
                // is set on the Jenkins job itself.
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing Python dependencies...'
                // --break-system-packages is needed because modern
                // Debian/Ubuntu Python installations mark the system
                // Python as "externally managed" and refuse plain `pip
                // install` outside a virtual environment; this flag
                // overrides that protection so dependencies install
                // directly on the Jenkins agent.
                sh 'pip install --break-system-packages -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running unit tests...'
                // Runs the pytest suite in test_app.py and writes
                // results in JUnit XML format to result.xml, which the
                // "post" block below feeds to the `junit` step so
                // Jenkins can display test results/trends in its UI.
                sh 'python3 -m pytest test_app.py --junitxml=result.xml'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'
                // Builds the image from the Dockerfile in the repo
                // root and tags it two ways: once with this build's
                // unique IMAGE_TAG (for traceability/rollback) and once
                // with "latest" (what most deployments default to
                // pulling).
                sh 'docker build -t $IMAGE_NAME:$IMAGE_TAG -t $IMAGE_NAME:latest .'
            }
        }

        stage('Push Docker Image') {
            steps {
                echo 'Pushing image to Docker Hub...'
                // Logs in to Docker Hub non-interactively by piping the
                // password through stdin, which avoids the password
                // ever appearing as a plain command-line argument
                // (where it could leak into shell history or process
                // listings).
                sh 'echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin'
                // Push both tags built in the previous stage.
                sh 'docker push $IMAGE_NAME:$IMAGE_TAG'
                sh 'docker push $IMAGE_NAME:latest'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                echo 'Deploying to Kubernetes cluster...'
                // Ensures the Deployment/Service objects described in
                // k8s/deployment.yaml exist and match what's in the
                // repo (creates them on first run, updates them on
                // later runs if the manifest changed).
                sh 'kubectl apply -f k8s/deployment.yaml'
                // Explicitly points the deployment at this build's
                // uniquely tagged image (rather than relying on
                // "latest", which Kubernetes may not re-pull if it
                // thinks it already has that tag cached) — this is what
                // actually triggers the rolling update to the new
                // version.
                sh 'kubectl set image deployment/cicd-app-deployment cicd-app=$IMAGE_NAME:$IMAGE_TAG'
                // Blocks until the rolling update finishes successfully
                // (or fails), so the pipeline doesn't report success
                // before the new pods are actually up and healthy.
                sh 'kubectl rollout status deployment/cicd-app-deployment'
            }
        }

        stage('Archive Artifact') {
            steps {
                echo 'Archiving app.py as build artifact...'
                // Saves a copy of app.py with this specific build in
                // Jenkins' build history, with a fingerprint (checksum)
                // so Jenkins can track which builds/downstream jobs
                // used this exact file — useful for auditing what code
                // was actually deployed for a given build number.
                archiveArtifacts artifacts: 'app.py', fingerprint: true
            }
        }
    }

    // Post-build actions that run after all stages complete, regardless
    // of (or depending on) the overall pipeline result.
    post {
        always {
            // Publishes the JUnit test results generated in the "Run
            // Tests" stage so Jenkins shows pass/fail counts and
            // trends. allowEmptyResults avoids failing the pipeline
            // just because result.xml is missing (e.g. if the Run
            // Tests stage itself never got that far).
            junit allowEmptyResults: true, testResults: 'result.xml'
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check console output.'
        }
    }
}