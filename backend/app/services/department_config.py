"""Department configuration loader - YAML-based department configs."""

import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "rag": {
        "top_k": 5,
        "min_score": 0.5,
        "rerank": True,
        "chunk_size": 512,
        "chunk_overlap": 50,
    },
    "llm": {
        "model": "mistral:7b",
        "temperature": 0.7,
        "max_tokens": 1024,
        "system_prompt": None,
    },
    "hitl": {
        "confidence_threshold": 0.7,
        "auto_approve": False,
        "require_approval_for_new_topics": True,
    },
    "vision": {
        "enabled": False,
        "model": "llava",
        "max_image_size": 2048,
    },
    "sub_agents": {
        "enabled": False,
        "analyzer": False,
        "researcher": False,
        "code_reviewer": False,
    },
}


class DepartmentConfigLoader:
    """Load and manage department-specific configurations."""

    def __init__(self, db: AsyncSession, config_dir: str | None = None):
        self.db = db
        self.config_dir = Path(config_dir) if config_dir else None

    async def get_config(self, department_id: UUID) -> dict:
        """Get merged config: defaults + DB settings + YAML overrides."""
        config = dict(DEFAULT_CONFIG)

        # Load from DB
        result = await self.db.execute(select(Department).where(Department.id == department_id))
        dept = result.scalar_one_or_none()
        if dept and dept.settings:
            config = self._deep_merge(config, dept.settings)

        # Load from YAML file if exists
        if self.config_dir:
            yaml_config = self._load_yaml(str(department_id))
            if yaml_config:
                config = self._deep_merge(config, yaml_config)

        return config

    async def update_config(self, department_id: UUID, updates: dict) -> dict:
        """Update department config in DB."""
        result = await self.db.execute(select(Department).where(Department.id == department_id))
        dept = result.scalar_one_or_none()
        if not dept:
            raise ValueError("Department not found")

        current = dict(dept.settings or {})
        merged = self._deep_merge(current, updates)
        dept.settings = merged
        await self.db.commit()
        await self.db.refresh(dept)

        return await self.get_config(department_id)

    def _load_yaml(self, dept_id: str) -> Optional[dict]:
        """Load YAML config file for a department."""
        if not self.config_dir:
            return None
        yaml_path = self.config_dir / f"{dept_id}.yaml"
        if not yaml_path.exists():
            yaml_path = self.config_dir / f"{dept_id}.yml"
        if not yaml_path.exists():
            return None
        try:
            with open(yaml_path) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load YAML config for dept {dept_id}: {e}")
            return None

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Deep merge two dicts, override takes precedence."""
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DepartmentConfigLoader._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
