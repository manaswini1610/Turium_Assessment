from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Item(Base):
    """A saved piece of knowledge: either a plain-text note or an ingested webpage."""

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    raw_content = Column(Text, nullable=False)
    source_type = Column(String(20), nullable=False)
    source_url = Column(String(2048), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chunks = relationship("Chunk", back_populates="item", cascade="all, delete-orphan")


class Chunk(Base):
    """A token-bounded slice of an item's content, stored with its embedding."""

    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)  # JSON-serialized list[float]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    item = relationship("Item", back_populates="chunks")
