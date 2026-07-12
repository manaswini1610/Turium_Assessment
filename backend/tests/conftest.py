import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# In-memory SQLite with a StaticPool keeps a single shared connection alive for
# the engine's lifetime, avoiding Windows file-lock issues an on-disk test DB
# would hit during teardown, while still giving each test a clean schema.
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session, monkeypatch):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Avoid real network/OpenAI calls in tests: embeddings are deterministic stubs.
    monkeypatch.setattr(
        "app.services.embedding_service.generate_embeddings",
        lambda texts: [[0.1, 0.2, 0.3] for _ in texts],
    )
    monkeypatch.setattr(
        "app.services.embedding_service.generate_single_embedding",
        lambda text: [0.1, 0.2, 0.3],
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
