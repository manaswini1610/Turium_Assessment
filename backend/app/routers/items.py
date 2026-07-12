import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item
from app.schemas import ItemSummary

logger = logging.getLogger("app.routers.items")

router = APIRouter(prefix="/items", tags=["items"])

PREVIEW_LENGTH = 200


@router.get("", response_model=List[ItemSummary])
def list_items(db: Session = Depends(get_db)) -> List[ItemSummary]:
    items = db.query(Item).order_by(Item.created_at.desc()).all()
    logger.info(f"Listing {len(items)} saved item(s)")

    summaries = []
    for item in items:
        preview = item.raw_content[:PREVIEW_LENGTH]
        if len(item.raw_content) > PREVIEW_LENGTH:
            preview += "..."
        summaries.append(
            ItemSummary(
                id=item.id,
                title=item.title,
                source_type=item.source_type,
                source_url=item.source_url,
                content_preview=preview,
                created_at=item.created_at,
            )
        )
    return summaries
