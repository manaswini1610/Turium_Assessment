import logging
from typing import List

from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError

from app.config import get_settings
from app.services.retrieval_service import RetrievedChunk

logger = logging.getLogger("app.llm_service")

NO_ANSWER_MESSAGE = "I could not find this information in the saved knowledge."

SYSTEM_PROMPT = f"""You are an AI assistant that answers questions only from the supplied context.

Rules:
1. Use only the information available in the context.
2. Do not use outside knowledge.
3. Do not invent or assume information.
4. When the context does not contain the answer, respond exactly:
   "{NO_ANSWER_MESSAGE}"
5. Keep the answer clear and concise.
6. Source references will be attached separately by the backend.
"""


class LLMServiceError(Exception):
    """Raised when the chat model cannot produce an answer (missing key, API failure, etc.)."""


_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    settings = get_settings()
    if not settings.openai_api_key:
        logger.error("OpenAI API key is not configured")
        raise LLMServiceError(
            "OpenAI API key is not configured. Set OPENAI_API_KEY in the environment."
        )
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def build_context(chunks: List[RetrievedChunk]) -> str:
    parts = [f"[Source {i}: {chunk.title}]\n{chunk.chunk_text}" for i, chunk in enumerate(chunks, start=1)]
    return "\n\n".join(parts)


def generate_answer(question: str, chunks: List[RetrievedChunk]) -> str:
    """Answers the question strictly from the given chunks, using the OpenAI chat model."""
    if not chunks:
        return NO_ANSWER_MESSAGE

    settings = get_settings()
    client = get_client()
    context = build_context(chunks)
    user_prompt = f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"

    try:
        response = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
    except AuthenticationError as exc:
        logger.error("OpenAI authentication failed while generating an answer")
        raise LLMServiceError("OpenAI authentication failed. Check your API key.") from exc
    except RateLimitError as exc:
        logger.error("OpenAI rate limit exceeded while generating an answer")
        raise LLMServiceError("OpenAI rate limit exceeded while generating an answer.") from exc
    except (APIConnectionError, APIError) as exc:
        logger.error(f"OpenAI chat request failed: {exc}")
        raise LLMServiceError("Failed to generate an answer from OpenAI.") from exc

    answer = (response.choices[0].message.content or "").strip()
    logger.info("LLM answer generated successfully")
    return answer or NO_ANSWER_MESSAGE
