import logging
from typing import List

import tiktoken

logger = logging.getLogger("app.chunking_service")

# ~500 tokens per chunk with ~100 tokens of overlap. See README.md for rationale.
CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 100
ENCODING_NAME = "cl100k_base"

_encoding = None


def _get_encoding():
    global _encoding
    if _encoding is None:
        _encoding = tiktoken.get_encoding(ENCODING_NAME)
    return _encoding


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_TOKENS,
    overlap: int = CHUNK_OVERLAP_TOKENS,
) -> List[str]:
    """Splits text into overlapping, roughly token-bounded chunks.

    Uses a sliding window over the token stream so that context near chunk
    boundaries is preserved in the neighboring chunk (the overlap).
    """
    if not text or not text.strip():
        return []

    encoding = _get_encoding()
    tokens = encoding.encode(text)

    if len(tokens) <= chunk_size:
        stripped = text.strip()
        return [stripped] if stripped else []

    chunks: List[str] = []
    step = chunk_size - overlap
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_str = encoding.decode(tokens[start:end]).strip()
        if chunk_str:
            chunks.append(chunk_str)
        if end == len(tokens):
            break
        start += step

    logger.info(f"Chunked text into {len(chunks)} chunk(s) from {len(tokens)} tokens")
    return chunks
