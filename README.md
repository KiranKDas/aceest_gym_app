# ACEest Fitness & Gym - Automated CI/CD DevOps Pipeline

[![ACEest CI/CD Pipeline](https://github.com/placeholder-user/aceest-fitness-gym/actions/workflows/main.yml/badge.svg)](https://github.com/placeholder-user/aceest-fitness-gym/actions/workflows/main.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📌 Executive Summary

**ACEest Fitness & Gym** is a lightweight, scalable fitness and gym management web application built on **Flask** with SQLite persistence. This project demonstrates an enterprise-grade DevOps workflow implementing **Version Control Strategy**, **Unit Testing Automation**, **Secure Containerization**, and **Dual-CI/CD Orchestration** across **GitHub Actions** and **Jenkins**.

---

## 🏗️ Architecture & Component Overview

```
                                  +-----------------------------+
                                  |   Developer Workspace       |
                                  | Git Commits (Conventional)  |
                                  +--------------+--------------+
                                                 |
                                           git push / PR
                                                 v
                                  +-----------------------------+
                                  |     GitHub Repository       |
                                  +-------+--------------+------+
                                          |              |
                    Webhook / PR Trigger  |              | Webhook / Polling
                                          v              v
         +-------------------------------------+   +-------------------------------------+
         |     GitHub Actions CI Pipeline      |   |       Jenkins BUILD Pipeline        |
         |-------------------------------------|   |-------------------------------------|
         | 1. Stage 1: Build & Lint (Flake8)   |   | 1. Git SCM Checkout (Clean Workspace)|
         | 2. Stage 2: Docker Image Assembly   |   | 2. Virtualenv / Dependency Install  |
         | 3. Stage 3: Containerized Pytest Run|   | 3. Smoke Test / Pytest Execution    |
         +-------------------------------------+   | 4. Quality Gate Status Reporting    |
                                                   +-------------------------------------+
```

### Core Application Capabilities
- **Role-based Authentication**: Secure authentication endpoint (`/api/auth/login`).
- **Client Profile & Member Management**: Complete intake and profile lifecycle (`/api/clients`).
- **AI Workout Program Recommendation**: Routine generator (`/api/clients/<name>/generate-program`).
- **Membership Status Tracking**: Real-time membership renewal and validity check (`/api/clients/<name>/membership`).
- **Workout & Exercise Logging**: Track workouts with sets, reps, and poundage (`/api/workouts`, `/api/exercises`).
- **Biometrics & Adherence Analytics**: Log body weight, waist, body fat, and adherence (`/api/metrics`, `/api/progress`).
- **Automated Health Check**: Production readiness and liveness probe (`/health`).

---

## ⚙️ Local Development Setup & Execution

### Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- `pip` and `virtualenv`
- Docker Engine (optional, for containerized run)

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the Application Locally
```bash
python3 app.py
```
The server will bind to `http://127.0.0.1:5000`. You can test it using `curl`:
```bash
curl -s http://127.0.0.1:5000/health
# Response: {"status":"UP","timestamp":"2026-10-07T..."}
```

---

## 🧪 Running Unit Tests Manually

The test suite is built on **Pytest** and exercises internal application logic, SQLite transactions, HTTP status codes, and error boundary conditions.

### Run All Unit Tests with Pytest
```bash
pytest -v
```

### Run Pytest with Detailed Tracebacks and Output
```bash
pytest -v -s --tb=short
```

### Run Code Linter (Flake8)
```bash
flake8 . --count --max-line-length=120 --exclude=venv,.git
```

---

## 🐳 Docker Containerization

The project uses a multi-layered Dockerfile based on `python:3.11-slim`, optimized for minimal image footprint and hardened security (non-root execution with user `appuser`, built-in container health checks, and unbuffered stdout/stderr logging).

### 1. Build the Docker Image
```bash
docker build -t aceest-fitness-gym:latest .
```

### 2. Run the Container
```bash
docker run -d --name aceest-app -p 5000:5000 aceest-fitness-gym:latest
```

### 3. Verify Container Status & Health
```bash
docker ps
curl http://localhost:5000/health
```

### 4. Execute Pytest Suite Inside the Running Container
```bash
docker run --rm aceest-fitness-gym:latest pytest -v
```

---

## 🔄 CI/CD Pipeline Architecture & Integration Logic

This project employs a two-tier Continuous Integration architecture to guarantee code stability, image integrity, and build reproducibility.

### Tier 1: GitHub Actions CI/CD Pipeline (`.github/workflows/main.yml`)
Triggered automatically on every `push` and `pull_request` against the `main` branch. It executes through three sequential, isolated jobs:

1. **Stage 1: Build & Lint Code (`lint-and-build`)**:
   - Checks out repository source code.
   - Configures Python 3.11 environment with cached `pip` packages.
   - Installs runtime and testing dependencies (`requirements.txt`).
   - Executes `flake8` to enforce PEP 8 standards, verifying syntax errors (`E9, F63, F7, F82`) and structural quality.
2. **Stage 2: Docker Image Assembly (`docker-build`)**:
   - Dependent on the success of Stage 1.
   - Configures Docker Buildx engine.
   - Builds the production Docker image adhering to caching best practices.
   - Exports and archives the compiled Docker image artifact for containerized testing.
3. **Stage 3: Containerized Pytest Suite (`containerized-tests`)**:
   - Dependent on the success of Stage 2.
   - Pulls down the assembled Docker container image artifact.
   - Loads the image into the Docker daemon.
   - Runs `pytest -v` **inside the built container environment**, ensuring environmental parity between test and production runtimes.

---

### Tier 2: Jenkins Automated BUILD & Quality Gate
In production and enterprise setups, Jenkins serves as an internal orchestration engine and secondary validation gate:

1. **Source Code Checkout**:
   - Polls GitHub or triggers via webhook on every push.
   - Fetches the clean branch and initializes an isolated workspace.
2. **Clean Environment Isolation**:
   - Creates a disposable Python virtual environment (`python3 -m venv .venv`).
   - Upgrades `pip` and cleanly installs frozen project dependencies (`requirements.txt`).
3. **Execution & Quality Gate Validation**:
   - Executes `flake8` quality checks.
   - Runs `pytest` test suite with JUnit XML reporting output (`pytest --junitxml=reports/results.xml`).
   - In containerized environments, triggers `docker build` and container health validation.
4. **Publishing & Artifact Archival**:
   - Publishes test reports directly to the Jenkins build dashboard.
   - Marks the build `SUCCESS` or halts the deployment on failure (`FAILURE`), ensuring broken builds never proceed to downstream staging/production.

---

## 📜 Version Control Strategy (VCS Maturity)

The Git history simulates a mature software evolution using the **Conventional Commits** specification:
- `feat:` Introduces a new feature or endpoint.
- `fix:` Patches a defect or unexpected behavior.
- `refactor:` Restructures code without changing external functionality.
- `build:` Updates dependency definitions or build tooling.
- `test:` Implements or updates automated unit/integration test suites.
- `ci:` Configures pipeline workflows, Docker builds, and deployment instructions.
- `docs:` Modifies documentation or project guides.

---

## 👥 Contributors & Academic Reference
- **Course**: CSIZG514 / SEZG514 - Introduction to DevOps (BITS Pilani)
- **Application**: ACEest Fitness & Gym Management System
- **Role**: Junior DevOps Engineer
