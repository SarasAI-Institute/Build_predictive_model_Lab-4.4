# MODULE 4 | LAB 4.4
# File: 04_docker_deploy.py
# Purpose: Generate all Docker deployment files and verify the setup
#          Dockerfile, docker-compose.yml, .env, .dockerignore
#          GitHub Actions CI pipeline
#          Cold-start verification script
# Saras AI Institute | Build Predictive Models & Modern Recommenders

import os
import json
import time
import subprocess
import requests
import pickle
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("  MODULE 4 | LAB 4.4")
print("  Docker Containerization + CI Pipeline")
print("=" * 60)

# ---------------------------------------------------------------------------
# SECTION 1: Generate Dockerfile
# ---------------------------------------------------------------------------
print("\n[1] Generating Dockerfile...")

dockerfile_content = '''# =============================================================================
# Dockerfile — Hybrid Recommender API
# Saras AI Institute | Build Predictive Models & Modern Recommenders
# =============================================================================

# Use Python 3.11 slim for smaller image size
FROM python:3.11-slim

# Metadata
LABEL maintainer="Saras AI Institute"
LABEL description="Hybrid Recommender API — LightFM + ALS"
LABEL version="1.0.0"

# Set working directory inside container
WORKDIR /app

# Install system dependencies needed for ML libraries
# libgomp1 is required by LightGBM and implicit (ALS)
RUN apt-get update && apt-get install -y \\
    libgomp1 \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching)
# If requirements.txt hasn't changed, this layer is cached
COPY requirements_module4.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements_module4.txt

# Copy application code
COPY app.py .

# Copy data artifacts (pkl files)
# In production: mount these as volumes instead of copying
COPY data/ ./data/

# Create output directory
RUN mkdir -p output

# Expose port 8000 for FastAPI
EXPOSE 8000

# Health check — Docker will call this every 30s
# If it fails 3 times, Docker marks the container unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD python -c "import requests; requests.get(\\'http://localhost:8000/health\\').raise_for_status()" \\
    || exit 1

# Environment variables with defaults
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV REDIS_TTL=3600
ENV ARTIFACTS_DIR=data
ENV TOP_K=10
ENV INTERACTION_THRESHOLD=3

# Run the FastAPI server with uvicorn
# --host 0.0.0.0 makes it accessible outside the container
# --workers 1 for demo (production: use gunicorn with multiple workers)
CMD ["uvicorn", "app:app", \\
     "--host", "0.0.0.0", \\
     "--port", "8000", \\
     "--workers", "1", \\
     "--log-level", "info"]
'''

with open("Dockerfile", "w") as f:
    f.write(dockerfile_content)
print("    Created -> Dockerfile")

# ---------------------------------------------------------------------------
# SECTION 2: Generate docker-compose.yml
# ---------------------------------------------------------------------------
print("\n[2] Generating docker-compose.yml...")

compose_content = '''# =============================================================================
# docker-compose.yml — Hybrid Recommender Stack
# Saras AI Institute | Build Predictive Models & Modern Recommenders
# =============================================================================
# Usage:
#   docker compose up          -> start all services
#   docker compose up -d       -> start in background (detached)
#   docker compose down        -> stop all services
#   docker compose logs -f app -> follow app logs
#   docker compose ps          -> check service status

version: "3.9"

services:

  # ---------------------------------------------------------------------------
  # Redis — Caching Layer
  # ---------------------------------------------------------------------------
  redis:
    image: redis:7-alpine
    container_name: recommender_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --save 60 1
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - recommender_network

  # ---------------------------------------------------------------------------
  # FastAPI App — Recommendation API
  # ---------------------------------------------------------------------------
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: recommender_app
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_TTL=${REDIS_TTL:-3600}
      - ARTIFACTS_DIR=data
      - TOP_K=${TOP_K:-10}
      - INTERACTION_THRESHOLD=${INTERACTION_THRESHOLD:-3}
    volumes:
      - ./data:/app/data:ro
      - ./output:/app/output
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c",
             "import requests; requests.get(\\'http://localhost:8000/health\\').raise_for_status()"]
      interval: 30s
      timeout: 10s
      start_period: 90s
      retries: 3
    networks:
      - recommender_network

# ---------------------------------------------------------------------------
# Volumes and Networks
# ---------------------------------------------------------------------------
volumes:
  redis_data:
    driver: local

networks:
  recommender_network:
    driver: bridge
'''

