"""Edge Agent management API for BYOD/hybrid deployments."""

from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.user import User

router = APIRouter()

# In-memory edge agent registry (in production, store in DB)
_edge_agents: dict[str, dict] = {}


class EdgeAgentRegister(BaseModel):
    agent_name: str
    hostname: str
    ip_address: str
    version: str
    capabilities: list[str] = []  # ["query", "embed", "rag", "ollama"]


class EdgeSyncRequest(BaseModel):
    agent_id: str
    sync_type: str = "model"  # "model", "config", "knowledge"


@router.post("/register")
async def register_edge_agent(
    body: EdgeAgentRegister,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Register a new edge agent."""
    import uuid
    agent_id = str(uuid.uuid4())

    _edge_agents[agent_id] = {
        "id": agent_id,
        "tenant_id": str(user.tenant_id),
        "agent_name": body.agent_name,
        "hostname": body.hostname,
        "ip_address": body.ip_address,
        "version": body.version,
        "capabilities": body.capabilities,
        "status": "online",
        "last_heartbeat": datetime.utcnow().isoformat(),
        "registered_at": datetime.utcnow().isoformat(),
    }

    # Log registration
    from app.models.audit_log import AuditLog
    log = AuditLog(
        tenant_id=user.tenant_id,
        user_id=user.id,
        action="edge_agent:registered",
        resource_type="edge_agent",
        resource_id=UUID(agent_id),
        details={"agent_name": body.agent_name, "hostname": body.hostname},
    )
    db.add(log)
    await db.commit()

    return {
        "agent_id": agent_id,
        "status": "registered",
        "api_endpoint": f"/api/v1/edge/{agent_id}",
    }


@router.get("/status")
async def list_edge_agents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """List all edge agents and their health status."""
    tenant_id = str(user.tenant_id)
    agents = [a for a in _edge_agents.values() if a["tenant_id"] == tenant_id]
    return {"data": agents, "total": len(agents)}


@router.get("/{agent_id}")
async def get_edge_agent(
    agent_id: str,
    user: User = Depends(require_role("member")),
):
    """Get edge agent details and health."""
    agent = _edge_agents.get(agent_id)
    if not agent or agent["tenant_id"] != str(user.tenant_id):
        return {"error": "Agent not found"}
    return agent


@router.post("/sync")
async def trigger_sync(
    body: EdgeSyncRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Trigger model/config/knowledge sync to an edge agent."""
    agent = _edge_agents.get(body.agent_id)
    if not agent or agent["tenant_id"] != str(user.tenant_id):
        return {"error": "Agent not found"}

    # In production, this would push to the edge agent via message queue or webhook
    from app.models.audit_log import AuditLog
    log = AuditLog(
        tenant_id=user.tenant_id,
        user_id=user.id,
        action=f"edge_agent:sync:{body.sync_type}",
        resource_type="edge_agent",
        resource_id=UUID(body.agent_id),
        details={"sync_type": body.sync_type},
    )
    db.add(log)
    await db.commit()

    return {
        "agent_id": body.agent_id,
        "sync_type": body.sync_type,
        "status": "sync_initiated",
    }


@router.post("/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str):
    """Receive heartbeat from edge agent."""
    agent = _edge_agents.get(agent_id)
    if not agent:
        return {"error": "Agent not found"}
    agent["last_heartbeat"] = datetime.utcnow().isoformat()
    agent["status"] = "online"
    return {"status": "ok"}
