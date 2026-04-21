"""
Tasks API schemas -- Pydantic modely pro request/response.

Zdroj pravdy je Task v models_data.py; tady jen zobrazovaci / vstupni twin.
"""
from datetime import datetime
from pydantic import BaseModel, Field


# ── Response ───────────────────────────────────────────────────────────────

class TaskInfo(BaseModel):
    """Polozka v seznamu i detailu. Obsahuje vsechna pole tasku."""
    id: int
    tenant_id: int | None = None
    persona_id: int | None = None

    source_type: str              # sms_inbox | email_inbox | manual | ai_generated
    source_id: int | None = None

    title: str
    description: str | None = None

    status: str                   # open | in_progress | done | cancelled | failed
    priority: str                 # high | normal | low
    due_at: datetime | None = None

    execution_conversation_id: int | None = None

    result_summary: str | None = None
    error: str | None = None

    created_by_user_id: int | None = None

    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    attempts: int


# ── Request ────────────────────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    """Manualni task z UI. source_type je vzdy 'manual' (nedava se sem)."""
    persona_id: int | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: str = "normal"              # high | normal | low
    due_at: datetime | None = None


class UpdateTaskRequest(BaseModel):
    """Parcialni update. Vsechna pole volitelne."""
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    priority: str | None = None
    due_at: datetime | None = None


class MarkTaskDoneRequest(BaseModel):
    """Manualni 'mark as done' s volitelnym shrnutim toho co se udelalo."""
    result_summary: str | None = None


class CancelTaskRequest(BaseModel):
    """Zruseni tasku s volitelnym duvodem (zapise se do result_summary)."""
    reason: str | None = None


# ── Counters / utility ─────────────────────────────────────────────────────

class OpenTaskCount(BaseModel):
    """Pro UI badge 'kolik tasku ma persona X otevrenych'."""
    persona_id: int
    count: int
