"""
Embedding service using sentence-transformers with BGE-large-en-v1.5.

Provides text-to-vector conversion for the RAG pipeline.
Lazy-loads the model on first call and falls back to random vectors
when the model is unavailable (e.g. in dev without GPU).
"""

import random
from typing import ClassVar

from loguru import logger

EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
EMBEDDING_DIM = 1024
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingService:
    """Singleton-style embedding service with lazy model loading."""

    _instance: ClassVar["EmbeddingService | None"] = None
    _model: ClassVar[object | None] = None
    _fallback: ClassVar[bool] = False

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Lazy loader
    # ------------------------------------------------------------------
    def _load_model(self) -> None:
        """Load the SentenceTransformer model (once)."""
        if self.__class__._model is not None or self.__class__._fallback:
            return

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

            logger.info("Loading embedding model: {}", EMBEDDING_MODEL)
            self.__class__._model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(
                "Embedding model loaded (dim={})",
                self.__class__._model.get_sentence_embedding_dimension(),
            )
        except Exception as exc:
            logger.warning(
                "Could not load embedding model ({}). Falling back to random vectors for dev.",
                exc,
            )
            self.__class__._fallback = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string and return a vector of floats."""
        self._load_model()

        if self.__class__._fallback:
            return self._random_vector()

        prefixed = f"{QUERY_PREFIX}{text}"
        vector = self.__class__._model.encode(prefixed, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts and return a list of vectors."""
        self._load_model()

        if self.__class__._fallback:
            return [self._random_vector() for _ in texts]

        prefixed = [f"{QUERY_PREFIX}{t}" for t in texts]
        vectors = self.__class__._model.encode(
            prefixed,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed document chunks (no query prefix) for indexing."""
        self._load_model()

        if self.__class__._fallback:
            return [self._random_vector() for _ in texts]

        vectors = self.__class__._model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _random_vector() -> list[float]:
        """Return a normalised random vector of EMBEDDING_DIM dimensions."""
        vec = [random.gauss(0, 1) for _ in range(EMBEDDING_DIM)]
        norm = sum(x * x for x in vec) ** 0.5
        return [x / norm for x in vec]

    @property
    def is_fallback(self) -> bool:
        return self.__class__._fallback
