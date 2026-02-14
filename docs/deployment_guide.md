# Deployment Guide

**Project Name**: The Expert — Universal Enterprise AI Platform
**Version**: 1.0
**Date**: 2026-02-12

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Architecture Overview](#2-architecture-overview)
3. [Local Development Setup](#3-local-development-setup)
4. [Docker Compose (Single Server)](#4-docker-compose-single-server)
5. [Kubernetes (Production)](#5-kubernetes-production)
6. [CI/CD Pipeline](#6-cicd-pipeline)
7. [Environment Configuration](#7-environment-configuration)
8. [SSL/TLS Configuration](#8-ssltls-configuration)
9. [Database Initialization](#9-database-initialization)
10. [Monitoring Stack](#10-monitoring-stack)
11. [Backup & Recovery](#11-backup--recovery)
12. [Scaling Guide](#12-scaling-guide)
13. [On-Premise Deployment](#13-on-premise-deployment)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Prerequisites

### 1.1 System Requirements

| Deployment | CPU | RAM | GPU | Storage | OS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Development** | 8 cores | 16 GB | ❌ Optional | 50 GB SSD | macOS / Linux |
| **Staging** | 16 cores | 64 GB | 1× RTX 4090 | 200 GB SSD | Ubuntu 22.04 |
| **Production (Small)** | 32 cores | 128 GB | 1× A100 40GB | 1 TB SSD | Ubuntu 22.04 |
| **Production (Medium)** | 64 cores | 256 GB | 2× A100 80GB | 2 TB SSD + 10 TB HDD | Ubuntu 22.04 |
| **Production (Large)** | K8s cluster | 512+ GB | 4× A100/H100 | 10 TB SSD + 50 TB HDD | Ubuntu 22.04 |

### 1.2 Software Requirements

| Software | Version | Purpose |
| :--- | :--- | :--- |
| Docker | 25+ | Containerization |
| Docker Compose | 2.24+ | Multi-container orchestration |
| Kubernetes | 1.29+ | Production orchestration |
| Helm | 3.14+ | K8s package manager |
| kubectl | 1.29+ | K8s CLI |
| Node.js | 20 LTS | Frontend build |
| Python | 3.11+ | Backend runtime |
| NVIDIA Driver | 550+ | GPU support |
| NVIDIA Container Toolkit | 1.14+ | GPU in Docker |
| Terraform | 1.7+ | Infrastructure as Code (optional) |

### 1.3 Install Docker & GPU Support

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install NVIDIA Container Toolkit (for GPU)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU
docker run --rm --gpus all nvidia/cuda:12.3.1-base-ubuntu22.04 nvidia-smi
```

---

## 2. Architecture Overview

### Service Map

```mermaid
graph TB
    subgraph "External"
        USER["Users / Browsers"]
        DNS["DNS (CloudFlare)"]
    end

    subgraph "Edge Layer"
        NGINX["Nginx\n:80/:443"]
    end

    subgraph "Application Layer"
        API["FastAPI\n:8000"]
        FRONTEND["Next.js\n:3000"]
        CELERY["Celery Workers\nx3"]
    end

    subgraph "AI Layer"
        OLLAMA["Ollama\n:11434"]
        TRITON["Triton Server\n:8001"]
    end

    subgraph "Data Layer"
        PG["PostgreSQL\n:5432"]
        QDRANT["Qdrant\n:6333"]
        REDIS["Redis\n:6379"]
        MINIO["MinIO\n:9000"]
    end

    subgraph "Auth"
        KC["Keycloak\n:8080"]
    end

    subgraph "Pipeline (Enterprise)"
        KAFKA["Kafka\n:9092"]
        SPARK["Spark\n:7077"]
        AIRFLOW["Airflow\n:8081"]
    end

    subgraph "Monitoring"
        GRAFANA["Grafana\n:3001"]
        PROMETHEUS["Prometheus\n:9090"]
        LANGFUSE["Langfuse\n:3002"]
    end

    USER --> DNS --> NGINX
    NGINX --> API
    NGINX --> FRONTEND
    API --> OLLAMA
    API --> TRITON
    API --> PG
    API --> QDRANT
    API --> REDIS
    API --> MINIO
    API --> KC
    API --> CELERY
    CELERY --> REDIS
    CELERY --> PG
    KAFKA --> SPARK --> QDRANT
    AIRFLOW --> SPARK
    API --> LANGFUSE
    PROMETHEUS --> GRAFANA
```

### Port Map

| Service | Port | Protocol |
| :--- | :--- | :--- |
| Nginx | 80, 443 | HTTP/HTTPS |
| FastAPI | 8000 | HTTP/WS |
| Next.js | 3000 | HTTP |
| PostgreSQL | 5432 | TCP |
| Qdrant | 6333 (HTTP), 6334 (gRPC) | HTTP/gRPC |
| Redis | 6379 | TCP |
| MinIO | 9000 (API), 9001 (Console) | HTTP |
| Keycloak | 8080 | HTTP |
| Ollama | 11434 | HTTP |
| Triton | 8000 (HTTP), 8001 (gRPC), 8002 (Metrics) | HTTP/gRPC |
| Kafka | 9092 | TCP |
| Grafana | 3001 | HTTP |
| Prometheus | 9090 | HTTP |
| Langfuse | 3002 | HTTP |
| Airflow | 8081 | HTTP |

---

## 3. Local Development Setup

### 3.1 Clone & Setup

```bash
# Clone repository
git clone https://github.com/your-org/the-expert.git
cd the-expert

# Copy environment files
cp .env.example .env
cp frontend/.env.example frontend/.env.local

# Edit .env with your settings
vim .env
```

### 3.2 Start Development Stack

```bash
# Start all services (without GPU)
docker compose -f docker-compose.dev.yml up -d

# Start with GPU support
docker compose -f docker-compose.dev.yml --profile gpu up -d

# Check status
docker compose -f docker-compose.dev.yml ps

# View logs
docker compose -f docker-compose.dev.yml logs -f api
```

### 3.3 Run Backend (Local Python)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run database migrations
alembic upgrade head

# Seed demo data
python -m app.db.seed

# Start API server
uvicorn app.main:app --reload --port 8000
```

### 3.4 Run Frontend (Local Node)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
# → http://localhost:3000
```

---

## 4. Docker Compose (Single Server)

### 4.1 Production Docker Compose

```yaml
# docker-compose.yml
version: "3.9"

x-common-env: &common-env
  DATABASE_URL: postgresql+asyncpg://expert:${DB_PASSWORD}@postgres:5432/the_expert
  REDIS_URL: redis://redis:6379/0
  QDRANT_URL: http://qdrant:6333
  MINIO_ENDPOINT: minio:9000
  MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
  MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
  KEYCLOAK_URL: http://keycloak:8080
  OLLAMA_URL: http://ollama:11434
  LANGFUSE_URL: http://langfuse:3002

services:
  # ─── REVERSE PROXY ───
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infra/nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
      - frontend
    restart: always

  # ─── APPLICATION ───
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      <<: *common-env
      ENVIRONMENT: production
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_started
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "2.0"
          memory: 4G

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://api:8000
      NEXT_PUBLIC_WS_URL: ws://api:8000
    ports:
      - "3000:3000"
    restart: always

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.celery_app worker -l info -c 4
    environment:
      <<: *common-env
    depends_on:
      - redis
      - postgres
    restart: always
    deploy:
      replicas: 2

  # ─── DATA LAYER ───
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: the_expert
      POSTGRES_USER: expert
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U expert"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always
    deploy:
      resources:
        limits:
          cpus: "4.0"
          memory: 16G

  qdrant:
    image: qdrant/qdrant:v1.7.4
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
      - "6334:6334"
    restart: always
    deploy:
      resources:
        limits:
          memory: 8G

  redis:
    image: redis:7.2-alpine
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
    restart: always

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    restart: always

  # ─── AUTH ───
  keycloak:
    image: quay.io/keycloak/keycloak:23.0
    command: start-dev --import-realm
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: ${KC_ADMIN_PASSWORD}
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: expert
      KC_DB_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./infra/keycloak/realm-export.json:/opt/keycloak/data/import/realm.json
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
    restart: always

  # ─── AI ENGINE ───
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: always

  # ─── MONITORING ───
  grafana:
    image: grafana/grafana:10.3.1
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3001:3000"
    restart: always

  prometheus:
    image: prom/prometheus:v2.49.1
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: always

  langfuse:
    image: langfuse/langfuse:2
    environment:
      DATABASE_URL: postgresql://expert:${DB_PASSWORD}@postgres:5432/langfuse
      NEXTAUTH_URL: http://langfuse:3002
      NEXTAUTH_SECRET: ${LANGFUSE_SECRET}
    ports:
      - "3002:3000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: always

volumes:
  postgres_data:
  qdrant_data:
  redis_data:
  minio_data:
  ollama_data:
  grafana_data:
  prometheus_data:
```

### 4.2 Start Production

```bash
# Build images
docker compose build

# Start all services
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head

# Seed initial data
docker compose exec api python -m app.db.seed

# Pull LLM models
docker compose exec ollama ollama pull llama3:8b-instruct-q4_K_M
docker compose exec ollama ollama pull llava:13b

# Verify all services are healthy
docker compose ps
```

---

## 5. Kubernetes (Production)

### 5.1 Namespace Structure

```bash
# Create namespaces
kubectl create namespace the-expert-core
kubectl create namespace the-expert-ai
kubectl create namespace the-expert-data
kubectl create namespace the-expert-monitoring
kubectl create namespace the-expert-auth
```

### 5.2 Helm Chart Structure

```
infra/helm/the-expert/
├── Chart.yaml
├── values.yaml
├── values-staging.yaml
├── values-production.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── api-deployment.yaml
│   ├── api-service.yaml
│   ├── api-hpa.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── celery-deployment.yaml
│   ├── ingress.yaml
│   ├── postgres-statefulset.yaml
│   ├── qdrant-statefulset.yaml
│   ├── redis-deployment.yaml
│   ├── minio-statefulset.yaml
│   ├── keycloak-deployment.yaml
│   ├── ollama-deployment.yaml
│   ├── triton-deployment.yaml
│   └── monitoring/
│       ├── grafana.yaml
│       ├── prometheus.yaml
│       └── langfuse.yaml
```

### 5.3 Deploy with Helm

```bash
# Add required Helm repos
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add prometheus https://prometheus-community.github.io/helm-charts
helm repo update

# Install/Upgrade (Production)
helm upgrade --install the-expert ./infra/helm/the-expert \
  --namespace the-expert-core \
  --values ./infra/helm/the-expert/values-production.yaml \
  --set secrets.dbPassword=$DB_PASSWORD \
  --set secrets.secretKey=$SECRET_KEY \
  --wait --timeout 10m

# Check deployment status
kubectl get pods -n the-expert-core
kubectl get pods -n the-expert-data
kubectl get pods -n the-expert-ai
```

### 5.4 Horizontal Pod Autoscaler

```yaml
# api-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: the-expert-core
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
```

---

## 6. CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Build & Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ghcr.io/${{ github.repository }}

jobs:
  # ─── LINT & TEST ───
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install & Lint Backend
        working-directory: ./backend
        run: |
          pip install -r requirements-dev.txt
          ruff check .
          mypy app/

      - name: Run Backend Tests
        working-directory: ./backend
        run: pytest --cov=app --cov-report=xml -v

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Lint & Test Frontend
        working-directory: ./frontend
        run: |
          npm ci
          npm run lint
          npm run type-check
          npm test -- --coverage

  # ─── BUILD IMAGES ───
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    strategy:
      matrix:
        service: [api, frontend, celery-worker]
    steps:
      - uses: actions/checkout@v4

      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build & Push
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service == 'celery-worker' && 'backend' || matrix.service }}
          push: true
          tags: |
            ${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:${{ github.sha }}
            ${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:latest

  # ─── DEPLOY STAGING ───
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Staging
        run: |
          helm upgrade --install the-expert ./infra/helm/the-expert \
            --namespace the-expert-staging \
            --values ./infra/helm/the-expert/values-staging.yaml \
            --set image.tag=${{ github.sha }}

  # ─── DEPLOY PRODUCTION ───
  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Production
        run: |
          helm upgrade --install the-expert ./infra/helm/the-expert \
            --namespace the-expert-core \
            --values ./infra/helm/the-expert/values-production.yaml \
            --set image.tag=${{ github.sha }}

      - name: Run DB Migrations
        run: |
          kubectl exec -n the-expert-core deploy/api -- alembic upgrade head
```

---

## 7. Environment Configuration

### `.env` Template

```bash
# ─── APPLICATION ───
ENVIRONMENT=production          # development | staging | production
SECRET_KEY=your-256bit-secret   # openssl rand -hex 32
DEBUG=false
LOG_LEVEL=info                  # debug | info | warning | error
ALLOWED_ORIGINS=https://app.the-expert.ai

# ─── DATABASE ───
DB_HOST=postgres
DB_PORT=5432
DB_NAME=the_expert
DB_USER=expert
DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# ─── REDIS ───
REDIS_URL=redis://redis:6379/0

# ─── QDRANT ───
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=                 # Optional: if Qdrant auth is enabled

# ─── MINIO ───
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=CHANGE_ME_STRONG_PASSWORD
MINIO_BUCKET=the-expert-storage
MINIO_USE_SSL=false

# ─── KEYCLOAK ───
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=the-expert
KEYCLOAK_CLIENT_ID=the-expert-api
KEYCLOAK_CLIENT_SECRET=CHANGE_ME
KC_ADMIN_PASSWORD=CHANGE_ME

# ─── AI / LLM ───
OLLAMA_URL=http://ollama:11434
TRITON_URL=http://triton:8001
DEFAULT_MODEL=llama3:8b-instruct-q4_K_M
EMBEDDING_MODEL=bge-large-en-v1.5
VISION_MODEL=llava:13b

# ─── CLOUD AI (Optional) ───
OPENAI_API_KEY=
GOOGLE_API_KEY=

# ─── MLFLOW ───
MLFLOW_TRACKING_URI=http://mlflow:5000

# ─── OBSERVABILITY ───
LANGFUSE_URL=http://langfuse:3002
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
GRAFANA_PASSWORD=CHANGE_ME

# ─── BILLING (Optional) ───
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
```

---

## 8. SSL/TLS Configuration

### Nginx with Let's Encrypt

```nginx
# infra/nginx/nginx.conf
upstream api_backend {
    server api:8000;
}

upstream frontend_app {
    server frontend:3000;
}

server {
    listen 80;
    server_name app.the-expert.ai api.the-expert.ai;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.the-expert.ai;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://frontend_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 443 ssl http2;
    server_name api.the-expert.ai;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # REST API
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 50M;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

---

## 9. Database Initialization

```bash
# Run migrations
docker compose exec api alembic upgrade head

# Create initial databases for Keycloak & Langfuse
docker compose exec postgres psql -U expert -c "CREATE DATABASE keycloak;"
docker compose exec postgres psql -U expert -c "CREATE DATABASE langfuse;"

# Seed demo data
docker compose exec api python -m app.db.seed

# Verify tables
docker compose exec postgres psql -U expert -d the_expert -c "\dt"

# Verify RLS is enabled
docker compose exec postgres psql -U expert -d the_expert -c \
  "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';"
```

---

## 10. Monitoring Stack

### Prometheus Config

```yaml
# infra/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "fastapi"
    static_configs:
      - targets: ["api:8000"]
    metrics_path: /metrics

  - job_name: "postgres"
    static_configs:
      - targets: ["postgres-exporter:9187"]

  - job_name: "redis"
    static_configs:
      - targets: ["redis-exporter:9121"]

  - job_name: "qdrant"
    static_configs:
      - targets: ["qdrant:6333"]
    metrics_path: /metrics

  - job_name: "triton"
    static_configs:
      - targets: ["triton:8002"]
    metrics_path: /metrics

  - job_name: "node"
    static_configs:
      - targets: ["node-exporter:9100"]
```

### Key Grafana Dashboards

| Dashboard | Panels |
| :--- | :--- |
| **System Health** | CPU, Memory, Disk, Network per service |
| **API Performance** | Request rate, P50/P95/P99 latency, Error rate |
| **AI Metrics** | Inference time, Token usage, Queue depth, Model accuracy |
| **Business KPIs** | Active users, Queries/day, Approval rate, Revenue |
| **PostgreSQL** | Connections, Query time, Cache hit ratio, Replication lag |
| **Qdrant** | Search latency, Collection size, Memory usage |

---

## 11. Backup & Recovery

### Automated Backup Schedule

| Data | Frequency | Retention | Method |
| :--- | :--- | :--- | :--- |
| PostgreSQL | Every 6 hours | 30 days | `pg_dump` → S3/MinIO |
| Qdrant Snapshots | Daily | 7 days | Qdrant snapshot API → S3 |
| MinIO Objects | Continuous | Unlimited | MinIO replication or S3 sync |
| Redis (RDB) | Every hour | 3 days | Redis BGSAVE → S3 |
| Keycloak Realm | Daily | 30 days | Realm export JSON → S3 |

### Backup Script

```bash
#!/bin/bash
# infra/scripts/backup.sh
set -euo pipefail

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/${DATE}"
S3_BUCKET="s3://the-expert-backups"

mkdir -p ${BACKUP_DIR}

echo "=== PostgreSQL Backup ==="
docker compose exec -T postgres pg_dump -U expert the_expert | \
  gzip > ${BACKUP_DIR}/postgres_${DATE}.sql.gz

echo "=== Qdrant Snapshot ==="
curl -X POST "http://localhost:6333/snapshots" | \
  jq -r '.result.name' > ${BACKUP_DIR}/qdrant_snapshot_name.txt

echo "=== Redis Backup ==="
docker compose exec redis redis-cli BGSAVE
sleep 5
docker compose cp redis:/data/dump.rdb ${BACKUP_DIR}/redis_${DATE}.rdb

echo "=== Upload to S3 ==="
aws s3 sync ${BACKUP_DIR} ${S3_BUCKET}/${DATE}/

echo "=== Cleanup old backups (30 days) ==="
find /backups -mtime +30 -delete

echo "✅ Backup complete: ${DATE}"
```

### Restore Procedure

```bash
# Restore PostgreSQL
gunzip < postgres_20260212.sql.gz | docker compose exec -T postgres psql -U expert the_expert

# Restore Qdrant
curl -X PUT "http://localhost:6333/snapshots/{snapshot_name}"

# Restore Redis
docker compose stop redis
docker compose cp redis_20260212.rdb redis:/data/dump.rdb
docker compose start redis
```

---

## 12. Scaling Guide

### When to Scale

| Signal | Action |
| :--- | :--- |
| API P95 latency > 3s | Scale API replicas (HPA) |
| GPU utilization > 85% | Add GPU node or switch to larger GPU |
| PostgreSQL CPU > 75% | Add read replicas |
| Qdrant memory > 80% | Add Qdrant nodes (cluster mode) |
| Redis memory > 80% | Increase maxmemory or add Redis cluster |
| Queue depth > 100 | Add Celery workers |

### Scaling Commands

```bash
# Scale API pods
kubectl scale deployment api -n the-expert-core --replicas=5

# Scale Celery workers
kubectl scale deployment celery-worker -n the-expert-core --replicas=4

# Add PostgreSQL read replica
helm upgrade the-expert-db bitnami/postgresql \
  --set readReplicas.replicaCount=2

# Scale Qdrant cluster
kubectl scale statefulset qdrant -n the-expert-data --replicas=3
```

---

## 13. On-Premise Deployment

### Quick Start (Docker Compose)

```bash
# Download package
curl -LO https://releases.the-expert.ai/v1.0/onprem-package.tar.gz
tar xzf onprem-package.tar.gz
cd the-expert-onprem/

# Configure
cp .env.example .env
vim .env  # Set passwords, domain, etc.

# Start
./install.sh

# Verify
./health-check.sh
```

### Air-Gapped Deployment

```bash
# On internet-connected machine: download all images
./scripts/download-images.sh
# → Creates: the-expert-images-v1.0.tar.gz (~15 GB)

# Transfer to air-gapped server via USB/secure transfer
scp the-expert-images-v1.0.tar.gz admin@air-gapped-server:/opt/

# On air-gapped server:
tar xzf the-expert-images-v1.0.tar.gz
./load-images.sh  # docker load all images
./install.sh      # Start services

# Download models separately
./scripts/download-models.sh
# → Creates: the-expert-models-v1.0.tar.gz (~10 GB)
# Transfer and load on air-gapped server
./load-models.sh
```

---

## 14. Troubleshooting

| Problem | Check | Fix |
| :--- | :--- | :--- |
| API returns 500 | `docker compose logs api` | Check DB connection, env vars |
| Ollama slow/timeout | `docker compose exec ollama ollama list` | Ensure model is loaded, check GPU |
| Keycloak login fails | `docker compose logs keycloak` | Check realm config, DB |
| Qdrant out of memory | `curl localhost:6333/collections` | Increase memory limit, optimize vectors |
| Redis connection refused | `docker compose exec redis redis-cli ping` | Check Redis is running, port |
| WebSocket disconnect | Check Nginx timeout settings | Increase `proxy_read_timeout` |
| RLS not filtering | Check `app.current_tenant` is set | Verify middleware, session vars |
| GPU not detected | `nvidia-smi` | Install NVIDIA Container Toolkit |

### Health Check Script

```bash
#!/bin/bash
# health-check.sh
echo "=== Service Health ==="
services=("api:8000/health" "qdrant:6333/healthz" "minio:9000/minio/health/live" "keycloak:8080/health")
for svc in "${services[@]}"; do
  status=$(curl -sf "http://${svc}" && echo "✅ OK" || echo "❌ FAIL")
  echo "  ${svc}: ${status}"
done

echo ""
echo "=== Database ==="
docker compose exec postgres pg_isready -U expert && echo "  PostgreSQL: ✅" || echo "  PostgreSQL: ❌"
docker compose exec redis redis-cli ping | grep -q PONG && echo "  Redis: ✅" || echo "  Redis: ❌"

echo ""
echo "=== GPU ==="
docker compose exec ollama nvidia-smi --query-gpu=name,utilization.gpu --format=csv 2>/dev/null || echo "  No GPU detected"
```

---

## Related Documents

- [Implementation Plan](./implementation_plan.md) — Architecture & tech design
- [Database Design](./database_design.md) — Full schema & ER diagram
- [API Specification](./api_specification.md) — API endpoints & examples
- [Tasks](./tasks.md) — Sprint-level breakdown
