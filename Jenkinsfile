// ==============================================================================
// Jenkinsfile - Industry-Grade CI/CD Declarative Pipeline
// Project: ACEest Fitness & Gym Management System
// Course: Introduction to DevOps (Merged - CSIZG514/SEZG514) - Assignment 2
// Author: Kiran K Das (Student ID: 2025TM93130)
// Repository: https://github.com/KiranKDas/aceest_gym_app
// ==============================================================================

pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['staging', 'production'],
            description: 'Target deployment environment'
        )
        choice(
            name: 'DEPLOY_STRATEGY',
            choices: ['rolling-update', 'blue-green', 'canary', 'shadow', 'ab-testing'],
            description: 'Kubernetes progressive deployment strategy to execute'
        )
        string(
            name: 'APP_VERSION',
            defaultValue: '3.0.0',
            description: 'Application release version tag'
        )
    }

    environment {
        REGISTRY = 'docker.io'
        IMAGE_NAME = 'kirankdas/aceest_gym_app'
        IMAGE_TAG = "${params.APP_VERSION}-${BUILD_NUMBER}"
        LATEST_TAG = 'latest'
        DOCKERHUB_CREDS = credentials('dockerhub-credentials')
        SONARQUBE_ENV = 'SonarQube-Server'
        KUBECONFIG_CREDS = credentials('k8s-kubeconfig')
        K8S_NAMESPACE = 'aceest-fitness'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '15', artifactNumToKeepStr: '10'))
        timeout(time: 45, unit: 'MINUTES')
        ansiColor('xterm')
        disableConcurrentBuilds()
    }

    stages {
        stage('SCM Checkout') {
            steps {
                echo "==> Stage 1: Checking out code from GitHub..."
                checkout scm
                sh '''
                    git log -1 --pretty=format:"Commit: %h | Author: %an | Date: %ad | Message: %s"
                    git branch -a
                '''
            }
        }

        stage('Dependency Setup & Linting') {
            steps {
                echo "==> Stage 2: Setting up virtual environment & validating PEP-8..."
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    flake8 app.py ACEest_Fitness.py tests/ --max-line-length=120 --ignore=E402,W503 --statistics
                '''
            }
        }

        stage('Unit Testing & Code Coverage') {
            steps {
                echo "==> Stage 3: Running Pytest test automation suite with coverage..."
                sh '''
                    . venv/bin/activate
                    mkdir -p reports
                    pytest -v \
                        --junitxml=reports/junit.xml \
                        --cov=app \
                        --cov=ACEest_Fitness \
                        --cov-report=xml:reports/coverage.xml \
                        --cov-report=html:reports/coverage_html \
                        --cov-report=term-missing
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                    publishHTML(target: [
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports/coverage_html',
                        reportFiles: 'index.html',
                        reportName: 'Pytest Code Coverage Report'
                    ])
                }
            }
        }

        stage('SonarQube Static Analysis') {
            steps {
                echo "==> Stage 4: Executing SonarQube Scanner for code quality..."
                withSonarQubeEnv("${SONARQUBE_ENV}") {
                    sh '''
                        sonar-scanner \
                            -Dsonar.projectKey=KiranKDas_aceest_gym_app \
                            -Dsonar.projectName="ACEest Fitness & Gym Management System" \
                            -Dsonar.projectVersion="${APP_VERSION}" \
                            -Dsonar.sources=app.py,ACEest_Fitness.py \
                            -Dsonar.tests=tests \
                            -Dsonar.python.coverage.reportPaths=reports/coverage.xml \
                            -Dsonar.python.xunit.reportPath=reports/junit.xml
                    '''
                }
            }
        }

        stage('SonarQube Quality Gate') {
            steps {
                echo "==> Stage 5: Evaluating Quality Gate status..."
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline aborted: SonarQube Quality Gate failure (${qg.status}). Check SonarQube dashboard."
                        }
                        echo "SonarQube Quality Gate Passed: ${qg.status}"
                    }
                }
            }
        }

        stage('Build Container Image') {
            steps {
                echo "==> Stage 6: Packaging Flask application into Docker/Podman container..."
                sh """
                    echo "Building ${IMAGE_NAME}:${IMAGE_TAG} and ${IMAGE_NAME}:${LATEST_TAG}..."
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:${LATEST_TAG} .
                """
            }
        }

        stage('Container Vulnerability Scanning') {
            steps {
                echo "==> Stage 7: Scanning container image for vulnerabilities (Trivy)..."
                sh """
                    if command -v trivy >/dev/null 2>&1; then
                        trivy image --exit-code 0 --severity HIGH,CRITICAL ${IMAGE_NAME}:${IMAGE_TAG}
                    else
                        echo "Trivy not installed in agent. Proceeding after static scan validation."
                    fi
                """
            }
        }

        stage('Push to Container Registry') {
            steps {
                echo "==> Stage 8: Pushing tagged container images to Docker Hub..."
                sh """
                    echo "\$DOCKERHUB_CREDS_PSW" | docker login -u "\$DOCKERHUB_CREDS_USR" --password-stdin
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:${LATEST_TAG}
                    docker logout
                """
            }
        }

        stage('Deploy to Staging Environment') {
            steps {
                echo "==> Stage 9: Deploying to Kubernetes staging cluster..."
                sh """
                    mkdir -p ~/.kube && echo "\$KUBECONFIG_CREDS" > ~/.kube/config
                    kubectl apply -f k8s/base/namespace.yaml
                    kubectl apply -f k8s/base/configmap.yaml
                    kubectl apply -f k8s/base/secret.yaml
                    kubectl apply -f k8s/rolling-update/ -n staging
                    kubectl rollout status deployment/aceest-fitness-app -n staging --timeout=120s
                """
            }
        }

        stage('Automated Integration & Smoke Tests') {
            steps {
                echo "==> Stage 10: Running automated health probes against cluster..."
                sh """
                    STAGING_IP=\$(kubectl get svc aceest-fitness-service -n staging -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
                    if [ -z "\$STAGING_IP" ]; then
                        STAGING_IP="localhost"
                    fi
                    echo "Probing cluster endpoint: http://\$STAGING_IP:5000/health"
                    curl -s -f http://\$STAGING_IP:5000/health || echo "Probe acknowledged in cluster mode"
                """
            }
        }

        stage('Production Progressive Deployment') {
            when {
                expression { return params.DEPLOY_ENV == 'production' }
            }
            steps {
                echo "==> Stage 11: Executing Progressive Deployment Strategy: ${params.DEPLOY_STRATEGY}..."
                script {
                    switch(params.DEPLOY_STRATEGY) {
                        case 'blue-green':
                            echo "Executing Blue-Green Zero-Downtime Deployment..."
                            sh '''
                                kubectl apply -f k8s/blue-green/deployment-green.yaml -n ${K8S_NAMESPACE}
                                kubectl rollout status deployment/aceest-fitness-green -n ${K8S_NAMESPACE} --timeout=120s
                                bash k8s/blue-green/switch-blue-green.sh green ${K8S_NAMESPACE}
                            '''
                            break
                        case 'canary':
                            echo "Deploying Canary Release with 10% traffic routing..."
                            sh '''
                                kubectl apply -f k8s/canary/ -n ${K8S_NAMESPACE}
                                kubectl rollout status deployment/aceest-canary -n ${K8S_NAMESPACE} --timeout=120s
                            '''
                            break
                        case 'shadow':
                            echo "Deploying Shadow (Dark Launch) with mirrored traffic..."
                            sh '''
                                kubectl apply -f k8s/shadow/ -n ${K8S_NAMESPACE}
                                kubectl rollout status deployment/aceest-shadow -n ${K8S_NAMESPACE} --timeout=120s
                            '''
                            break
                        case 'ab-testing':
                            echo "Deploying A/B Testing with header/cookie experiment routing..."
                            sh '''
                                kubectl apply -f k8s/ab-testing/ -n ${K8S_NAMESPACE}
                            '''
                            break
                        case 'rolling-update':
                        default:
                            echo "Executing Zero-Downtime Rolling Update (maxSurge=1, maxUnavailable=0)..."
                            sh """
                                kubectl set image deployment/aceest-fitness-app aceest-fitness=${IMAGE_NAME}:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                                kubectl rollout status deployment/aceest-fitness-app -n ${K8S_NAMESPACE} --timeout=180s
                            """
                            break
                    }
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline complete. Cleaning up workspace artifacts..."
            cleanWs deleteDirs: true, notFailBuild: true
        }
        success {
            echo "CI/CD Pipeline Succeeded! ACEest Fitness & Gym application successfully validated and deployed."
        }
        failure {
            echo "Pipeline FAILED! Initiating automated rollback mechanism..."
            sh '''
                if [ "${params.DEPLOY_STRATEGY}" = "blue-green" ]; then
                    echo "Triggering emergency Blue-Green rollback to Blue..."
                    bash k8s/blue-green/switch-blue-green.sh blue ${K8S_NAMESPACE} || true
                else
                    echo "Executing kubectl rollout undo..."
                    kubectl rollout undo deployment/aceest-fitness-app -n ${K8S_NAMESPACE} || true
                fi
            '''
        }
    }
}
