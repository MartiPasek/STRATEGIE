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
from modules.audit.api.router import router as audit_router
from modules.notifications.api.sms_gateway_router import router as sms_gateway_router
from modules.notifications.api.sms_ui_router import router as sms_ui_router
from modules.notifications.api.email_router import router as email_router
from modules.notifications.api.email_ui_router import router as email_ui_router
from modules.notifications.api.notifications_router import router as notifications_router
from modules.notifications.api.consent_router import router as consent_router
from modules.tasks.api.router import router as tasks_router
from modules.thoughts.api.router import router as thoughts_router
from modules.thoughts.api.questions_router import router as marti_questions_router
from modules.admin.api.router import router as admin_router
from modules.notebook.api.router import router as notebook_router
from modules.media.api.router import router as media_router

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
app.include_router(audit_router)
app.include_router(sms_gateway_router)
app.include_router(sms_ui_router)
app.include_router(email_router)
app.include_router(email_ui_router)
app.include_router(notifications_router)
app.include_router(consent_router)
app.include_router(tasks_router)
app.include_router(thoughts_router)
app.include_router(notebook_router)
app.include_router(marti_questions_router)
app.include_router(admin_router)
app.include_router(media_router)

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