with open("docker-compose.yml", "w") as f:
    f.write(compose_content)
print("    Created -> docker-compose.yml")

# ---------------------------------------------------------------------------
# SECTION 3: Generate .env file
# ---------------------------------------------------------------------------
print("\n[3] Generating .env file...")

env_content = '''# =============================================================================
# .env — Environment Variables for Docker Compose
# Saras AI Institute | Build Predictive Models & Modern Recommenders
# =============================================================================
# Copy this file to .env and adjust values for your environment
# Never commit .env with real secrets to version control

# Redis Configuration
REDIS_TTL=3600
REDIS_HOST=redis
REDIS_PORT=6379

# API Configuration
TOP_K=10
INTERACTION_THRESHOLD=3

# MLflow Configuration
MLFLOW_TRACKING_URI=sqlite:///data/mlflow.db

# Environment
ENVIRONMENT=development
LOG_LEVEL=info
'''

with open(".env", "w") as f:
    f.write(env_content)
print("    Created -> .env")

# ---------------------------------------------------------------------------
# SECTION 4: Generate .dockerignore
# ---------------------------------------------------------------------------
print("\n[4] Generating .dockerignore...")

dockerignore_content = '''# =============================================================================
# .dockerignore — Files excluded from Docker build context
# Keeps the Docker image lean and build times fast
# =============================================================================

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.pyo
.Python

# Virtual environments
venv/
env/
.env/
recommender_env/

# Jupyter notebooks
*.ipynb
.ipynb_checkpoints/

# Git
.git/
.gitignore

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Test artifacts
.pytest_cache/
.coverage
htmlcov/

# Large data files (mount as volumes instead)
data/events.csv
data/item_properties_part1.csv
data/item_properties_part2.csv

# Output charts (generated at runtime)
output/

# Documentation
*.md
docs/

# OS files
.DS_Store
Thumbs.db

# MLflow database (mount as volume)
data/*.db

# Logs
*.log
logs/
'''

with open(".dockerignore", "w") as f:
    f.write(dockerignore_content)
print("    Created -> .dockerignore")

# ---------------------------------------------------------------------------
# SECTION 5: Generate GitHub Actions CI Pipeline
# ---------------------------------------------------------------------------
print("\n[5] Generating GitHub Actions CI pipeline...")

os.makedirs(".github/workflows", exist_ok=True)

ci_content = '''# =============================================================================
# .github/workflows/ci.yml — GitHub Actions CI Pipeline
# Saras AI Institute | Build Predictive Models & Modern Recommenders
# =============================================================================
# Triggers on every push to main and every pull request
# Pipeline: Lint -> Unit Tests -> Build Docker -> Integration Test

name: Recommender CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:

  # ---------------------------------------------------------------------------
  # Job 1: Lint and Code Quality
  # ---------------------------------------------------------------------------
  lint:
    name: Code Quality Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install linting tools
        run: |
          pip install flake8 black isort
          echo "Linting tools installed"

      - name: Check code formatting with black
        run: |
          black --check --diff app.py scripts/
        continue-on-error: true

      - name: Check import ordering with isort
        run: |
          isort --check-only app.py scripts/
        continue-on-error: true

      - name: Lint with flake8
        run: |
          flake8 app.py scripts/ \\
            --max-line-length=100 \\
            --ignore=E501,W503,E203 \\
            --count --statistics
        continue-on-error: true

  # ---------------------------------------------------------------------------
  # Job 2: Unit Tests
  # ---------------------------------------------------------------------------
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: lint

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install pytest pytest-cov numpy scipy

      - name: Run unit tests
        run: |
          pytest scripts/03_test_suite.py \\
            -v \\
            --tb=short \\
            -k "not TestAPI and not TestEndToEnd" \\
            --cov=app \\
            --cov-report=term-missing \\
            --cov-fail-under=70
        env:
          DATA_DIR: data

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: htmlcov/

  # ---------------------------------------------------------------------------
  # Job 3: Build Docker Image
  # ---------------------------------------------------------------------------
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: unit-tests

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: recommender-api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Verify image was built
        run: |
          docker images | grep recommender-api
          echo "Docker build successful"

  # ---------------------------------------------------------------------------
  # Job 4: Integration Test with Docker Compose
  # ---------------------------------------------------------------------------
  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: build

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Start services with docker compose
        run: |
          docker compose up -d
          echo "Waiting for services to be healthy..."
          sleep 30

      - name: Check service health
        run: |
          docker compose ps
          curl -f http://localhost:8000/health || exit 1
          echo "Health check passed"

      - name: Run integration tests
        run: |
          pip install pytest httpx requests numpy
          pytest scripts/03_test_suite.py \\
            -v \\
            --tb=short \\
            -k "TestAPI or TestEndToEnd" \\
            --timeout=60
        env:
          API_URL: http://localhost:8000

      - name: Show service logs on failure
        if: failure()
        run: |
          docker compose logs app
          docker compose logs redis

      - name: Stop services
        if: always()
        run: docker compose down
'''

