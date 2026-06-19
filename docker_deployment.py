# =============================================================================
# MODULE 4 | LAB 4.4
# File: 04_docker_deploy.py
# Purpose: Automate the generation of containerization configurations, 
#          multi-container compose manifests, .dockerignore settings, 
#          GitHub Actions CI automation pipelines, and shell verifiers.
# Saras AI Institute | Build Predictive Models & Modern Recommenders
# =============================================================================

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

# TODO: Complete the Dockerfile multi-line configuration string.
# Requirements:
# - Base Image: python:3.11-slim
# - Workdir: /app
# - System dependencies to RUN: apt-get update and install libgomp1, gcc, g++
# - COPY and RUN pip install against 'requirements_module4.txt'
# - COPY source codes ('app.py') and 'data/' directory layers inside the container
# - EXPOSE port 8000
# - Configure ENV defaults: REDIS_HOST=redis, REDIS_PORT=6379, ARTIFACTS_DIR=data
# - CMD execution script layout calling uvicorn pointing to host 0.0.0.0 and port 8000
dockerfile_content = '''# TODO: Define base configuration parameters
FROM python:3.11-slim

WORKDIR /app

# TODO: Add your multi-line commands installing system dependencies, python packages,
# copying source fields, exposing ports, and launching uvicorn wrappers.
'''

with open("Dockerfile", "w") as f:
    f.write(dockerfile_content)
print("    Created -> Dockerfile")


# ---------------------------------------------------------------------------
# SECTION 2: Generate docker-compose.yml
# ---------------------------------------------------------------------------
print("\n[2] Generating docker-compose.yml...")

# TODO: Complete the docker-compose multi-service manifest structure string.
# Requirements:
# - Service 1: 'redis' using 'redis:7-alpine', exposing port 6379, map volume 'redis_data:/data'
# - Service 2: 'app' setting up a context build '.' using your Dockerfile, exposing port 8000
#   Map environmental flags: REDIS_HOST=redis, REDIS_PORT=6379, TOP_K=${TOP_K:-10}
#   Link volumes to persist output plots and mount data read-only ('./data:/app/data:ro')
#   Enforce strict creation ordering using 'depends_on' pointing to a healthy redis service container
# - Define standard driver networks and volumes at the root level boundary blocks
compose_content = '''# TODO: Establish version parameters and map services configurations
version: "3.9"

services:
  redis:
    # TODO: Populate your Redis configuration blocks
    pass

  app:
    # TODO: Populate your FastAPI application service boundaries
    pass
'''

with open("docker-compose.yml", "w") as f:
    f.write(compose_content)
print("    Created -> docker-compose.yml")


# ---------------------------------------------------------------------------
# SECTION 3: Generate .env file
# ---------------------------------------------------------------------------
print("\n[3] Generating .env file...")

# TODO: Build an environment configuration string tracking local environment tokens
# Variables: REDIS_TTL=3600, REDIS_HOST=redis, REDIS_PORT=6379, TOP_K=10, INTERACTION_THRESHOLD=3
env_content = '''# TODO: Declare key-value pairs mapping environmental default configurations
'''

with open(".env", "w") as f:
    f.write(env_content)
print("    Created -> .env")


# ---------------------------------------------------------------------------
# SECTION 4: Generate .dockerignore
# ---------------------------------------------------------------------------
print("\n[4] Generating .dockerignore...")

# TODO: Construct a comprehensive exclusion list matching files that must stay out of the build matrix.
# Block patterns matching: __pycache__/, *.ipynb, .git/, venv/, .pytest_cache/, large raw data source 
# files like 'data/events.csv' (which are mounted via volumes instead of hardcopied), and local 'output/' plots.
dockerignore_content = '''# TODO: Add pattern filters to exclude unnecessary local files from the build context
'''

with open(".dockerignore", "w") as f:
    f.write(dockerignore_content)
print("    Created -> .dockerignore")


# ---------------------------------------------------------------------------
# SECTION 5: Generate GitHub Actions CI Pipeline
# ---------------------------------------------------------------------------
print("\n[5] Generating GitHub Actions CI pipeline...")

os.makedirs(".github/workflows", exist_ok=True)

# TODO: Structure a continuous integration workflow configuration string saved to '.github/workflows/ci.yml'.
# Requirements:
# - Trigger: filter execution runs on push or pull requests targeting the 'main' branch
# - Job 1: 'lint' running ubuntu-latest, checking code format checks using flake8, black, or isort
# - Job 2: 'unit-tests' executing pytest targeting 'scripts/03_test_suite.py' with exclusions flags 
#   configured to run structural code blocks only (-k "not TestAPI and not TestEndToEnd")
# - Job 3: 'build' running Docker build verification actions cleanly
# - Job 4: 'integration' spinning up containers via 'docker compose up -d' and verifying the /health endpoint contract
ci_content = '''# TODO: Map automated multi-stage CI pipelines tracking sequential check triggers
name: Recommender CI Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  # TODO: Construct code quality check, validation test runner, and docker compose build stages
'''

with open(".github/workflows/ci.yml", "w") as f:
    f.write(ci_content)
print("    Created -> .github/workflows/ci.yml")


# ---------------------------------------------------------------------------
# SECTION 6: Generate Cold-Start Verification Script
# ---------------------------------------------------------------------------
print("\n[6] Generating cold-start verification script...")

# TODO: Complete the bash automation script string to test live multi-container orchestration responses.
# Requirements:
# - Step 1: Use a 'while' loop with curl to ping 'http://localhost:8000/health' sequentially until ready
# - Step 2: Validate health JSON outputs ensuring 'als_loaded' and 'lfm_loaded' flags return True
# - Step 3: Trigger a test curl against the recommendation path '/recommend/125625?top_k=5&use_cache=true'
# - Step 4: Verify that a subsequent duplicate endpoint query logs data['cached'] as True via Redis memory lookups
verify_script = '''#!/bin/bash
set -e

echo "============================================================"
echo "  Cold-Start Verification — Student Lab Automation"
echo "============================================================"

# TODO: Implement bash testing validation routines pining endpoints and evaluating json responses
'''

os.makedirs("scripts", exist_ok=True)
with open("scripts/verify_coldstart.sh", "w") as f:
    f.write(verify_script)
os.chmod("scripts/verify_coldstart.sh", 0o755) # Modifies permissions to enable execution access
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
# SECTION 8: Try Docker Build (if Docker is available)
# ---------------------------------------------------------------------------
print("\n[8] Checking Docker availability...")

docker_available = False
try:
    result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        docker_available = True
        print(f"    Docker found: {result.stdout.strip()}")
    else:
        print("    Docker not available locally.")
except Exception:
    print("    Docker daemon not found.")

if docker_available:
    print("\n    To build and start your containerized system:")
    print("    Step 1: docker compose build")
    print("    Step 2: docker compose up -d")
    print("    Step 3: bash scripts/verify_coldstart.sh")
else:
    print("\n    Ensure Docker Desktop is running before deploying.")

print("\n" + "=" * 60)
print("  LAB 4.4 COMPLETE — DOCKER DEPLOYMENT STACK")
print("=" * 60)
