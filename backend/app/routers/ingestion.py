import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Chunk, Item
from app.schemas import IngestRequestBody, IngestResponse, NoteIngestRequest
from app.services import chunking_service, embedding_service, url_service
from app.services.embedding_service import EmbeddingServiceError
from app.services.url_service import URLFetchError

logger = logging.getLogger("app.routers.ingestion")

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_content(payload: IngestRequestBody, db: Session = Depends(get_db)) -> IngestResponse:
    if isinstance(payload, NoteIngestRequest):
        title = payload.title.strip()
        raw_content = payload.content.strip()
        source_type = "note"
        source_url = None

        if not title or not raw_content:
            logger.error("Rejected note ingestion with empty title or content")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Note title and content must not be empty.",
            )
        logger.info(f"Ingesting note titled '{title}'")
    else:
        try:
            title, raw_content = url_service.fetch_and_extract(payload.url)
        except URLFetchError as exc:
            logger.error(f"URL ingestion failed for {payload.url}: {exc}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        source_type = "url"
        source_url = payload.url
        logger.info(f"Ingesting URL '{payload.url}' (extracted title: '{title}')")

    item = Item(title=title, raw_content=raw_content, source_type=source_type, source_url=source_url)
    db.add(item)
    db.commit()
    db.refresh(item)

    chunks = chunking_service.chunk_text(raw_content)
    if not chunks:
        db.delete(item)
        db.commit()
        logger.error(f"No chunks could be produced for item_id={item.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is too short or empty to process.",
        )

    try:
        embeddings = embedding_service.generate_embeddings(chunks)
    except EmbeddingServiceError as exc:
        db.delete(item)
        db.commit()
        logger.error(f"Embedding generation failed for item_id={item.id}: {exc}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    for index, (chunk_content, embedding) in enumerate(zip(chunks, embeddings)):
        db.add(
            Chunk(
                item_id=item.id,
                chunk_index=index,
                chunk_text=chunk_content,
                embedding=embedding_service.serialize_embedding(embedding),
            )
        )
    db.commit()

    logger.info(f"Item {item.id} ingested successfully with {len(chunks)} chunk(s)")

    return IngestResponse(
        id=item.id,
        title=item.title,
        source_type=item.source_type,
        source_url=item.source_url,
        chunk_count=len(chunks),
        created_at=item.created_at,
    )
