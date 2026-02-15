"""Registry for trainer and deployer implementations.

Usage:
    from ml.training.registry import get_trainer, get_deployer, list_trainers, list_deployers

    # Get a trainer class by key
    TrainerClass = get_trainer("lora")
    trainer = TrainerClass()

    # Get a deployer class by key
    DeployerClass = get_deployer("ollama")
    deployer = DeployerClass()
"""

import logging
from typing import Optional

from ml.training.base import BaseTrainer, BaseDeployer

logger = logging.getLogger(__name__)

_trainers: dict[str, type[BaseTrainer]] = {}
_deployers: dict[str, type[BaseDeployer]] = {}


# ---------------------------------------------------------------------------
# Trainer registry
# ---------------------------------------------------------------------------

def register_trainer(key: str, cls: type[BaseTrainer]) -> None:
    """Register a trainer implementation under the given key."""
    _trainers[key] = cls
    logger.debug(f"Registered trainer: {key} -> {cls.__name__}")


def get_trainer(key: str) -> type[BaseTrainer]:
    """Look up a trainer class by registry key. Raises KeyError if not found."""
    if key not in _trainers:
        available = ", ".join(_trainers.keys()) or "(none)"
        raise KeyError(f"Unknown trainer '{key}'. Available: {available}")
    return _trainers[key]


def list_trainers() -> dict[str, str]:
    """Return {key: class_name} for all registered trainers."""
    return {k: v.__name__ for k, v in _trainers.items()}


# ---------------------------------------------------------------------------
# Deployer registry
# ---------------------------------------------------------------------------

def register_deployer(key: str, cls: type[BaseDeployer]) -> None:
    """Register a deployer implementation under the given key."""
    _deployers[key] = cls
    logger.debug(f"Registered deployer: {key} -> {cls.__name__}")


def get_deployer(key: str) -> type[BaseDeployer]:
    """Look up a deployer class by registry key. Raises KeyError if not found."""
    if key not in _deployers:
        available = ", ".join(_deployers.keys()) or "(none)"
        raise KeyError(f"Unknown deployer '{key}'. Available: {available}")
    return _deployers[key]


def list_deployers() -> dict[str, str]:
    """Return {key: class_name} for all registered deployers."""
    return {k: v.__name__ for k, v in _deployers.items()}


# ---------------------------------------------------------------------------
# Auto-discover built-in implementations on import
# ---------------------------------------------------------------------------

def _auto_register() -> None:
    """Import built-in modules so they self-register."""
    try:
        import ml.training.lora_trainer  # noqa: F401
    except ImportError:
        logger.debug("lora_trainer not available")

    try:
        import ml.training.deployers  # noqa: F401
    except ImportError:
        logger.debug("deployers not available")


_auto_register()
