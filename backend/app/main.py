from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import ingestion, items, query
from app.utils.logger import configure_logging

configure_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Knowledge Inbox",
    description="Save notes and webpages, then ask questions answered only from your saved content.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router)
app.include_router(items.router)
app.include_router(query.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
