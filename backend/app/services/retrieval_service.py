import logging
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Chunk, Item
from app.services import embedding_service

logger = logging.getLogger("app.retrieval_service")


@dataclass
class RetrievedChunk:
    chunk_id: int
    item_id: int
    title: str
    source_type: str
    source_url: Optional[str]
    chunk_text: str
    similarity: float


def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    a = np.array(vector_a, dtype=float)
    b = np.array(vector_b, dtype=float)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def _to_retrieved_chunk(chunk: Chunk, similarity: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk.id,
        item_id=chunk.item.id,
        title=chunk.item.title,
        source_type=chunk.item.source_type,
        source_url=chunk.item.source_url,
        chunk_text=chunk.chunk_text,
        similarity=similarity,
    )


def retrieve_relevant_chunks(db: Session, question: str, top_k: int = 3) -> List[RetrievedChunk]:
    """Embeds the question, ranks all chunks by cosine similarity, keeps the
    top-k most similar, and then drops any of those that fall below the
    configured similarity threshold. The threshold is applied after the
    top-k cut so that irrelevant chunks never reach the caller or the LLM."""
    settings = get_settings()
    question_embedding = embedding_service.generate_single_embedding(question)

    all_chunks = db.query(Chunk).join(Item, Chunk.item_id == Item.id).all()
    if not all_chunks:
        logger.info("No chunks exist yet for retrieval")
        return []

    scored = [
        (chunk, cosine_similarity(question_embedding, embedding_service.deserialize_embedding(chunk.embedding)))
        for chunk in all_chunks
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    top_candidates = scored[:top_k]
    relevant = [
        _to_retrieved_chunk(chunk, similarity)
        for chunk, similarity in top_candidates
        if similarity >= settings.similarity_threshold
    ]

    logger.info(
        f"Retrieved {len(relevant)} of {len(top_candidates)} top-{top_k} candidate(s) "
        f"above similarity threshold {settings.similarity_threshold} "
        f"({len(all_chunks)} total chunk(s) in knowledge base)"
    )
    return relevant
