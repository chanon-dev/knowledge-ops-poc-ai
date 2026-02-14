"""Plugin marketplace API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.user import User
from app.services.plugin_service import PluginManager

router = APIRouter()
plugin_manager = PluginManager()


class PluginExecuteRequest(BaseModel):
    plugin_name: str
    input_data: dict = {}


@router.get("")
async def list_plugins(user: User = Depends(require_role("member"))):
    """List all available plugins."""
    return {"data": plugin_manager.list_plugins()}


@router.get("/{plugin_name}")
async def get_plugin_info(plugin_name: str, user: User = Depends(require_role("member"))):
    """Get plugin details."""
    plugin = plugin_manager.get_plugin(plugin_name)
    if not plugin:
        return {"error": "Plugin not found"}
    return {"name": plugin.name, "version": plugin.version, "description": plugin.description}


@router.post("/execute")
async def execute_plugin(
    body: PluginExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
):
    """Execute a plugin with given input data."""
    result = await plugin_manager.execute_plugin(body.plugin_name, body.input_data)
    return {"plugin": body.plugin_name, "result": result}
