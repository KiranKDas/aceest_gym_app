# ACEest Fitness & Gym - Automated CI/CD DevOps Pipeline

[![Jenkins Pipeline](https://img.shields.io/badge/Jenkins-Pipeline%20Passed-blue.svg?logo=jenkins)](Jenkinsfile)
[![Pytest Coverage](https://img.shields.io/badge/Pytest-Coverage%2092%25-brightgreen.svg?logo=pytest)](reports/junit.xml)
[![SonarQube](https://img.shields.io/badge/SonarQube-Quality%20Gate%20Passed-success.svg?logo=sonarqube)](sonar-project.properties)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-5%20Deploy%20Strategies-326CE5.svg?logo=kubernetes)](k8s/)
[![Docker Hub](https://img.shields.io/badge/Docker-Hub%20Ready-2496ED.svg?logo=docker)](Dockerfile)

**Course:** Introduction to DEVOPS (Merged - CSIZG514 / SEZG514) (S1-25)  
**Student:** Kiran K Das (Student ID: `2025TM93130`)  
**Institution:** BITS Pilani - Work Integrated Learning Programmes (WILP)  
**Repository:** https://github.com/KiranKDas/aceest_gym_app  

---

## 📌 Executive Summary

**ACEest Fitness & Gym** is a scalable, cloud-native fitness and gym management web application built on **Flask** with SQLite persistence and RESTful microservices. Originally prototyped in Assignment 1, this project demonstrates the complete **Assignment 2** enterprise DevOps lifecycle:
1. **Application Evolution**: Migration and modularization of 10 incremental application versions (`versions/` and `ACEest_Fitness.py`).
2. **Version Control**: Git workflow with semantic release tags (`v1.0.0` to `v3.0.0`) and structured branching.
3. **Automated Testing**: 23 Pytest unit/integration tests with **92% statement code coverage**.
4. **Code Quality**: SonarQube Scanner integration with zero-defect Quality Gate enforcement.
5. **Containerization**: Multi-stage, non-root hardened Docker/Podman container images.
6. **Continuous Integration**: 11-stage Declarative Jenkins Pipeline with automated rollback.
7. **Continuous Delivery**: **5 Kubernetes Deployment Strategies** (Rolling Update, Blue-Green, Canary, Shadow, A/B Testing).

---

## 🏗️ End-to-End CI/CD Architecture

```
 Developer Workspace -> Git Commit / Tag -> GitHub (KiranKDas/aceest_gym_app)
                                                |
                                    Webhook / Polling Trigger
                                                v
               +----------------------------------------------------------------+
               |                  Jenkins Declarative Pipeline                  |
               |----------------------------------------------------------------|
               | Stage 1:  SCM Checkout (Git Commit & Branch Tracking)          |
               | Stage 2:  Dependency Setup & PEP-8 Linting (Flake8)            |
               | Stage 3:  Automated Pytest Suite (92% Coverage & JUnit XML)    |
               | Stage 4:  SonarQube Static Analysis Scanner                    |
               | Stage 5:  SonarQube Quality Gate Gatekeeper (Abort on Defect)  |
               | Stage 6:  Podman / Docker Multi-Stage Container Packaging      |
               | Stage 7:  Container Vulnerability Scanning (Trivy)             |
               | Stage 8:  Docker Hub Registry Distribution (:3.0.0 & :latest)  |
               | Stage 9:  Kubernetes Staging Cluster Deployment                |
               | Stage 10: Automated Health & Readiness Probes (/health)        |
               | Stage 11: Production Progressive Deployment                     |
               +-------------------------------+--------------------------------+
                                               |
             +--------------------+------------+------------+--------------------+
             |                    |                         |                    |
       RollingUpdate          Blue-Green                  Canary               Shadow / A/B
     (Zero-Downtime)      (Instant Cutover)             (10% Slice)         (Dark / Experiment)
```

---

## 📂 Repository Structure

```
aceest_gym_app/
├── app.py                    # Modular Flask Application & REST API
├── ACEest_Fitness.py         # Assignment 2 Unified WSGI Entrypoint
├── versions/                 # Original Code Versions from Assignment 1 & 2
│   ├── Aceestver-1.0.py      # v1.0.0 Basic Catalog & Routines
│   ├── Aceestver-1.1.py      # v1.1.0 Caloric Factors (22, 35, 26 kcal/kg)
│   ├── Aceestver1.1.2.py     # Attendance & Matplotlib UI
│   ├── Aceestver2.0.1.py     # SQLite Persistence Layer
│   ├── Aceestver-2.1.2.py    # Database Constraint Hardening
│   ├── Aceestver-2.2.1.py    # Weight Progress Visualizer
│   ├── Aceestver-2.2.4.py    # Full Workout & Adherence Suite
│   ├── Aceestver-3.0.1.py    # Milestone Release
│   ├── Aceestver-3.1.2.py    # RBAC Auth & PDF Reporting
│   └── Aceestver-3.2.4.py    # Enterprise Gym Application
├── tests/                    # 23 Automated Pytest Cases
│   ├── test_app.py           # Assignment 1 Application & CRUD Tests (15 tests)
│   └── test_assignment2_pipeline.py # Assignment 2 Calorie, BMI, & Pipeline Tests (8 tests)
├── k8s/                      # Kubernetes Orchestration Manifests
│   ├── base/                 # Namespace, ConfigMap, Secret
│   ├── rolling-update/       # maxSurge: 1, maxUnavailable: 0
│   ├── blue-green/           # Blue (v2.2.0) vs Green (v3.0.0) with switch script
│   ├── canary/               # 10% Canary Ingress & Replica Ratio
│   ├── shadow/               # Dark Launch & Traffic Mirroring
│   ├── ab-testing/           # Header (X-Experiment-Group: B) & Cookie Routing
│   └── rollback/             # Automated Rollback & Verification Scripts
├── Dockerfile                # Multi-stage, Non-Root Hardened Container Definition
├── Jenkinsfile               # Declarative 11-Stage Pipeline with Quality Gate & Rollback
├── sonar-project.properties  # SonarQube Scanner Configuration
├── pytest.ini                # Pytest Test Automation & Coverage Flags
├── docker-compose.yml        # Local Developer Stack (App + SonarQube + Postgres)
├── build_and_push.sh         # Podman/Docker Image Build & Tagging Utility
└── requirements.txt          # Python Dependencies
```

---

## 🚀 Progressive Kubernetes Deployment Strategies

| Strategy | Manifest Directory | Mechanism | Verification / Cutover Command |
| :--- | :--- | :--- | :--- |
| **Rolling Update** | `k8s/rolling-update/` | Zero-downtime rolling replacement (`maxSurge: 1`, `maxUnavailable: 0`). | `kubectl set image deployment/aceest-fitness-app aceest-fitness=kirankdas/aceest_gym_app:3.0.0 -n aceest-fitness` |
| **Blue-Green** | `k8s/blue-green/` | Parallel Blue (`v2.2.0`) and Green (`v3.0.0`) pods; instant Service selector cutover. | `bash k8s/blue-green/switch-blue-green.sh green aceest-fitness` (Rollback: `bash k8s/blue-green/switch-blue-green.sh blue aceest-fitness`) |
| **Canary Release** | `k8s/canary/` | Routes 10% of traffic to candidate release (`v3.0.0`) via NGINX Ingress `canary-weight: "10"`. | `kubectl apply -f k8s/canary/ -n aceest-fitness` |
| **Shadow Deployment** | `k8s/shadow/` | Dark launch duplicating live traffic to shadow backend without affecting user response. | `kubectl apply -f k8s/shadow/ -n aceest-fitness` |
| **A/B Testing** | `k8s/ab-testing/` | Routes users based on HTTP Header (`X-Experiment-Group: B`) or session cookie. | `curl -H "X-Experiment-Group: B" http://fitness.aceest.local/` |
| **Emergency Rollback** | `k8s/rollback/` | Immediate reversion to previous stable revision upon probe failure. | `bash k8s/rollback/rollback.sh aceest-fitness-app aceest-fitness` |

---

## 🧪 Local Execution & Testing

```bash
# 1. Setup Virtual Environment & Dependencies
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Run Test Automation Suite with Coverage
pytest

# 3. Static Syntax & Code Style Check
flake8 app.py ACEest_Fitness.py tests/ --max-line-length=120 --ignore=E402,W503

# 4. Build Multi-Tag Container Images with Podman or Docker
chmod +x build_and_push.sh
./build_and_push.sh

# 5. Launch Application
python3 ACEest_Fitness.py
# Verify probe: curl http://localhost:5000/health
```
