from datetime import datetime
from enum import Enum
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    note = "note"
    url = "url"


class NoteIngestRequest(BaseModel):
    source_type: Literal[SourceType.note]
    title: str = Field(..., min_length=1, max_length=300, description="Title of the note")
    content: str = Field(..., min_length=1, description="Plain text content of the note")


class URLIngestRequest(BaseModel):
    source_type: Literal[SourceType.url]
    url: str = Field(..., min_length=1, description="Webpage URL to ingest")


IngestRequestBody = Annotated[
    Union[NoteIngestRequest, URLIngestRequest],
    Field(discriminator="source_type"),
]


class IngestResponse(BaseModel):
    id: int
    title: str
    source_type: SourceType
    source_url: Optional[str] = None
    chunk_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemSummary(BaseModel):
    id: int
    title: str
    source_type: SourceType
    source_url: Optional[str] = None
    content_preview: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question to ask about your saved knowledge")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of chunks to retrieve")


class SourceItem(BaseModel):
    item_id: int
    title: str
    source_type: SourceType
    source_url: Optional[str] = None
    snippet: str
    similarity_score: float


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