with open(".github/workflows/ci.yml", "w") as f:
    f.write(ci_content)
print("    Created -> .github/workflows/ci.yml")

# ---------------------------------------------------------------------------
# SECTION 6: Generate Cold-Start Verification Script
# ---------------------------------------------------------------------------
print("\n[6] Generating cold-start verification script...")

verify_script = '''#!/bin/bash
# =============================================================================
# verify_coldstart.sh — Verify Docker cold-start behavior
# Saras AI Institute | Build Predictive Models & Modern Recommenders
# =============================================================================
# Usage: bash scripts/verify_coldstart.sh
# Run AFTER: docker compose up -d

set -e

BASE_URL="http://localhost:8000"
MAX_WAIT=120
WAIT_INTERVAL=5

echo "============================================================"
echo "  Cold-Start Verification"
echo "  Hybrid Recommender — Docker Deployment"
echo "============================================================"

# Step 1: Wait for services
echo ""
echo "[1] Waiting for services to be ready..."
elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
    if curl -sf "$BASE_URL/health" > /dev/null 2>&1; then
        echo "    Services ready after ${elapsed}s"
        break
    fi
    echo "    Waiting... (${elapsed}s elapsed)"
    sleep $WAIT_INTERVAL
    elapsed=$((elapsed + WAIT_INTERVAL))
done

if [ $elapsed -ge $MAX_WAIT ]; then
    echo "    ERROR: Services did not start within ${MAX_WAIT}s"
    docker compose logs
    exit 1
fi

# Step 2: Health check
echo ""
echo "[2] Running health check..."
HEALTH=$(curl -sf "$BASE_URL/health")
echo "    Response: $HEALTH"

ALS_LOADED=$(echo $HEALTH | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[\'als_loaded\'])")
LFM_LOADED=$(echo $HEALTH | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[\'lfm_loaded\'])")

echo "    ALS loaded    : $ALS_LOADED"
echo "    LightFM loaded: $LFM_LOADED"

if [ "$ALS_LOADED" != "True" ] || [ "$LFM_LOADED" != "True" ]; then
    echo "    ERROR: Models not loaded correctly"
    exit 1
fi

# Step 3: Test recommendation endpoint
echo ""
echo "[3] Testing /recommend endpoint..."
RECS=$(curl -sf "$BASE_URL/recommend/125625?top_k=5&use_cache=true")
echo "    Response: $RECS"
ENGINE=$(echo $RECS | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[\'engine\'])")
N_RECS=$(echo $RECS | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d[\'recommendations\']))")
LATENCY=$(echo $RECS | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[\'latency_ms\'])")
echo "    Engine      : $ENGINE"
echo "    Recs count  : $N_RECS"
echo "    Latency     : ${LATENCY}ms"

# Step 4: Test Redis caching
echo ""
echo "[4] Testing Redis caching..."
# First request (cold)
curl -sf "$BASE_URL/recommend/125625?top_k=5&use_cache=true" > /dev/null
# Second request (warm)
WARM=$(curl -sf "$BASE_URL/recommend/125625?top_k=5&use_cache=true")
CACHED=$(echo $WARM | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[\'cached\'])")
echo "    Second request cached: $CACHED"

# Step 5: Stats
echo ""
echo "[5] System stats..."
STATS=$(curl -sf "$BASE_URL/stats")
echo "    $STATS"

# Summary
echo ""
echo "============================================================"
echo "  COLD-START VERIFICATION COMPLETE"
echo "============================================================"
echo "  Health check : PASSED"
echo "  Endpoint     : PASSED"
echo "  Engine used  : $ENGINE"
echo "  Recs returned: $N_RECS"
echo "  First latency: ${LATENCY}ms"
echo "  Redis caching: $CACHED"
echo ""
echo "  docker compose ps:"
docker compose ps
echo "============================================================"
'''

