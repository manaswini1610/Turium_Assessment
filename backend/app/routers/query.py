import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item
from app.schemas import QueryRequest, QueryResponse, SourceItem
from app.services import llm_service, retrieval_service
from app.services.embedding_service import EmbeddingServiceError
from app.services.llm_service import NO_ANSWER_MESSAGE, LLMServiceError

logger = logging.getLogger("app.routers.query")

router = APIRouter(prefix="/query", tags=["query"])

SNIPPET_LENGTH = 250


@router.post("", response_model=QueryResponse, status_code=status.HTTP_200_OK)
def query_knowledge(payload: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    if not payload.question.strip():
        logger.error("Rejected query with empty/whitespace-only question")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question must not be empty.")

    has_items = db.query(Item.id).first() is not None
    if not has_items:
        logger.info("Query attempted with no saved content in the knowledge base")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No saved content exists yet. Add a note or URL before asking questions.",
        )

    try:
        retrieved_chunks = retrieval_service.retrieve_relevant_chunks(db, payload.question, payload.top_k)
    except EmbeddingServiceError as exc:
        logger.error(f"Embedding failure during query execution: {exc}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    logger.info(f"Query executed: retrieved {len(retrieved_chunks)} relevant chunk(s)")

    if not retrieved_chunks:
        return QueryResponse(answer=NO_ANSWER_MESSAGE, sources=[])

    try:
        answer = llm_service.generate_answer(payload.question, retrieved_chunks)
    except LLMServiceError as exc:
        logger.error(f"LLM failure during query execution: {exc}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    if answer == NO_ANSWER_MESSAGE:
        logger.info("Query answered with no citable sources")
        return QueryResponse(answer=answer, sources=[])

    sources = [
        SourceItem(
            item_id=chunk.item_id,
            title=chunk.title,
            source_type=chunk.source_type,
            source_url=chunk.source_url,
            snippet=chunk.chunk_text[:SNIPPET_LENGTH] + ("..." if len(chunk.chunk_text) > SNIPPET_LENGTH else ""),
            similarity_score=round(chunk.similarity, 4),
        )
        for chunk in retrieved_chunks
    ]

    logger.info(f"Query answered with {len(sources)} cited source(s)")
    return QueryResponse(answer=answer, sources=sources)
