"""Deployment target implementations.

Each deployer implements BaseDeployer and self-registers in the registry.
To add a new target: create a class, implement deploy(), and call register_deployer().
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from ml.training.base import BaseDeployer
from ml.training.registry import register_deployer

logger = logging.getLogger(__name__)


class OllamaDeployer(BaseDeployer):
    """Deploy a fine-tuned model to a local Ollama instance."""

    def deploy(
        self,
        model_path: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        num_ctx: int = 4096,
        **kwargs,
    ) -> dict:
        lines = [
            f"FROM {model_path}",
            f"PARAMETER temperature {temperature}",
            f"PARAMETER top_p {top_p}",
            f"PARAMETER num_ctx {num_ctx}",
        ]
        if system_prompt:
            lines.append(f"\nSYSTEM {system_prompt}")

        modelfile_content = "\n".join(lines) + "\n"
        modelfile_path = Path(model_path) / "Modelfile"
        modelfile_path.write_text(modelfile_content)

        try:
            subprocess.run(
                ["ollama", "create", model_name, "-f", str(modelfile_path)],
                check=True, capture_output=True, text=True,
            )
            logger.info(f"Model {model_name} deployed to Ollama")
            return {"status": "success", "model_name": model_name, "target": "ollama"}
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to deploy to Ollama: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error("Ollama CLI not found. Is Ollama installed?")
            raise


# ---------------------------------------------------------------------------
# Self-register
# ---------------------------------------------------------------------------

register_deployer("ollama", OllamaDeployer)
