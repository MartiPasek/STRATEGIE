from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
import os

from core.config import settings
from core.logging import setup_logging
from modules.ai_processing.api.router import router as ai_processing_router
from modules.conversation.api.router import router as conversation_router
from modules.conversation.api.dm_router import router as dm_router
from modules.auth.api.router import router as auth_router
from modules.memory.api.router import router as memory_router
from modules.projects.api.router import router as projects_router
from modules.personas.api.router import router as personas_router
from modules.rag.api.router import router as rag_router

setup_logging()

app = FastAPI(
    title="STRATEGIE API",
    description="Modular enterprise AI platform",
    version="0.1.0",
)

# Trusted hosts -- ochrana proti Host header attack. V production tam musi
# byt jen app.strategie-system.com. V dev puštíme localhost varianty.
# Hodnoty z env var APP_TRUSTED_HOSTS (comma-separated).
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts_list,
)

app.include_router(ai_processing_router)
app.include_router(conversation_router)
app.include_router(dm_router)
app.include_router(auth_router)
app.include_router(memory_router)
app.include_router(projects_router)
app.include_router(personas_router)
app.include_router(rag_router)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
INDEX = os.path.join(static_dir, "index.html")


@app.get("/")
def index():
    return FileResponse(INDEX)


@app.get("/invite/{token}")
def invite_page(token: str):
    """Pozvánkový link — vrátí stejný index.html, JS se postará o přijetí."""
    return FileResponse(INDEX)


@app.get("/reset/{token}")
def reset_page(token: str):
    """Password reset link — vrátí index.html, JS si token z URL vezme sám."""
    return FileResponse(INDEX)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
