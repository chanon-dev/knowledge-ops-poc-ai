from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    api_keys,
    approvals,
    auth,
    billing,
    branding,
    conversations,
    data_export,
    departments,
    edge,
    health,
    knowledge,
    models,
    plugins,
    query,
    stripe_webhooks,
    tenants,
    users,
    webhooks,
    ws,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(branding.router, prefix="/branding", tags=["branding"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(edge.router, prefix="/edge", tags=["edge"])
api_router.include_router(data_export.router, prefix="/data", tags=["data-export"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["plugins"])
api_router.include_router(stripe_webhooks.router, tags=["stripe"])
api_router.include_router(ws.router, tags=["websocket"])