os.makedirs("scripts", exist_ok=True)
with open("scripts/verify_coldstart.sh", "w") as f:
    f.write(verify_script)
os.chmod("scripts/verify_coldstart.sh", 0o755)
print("    Created -> scripts/verify_coldstart.sh")

# ---------------------------------------------------------------------------
# SECTION 7: Verify All Files Created
# ---------------------------------------------------------------------------
print("\n[7] Verifying all deployment files created...")

files_to_check = [
    ("Dockerfile",                    "Container image definition"),
    ("docker-compose.yml",            "Service orchestration"),
    (".env",                          "Environment variables"),
    (".dockerignore",                 "Build context exclusions"),
    (".github/workflows/ci.yml",      "GitHub Actions CI pipeline"),
    ("scripts/verify_coldstart.sh",   "Cold-start verification"),
]

all_good = True
print(f"\n    {'File':<40} {'Status':>8}  Description")
print(f"    {'-'*75}")
for filepath, description in files_to_check:
    exists = os.path.exists(filepath)
    status = "OK" if exists else "MISSING"
    if not exists:
        all_good = False
    print(f"    {filepath:<40} {status:>8}  {description}")

# ---------------------------------------------------------------------------
# SECTION 8: Show Folder Structure
# ---------------------------------------------------------------------------
print("\n[8] Final project structure:")
print("""
    Recommender_demo/              <- root folder
    │
    ├── app.py                     <- FastAPI application (Lab 4.1)
    ├── Dockerfile                 <- Container image definition
    ├── docker-compose.yml         <- App + Redis orchestration
    ├── .env                       <- Environment variables
    ├── .dockerignore              <- Build context exclusions
    │
    ├── .github/
    │   └── workflows/
    │       └── ci.yml             <- GitHub Actions CI pipeline
    │
    ├── scripts/
    │   ├── verify_coldstart.sh    <- Cold-start verification
    │   ├── 01_mlflow_fastapi.py   <- Lab 4.1
    │   ├── 02_monitoring.py       <- Lab 4.2
    │   ├── 03_test_suite.py       <- Lab 4.3
    │   └── 04_docker_deploy.py    <- Lab 4.4 (this file)
    │
    ├── data/
    │   ├── als_artifacts.pkl
    │   ├── lightfm_artifacts.pkl
    │   ├── faiss_artifacts.pkl
    │   ├── faiss_index.bin
    │   ├── routing_split.pkl
    │   └── mlflow.db
    │
    └── output/                    <- Charts and plots
""")

# ---------------------------------------------------------------------------
# SECTION 9: Docker Commands Reference
# ---------------------------------------------------------------------------
print("[9] Docker commands reference:")
print("""
    BUILD AND START:
    ┌─────────────────────────────────────────────────────────────┐
    │ docker compose build              Build the app image        │
    │ docker compose up                 Start all services         │
    │ docker compose up -d              Start in background        │
    │ docker compose up --build         Rebuild and start          │
    └─────────────────────────────────────────────────────────────┘

    MONITORING:
    ┌─────────────────────────────────────────────────────────────┐
    │ docker compose ps                 Check service status       │
    │ docker compose logs -f app        Follow app logs            │
    │ docker compose logs redis         Show Redis logs            │
    │ docker stats                      Live resource usage        │
    └─────────────────────────────────────────────────────────────┘

    TESTING:
    ┌─────────────────────────────────────────────────────────────┐
    │ bash scripts/verify_coldstart.sh  Run cold-start check      │
    │ curl localhost:8000/health        Quick health check        │
    │ curl localhost:8000/stats         System statistics         │
    │ curl localhost:8000/recommend/1   Test recommendation       │
    └─────────────────────────────────────────────────────────────┘

    STOP AND CLEAN:
    ┌─────────────────────────────────────────────────────────────┐
    │ docker compose down               Stop all services         │
    │ docker compose down -v            Stop and remove volumes   │
    │ docker system prune               Clean up unused resources │
    └─────────────────────────────────────────────────────────────┘
""")

