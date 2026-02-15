"""Backwards-compatible deployer interface.

Delegates to registered deployer implementations via the registry.
For new code, use the registry directly:
    from ml.training.registry import get_deployer
    deployer = get_deployer("ollama")()
"""

import logging
from typing import Optional

from ml.training.registry import get_deployer

logger = logging.getLogger(__name__)


class ModelDeployer:
    """Convenience wrapper that dispatches to the registry."""

    def deploy_to_ollama(
        self,
        model_path: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> dict:
        deployer = get_deployer("ollama")()
        return deployer.deploy(
            model_path=model_path,
            model_name=model_name,
            system_prompt=system_prompt,
            **kwargs,
        )

    def deploy(
        self,
        target_key: str,
        model_path: str,
        model_name: str,
        **kwargs,
    ) -> dict:
        """Deploy using any registered target by key."""
        deployer = get_deployer(target_key)()
        return deployer.deploy(
            model_path=model_path,
            model_name=model_name,
            **kwargs,
        )
