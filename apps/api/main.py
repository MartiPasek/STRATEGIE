from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

from core.logging import setup_logging
from modules.ai_processing.api.router import router as ai_processing_router

setup_logging()

app = FastAPI(
    title="STRATEGIE API",
    description="Modular enterprise AI platform",
    version="0.1.0",
)

app.include_router(ai_processing_router)

INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html")


@app.get("/")
def index():
    return FileResponse(INDEX_PATH)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": "0.1.0",
        "index_path": INDEX_PATH,
        "exists": os.path.exists(INDEX_PATH),
    }
