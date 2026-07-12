import json
import logging
from typing import List

from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError

from app.config import get_settings

logger = logging.getLogger("app.embedding_service")


class EmbeddingServiceError(Exception):
    """Raised when embeddings cannot be generated (missing key, API failure, etc.)."""


_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    settings = get_settings()
    if not settings.openai_api_key:
        logger.error("OpenAI API key is not configured")
        raise EmbeddingServiceError(
            "OpenAI API key is not configured. Set OPENAI_API_KEY in the environment."
        )
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generates embeddings for one or more text chunks in a single API call."""
    if not texts:
        return []

    settings = get_settings()
    client = get_client()

    try:
        response = client.embeddings.create(model=settings.openai_embedding_model, input=texts)
    except AuthenticationError as exc:
        logger.error("OpenAI authentication failed while generating embeddings")
        raise EmbeddingServiceError("OpenAI authentication failed. Check your API key.") from exc
    except RateLimitError as exc:
        logger.error("OpenAI rate limit exceeded while generating embeddings")
        raise EmbeddingServiceError("OpenAI rate limit exceeded while generating embeddings.") from exc
    except (APIConnectionError, APIError) as exc:
        logger.error(f"OpenAI embedding request failed: {exc}")
        raise EmbeddingServiceError("Failed to generate embeddings from OpenAI.") from exc

    embeddings = [item.embedding for item in response.data]
    logger.info(f"Generated {len(embeddings)} embedding(s)")
    return embeddings


def generate_single_embedding(text: str) -> List[float]:
    return generate_embeddings([text])[0]


def serialize_embedding(embedding: List[float]) -> str:
    return json.dumps(embedding)


def deserialize_embedding(data: str) -> List[float]:
    return json.loads(data)
