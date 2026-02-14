# API Specification

**Project Name**: The Expert — Universal Enterprise AI Platform
**Version**: v1.0
**Base URL**: `https://api.the-expert.ai/api/v1`
**Protocol**: REST + WebSocket
**Auth**: Bearer JWT (Keycloak OIDC) or API Key
**Format**: JSON (application/json)

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Common Headers & Errors](#2-common-headers--errors)
3. [Query (AI Chat)](#3-query-ai-chat)
4. [Departments](#4-departments)
5. [Knowledge Base](#5-knowledge-base)
6. [Approvals (HITL)](#6-approvals-hitl)
7. [Conversations & Messages](#7-conversations--messages)
8. [Users](#8-users)
9. [Models (AI/ML)](#9-models-aiml)
10. [Analytics](#10-analytics)
11. [Billing & Subscription](#11-billing--subscription)
12. [API Keys](#12-api-keys)
13. [WebSocket (Real-time Chat)](#13-websocket-real-time-chat)
14. [Webhooks](#14-webhooks)
15. [Rate Limiting](#15-rate-limiting)

---

## 1. Authentication

### 1.1 Login (Get JWT Token)

```
POST /auth/login
Content-Type: application/json
```

**Request:**

```json
{
  "email": "user@acme.com",
  "password": "********"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "usr_abc123",
    "email": "user@acme.com",
    "full_name": "Chanon S.",
    "role": "admin",
    "tenant_id": "tnt_xyz789",
    "departments": [
      {"id": "dept_001", "name": "IT Operations", "role": "approver"},
      {"id": "dept_002", "name": "HR", "role": "member"}
    ]
  }
}
```

### 1.2 Refresh Token

```
POST /auth/refresh
Content-Type: application/json
Authorization: Bearer <refresh_token>
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOi...",
  "expires_in": 3600
}
```

### 1.3 SSO Login (Redirect-based)

```
GET /auth/sso?tenant=acme-corp
→ Redirect to Keycloak login page
→ Callback: /auth/callback?code=xxx&state=yyy
```

---

## 2. Common Headers & Errors

### Required Headers

| Header | Value | Required |
| :--- | :--- | :--- |
| `Authorization` | `Bearer <jwt_token>` or `ApiKey <key>` | ✅ Yes |
| `Content-Type` | `application/json` | ✅ Yes (POST/PUT) |
| `X-Request-ID` | UUID (idempotency key) | 🟡 Optional |
| `Accept-Language` | `en`, `th` | 🟡 Optional |

### Pagination

All list endpoints support pagination:

```
GET /api/v1/departments?page=1&per_page=20&sort=created_at&order=desc
```

**Response envelope:**

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 85,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

### Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Department ID is required",
    "details": [
      {"field": "department_id", "reason": "Field is required"}
    ],
    "request_id": "req_abc123"
  }
}
```

### HTTP Status Codes

| Code | Meaning | When |
| :--- | :--- | :--- |
| `200` | OK | Successful GET/PUT |
| `201` | Created | Successful POST (create) |
| `204` | No Content | Successful DELETE |
| `400` | Bad Request | Validation error |
| `401` | Unauthorized | Missing/invalid token |
| `403` | Forbidden | No permission (wrong role/department) |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Duplicate resource |
| `429` | Too Many Requests | Rate limit / quota exceeded |
| `500` | Internal Server Error | Unexpected server error |

---

## 3. Query (AI Chat)

### 3.1 Submit Query

```
POST /query
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Request (form-data):**

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `department_id` | string | ✅ | Target department UUID |
| `query_text` | string | ✅ | User's question |
| `image` | file | ❌ | Screenshot/image (PNG, JPG, max 10MB) |
| `conversation_id` | string | ❌ | Continue existing conversation |
| `context` | JSON string | ❌ | Additional context metadata |
| `model_preference` | string | ❌ | `"auto"`, `"fast"`, `"accurate"` |

**Response (200):**

```json
{
  "query_id": "msg_2026021201",
  "conversation_id": "conv_abc123",
  "department": {
    "id": "dept_001",
    "name": "IT Operations",
    "icon": "🖥️"
  },
  "answer": "Based on the OOM killer logs, your Java heap is configured at 2GB but the container limit is 1.5GB.\n\n**Solution:**\n1. Increase container memory limit to 4GB\n2. Set JVM: `-Xmx2g -Xms1g`\n3. Add `-XX:+UseContainerSupport`",
  "confidence": 0.92,
  "status": "completed",
  "sources": [
    {
      "doc_id": "kb_123",
      "title": "JVM Troubleshooting Guide",
      "chunk_id": "chk_456",
      "relevance": 0.95,
      "snippet": "When OOM killer triggers on a containerized JVM..."
    },
    {
      "doc_id": "kb_789",
      "title": "K8s Memory Limits",
      "chunk_id": "chk_012",
      "relevance": 0.87,
      "snippet": "Container memory limits must exceed JVM heap..."
    }
  ],
  "model_used": "llama3-8b-it-ops-v3",
  "tokens": {
    "input": 512,
    "output": 256
  },
  "latency_ms": 1250,
  "requires_approval": false,
  "created_at": "2026-02-12T15:30:00Z"
}
```

**Response (Pending Approval — confidence < threshold):**

```json
{
  "query_id": "msg_2026021202",
  "conversation_id": "conv_abc123",
  "status": "pending_approval",
  "message": "I'm not confident enough to answer directly. This has been sent to an expert for review.",
  "approval_id": "apr_xyz789",
  "estimated_review_time": "within 4 hours",
  "confidence": 0.62
}
```

### 3.2 Query with Streaming (SSE)

```
POST /query/stream
Content-Type: application/json
Authorization: Bearer <token>
Accept: text/event-stream
```

**Request:**

```json
{
  "department_id": "dept_001",
  "query_text": "How to fix nginx 502 bad gateway?"
}
```

**Response (Server-Sent Events):**

```
event: start
data: {"query_id": "msg_001", "model": "llama3-8b"}

event: token
data: {"content": "A 502 "}

event: token
data: {"content": "Bad Gateway "}

event: token
data: {"content": "error typically means..."}

event: sources
data: {"sources": [{"title": "Nginx Troubleshooting", "relevance": 0.93}]}

event: done
data: {"total_tokens": 384, "latency_ms": 2100, "confidence": 0.91}
```

---

## 4. Departments

### 4.1 List Departments

```
GET /departments
Authorization: Bearer <token>
```

**Response (200):**

```json
{
  "data": [
    {
      "id": "dept_001",
      "name": "IT Operations",
      "slug": "it-ops",
      "icon": "🖥️",
      "description": "Server, Network, Code troubleshooting",
      "status": "active",
      "member_count": 25,
      "doc_count": 142,
      "query_count_today": 38,
      "sort_order": 1
    },
    {
      "id": "dept_002",
      "name": "HR & People",
      "slug": "hr",
      "icon": "👥",
      "description": "Policies, Benefits, Onboarding",
      "status": "active",
      "member_count": 8,
      "doc_count": 56,
      "query_count_today": 12,
      "sort_order": 2
    }
  ]
}
```

### 4.2 Create Department

```
POST /departments
Authorization: Bearer <token>   (requires: admin/owner)
```

**Request:**

```json
{
  "name": "Legal",
  "slug": "legal",
  "icon": "⚖️",
  "description": "Contracts, Compliance, NDA",
  "config": {
    "model": {
      "system_prompt": "You are a legal expert. Always cite the relevant law or contract clause.",
      "temperature": 0.2,
      "max_tokens": 1500
    },
    "approval": {
      "required_for": "all_answers",
      "approver_role": "approver",
      "auto_approve_confidence": 0.98
    }
  }
}
```

**Response (201):**

```json
{
  "id": "dept_003",
  "name": "Legal",
  "slug": "legal",
  "status": "active",
  "created_at": "2026-02-12T16:00:00Z"
}
```

### 4.3 Update Department

```
PUT /departments/{department_id}
Authorization: Bearer <token>   (requires: admin/owner)
```

### 4.4 Delete Department (Archive)

```
DELETE /departments/{department_id}
Authorization: Bearer <token>   (requires: owner)
```

**Response (204):** No Content

### 4.5 Department Members

```
GET    /departments/{department_id}/members
POST   /departments/{department_id}/members      — Add member
PUT    /departments/{department_id}/members/{user_id}  — Update role
DELETE /departments/{department_id}/members/{user_id}  — Remove member
```

**Add Member Request:**

```json
{
  "user_id": "usr_abc123",
  "role": "approver"
}
```

---

## 5. Knowledge Base

### 5.1 List Documents

```
GET /knowledge/{department_id}?status=indexed&page=1&per_page=20
Authorization: Bearer <token>
```

**Response (200):**

```json
{
  "data": [
    {
      "id": "doc_001",
      "title": "Server Runbook v3.pdf",
      "source_type": "pdf",
      "file_size": 2048576,
      "status": "indexed",
      "chunk_count": 45,
      "uploaded_by": {"id": "usr_001", "name": "Chanon S."},
      "metadata": {
        "page_count": 42,
        "tags": ["server", "linux"],
        "language": "en"
      },
      "created_at": "2026-02-10T10:00:00Z"
    }
  ]
}
```

### 5.2 Upload Document

```
POST /knowledge/{department_id}/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `file` | file | ✅ | Document (PDF, DOCX, TXT, MD, CSV, max 50MB) |
| `title` | string | ❌ | Custom title (default: filename) |
| `tags` | string | ❌ | Comma-separated tags |

**Response (202 Accepted):**

```json
{
  "id": "doc_002",
  "title": "Networking Guide.pdf",
  "status": "processing",
  "message": "Document is being processed. Check status with GET /knowledge/{dept_id}/{doc_id}"
}
```

### 5.3 Get Document Status

```
GET /knowledge/{department_id}/{document_id}
```

### 5.4 Delete Document

```
DELETE /knowledge/{department_id}/{document_id}
```

Removes document + all chunks + Qdrant vectors.

---

## 6. Approvals (HITL)

### 6.1 List Pending Approvals

```
GET /approvals?status=pending&department_id=dept_001&page=1
Authorization: Bearer <token>   (requires: approver role)
```

**Response (200):**

```json
{
  "data": [
    {
      "id": "apr_001",
      "department": {"id": "dept_001", "name": "IT Operations"},
      "message": {
        "id": "msg_123",
        "user_query": "Oracle DB shows ORA-12514 TNS listener error",
        "image_url": "https://minio.../tenant_001/images/msg_123.png"
      },
      "original_answer": "The ORA-12514 error indicates...",
      "confidence": 0.68,
      "status": "pending",
      "priority": "normal",
      "requested_by": {"id": "usr_001", "name": "System"},
      "expires_at": "2026-02-13T15:30:00Z",
      "created_at": "2026-02-12T15:30:00Z"
    }
  ],
  "pagination": {
    "total_items": 5,
    "page": 1
  }
}
```

### 6.2 Approve Answer

```
POST /approvals/{approval_id}/approve
Authorization: Bearer <token>   (requires: approver role)
```

**Request:**

```json
{
  "approved_answer": "The ORA-12514 error means the listener cannot find the service. Fix:\n1. Check `lsnrctl status`\n2. Verify `tnsnames.ora` service name matches\n3. Restart listener: `lsnrctl reload`",
  "reviewer_notes": "AI answer was mostly correct, added specific commands"
}
```

**Response (200):**

```json
{
  "id": "apr_001",
  "status": "approved",
  "message": "Answer approved and indexed into knowledge base",
  "knowledge_indexed": true,
  "reviewed_at": "2026-02-12T16:45:00Z"
}
```

### 6.3 Reject Answer

```
POST /approvals/{approval_id}/reject
Authorization: Bearer <token>
```

**Request:**

```json
{
  "rejection_reason": "The answer suggests restarting the database which is dangerous in production",
  "corrected_answer": "Do NOT restart the database. Instead:\n1. Check listener config...",
  "reviewer_notes": "AI hallucinated a dangerous solution"
}
```

---

## 7. Conversations & Messages

### 7.1 List Conversations

```
GET /conversations?department_id=dept_001&page=1&per_page=20
```

### 7.2 Get Conversation Messages

```
GET /conversations/{conversation_id}/messages?page=1&per_page=50
```

**Response (200):**

```json
{
  "conversation": {
    "id": "conv_001",
    "title": "OOM Killer Issue on web-prod-03",
    "department": {"id": "dept_001", "name": "IT Operations"},
    "status": "active",
    "message_count": 4
  },
  "data": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "Server web-prod-03 showing OOM killer messages",
      "image_url": null,
      "created_at": "2026-02-12T15:30:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "Based on the OOM killer logs...",
      "confidence": 0.92,
      "sources": [...],
      "model_used": "llama3-8b-it-ops-v3",
      "created_at": "2026-02-12T15:30:02Z"
    }
  ]
}
```

### 7.3 Delete Conversation

```
DELETE /conversations/{conversation_id}
```

---

## 8. Users

### 8.1 CRUD Endpoints

```
GET    /users                    — List users (admin)
POST   /users                    — Invite user (admin)
GET    /users/{user_id}          — Get user profile
PUT    /users/{user_id}          — Update user
DELETE /users/{user_id}          — Deactivate user (admin)
GET    /users/me                 — Current user profile
PUT    /users/me/preferences     — Update preferences
```

### 8.2 Invite User

```
POST /users
Authorization: Bearer <token>   (requires: admin)
```

**Request:**

```json
{
  "email": "newuser@acme.com",
  "full_name": "New User",
  "role": "member",
  "departments": [
    {"department_id": "dept_001", "role": "member"},
    {"department_id": "dept_002", "role": "viewer"}
  ]
}
```

---

## 9. Models (AI/ML)

### 9.1 List Model Adapters

```
GET /models?department_id=dept_001
Authorization: Bearer <token>   (requires: admin)
```

**Response (200):**

```json
{
  "data": [
    {
      "id": "mdl_001",
      "name": "it-ops-adapter-v3",
      "base_model": "meta-llama/Llama-3-8b-Instruct",
      "version": "3.0.0",
      "status": "production",
      "metrics": {
        "bleu": 0.72,
        "rouge_l": 0.81,
        "f1": 0.85,
        "training_samples": 5000
      },
      "deployed_at": "2026-02-10T08:00:00Z"
    }
  ]
}
```

### 9.2 Trigger Training

```
POST /models/train
Authorization: Bearer <token>   (requires: admin, Enterprise tier)
```

**Request:**

```json
{
  "department_id": "dept_001",
  "base_model": "meta-llama/Llama-3-8b-Instruct",
  "config": {
    "lora_r": 16,
    "lora_alpha": 32,
    "epochs": 3,
    "learning_rate": 0.0002,
    "batch_size": 8
  }
}
```

**Response (202 Accepted):**

```json
{
  "job_id": "job_001",
  "status": "queued",
  "estimated_time_minutes": 45,
  "message": "Training job queued. Monitor with GET /models/training/{job_id}"
}
```

### 9.3 Training Job Status

```
GET /models/training/{job_id}
```

---

## 10. Analytics

### 10.1 Usage Overview

```
GET /analytics/usage?from=2026-02-01&to=2026-02-12
Authorization: Bearer <token>   (requires: admin)
```

**Response (200):**

```json
{
  "period": {"from": "2026-02-01", "to": "2026-02-12"},
  "summary": {
    "total_queries": 2450,
    "unique_users": 89,
    "auto_resolved": 1960,
    "escalated": 490,
    "avg_confidence": 0.87,
    "avg_latency_ms": 1800,
    "tokens_used": 1250000
  },
  "by_department": [
    {"department": "IT Operations", "queries": 1800, "confidence": 0.89},
    {"department": "HR", "queries": 450, "confidence": 0.84},
    {"department": "Legal", "queries": 200, "confidence": 0.82}
  ],
  "daily": [
    {"date": "2026-02-01", "queries": 180, "auto_resolved": 145},
    {"date": "2026-02-02", "queries": 210, "auto_resolved": 172}
  ]
}
```

### 10.2 AI Performance

```
GET /analytics/ai-performance?department_id=dept_001
```

### 10.3 Export (CSV)

```
GET /analytics/export?format=csv&from=2026-02-01&to=2026-02-12
```

---

## 11. Billing & Subscription

### 11.1 Current Subscription

```
GET /billing/subscription
```

**Response (200):**

```json
{
  "plan": "enterprise",
  "price_per_user": 79.00,
  "billing_cycle": "annual",
  "current_users": 85,
  "max_users": null,
  "status": "active",
  "current_period": {
    "start": "2026-01-01",
    "end": "2026-12-31"
  },
  "usage_this_period": {
    "queries": 45000,
    "limit": null,
    "departments": 4,
    "max_departments": null
  }
}
```

### 11.2 Usage Summary

```
GET /billing/usage?period=current
```

### 11.3 Invoice History

```
GET /billing/invoices?page=1
```

### 11.4 Upgrade Plan

```
POST /billing/upgrade
```

**Request:**

```json
{
  "plan_tier": "enterprise",
  "billing_cycle": "annual"
}
```

---

## 12. API Keys

### 12.1 CRUD Endpoints

```
GET    /api-keys                 — List API keys
POST   /api-keys                 — Create new key
DELETE /api-keys/{key_id}        — Revoke key
```

### 12.2 Create API Key

```
POST /api-keys
Authorization: Bearer <token>   (requires: admin)
```

**Request:**

```json
{
  "name": "CI/CD Pipeline",
  "permissions": ["query", "knowledge.read"],
  "rate_limit": 200,
  "expires_in_days": 365
}
```

**Response (201):**

```json
{
  "id": "key_001",
  "name": "CI/CD Pipeline",
  "key": "exp_sk_live_abc123xyz789...",
  "key_prefix": "exp_sk_li",
  "permissions": ["query", "knowledge.read"],
  "rate_limit": 200,
  "expires_at": "2027-02-12T00:00:00Z",
  "message": "⚠️ Save this key now. It will not be shown again."
}
```

---

## 13. WebSocket (Real-time Chat)

### Connection

```
WS wss://api.the-expert.ai/ws/chat/{department_id}
Headers:
  Authorization: Bearer <token>
```

### Client → Server Messages

```json
// Send query
{
  "type": "query",
  "data": {
    "text": "How to fix nginx 502?",
    "conversation_id": "conv_001",
    "image_base64": null
  }
}

// Ping (keepalive)
{"type": "ping"}
```

### Server → Client Messages

```json
// Streaming tokens
{"type": "token", "data": {"content": "The 502 error "}}
{"type": "token", "data": {"content": "typically means..."}}

// Sources
{"type": "sources", "data": {"sources": [...]}}

// Complete
{"type": "done", "data": {"query_id": "msg_001", "confidence": 0.91, "latency_ms": 2100}}

// Errors
{"type": "error", "data": {"code": "QUOTA_EXCEEDED", "message": "Daily limit reached"}}

// Notifications (new approval, etc.)
{"type": "notification", "data": {"type": "new_approval", "count": 3}}

// Pong
{"type": "pong"}
```

---

## 14. Webhooks

### 14.1 Configure Webhook

```
POST /webhooks
Authorization: Bearer <token>   (requires: admin)
```

**Request:**

```json
{
  "url": "https://acme.com/webhooks/the-expert",
  "events": ["query.created", "approval.completed", "knowledge.indexed"],
  "secret": "whsec_abc123..."
}
```

### 14.2 Webhook Payload

```json
{
  "event": "approval.completed",
  "timestamp": "2026-02-12T16:45:00Z",
  "data": {
    "approval_id": "apr_001",
    "status": "approved",
    "department": "IT Operations",
    "query_summary": "ORA-12514 TNS listener error"
  },
  "signature": "sha256=abc123..."
}
```

### 14.3 Available Events

| Event | Trigger |
| :--- | :--- |
| `query.created` | New query submitted |
| `query.completed` | AI response generated |
| `approval.created` | New approval request |
| `approval.completed` | Expert approved/rejected |
| `knowledge.uploaded` | New document uploaded |
| `knowledge.indexed` | Document finished processing |
| `model.training_started` | Training job started |
| `model.deployed` | New model version deployed |
| `user.invited` | New user invited |
| `subscription.changed` | Plan upgraded/downgraded |

---

## 15. Rate Limiting

### Limits by Tier

| Tier | API Rate | Query Rate | Burst |
| :--- | :--- | :--- | :--- |
| Free | 20 req/min | 50 queries/day | 5 req/sec |
| Professional | 100 req/min | 500 queries/day | 20 req/sec |
| Enterprise | 1,000 req/min | Unlimited | 100 req/sec |
| API Key | Custom (per key) | Custom | Custom |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1707753600
X-Quota-Limit: 500
X-Quota-Used: 123
X-Quota-Reset: 2026-02-13T00:00:00Z
```

### Exceeded Response (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded. Try again in 45 seconds.",
    "retry_after": 45
  }
}
```

```json
{
  "error": {
    "code": "DAILY_QUOTA_EXCEEDED",
    "message": "You've used 500/500 queries today.",
    "upgrade_url": "/settings/billing?plan=enterprise",
    "reset_at": "2026-02-13T00:00:00Z"
  }
}
```

---

## Related Documents

- [Implementation Plan](./implementation_plan.md) — Architecture & tech design
- [Database Design](./database_design.md) — Full schema & ER diagram
- [Tasks](./tasks.md) — Sprint-level breakdown
- [Subscription Plan](./subscription_plan.md) — Pricing tiers & billing
