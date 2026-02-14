# Project Task Breakdown

**Project Name**: The Expert — Universal Enterprise AI Platform
**Version**: 1.0
**Date**: 2026-02-12
**Methodology**: Agile Scrum — 2-week sprints

---

## Table of Contents

1. [Phase 1: MVP Foundation (Month 1-3)](#phase-1-mvp-foundation-month-1-3)
2. [Phase 2: Enterprise Features (Month 4-6)](#phase-2-enterprise-features-month-4-6)
3. [Phase 3: Scale & Compliance (Month 7-9)](#phase-3-scale--compliance-month-7-9)
4. [Phase 4: Global Launch (Month 10-12)](#phase-4-global-launch-month-10-12)
5. [Sprint Calendar](#sprint-calendar)
6. [Definition of Done](#definition-of-done)
7. [Risk-Dependent Tasks](#risk-dependent-tasks)

---

## Legend

| Symbol | Meaning |
| :--- | :--- |
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Completed |
| 🔴 | Critical path |
| 🟡 | Important |
| 🟢 | Nice to have |
| `BE` | Backend (FastAPI) |
| `FE` | Frontend (Next.js) |
| `ML` | ML Engineering |
| `DO` | DevOps |
| `PM` | Product Management |

---

## Phase 1: MVP Foundation (Month 1-3)

**Goal**: Working chat + RAG + Auth for one department (IT Ops) with 3 pilot customers.

---

### Sprint 1-2 (Week 1-4): Infrastructure & Core Backend

#### 🔴 1.1 Project Setup & DevOps Foundation

- [x] `DO` Initialize monorepo structure (`/frontend`, `/backend`, `/infra`, `/ml`, `/docs`)
- [x] `DO` Create `docker-compose.yml` for local development (all services)
- [x] `DO` Setup CI/CD pipeline (GitHub Actions / GitLab CI)
  - [x] Lint + type-check on PR
  - [x] Unit tests on PR
  - [x] Build Docker images on merge to `main`
  - [x] Deploy to staging on merge to `develop`
- [ ] `DO` Setup staging environment (cloud VM or K8s cluster)
- [x] `DO` Configure `.env` management (dev/staging/prod)
- [x] `DO` Setup Terraform for cloud infrastructure (if applicable)

#### 🔴 1.2 Database Setup

- [x] `BE` Install & configure PostgreSQL 16 with Docker
- [x] `BE` Create initial Alembic migration setup
- [x] `BE` Design & create core tables:
  - [x] `tenants` table
  - [x] `users` table
  - [x] `departments` table
  - [x] `department_members` table
  - [x] `knowledge_docs` table
  - [x] `query_logs` table
  - [x] `approvals` table
- [x] `BE` Enable Row-Level Security (RLS) on all tenant-scoped tables
- [x] `BE` Create RLS policies for tenant isolation
- [x] `BE` Create seed data script (demo tenant + users)
- [x] `BE` Setup Qdrant vector database with Docker
- [x] `BE` Create initial Qdrant collection (with tenant/dept payload schema)
- [x] `BE` Setup Redis 7.2 with Docker
- [x] `BE` Setup MinIO with Docker (create default buckets)

#### 🔴 1.3 Authentication & Authorization

- [x] `BE` Deploy Keycloak 23 (Docker)
- [x] `BE` Create default realm configuration
- [x] `BE` Configure OIDC client for the Next.js app
- [x] `BE` Configure OIDC client for the FastAPI backend
- [x] `BE` Implement JWT validation middleware in FastAPI
- [x] `BE` Implement tenant context extraction from JWT claims
- [x] `BE` Implement RBAC middleware (role-based access per department)
- [x] `BE` Create API key generation & validation system
- [x] `BE` Write auth unit tests (JWT, RBAC, tenant isolation)

#### 🔴 1.4 FastAPI Backend Core

- [x] `BE` Initialize FastAPI project with Pydantic v2
- [x] `BE` Setup project structure (`api/`, `services/`, `models/`, `agents/`, `integrations/`)
- [x] `BE` Create database session management (async SQLAlchemy)
- [x] `BE` Create dependency injection for DB, Auth, Tenant context
- [x] `BE` Implement tenant context middleware (set `app.current_tenant` for RLS)
- [x] `BE` Create core exception handlers (400, 401, 403, 404, 429, 500)
- [x] `BE` Implement rate limiting middleware (Redis-based, per tenant)
- [x] `BE` Create health check endpoint (`/health`, `/ready`)
- [x] `BE` Setup request logging middleware (structured JSON logs)
- [x] `BE` Write API integration tests (health, auth)

---

### Sprint 3-4 (Week 5-8): RAG Pipeline & Chat Interface

#### 🔴 1.5 RAG Pipeline Implementation

- [x] `ML` Select & download embedding model (BGE-large-en-v1.5)
- [x] `ML` Implement document ingestion pipeline:
  - [x] Text extraction from PDF, DOCX, TXT, MD
  - [x] Text chunking (RecursiveCharacterTextSplitter, 512 tokens, 50 overlap)
  - [x] Embedding generation (batch processing)
  - [x] Vector storage in Qdrant (with tenant/dept payload metadata)
- [x] `ML` Implement retrieval pipeline:
  - [x] Query embedding
  - [x] Qdrant similarity search (with tenant + department filtering)
  - [x] Reranking (cross-encoder or simple relevance scoring)
  - [x] Context window construction (top-K results → prompt)
- [x] `BE` Create knowledge upload API endpoint (`POST /api/v1/knowledge/{dept_id}/upload`)
- [x] `BE` Create knowledge listing API endpoint (`GET /api/v1/knowledge/{dept_id}`)
- [x] `BE` Create knowledge deletion endpoint (`DELETE /api/v1/knowledge/{dept_id}/{doc_id}`)
- [x] `BE` Implement async document processing (Celery task for ingestion)
- [x] `ML` Write RAG pipeline unit tests (ingestion, retrieval, accuracy)

#### 🔴 1.6 LLM Integration (Ollama)

- [x] `ML` Deploy Ollama with Docker
- [ ] `ML` Download base models (Llama 3 8B Instruct, Mistral 7B)
- [x] `ML` Implement LLM inference client (Ollama API wrapper)
- [x] `ML` Create prompt templates per department type
- [x] `ML` Implement response streaming (SSE/WebSocket)
- [x] `ML` Add confidence scoring logic
- [ ] `ML` Write inference tests (latency, quality, streaming)

#### 🔴 1.7 LangGraph Orchestrator

- [x] `BE` Design state machine graph (nodes, edges, conditions)
- [x] `BE` Implement core nodes:
  - [x] `receive_query` — Parse input (text + optional image)
  - [x] `route_department` — Select correct department config
  - [x] `rag_search` — Execute RAG retrieval
  - [x] `confidence_check` — Evaluate answer confidence
  - [x] `generate_answer` — Call LLM with RAG context
  - [x] `return_answer` — Format and return response
- [x] `BE` Implement edge conditions (confidence thresholds)
- [x] `BE` Add query logging (save to `query_logs` table)
- [ ] `BE` Write orchestrator tests (full flow, edge cases)

#### 🔴 1.8 Query API Endpoint

- [x] `BE` Create `POST /api/v1/query` endpoint
- [x] `BE` Implement request validation (text, department_id, optional image)
- [x] `BE` Wire endpoint to LangGraph orchestrator
- [x] `BE` Implement response serialization (answer, sources, confidence, timing)
- [x] `BE` Create WebSocket endpoint (`WS /ws/chat/{dept_id}`) for streaming
- [x] `BE` Add quota checking before query execution
- [x] `BE` Write query endpoint integration tests

---

### Sprint 5-6 (Week 9-12): Frontend & Pilot Launch

#### 🔴 1.9 Frontend — Core UI

- [x] `FE` Initialize Next.js 14 project (App Router)
- [x] `FE` Install & configure ShadCN/UI + Tailwind CSS 3
- [x] `FE` Setup Keycloak OIDC integration (next-auth or custom)
- [x] `FE` Create layout shell:
  - [x] Sidebar navigation
  - [x] Top bar (user avatar, tenant name, logout)
  - [x] Department selector (category dropdown/tabs)
- [x] `FE` Implement login page (redirect to Keycloak)
- [x] `FE` Implement auth callback handler

#### 🔴 1.10 Frontend — Chat Interface

- [x] `FE` Create `ChatWindow` component
- [x] `FE` Create `MessageBubble` component (user/AI variants)
- [x] `FE` Create `DepartmentSelector` component (category tabs with icons)
- [x] `FE` Implement text input with send button
- [x] `FE` Implement image/screenshot upload preview
- [x] `FE` Implement WebSocket connection for streaming responses
- [x] `FE` Display AI response with source citations (expandable)
- [x] `FE` Display confidence score badge
- [x] `FE` Implement chat history (per session)
- [x] `FE` Add loading/typing indicator during AI processing
- [x] `FE` Responsive design (mobile + desktop)

#### 🟡 1.11 Frontend — Knowledge Management

- [x] `FE` Create knowledge base page (per department)
- [x] `FE` Implement document upload form (drag-and-drop file upload)
- [x] `FE` Display document list (title, type, chunks, status, date)
- [x] `FE` Implement document deletion with confirmation
- [x] `FE` Show processing status (uploading → processing → indexed)

#### 🟡 1.12 Pilot Launch Preparation

- [ ] `PM` Identify 3 pilot customers (internal + external)
- [ ] `PM` Create onboarding guide document
- [x] `PM` Setup demo tenant with sample IT Ops knowledge base
- [ ] `DO` Deploy to staging environment
- [ ] `DO` Run load test (100 concurrent users, 50 req/sec)
- [ ] `BE` Fix any bugs found during pilot testing
- [ ] `PM` Collect pilot feedback (survey + interviews)

---

## Phase 2: Enterprise Features (Month 4-6)

**Goal**: Multi-department, Custom Models, Human-in-the-Loop, SSO, Analytics. 10 paying tenants.

---

### Sprint 7-8 (Week 13-16): Multi-Department & HITL

#### 🔴 2.1 Multi-Department System

- [x] `BE` Create Department CRUD API:
  - [x] `POST /api/v1/departments` — Create department
  - [x] `GET /api/v1/departments` — List departments
  - [x] `PUT /api/v1/departments/{id}` — Update department config
  - [x] `DELETE /api/v1/departments/{id}` — Archive department
- [x] `BE` Implement department configuration loader (YAML-based)
- [ ] `BE` Create department-specific Qdrant collection provisioning
- [x] `BE` Implement department-level access control (RBAC per dept)
- [x] `BE` Create department member management API
- [x] `FE` Create department management settings page
- [x] `FE` Create department creation wizard (name, icon, description, roles)
- [x] `FE` Update chat to dynamically load departments from API
- [x] `FE` Add department-specific styling (icon, color accent)
- [x] `BE` Write multi-department integration tests

#### 🔴 2.2 Human-in-the-Loop (HITL) Workflow

- [x] `BE` Add HITL nodes to LangGraph:
  - [x] `escalate_to_human` — Create approval ticket when confidence < threshold
  - [x] `wait_for_approval` — Pause workflow, notify reviewer
  - [x] `process_approval` — Update knowledge base with approved answer
  - [x] `process_rejection` — Log rejection, prompt expert for corrected answer
- [x] `BE` Create Approval API:
  - [x] `GET /api/v1/approvals` — List pending approvals (filtered by dept)
  - [x] `GET /api/v1/approvals/{id}` — Get approval detail
  - [x] `POST /api/v1/approvals/{id}/approve` — Approve answer (with optional edit)
  - [x] `POST /api/v1/approvals/{id}/reject` — Reject with reason + corrected answer
- [x] `BE` Implement approval notification system (email + in-app)
- [x] `BE` Auto-index approved answers into Qdrant
- [x] `FE` Create approval queue page (list of pending items)
- [x] `FE` Create approval detail view (query, AI answer, edit field, approve/reject)
- [x] `FE` Add approval badge count to sidebar navigation
- [ ] `FE` Real-time update when new approval arrives (WebSocket)
- [ ] `BE` Write HITL workflow tests (approve path, reject path, edge cases)

---

### Sprint 9-10 (Week 17-20): Custom Models & Vision

#### 🔴 2.3 Screenshot/Image Analysis (Vision Pipeline)

- [ ] `ML` Deploy vision model (LLaVA 1.6 or Llama 3.2 Vision via Ollama)
- [x] `ML` Implement image preprocessing pipeline:
  - [x] Resize/compress to max 2048px
  - [x] Format conversion (PNG/JPG → standardized)
  - [ ] Store original in MinIO (`tenant-{id}/dept-{id}/images/`)
- [x] `ML` Implement vision inference:
  - [x] Extract text from screenshot (OCR-like)
  - [x] Describe visual elements (error dialogs, UI state)
  - [x] Combine extracted info with text query
- [ ] `BE` Update query endpoint to accept `multipart/form-data` with image
- [x] `BE` Add vision node to LangGraph state machine
- [x] `FE` Implement image upload preview in chat (thumbnail + remove)
- [x] `FE` Implement paste-from-clipboard for screenshots
- [ ] `ML` Write vision pipeline tests (accuracy on sample screenshots)

#### 🔴 2.4 Custom Model Fine-Tuning Pipeline

- [ ] `ML` Setup training infrastructure:
  - [ ] Configure GPU server for training (A100 or 2× RTX 4090)
  - [x] Install PyTorch 2.2+, HuggingFace Transformers, PEFT
  - [ ] Setup MLflow server for experiment tracking
- [x] `ML` Implement training data pipeline:
  - [x] Export approved Q&A pairs from PostgreSQL
  - [x] Convert to instruction-tuning format (instruction/input/output JSON)
  - [x] Data cleaning & deduplication
  - [x] Train/validation/test split (80/10/10)
- [x] `ML` Implement LoRA fine-tuning script:
  - [x] Load base model (Llama 3 8B)
  - [x] Configure LoRA (r=16, alpha=32, target_modules)
  - [x] Training loop with evaluation metrics (BLEU, ROUGE, F1)
  - [x] Save adapter weights + MLflow logging
- [x] `ML` Implement model deployment pipeline:
  - [x] ONNX export + quantization (INT8)
  - [x] Register in MLflow Model Registry (staging → production)
  - [ ] Deploy to Triton Inference Server
  - [x] Hot-swap adapter without restart
- [x] `ML` Create Airflow DAG for automated retraining:
  - [x] Trigger: >50 new approved answers since last training
  - [x] Steps: Export → Clean → Train → Evaluate → Deploy
  - [x] Rollback if evaluation metrics drop
- [x] `BE` Create model management API:
  - [x] `GET /api/v1/models` — List trained models per department
  - [x] `POST /api/v1/models/train` — Trigger training run
  - [x] `GET /api/v1/models/{id}/status` — Training status
- [x] `FE` Create model management page (list versions, metrics, status)
- [ ] `ML` Write training pipeline tests (data format, training loop, deployment)

---

### Sprint 11-12 (Week 21-24): SSO & Analytics

#### 🟡 2.5 SSO Integration (Keycloak Enterprise)

- [ ] `BE` Implement multi-realm Keycloak management (one realm per tenant)
- [ ] `BE` Create tenant onboarding API (auto-create realm + admin user)
- [ ] `BE` Support SAML 2.0 integration (for clients with existing IdP)
- [ ] `BE` Support LDAP/AD sync (for on-premise enterprise clients)
- [ ] `BE` Implement group-to-department role mapping
- [ ] `FE` Create SSO configuration page (for tenant admins)
- [ ] `BE` Write SSO integration tests

#### 🟡 2.6 Analytics Dashboard

- [x] `BE` Create analytics aggregation service:
  - [x] Queries per day/week/month (by department)
  - [x] Avg confidence score trend
  - [x] MTTR (Mean Time to Resolution) tracking
  - [x] Top queried topics per department
  - [x] Approval rate (auto vs human)
  - [x] Model accuracy over time
  - [x] Active users per department
- [x] `BE` Create analytics API endpoints:
  - [x] `GET /api/v1/analytics/usage` — Usage overview
  - [x] `GET /api/v1/analytics/departments/{id}` — Per-department stats
  - [x] `GET /api/v1/analytics/ai-performance` — AI metrics
  - [x] `GET /api/v1/analytics/export` — CSV/JSON export
- [x] `FE` Create analytics dashboard page:
  - [x] Usage charts (line, bar, pie) using Recharts or Chart.js
  - [x] Department comparison view
  - [x] Date range selector
  - [x] Export button (CSV download)
- [x] `BE` Write analytics tests

#### 🟡 2.7 Sub-Agent Integration

- [x] `ML` Implement CrewAI research agent:
  - [x] "Analyzer" agent: Deep-dive into complex errors (multi-step reasoning)
  - [x] "Researcher" agent: Search external docs (optional internet access)
- [x] `ML` Implement AutoGen code analysis agent:
  - [x] Parse code snippets from queries
  - [x] Identify potential bugs or misconfigurations
  - [x] Suggest code fixes
- [x] `BE` Integrate sub-agents into LangGraph as optional nodes
- [x] `BE` Add config flag to enable/disable per department

---

## Phase 3: Scale & Compliance (Month 7-9)

**Goal**: Big Data pipeline, Billing/Payments, BYOD, White-labeling. 50 tenants. SOC2 audit started.

---

### Sprint 13-14 (Week 25-28): Big Data & Billing

#### 🟡 3.1 Big Data Pipeline

- [ ] `DO` Deploy Apache Kafka cluster (3 brokers)
- [ ] `DO` Deploy Apache Spark cluster (1 master + 2 workers)
- [ ] `DO` Deploy Apache Airflow (scheduler + webserver + workers)
- [ ] `BE` Create Kafka producer integration (publish events on query, approval, upload)
- [ ] `BE` Create Kafka topics:
  - [ ] `queries.{tenant_id}` — All queries
  - [ ] `approvals.{tenant_id}` — Approval events
  - [ ] `knowledge.{tenant_id}` — Document ingestion events
- [ ] `ML` Create Spark ETL jobs:
  - [ ] Consume from Kafka → Clean → Transform
  - [ ] Batch embedding generation (every 6 hours)
  - [ ] Deduplication pipeline
  - [ ] Archive to HDFS (cold storage, 90+ days)
- [x] `DO` Create Airflow DAGs:
  - [ ] Hourly: Kafka → Spark → Qdrant (incremental)
  - [x] Nightly: Full consistency check (PG ↔ Qdrant)
  - [x] Weekly: HDFS archival + cleanup
  - [ ] Monthly: Training data export for retraining
- [ ] `BE` Write data pipeline integration tests

#### 🔴 3.2 Billing & Subscription System

- [x] `BE` Create billing database tables:
  - [x] `subscriptions` — Plan tier, pricing, cycle, Stripe ID
  - [x] `usage_records` — Daily usage per tenant/user
  - [x] `invoices` — Generated invoices
  - [x] `api_keys` — API key management
- [x] `BE` Implement Stripe integration:
  - [x] Create customers on tenant signup
  - [x] Create subscriptions (monthly/annual)
  - [x] Handle webhooks: `invoice.paid`, `payment_failed`, `subscription.deleted`
  - [x] Metered billing for usage add-ons
- [x] `BE` Implement usage metering service:
  - [x] Track queries per day (Redis counter)
  - [x] Track image queries separately
  - [x] Track token usage per model
  - [ ] Report usage to Stripe at end of billing cycle
- [x] `BE` Implement quota enforcement:
  - [x] Check quota before query execution
  - [ ] Return 429 with upgrade prompt on quota exceeded
  - [ ] Grace period for overages (10% buffer)
- [x] `BE` Create billing API:
  - [x] `GET /api/v1/billing/subscription` — Current plan details
  - [ ] `POST /api/v1/billing/subscribe` — Start subscription
  - [x] `POST /api/v1/billing/upgrade` — Upgrade plan
  - [x] `GET /api/v1/billing/usage` — Usage summary
  - [x] `GET /api/v1/billing/invoices` — Invoice history
- [x] `FE` Create billing settings page:
  - [x] Current plan display
  - [x] Usage meter (queries used / limit)
  - [x] Plan comparison table with upgrade buttons
  - [ ] Payment method management (Stripe Elements)
  - [ ] Invoice history with download links
- [x] `BE` Write billing tests (subscription lifecycle, quota, webhooks)

---

### Sprint 15-16 (Week 29-32): BYOD & White-Label

#### 🟡 3.3 BYOD / Hybrid Deployment

- [ ] `DO` Create Edge Agent Docker image:
  - [ ] Lightweight FastAPI + Ollama + Qdrant (single container)
  - [ ] Auto-connect to central cloud for model updates
  - [ ] Local data processing (query + embed + store locally)
  - [ ] Sync anonymized vectors/usage stats to cloud (optional)
- [ ] `BE` Implement VPC Private Link configuration:
  - [ ] Support client's PostgreSQL connection string
  - [ ] Support client's S3/MinIO endpoint
  - [ ] Connection pooling with PgBouncer
- [x] `BE` Create Edge Agent management API:
  - [x] `POST /api/v1/edge/register` — Register edge agent
  - [x] `GET /api/v1/edge/status` — Agent health status
  - [x] `POST /api/v1/edge/sync` — Trigger model sync
- [ ] `DO` Create Edge Agent installation script (bash + Docker)
- [ ] `PM` Write BYOD deployment guide
- [ ] `BE` Write BYOD integration tests

#### 🟡 3.4 White-Labeling

- [x] `BE` Add tenant branding config:
  - [x] `logo_url` — Custom logo
  - [x] `primary_color` — Brand color
  - [x] `secondary_color` — Accent color
  - [ ] `custom_domain` — CNAME mapping
  - [x] `company_name` — Display name
- [ ] `FE` Implement dynamic theming (CSS variables from tenant config)
- [ ] `FE` Implement custom logo rendering (sidebar + login page)
- [ ] `DO` Setup custom domain mapping (Nginx + Let's Encrypt auto-SSL)
- [x] `FE` Create white-label settings page (logo upload, color picker, domain)
- [ ] `BE` Write white-label tests

#### 🟡 3.5 Compliance & Security Hardening

- [ ] `DO` Implement HashiCorp Vault for secret management
- [ ] `DO` Setup container vulnerability scanning (Trivy in CI/CD)
- [ ] `DO` Setup dependency vulnerability scanning (Snyk / Dependabot)
- [x] `BE` Implement comprehensive audit logging:
  - [x] All data access events
  - [x] All configuration changes
  - [x] All authentication events
  - [x] Immutable log storage (append-only)
- [x] `BE` Implement data retention policies:
  - [x] Auto-purge expired data per tenant config
  - [x] GDPR right-to-be-forgotten API
  - [x] Data export API (tenant data portability)
- [ ] `PM` Begin SOC 2 Type II audit preparation
- [ ] `PM` Create security documentation (architecture, controls, policies)

---

## Phase 4: Global Launch (Month 10-12)

**Goal**: Marketplace foundations, Advanced Analytics, Multi-region, Break-even. 100+ tenants.

---

### Sprint 17-18 (Week 33-36): Advanced Features

#### 🟢 4.1 Advanced Analytics

- [x] `BE` Implement AI performance tracking:
  - [x] Answer accuracy trend (based on approval/rejection rates)
  - [x] Model drift detection (confidence score degradation)
  - [x] Topic clustering (what questions are asked most?)
  - [x] Department comparison metrics
- [x] `BE` Implement team productivity metrics:
  - [x] Queries per user per day
  - [x] Self-service rate (auto-resolved vs escalated)
  - [x] Knowledge base growth rate
  - [x] Time saved calculation per tenant
- [x] `FE` Create executive dashboard (C-level summary view)
- [x] `FE` Create department comparison charts
- [ ] `FE` Implement scheduled report generation (email weekly summary)

#### 🟢 4.2 Integration Ecosystem

- [x] `BE` Create webhook system:
  - [x] Configurable event triggers (query.created, approval.completed, etc.)
  - [x] Webhook URL management API
  - [x] Retry logic with exponential backoff
- [x] `BE` Build Jira integration:
  - [x] Auto-create Jira ticket on escalation
  - [ ] Sync resolution status back
- [ ] `BE` Build ServiceNow integration:
  - [ ] Create incidents from unresolved queries
  - [ ] Read CMDB for context enrichment
- [x] `BE` Build PagerDuty integration:
  - [x] Trigger alert on critical escalations
  - [x] Acknowledge/resolve from The Expert
- [x] `BE` Build Slack/Teams integration:
  - [x] Slash command `/expert ask <question>`
  - [x] Notification channel for approvals
- [ ] `PM` Create integration documentation & setup guides

---

### Sprint 19-20 (Week 37-40): Production Hardening

#### 🔴 4.3 Performance Optimization

- [x] `DO` Implement Kubernetes Horizontal Pod Autoscaler (HPA):
  - [x] API server: scale 3→20 based on CPU/request rate
  - [ ] Triton server: scale 2→8 based on GPU utilization
- [ ] `DO` Setup multi-region deployment (primary + DR):
  - [ ] Primary: Singapore (APAC)
  - [ ] DR: Tokyo or Sydney
  - [ ] Database replication (async, read replicas)
- [x] `BE` Implement caching strategy:
  - [x] Query result cache (Redis, 1-hour TTL for identical queries)
  - [x] RAG result cache (Redis, department-scoped)
  - [x] Embedding cache (avoid re-embedding same documents)
- [ ] `DO` Run production load tests:
  - [ ] Target: 1,000 concurrent users, 200 req/sec
  - [ ] P95 latency < 3 seconds
  - [ ] Zero data leakage between tenants
- [ ] `DO` Implement chaos testing (network failures, node failures)

#### 🔴 4.4 Monitoring & Alerting

- [x] `DO` Deploy Grafana + Prometheus stack
- [x] `DO` Create dashboards:
  - [x] System health (CPU, memory, disk, network)
  - [x] API performance (request rate, latency, errors)
  - [x] AI performance (inference time, token usage, queue depth)
  - [ ] Business metrics (active tenants, queries, revenue)
- [ ] `DO` Deploy Langfuse for LLM tracing
- [x] `DO` Deploy Loki for centralized logging
- [x] `DO` Configure alerts:
  - [x] P95 latency > 3s → PagerDuty
  - [x] Error rate > 1% → Slack + PagerDuty
  - [x] GPU utilization > 90% → Scale warning
  - [x] Database CPU > 80% → Scale warning
  - [ ] Approval queue > 50 items → Email to dept leads
- [ ] `DO` Create runbooks for each alert scenario

---

### Sprint 21-22 (Week 41-44): On-Premise Package & Launch

#### 🟡 4.5 On-Premise Deployment Package

- [x] `DO` Create Kubernetes Helm chart for full stack deployment
- [x] `DO` Create Docker Compose config for small deployments
- [ ] `DO` Create installation script (automated setup wizard)
- [ ] `DO` Create hardware sizing guide:
  - [ ] Small (100 users): 2× servers, 1× GPU
  - [ ] Medium (500 users): 4× servers, 2× GPU
  - [ ] Large (1000+ users): K8s cluster, 4× GPU
- [ ] `DO` Create air-gapped deployment package (all images + models offline)
- [ ] `PM` Create on-premise installation guide (step-by-step)
- [ ] `PM` Create on-premise maintenance guide (backup, update, troubleshoot)
- [ ] `DO` Test full on-premise deployment (clean Ubuntu 22.04 server)

#### 🟢 4.6 Marketplace Foundations

- [x] `BE` Design plugin architecture:
  - [x] Plugin interface definition (input/output contract)
  - [x] Plugin discovery & registration API
  - [x] Sandboxed execution environment
- [x] `BE` Create 2-3 example plugins:
  - [x] "Log Parser" (parse common log formats: Apache, Nginx, syslog)
  - [x] "Config Validator" (validate YAML/JSON configs against schema)
  - [x] "Incident Report Generator" (auto-generate incident summary)
- [x] `FE` Create marketplace UI (browse, install, configure)
- [ ] `PM` Create plugin development documentation & SDK

---

### Sprint 23-24 (Week 45-48): Launch & Stabilize

#### 🔴 4.7 Official Launch

- [ ] `PM` Prepare launch announcement (blog post, press release)
- [ ] `PM` Create product demo video (3-5 minutes)
- [ ] `PM` Create customer case studies (from pilot customers)
- [ ] `PM` Setup product website (landing page + pricing + docs)
- [ ] `PM` Setup customer support system (Intercom / Zendesk)
- [ ] `PM` Setup community forum (Discourse) or Discord server
- [ ] `DO` Final security audit (penetration testing)
- [ ] `DO` Verify SOC 2 compliance checklist
- [ ] `DO` Deploy production environment (multi-region)
- [ ] `PM` Execute launch campaign (LinkedIn, conferences, emails)

#### 🟡 4.8 Post-Launch Optimization

- [ ] `PM` Monitor customer feedback & feature requests
- [ ] `BE` Fix critical bugs (P0/P1 within 24 hours)
- [ ] `ML` Retrain models with new customer data (first batch)
- [ ] `FE` UX improvements based on user behavior analytics
- [ ] `PM` Plan Year 2 roadmap based on market feedback

---

## Sprint Calendar

| Sprint | Week | Dates (2026) | Focus |
| :--- | :--- | :--- | :--- |
| Sprint 1 | W1-W2 | Feb 16 - Mar 1 | Infrastructure, DB, DevOps Setup |
| Sprint 2 | W3-W4 | Mar 2 - Mar 15 | Auth (Keycloak), FastAPI Core |
| Sprint 3 | W5-W6 | Mar 16 - Mar 29 | RAG Pipeline, Embeddings, Qdrant |
| Sprint 4 | W7-W8 | Mar 30 - Apr 12 | LLM Integration, LangGraph, Query API |
| Sprint 5 | W9-W10 | Apr 13 - Apr 26 | Frontend Core (Chat, Auth, Layout) |
| Sprint 6 | W11-W12 | Apr 27 - May 10 | Frontend Polish, Knowledge UI, **Pilot Launch** |
| Sprint 7 | W13-W14 | May 11 - May 24 | Multi-Department System |
| Sprint 8 | W15-W16 | May 25 - Jun 7 | Human-in-the-Loop (HITL) |
| Sprint 9 | W17-W18 | Jun 8 - Jun 21 | Vision/Image Analysis Pipeline |
| Sprint 10 | W19-W20 | Jun 22 - Jul 5 | Custom Model Training (LoRA) |
| Sprint 11 | W21-W22 | Jul 6 - Jul 19 | SSO Enterprise, Sub-Agents |
| Sprint 12 | W23-W24 | Jul 20 - Aug 2 | Analytics Dashboard |
| Sprint 13 | W25-W26 | Aug 3 - Aug 16 | Big Data Pipeline (Kafka/Spark) |
| Sprint 14 | W27-W28 | Aug 17 - Aug 30 | Billing & Payments (Stripe) |
| Sprint 15 | W29-W30 | Aug 31 - Sep 13 | BYOD / Edge Agent |
| Sprint 16 | W31-W32 | Sep 14 - Sep 27 | White-Label, Compliance |
| Sprint 17 | W33-W34 | Sep 28 - Oct 11 | Advanced Analytics |
| Sprint 18 | W35-W36 | Oct 12 - Oct 25 | Integration Ecosystem |
| Sprint 19 | W37-W38 | Oct 26 - Nov 8 | Performance & Scaling |
| Sprint 20 | W39-W40 | Nov 9 - Nov 22 | Monitoring & Alerting |
| Sprint 21 | W41-W42 | Nov 23 - Dec 6 | On-Premise Package |
| Sprint 22 | W43-W44 | Dec 7 - Dec 20 | Marketplace Foundations |
| Sprint 23 | W45-W46 | Dec 21 - Jan 3 | Launch Preparation |
| Sprint 24 | W47-W48 | Jan 4 - Jan 17 | **Official Launch** 🚀 |

---

## Definition of Done

Every task must meet the following criteria before being marked `[x]`:

| Criterion | Detail |
| :--- | :--- |
| **Code Complete** | Feature implemented as described |
| **Unit Tests** | ≥80% coverage for new code |
| **Integration Tests** | Key flows tested end-to-end |
| **Documentation** | API docs updated (OpenAPI), README updated |
| **Code Review** | PR approved by ≥1 reviewer |
| **Security Check** | No hardcoded secrets, input validation, auth verified |
| **Tenant Isolation** | Verified: no cross-tenant data leakage |
| **Performance** | Meets latency targets (P95 < 3s for queries) |
| **Accessibility** | UI meets WCAG 2.1 AA |
| **Deployed to Staging** | Feature available and tested in staging |

---

## Risk-Dependent Tasks

These tasks are conditional based on external factors:

| Condition | If True → Do | If False → Skip |
| :--- | :--- | :--- |
| Pilot customer needs SAML SSO | Sprint 11: SAML implementation | Use OIDC only |
| GPU budget approved for A100 | Use Triton + vLLM for production | Ollama + CPU fallback |
| >100 tenants by Month 9 | Multi-region deployment (Sprint 19) | Single-region is fine |
| SOC 2 audit required for enterprise deal | Start compliance work (Sprint 16) | Defer to Year 2 |
| Customer requests air-gapped deployment | Build offline installer (Sprint 21) | Docker Compose is sufficient |

---

## Related Documents

- [Implementation Plan](./implementation_plan.md) — Detailed architecture & tech design
- [Proposal](./proposal.md) — Business proposal & financials
- [BRD](./brd.md) — Business Requirements
- [PRD](./prd.md) — Product Requirements
- [Subscription Plan](./subscription_plan.md) — Pricing & billing details
