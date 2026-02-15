"""Abstract base classes for trainers and deployers.

New training methods or deployment targets should subclass these
and register themselves via the registry module.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseTrainer(ABC):
    """Interface that all training method implementations must follow."""

    @abstractmethod
    def setup(self, base_model: str, **kwargs) -> None:
        """Load the base model and prepare for training."""

    @abstractmethod
    def train(
        self,
        train_data: list[dict],
        val_data: list[dict],
        output_dir: str = "./output",
        epochs: int = 3,
        lr: float = 2e-4,
        batch_size: int = 4,
        **kwargs,
    ) -> dict:
        """Run training and return metrics dict."""

    @abstractmethod
    def evaluate(self, test_data: list[dict]) -> dict:
        """Evaluate model on test data and return metrics dict."""

    @abstractmethod
    def save_adapter(self, output_dir: str) -> None:
        """Save the trained model/adapter to disk."""

    @property
    @abstractmethod
    def device_info(self) -> dict:
        """Return device information for logging."""


class BaseDeployer(ABC):
    """Interface that all deployment target implementations must follow."""

    @abstractmethod
    def deploy(self, model_path: str, model_name: str, **kwargs) -> dict:
        """Deploy a trained model and return status dict."""
