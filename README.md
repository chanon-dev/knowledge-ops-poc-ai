# The Expert — Universal Enterprise AI Platform

## 🚀 Quick Start (Development)

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### 1. Setup Backend & Infrastructure

```bash
# 1. Start Infrastructure (Postgres, Redis, Qdrant, MinIO, Keycloak, Ollama)
docker-compose -f docker-compose.dev.yml up -d

# Check if services are running
docker-compose -f docker-compose.dev.yml ps
```

### 2. Setup Backend Application

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (create tables)
# Note: Wait for Postgres to be ready first!
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --port 8000
```

### 3. Setup Frontend Application

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit: <http://localhost:3000>

## 📂 Project Structure

- `backend/`: FastAPI application
  - `app/models/`: Database models (Tenant, User, Department)
  - `app/core/`: Configuration
  - `alembic/`: Database migrations
- `frontend/`: Next.js application (App Router)
- `infra/`: Infrastructure configuration (Postgres init, Keycloak realm)
- `docs/`: Documentation (Architecture, API, Schema)
- `docker-compose.dev.yml`: Local development stack
