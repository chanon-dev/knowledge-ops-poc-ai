# Running Guide — The Expert

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Docker & Docker Compose | 24+ | `docker --version` |
| Node.js | 18+ | `node --version` |
| Python | 3.11+ | `python3 --version` |
| npm | 9+ | `npm --version` |

---

## Quick Start (TL;DR)

เปิด **4 terminals** แล้วรันตามลำดับ:

```bash
# Terminal 1 — Infrastructure (Docker)
docker compose -f docker-compose.dev.yml up -d

# Terminal 2 — Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3 — Frontend
cd frontend
npm run dev

# Terminal 4 — Celery Worker (async tasks)
cd backend
source venv/bin/activate
celery -A app.services.celery_worker:celery_app worker --loglevel=info
```

เปิด browser: http://localhost:3000

---

## รายละเอียดแต่ละ step

### Step 1: Setup Environment Variables

สร้างไฟล์ `.env` ที่ root ของ project:

```bash
cp .env.example .env
```

หากยังไม่มี `.env.example` ให้สร้าง `.env` ด้วยตัวเอง:

```env
# Database
POSTGRES_PASSWORD=expert_secret

# MinIO (Object Storage)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# Keycloak (Auth)
KC_ADMIN_PASSWORD=admin

# Stripe (Billing) — optional สำหรับ dev
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

ไฟล์ `frontend/.env.local` ควรมี:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-change-in-production
```

---

### Step 2: Start Infrastructure Services (Docker)

```bash
docker compose -f docker-compose.dev.yml up -d
```

รอให้ services ทั้งหมดพร้อม:

```bash
docker compose -f docker-compose.dev.yml ps
```

| Service | Port | URL | หน้าที่ |
|---------|------|-----|---------|
| PostgreSQL | 5433 | `localhost:5433` | Database หลัก |
| Redis | 6379 | `localhost:6379` | Cache / Rate limit / Celery broker |
| Qdrant | 6333 | http://localhost:6333/dashboard | Vector search (RAG) |
| MinIO | 9000 / 9001 | http://localhost:9001 (console) | File & document storage |
| Keycloak | 8081 | http://localhost:8081 | Authentication (SSO/OIDC) |
| Ollama | 11434 | http://localhost:11434 | LLM inference |

**Pull LLM model (ครั้งแรกเท่านั้น):**

```bash
docker exec -it $(docker ps -qf "name=ollama") ollama pull llama3:8b
```

---

### Step 3: Backend (FastAPI)

#### 3.1 สร้าง Virtual Environment & Install Dependencies (ครั้งแรก)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

#### 3.2 Setup Database (ครั้งแรก)

```bash
source venv/bin/activate
alembic upgrade head
```

#### 3.3 Seed Data (optional — ครั้งแรก)

```bash
python3 -m app.db.seed
```

#### 3.4 Start Backend Server

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

ตรวจสอบ:
- Health Check: http://localhost:8000/health → `{"status":"ok"}`
- API Docs (Swagger): http://localhost:8000/api/v1/docs
- API Docs (ReDoc): http://localhost:8000/api/v1/redoc

---

### Step 4: Celery Worker (Async Task Processing)

จำเป็นสำหรับ: document ingestion, approved answer reindexing

เปิด **terminal ใหม่**:

```bash
cd backend
source venv/bin/activate
celery -A app.services.celery_worker:celery_app worker --loglevel=info
```

ต้องการ Redis รันอยู่ก่อน (Step 2)

---

### Step 5: Frontend (Next.js)

#### 5.1 Install Dependencies (ครั้งแรก)

```bash
cd frontend
npm install
```

#### 5.2 Start Development Server

```bash
npm run dev
```

เปิด browser: http://localhost:3000

#### 5.3 Production Build (optional)

```bash
npm run build
npm run start
```

---

### Step 6: Monitoring Stack (optional)

```bash
docker compose -f infra/monitoring/docker-compose.monitoring.yml up -d
```

| Service | Port | URL | Login |
|---------|------|-----|-------|
| Grafana | 3001 | http://localhost:3001 | admin / admin |
| Prometheus | 9090 | http://localhost:9090 | — |
| Loki | 3100 | http://localhost:3100 | — |

---

## สรุปทุก Process ที่ต้อง Run

