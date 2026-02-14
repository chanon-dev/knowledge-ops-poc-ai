"""
Text chunking service using recursive character splitting.

Splits documents into overlapping chunks suitable for embedding and
retrieval.  Uses a token-aware approach (approximate) with configurable
chunk size and overlap.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field

from loguru import logger


# Rough token estimator: 1 token ~ 4 characters for English text.
_CHARS_PER_TOKEN = 4

# Hierarchy of separators used by the recursive splitter (most preferred first).
_SEPARATORS: list[str] = [
    "\n\n",   # paragraph break
    "\n",     # line break
    ". ",     # sentence end
    "? ",     # question end
    "! ",     # exclamation end
    "; ",     # semicolon
    ", ",     # comma
    " ",      # word boundary
    "",       # single-character fallback
]


@dataclass
class TextChunker:
    """Recursive character text splitter with token-aware sizing."""

    chunk_size: int = 512        # target chunk size in *tokens*
    chunk_overlap: int = 50      # overlap in *tokens*
    separators: list[str] = field(default_factory=lambda: list(_SEPARATORS))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def _chunk_chars(self) -> int:
        return self.chunk_size * _CHARS_PER_TOKEN

    @property
    def _overlap_chars(self) -> int:
        return self.chunk_overlap * _CHARS_PER_TOKEN

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def chunk_text(self, text: str) -> list[str]:
        """Split *text* into a list of chunk strings."""
        if not text or not text.strip():
            return []

        # Normalise whitespace inside the text (preserve paragraph breaks).
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        chunks = self._split_recursive(text.strip(), self.separators)

        # Post-process: strip, de-dup empty, enforce minimum length.
        result: list[str] = []
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) < 20:
                # Too small on its own -- merge with previous if possible.
                if result:
                    result[-1] = result[-1] + " " + chunk
                continue
            result.append(chunk)

        logger.debug("Chunked {} chars -> {} chunks", len(text), len(result))
        return result

    def chunk_document(self, text: str, metadata: dict | None = None) -> list[dict]:
        """
        Chunk a full document and return enriched dicts.

        Each returned dict has the keys:
            - content: the chunk text
            - chunk_index: 0-based index
            - token_count: estimated token count
            - metadata: copy of caller-supplied metadata with chunk info merged
        """
        metadata = metadata or {}
        chunks = self.chunk_text(text)
        result: list[dict] = []

        for idx, content in enumerate(chunks):
            token_count = max(1, len(content) // _CHARS_PER_TOKEN)
            chunk_meta = {
                **metadata,
                "chunk_index": idx,
                "token_count": token_count,
                "total_chunks": len(chunks),
            }
            result.append(
                {
                    "content": content,
                    "chunk_index": idx,
                    "token_count": token_count,
                    "metadata": chunk_meta,
                }
            )

        return result

    # ------------------------------------------------------------------
    # Recursive splitter
    # ------------------------------------------------------------------
    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        """Core recursive splitting logic."""
        final_chunks: list[str] = []

        # Pick the best separator that actually occurs in the text.
        separator = separators[-1]
        remaining_seps = []
        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                remaining_seps = []
                break
            if sep in text:
                separator = sep
                remaining_seps = separators[i + 1 :]
                break

        # Split text on the chosen separator.
        splits = text.split(separator) if separator else list(text)

        # Merge small adjacent splits until they reach chunk_chars.
        good_splits: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for piece in splits:
            piece_len = len(piece) + len(separator)
            if current_len + piece_len > self._chunk_chars and current_chunk:
                merged = separator.join(current_chunk)
                if len(merged) > self._chunk_chars and remaining_seps:
                    # Recursively split the over-sized merged chunk.
                    final_chunks.extend(self._split_recursive(merged, remaining_seps))
                else:
                    good_splits.append(merged)

                # Overlap: keep trailing pieces whose total length < overlap.
                overlap_pieces: list[str] = []
                overlap_len = 0
                for p in reversed(current_chunk):
                    if overlap_len + len(p) + len(separator) > self._overlap_chars:
                        break
                    overlap_pieces.insert(0, p)
                    overlap_len += len(p) + len(separator)
                current_chunk = overlap_pieces
                current_len = overlap_len

            current_chunk.append(piece)
            current_len += piece_len

        # Flush remaining.
        if current_chunk:
            merged = separator.join(current_chunk)
            if len(merged) > self._chunk_chars and remaining_seps:
                final_chunks.extend(self._split_recursive(merged, remaining_seps))
            else:
                good_splits.append(merged)

        final_chunks.extend(good_splits)
        return final_chunks
