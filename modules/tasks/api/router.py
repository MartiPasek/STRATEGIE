"""
Tasks API router.
Base: /api/v1/tasks

Manualni CRUD pro task frontu. Auto-create ze SMS probiha v notifications modulu
(Commit 4 volá service.create_task_from_source()). Exekuce AI tasku probiha v
task_worker.py (Commit 3+5).
"""
from fastapi import APIRouter, HTTPException, Request

from core.logging import get_logger
from modules.tasks.application import service as task_service
from modules.tasks.application.service import (
    TaskError, TaskNotFound, TaskForbidden,
    InvalidTaskTransition, InvalidTaskInput,
)
from modules.tasks.api.schemas import (
    TaskInfo, CreateTaskRequest, UpdateTaskRequest,
    MarkTaskDoneRequest, CancelTaskRequest, OpenTaskCount,
)

logger = get_logger("tasks.api")

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


# ── Auth helper (stejny pattern jako v projects router) ────────────────────

def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")


# ── Exception -> HTTP mapping ──────────────────────────────────────────────

def _raise_http(exc: TaskError) -> None:
    if isinstance(exc, TaskNotFound):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, TaskForbidden):
        raise HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, InvalidTaskInput):
        raise HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, InvalidTaskTransition):
        raise HTTPException(status_code=409, detail=str(exc))
    # Fallback na 400 pro obecne TaskError.
    raise HTTPException(status_code=400, detail=str(exc))


# ── Endpointy ──────────────────────────────────────────────────────────────

@router.get("/list", response_model=list[TaskInfo])
def list_tasks(
    req: Request,
    persona_id: int | None = None,
    status: str | None = None,
    source_type: str | None = None,
    source_id: int | None = None,
    limit: int = 100,
):
    """
    Seznam tasku aktualniho tenantu. Volitelne filtry:
      - persona_id    -- jen tasky dane persony
      - status        -- open | in_progress | done | cancelled | failed
      - source_type   -- sms_inbox | email_inbox | manual | ai_generated
      - source_id     -- pro grupovani pod konkretni SMS/email
      - limit         -- 1..500, default 100
    """
    user_id = _get_uid(req)
    try:
        rows = task_service.list_tasks_for_user(
            user_id,
            persona_id=persona_id,
            status=status,
            source_type=source_type,
            source_id=source_id,
            limit=limit,
        )
    except TaskError as e:
        _raise_http(e)
    return [TaskInfo(**r) for r in rows]


@router.get("/open-count", response_model=OpenTaskCount)
def open_count(req: Request, persona_id: int):
    """
    Pocet otevrenych (open + in_progress) tasku pro personu.
    Pouzivano pro badge na persona ikonce v UI.
    """
    user_id = _get_uid(req)
    count = task_service.count_open_tasks_for_persona(user_id, persona_id)
    return OpenTaskCount(persona_id=persona_id, count=count)


@router.get("/{task_id}", response_model=TaskInfo)
def get_task(task_id: int, req: Request):
    """Detail jednoho tasku vcetne result_summary / error."""
    user_id = _get_uid(req)
    try:
        t = task_service.get_task(user_id, task_id)
    except TaskError as e:
        _raise_http(e)
    return TaskInfo(**t)


@router.post("/", response_model=TaskInfo)
def create_task(body: CreateTaskRequest, req: Request):
    """
    Vytvori manualni task (source_type='manual', created_by_user_id=<user>).
    Pro systemove zalozeni ze SMS / emailu se nepouziva tento endpoint --
    to dela notifications modul primo pres service.create_task_from_source().
    """
    user_id = _get_uid(req)
    try:
        t = task_service.create_task(
            user_id=user_id,
            persona_id=body.persona_id,
            title=body.title,
            description=body.description,
            priority=body.priority,
            due_at=body.due_at,
        )
    except TaskError as e:
        _raise_http(e)
    return TaskInfo(**t)


@router.patch("/{task_id}", response_model=TaskInfo)
def update_task(task_id: int, body: UpdateTaskRequest, req: Request):
    """Parcialni edit. Nezmena status (ten se meni pres mark-done / cancel)."""
    user_id = _get_uid(req)
    try:
        t = task_service.update_task(
            user_id,
            task_id,
            title=body.title,
            description=body.description,
            priority=body.priority,
            due_at=body.due_at,
        )
    except TaskError as e:
        _raise_http(e)
    return TaskInfo(**t)


@router.post("/{task_id}/mark-done", response_model=TaskInfo)
def mark_task_done(task_id: int, body: MarkTaskDoneRequest, req: Request):
    """
    Oznaci task jako hotovy. Pokud byl posledni open task nad SMS zdrojem,
    automaticky nastavi sms_inbox.processed_at = now (cascade).
    """
    user_id = _get_uid(req)
    try:
        t = task_service.mark_task_done(
            user_id,
            task_id,
            result_summary=body.result_summary,
        )
    except TaskError as e:
        _raise_http(e)
    return TaskInfo(**t)


@router.post("/{task_id}/cancel", response_model=TaskInfo)
def cancel_task(task_id: int, body: CancelTaskRequest, req: Request):
    """
    Zrusi task. Neovlivni processed_at zdroje.
    Telo je volitelne -- pokud body.reason=None, zapise se jen status='cancelled'.
    """
    user_id = _get_uid(req)
    try:
        t = task_service.cancel_task(user_id, task_id, reason=body.reason)
    except TaskError as e:
        _raise_http(e)
    return TaskInfo(**t)


@router.delete("/{task_id}")
def delete_task(task_id: int, req: Request):
    """Tvrdy delete tasku. Pro normalni skryti pouzij cancel."""
    user_id = _get_uid(req)
    try:
        task_service.delete_task(user_id, task_id)
    except TaskError as e:
        _raise_http(e)
    return {"ok": True, "deleted_id": task_id}