# ---------------------------------------------------------------------------
# SECTION 10: Try Docker Build (if Docker is available)
# ---------------------------------------------------------------------------
print("[10] Checking Docker availability...")

docker_available = False
try:
    result = subprocess.run(
        ["docker", "--version"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        docker_available = True
        print(f"    Docker found: {result.stdout.strip()}")
    else:
        print("    Docker not available")
except Exception:
    print("    Docker not found — install from https://docker.com")

if docker_available:
    print("\n    To build and start your containerized system:")
    print("    Step 1: docker compose build")
    print("    Step 2: docker compose up -d")
    print("    Step 3: bash scripts/verify_coldstart.sh")
    print("    Step 4: open http://localhost:8000/docs")
else:
    print("\n    Install Docker Desktop from: https://docker.com")
    print("    Then run:")
    print("    docker compose build && docker compose up -d")

# ---------------------------------------------------------------------------
# SECTION 11: Week 4 Deliverable Checklist
# ---------------------------------------------------------------------------
print("\n[11] Week 4 Deliverable Checklist:")
print("""
    ┌──────────────────────────────────────────────────────────┐
    │  WEEK 4 DELIVERABLE CHECKLIST                           │
    ├──────────────────────────────────────────────────────────┤
    │                                                          │
    │  Lab 4.1 — FastAPI + MLflow + Benchmark                 │
    │  [ ] MLflow experiment registered (2 runs)              │
    │  [ ] /recommend endpoint serving recommendations        │
    │  [ ] p99 latency < 50ms (cache warm)                    │
    │  [ ] output/01_fastapi_latency.png saved                │
    │                                                          │
    │  Lab 4.2 — Monitoring Dashboard                         │
    │  [ ] Coverage, novelty, diversity computed              │
    │  [ ] Catalog change simulation (+500 items)             │
    │  [ ] Alerts trigger on >10% metric change               │
    │  [ ] output/02_monitoring_dashboard.png saved           │
    │                                                          │
    │  Lab 4.3 — Test Suite                                   │
    │  [ ] Unit tests pass (normalization, routing, exclusion)│
    │  [ ] Integration tests pass (API contract)              │
    │  [ ] E2E tests pass (seeded dataset)                    │
    │  [ ] pytest -v shows all PASSED                         │
    │                                                          │
    │  Lab 4.4 — Docker Deployment                            │
    │  [ ] Dockerfile created                                 │
    │  [ ] docker-compose.yml created                         │
    │  [ ] docker compose up cold-start verified              │
    │  [ ] GitHub Actions CI pipeline created                 │
    │  [ ] verify_coldstart.sh passes all checks              │
    │                                                          │
    └──────────────────────────────────────────────────────────┘
""")

# ---------------------------------------------------------------------------
# FINAL SUMMARY
# ---------------------------------------------------------------------------
print("=" * 60)
print("  LAB 4.4 COMPLETE — DOCKER DEPLOYMENT STACK")
print("=" * 60)
print(f"""
  Files created     : {len(files_to_check)}
  All files present : {'YES' if all_good else 'CHECK MISSING FILES'}
  Docker available  : {'YES' if docker_available else 'Install Docker Desktop'}

  To deploy:
  1. docker compose build
  2. docker compose up -d
  3. bash scripts/verify_coldstart.sh
  4. open http://localhost:8000/docs

  CI Pipeline:
  Push to GitHub -> lint -> unit tests -> build -> integration

  Congratulations! The Hybrid Discovery Engine is
  fully containerized and production-ready.
""")
print("   MODULE 4 COMPLETE -> Final Project: Week 5")