| # | Process | Command | Terminal | Required |
|---|---------|---------|----------|----------|
| 1 | Docker Infrastructure | `docker compose -f docker-compose.dev.yml up -d` | 1 | ต้องมี |
| 2 | FastAPI Backend | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` | 2 | ต้องมี |
| 3 | Next.js Frontend | `cd frontend && npm run dev` | 3 | ต้องมี |
| 4 | Celery Worker | `celery -A app.services.celery_worker:celery_app worker --loglevel=info` | 4 | ต้องมี (async tasks) |
| 5 | Monitoring | `docker compose -f infra/monitoring/docker-compose.monitoring.yml up -d` | — | optional |

---

## Port Summary

| Port | Service | Type |
|------|---------|------|
| 3000 | Next.js Frontend | App |
| 8000 | FastAPI Backend | App |
| 5433 | PostgreSQL | Docker |
| 6379 | Redis | Docker |
| 6333 | Qdrant | Docker |
| 8081 | Keycloak | Docker |
| 9000 | MinIO API | Docker |
| 9001 | MinIO Console | Docker |
| 11434 | Ollama | Docker |
| 3001 | Grafana (optional) | Docker |
| 9090 | Prometheus (optional) | Docker |

---

## Quick Verification

หลังจาก start ทุกอย่างแล้ว ตรวจสอบด้วย:

```bash
# Backend health
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# Expected: 200

# PostgreSQL
docker compose -f docker-compose.dev.yml exec postgres pg_isready -U expert
# Expected: accepting connections

# Redis
redis-cli ping
# Expected: PONG

# Qdrant
curl http://localhost:6333/healthz
# Expected: OK

# Ollama
curl http://localhost:11434/api/tags
# Expected: JSON with models list

# MinIO
curl -s -o /dev/null -w "%{http_code}" http://localhost:9001
# Expected: 200

# Keycloak
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081
# Expected: 200
```

---

## Architecture Overview

```
Browser (localhost:3000)
   │
   ├──► Next.js Frontend ──────────────────────────────────┐
   │                                                        │
   │    FastAPI Backend (localhost:8000) ◄───────────────────┘
   │       │
   │       ├──► PostgreSQL (5433)    — Relational data, RLS tenant isolation
   │       ├──► Qdrant (6333)        — Vector search (RAG pipeline)
   │       ├──► Redis (6379)         — Cache, rate limit, Celery broker
   │       ├──► MinIO (9000)         — Document & image storage
   │       ├──► Ollama (11434)       — LLM inference (Llama 3, Mistral)
   │       ├──► Keycloak (8081)      — SSO / OIDC authentication
   │       └──► Celery Worker        — Async document ingestion
   │
   └──► Grafana (3001) ──► Prometheus (9090) ──► Loki (3100)
```

---

## Shutdown

```bash
# Stop backend (Ctrl+C in terminal)
# Stop frontend (Ctrl+C in terminal)
# Stop Celery (Ctrl+C in terminal)

# Stop Docker infrastructure
docker compose -f docker-compose.dev.yml down

# Stop monitoring (if running)
docker compose -f infra/monitoring/docker-compose.monitoring.yml down

# Stop AND remove all data (reset)
docker compose -f docker-compose.dev.yml down -v
```

---

## Common Issues

### Port already in use

```bash
# หา process ที่ใช้ port
lsof -i :8000
# kill process
kill -9 <PID>
```

### Docker services ไม่ขึ้น

```bash
docker compose -f docker-compose.dev.yml logs <service-name>
# เช่น: docker compose -f docker-compose.dev.yml logs postgres
```

### Database connection refused

ตรวจสอบว่า PostgreSQL container พร้อมแล้ว:

```bash
docker compose -f docker-compose.dev.yml exec postgres pg_isready -U expert
```

### Ollama model not found

```bash
docker exec -it $(docker ps -qf "name=ollama") ollama pull llama3:8b
```

### Celery worker ไม่ connect Redis

ตรวจสอบว่า Redis container รันอยู่:

```bash
docker compose -f docker-compose.dev.yml ps redis
redis-cli ping
```

### Frontend build error

```bash
cd frontend
rm -rf .next node_modules
npm install
npm run build
```

### Backend import error

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python3 -c "from app.main import app; print('OK')"
```
