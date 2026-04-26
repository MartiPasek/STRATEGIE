"""
Tasks application service -- business logika nad tabulkou `tasks`.

Task jako first-class entita pro AI personu:
  - list_tasks_for_user       -- filtrovat podle persony/statusu/zdroje
  - get_task                  -- detail vcetne result_summary a error
  - create_task               -- manualni vytvoreni z UI (source_type='manual')
  - create_task_from_source   -- systemova cesta (SMS/email webhook, AI-generated)
  - update_task               -- edit title/description/priority/due_at (manual)
  - mark_task_done            -- ukonci task + prenese result_summary +
                                 pokud byl posledni open task nad SMS/emailem,
                                 nastavi source.processed_at = now
  - cancel_task               -- user zrusil, zustava v historii s stavem 'cancelled'
  - delete_task               -- tvrdy delete (admin, typicky ne)

Guards:
  - Task je per-tenant, user vidi jen tasky sveho last_active_tenant_id.
  - Manualni vytvoreni / edit / mark-done je povoleno libovolnemu clenovi
    tenantu (pozdeji muze byt restrikce per persona, TBD).

Sdileni se source tabulkami (sms_inbox, email_inbox) je weak -- pouze pres
source_type + source_id. Zapis processed_at do source tabulky je zodpovednost
TaskService, ne source repository.
"""
from datetime import datetime, timezone

from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User
from modules.core.infrastructure.models_data import Task, SmsInbox

logger = get_logger("tasks.service")


# ── Exceptions ─────────────────────────────────────────────────────────────

class TaskError(Exception):
    """Obecna chyba task operace."""


class TaskNotFound(TaskError):
    """Task s danym ID neexistuje (nebo nepatri tenantu usera)."""


class TaskForbidden(TaskError):
    """User nema opravneni k teto operaci (cross-tenant pokus apod.)."""


class InvalidTaskTransition(TaskError):
    """Pokus o prechod stavu, ktery neni povolen (napr. done -> in_progress)."""


class InvalidTaskInput(TaskError):
    """Spatny vstup (prazdny title, neznamy priority, atd.)."""


# ── Konstanty ──────────────────────────────────────────────────────────────

_ALLOWED_STATUSES = {"open", "in_progress", "done", "cancelled", "failed"}
_ALLOWED_PRIORITIES = {"high", "normal", "low"}
_ALLOWED_SOURCE_TYPES = {
    "sms_inbox",
    "email_inbox",
    "manual",
    "ai_generated",
    # Faze 12b: async Whisper transkripce audio uploadu. source_id = media_files.id.
    # Executor zavola whisper_provider.transcribe a ulozi vysledek do
    # media_files.transcript pres save_transcript().
    "media_transcribe",
}

# Prechody stavu, ktere pres mark_task_done / cancel_task povolujeme.
# open | in_progress -> done        (mark_task_done)
# open | in_progress -> cancelled   (cancel_task)
# failed             -> open        (retry, pres update_task status setup)
# done / cancelled   -> (nic)       (terminal)
_TERMINAL_STATUSES = {"done", "cancelled"}


# ── Helpers ────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_current_tenant(user_id: int) -> int | None:
    """Vraci last_active_tenant_id usera, ci None pokud neni nastaven."""
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        return u.last_active_tenant_id if u else None
    finally:
        cs.close()


def _task_to_dict(t: Task) -> dict:
    """Serializace task radku do dict pro API response / logy."""
    return {
        "id": t.id,
        "tenant_id": t.tenant_id,
        "persona_id": t.persona_id,
        "source_type": t.source_type,
        "source_id": t.source_id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "due_at": t.due_at,
        "execution_conversation_id": t.execution_conversation_id,
        "result_summary": t.result_summary,
        "error": t.error,
        "created_by_user_id": t.created_by_user_id,
        "created_at": t.created_at,
        "started_at": t.started_at,
        "completed_at": t.completed_at,
        "attempts": t.attempts,
    }


def _assert_tenant_access(task: Task, user_tenant_id: int | None) -> None:
    """Odmitne task z jineho tenantu."""
    if task.tenant_id is not None and task.tenant_id != user_tenant_id:
        raise TaskForbidden(
            f"Task {task.id} patri jinemu tenantu ({task.tenant_id}), "
            f"nemuzes ho videt z tvoho aktivniho tenantu."
        )


# ── Read operace ───────────────────────────────────────────────────────────

def list_tasks_for_user(
    user_id: int,
    *,
    persona_id: int | None = None,
    status: str | None = None,
    source_type: str | None = None,
    source_id: int | None = None,
    limit: int = 100,
) -> list[dict]:
    """
    Seznam tasku aktualniho tenantu usera, volitelne filtrovany. Razeno
    podle created_at DESC (nejnovejsi nahore).

    Pro UI tab "Prichozi" (pres SMS kartu): source_type='sms_inbox',
    source_id=<sms.id>, status filtrovat nechame na UI (zobrazit vsechny).
    """
    tenant_id = _get_current_tenant(user_id)
    if tenant_id is None:
        return []

    if status is not None and status not in _ALLOWED_STATUSES:
        raise InvalidTaskInput(f"Neznamy status '{status}'.")
    if source_type is not None and source_type not in _ALLOWED_SOURCE_TYPES:
        raise InvalidTaskInput(f"Neznamy source_type '{source_type}'.")

    ds = get_data_session()
    try:
        q = ds.query(Task).filter(Task.tenant_id == tenant_id)
        if persona_id is not None:
            q = q.filter(Task.persona_id == persona_id)
        if status is not None:
            q = q.filter(Task.status == status)
        if source_type is not None:
            q = q.filter(Task.source_type == source_type)
        if source_id is not None:
            q = q.filter(Task.source_id == source_id)
        q = q.order_by(Task.created_at.desc()).limit(max(1, min(limit, 500)))
        return [_task_to_dict(t) for t in q.all()]
    finally:
        ds.close()


def get_task(user_id: int, task_id: int) -> dict:
    """Detail jednoho tasku. 404 pokud neexistuje, 403 pokud cross-tenant."""
    tenant_id = _get_current_tenant(user_id)
    ds = get_data_session()
    try:
        t = ds.query(Task).filter_by(id=task_id).first()
        if t is None:
            raise TaskNotFound(f"Task {task_id} neexistuje.")
        _assert_tenant_access(t, tenant_id)
        return _task_to_dict(t)
    finally:
        ds.close()


def count_open_tasks_for_persona(user_id: int, persona_id: int) -> int:
    """
    Pomocny counter pro UI badge -- kolik openHPS a in_progress tasku personu
    cekaj. Scope je aktualni tenant usera.
    """
    tenant_id = _get_current_tenant(user_id)
    if tenant_id is None:
        return 0
    ds = get_data_session()
    try:
        return (
            ds.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.persona_id == persona_id,
                Task.status.in_(["open", "in_progress"]),
            )
            .count()
        )
    finally:
        ds.close()


# ── Write operace ──────────────────────────────────────────────────────────

def _validate_create_input(title: str, priority: str, source_type: str) -> None:
    if not (title and title.strip()):
        raise InvalidTaskInput("Title nesmi byt prazdny.")
    if len(title) > 255:
        raise InvalidTaskInput("Title je delsi nez 255 znaku.")
    if priority not in _ALLOWED_PRIORITIES:
        raise InvalidTaskInput(f"Neznama priorita '{priority}'.")
    if source_type not in _ALLOWED_SOURCE_TYPES:
        raise InvalidTaskInput(f"Neznamy source_type '{source_type}'.")


def create_task(
    *,
    user_id: int,
    persona_id: int | None,
    title: str,
    description: str | None = None,
    priority: str = "normal",
    due_at: datetime | None = None,
) -> dict:
    """
    Manualni vytvoreni tasku z UI. source_type='manual', source_id=NULL.
    Vraci full dict noveho tasku vcetne ID.
    """
    _validate_create_input(title, priority, source_type="manual")
    tenant_id = _get_current_tenant(user_id)
    if tenant_id is None:
        raise TaskForbidden("Nemas aktivni tenant, task nelze zalozit.")

    ds = get_data_session()
    try:
        t = Task(
            tenant_id=tenant_id,
            persona_id=persona_id,
            source_type="manual",
            source_id=None,
            title=title.strip(),
            description=(description.strip() if description else None),
            status="open",
            priority=priority,
            due_at=due_at,
            created_by_user_id=user_id,
        )
        ds.add(t)
        ds.commit()
        ds.refresh(t)
        logger.info(
            f"TASK | created manual | id={t.id} | tenant={tenant_id} | "
            f"persona={persona_id} | by_user={user_id} | title={title[:60]!r}"
        )
        return _task_to_dict(t)
    finally:
        ds.close()


def create_task_from_source(
    *,
    tenant_id: int | None,
    persona_id: int | None,
    source_type: str,
    source_id: int | None,
    title: str,
    description: str | None = None,
    priority: str = "normal",
    due_at: datetime | None = None,
) -> dict:
    """
    Systemove / automaticke zalozeni tasku (webhook, AI).
    Nema created_by_user_id (NULL = system).

    source_type: 'sms_inbox' | 'email_inbox' | 'ai_generated'
    """
    if source_type == "manual":
        raise InvalidTaskInput(
            "Pro manualni vytvoreni pouzij create_task() (zapise created_by_user_id)."
        )
    _validate_create_input(title, priority, source_type=source_type)

    ds = get_data_session()
    try:
        t = Task(
            tenant_id=tenant_id,
            persona_id=persona_id,
            source_type=source_type,
            source_id=source_id,
            title=title.strip(),
            description=(description.strip() if description else None),
            status="open",
            priority=priority,
            due_at=due_at,
            created_by_user_id=None,
        )
        ds.add(t)
        ds.commit()
        ds.refresh(t)
        logger.info(
            f"TASK | created system | id={t.id} | tenant={tenant_id} | "
            f"persona={persona_id} | source={source_type}:{source_id} | "
            f"title={title[:60]!r}"
        )
        return _task_to_dict(t)
    finally:
        ds.close()


def update_task(
    user_id: int,
    task_id: int,
    *,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    due_at: datetime | None = None,
) -> dict:
    """
    Parcialni edit tasku (jen pole, ktera user dodal). Nezdmena status --
    status se meni pres mark_task_done / cancel_task.
    """
    tenant_id = _get_current_tenant(user_id)
    ds = get_data_session()
    try:
        t = ds.query(Task).filter_by(id=task_id).first()
        if t is None:
            raise TaskNotFound(f"Task {task_id} neexistuje.")
        _assert_tenant_access(t, tenant_id)

        if t.status in _TERMINAL_STATUSES:
            raise InvalidTaskTransition(
                f"Task {task_id} je v terminalnim stavu '{t.status}', nelze editovat."
            )

        if title is not None:
            if not title.strip():
                raise InvalidTaskInput("Title nesmi byt prazdny.")
            if len(title) > 255:
                raise InvalidTaskInput("Title je delsi nez 255 znaku.")
            t.title = title.strip()
        if description is not None:
            t.description = description.strip() or None
        if priority is not None:
            if priority not in _ALLOWED_PRIORITIES:
                raise InvalidTaskInput(f"Neznama priorita '{priority}'.")
            t.priority = priority
        if due_at is not None:
            t.due_at = due_at

        ds.commit()
        ds.refresh(t)
        logger.info(f"TASK | updated | id={task_id} | by_user={user_id}")
        return _task_to_dict(t)
    finally:
        ds.close()


def mark_task_done(
    user_id: int | None,
    task_id: int,
    *,
    result_summary: str | None = None,
) -> dict:
    """
    Ukonci task jako uspesne splneny. Volane bud manualne (user_id = kdo klikl)
    nebo z executoru (user_id = None, AI).

    SIDE EFFECT: pokud byl tohle posledni open/in_progress task nad zdrojem
    (sms_inbox/email_inbox), nastavi source.processed_at = now. Tim se SMS
    presune ve UI ze "Prichozich" do "Zpracovanych".
    """
    tenant_id = _get_current_tenant(user_id) if user_id else None

    ds = get_data_session()
    try:
        t = ds.query(Task).filter_by(id=task_id).first()
        if t is None:
            raise TaskNotFound(f"Task {task_id} neexistuje.")
        if user_id is not None:
            _assert_tenant_access(t, tenant_id)

        if t.status in _TERMINAL_STATUSES:
            raise InvalidTaskTransition(
                f"Task {task_id} je uz v terminalnim stavu '{t.status}'."
            )

        now = _now()
        t.status = "done"
        t.completed_at = now
        if t.started_at is None:
            t.started_at = now
        if result_summary is not None:
            t.result_summary = result_summary.strip() or None

        # Cascade na source: pokud byl tohle posledni open task pro tu SMS,
        # oznacime SMS jako zpracovanou (processed_at=now).
        cascade = _maybe_mark_source_processed(ds, t, now)

        ds.commit()
        ds.refresh(t)
        logger.info(
            f"TASK | done | id={task_id} | by_user={user_id} | "
            f"source={t.source_type}:{t.source_id} | cascade_processed={cascade}"
        )
        return _task_to_dict(t)
    finally:
        ds.close()


def cancel_task(user_id: int, task_id: int, *, reason: str | None = None) -> dict:
    """
    Zrusi task (user rozhodl ze se nebude delat). Status='cancelled'.
    Neovlivni processed_at zdroje -- cancel != done.
    """
    tenant_id = _get_current_tenant(user_id)
    ds = get_data_session()
    try:
        t = ds.query(Task).filter_by(id=task_id).first()
        if t is None:
            raise TaskNotFound(f"Task {task_id} neexistuje.")
        _assert_tenant_access(t, tenant_id)

        if t.status in _TERMINAL_STATUSES:
            raise InvalidTaskTransition(
                f"Task {task_id} je uz v terminalnim stavu '{t.status}'."
            )

        t.status = "cancelled"
        t.completed_at = _now()
        if reason:
            # Ulozime do result_summary jako "zruseno: duvod" -- ne do error,
            # protoze to nebyla chyba, jen uzivatelske rozhodnuti.
            t.result_summary = f"[zruseno] {reason.strip()}"

        ds.commit()
        ds.refresh(t)
        logger.info(f"TASK | cancelled | id={task_id} | by_user={user_id}")
        return _task_to_dict(t)
    finally:
        ds.close()


def delete_task(user_id: int, task_id: int) -> None:
    """
    Tvrdy delete (typicky pro testy / admin cleanup). Task zmizi z DB.
    Pro bezne skryti preferuj cancel_task.
    """
    tenant_id = _get_current_tenant(user_id)
    ds = get_data_session()
    try:
        t = ds.query(Task).filter_by(id=task_id).first()
        if t is None:
            raise TaskNotFound(f"Task {task_id} neexistuje.")
        _assert_tenant_access(t, tenant_id)

        ds.delete(t)
        ds.commit()
        logger.info(f"TASK | deleted | id={task_id} | by_user={user_id}")
    finally:
        ds.close()


# ── Source cascade (SMS/email -> processed) ────────────────────────────────

def _maybe_mark_source_processed(ds, task: Task, now: datetime) -> bool:
    """
    Pokud je `task` napojen na zdroj (sms_inbox) a po jeho prechodu na 'done'
    uz nezbyva zadny dalsi open/in_progress task nad tim samym zdrojem,
    nastavi source.processed_at = now.

    POZOR K EMAILUM: u email_inbox se cascade ZAMERNE NEDELA. Task u emailu
    je opt-in ("Navrhni odpoved") a jeho vysledek je jen DRAFT -- email
    zavrit musi user explicitne pres reply-send nebo mark-processed.
    Kdyby cascade tu byla, email by zmizel z 'Prichozi' jakmile AI dobehne
    s draftem, uz driv nez ho user vidi.

    Helper _cascade_email zustava v kodu pro pripadne budouci pouziti
    (napr. kdyby prisel scenar "automaticky odeslat AI draft bez user
    potvrzeni" -- dnes se nepouziva).

    Vraci True pokud k cascade doslo.
    """
    if task.source_type == "sms_inbox" and task.source_id is not None:
        return _cascade_sms(ds, task, now)
    # Email cascade by default DISABLED -- viz docstring.
    return False


def _cascade_sms(ds, task: Task, now: datetime) -> bool:
    """Cascade dokonceni tasku -> sms_inbox.processed_at."""
    remaining = (
        ds.query(Task)
        .filter(
            Task.source_type == "sms_inbox",
            Task.source_id == task.source_id,
            Task.id != task.id,
            Task.status.in_(["open", "in_progress"]),
        )
        .count()
    )
    if remaining > 0:
        return False

    sms = ds.query(SmsInbox).filter_by(id=task.source_id).first()
    if sms is None:
        return False
    if sms.processed_at is not None:
        return False

    sms.processed_at = now
    return True


def _cascade_email(ds, task: Task, now: datetime) -> bool:
    """Cascade dokonceni tasku -> email_inbox.processed_at."""
    from modules.core.infrastructure.models_data import EmailInbox

    remaining = (
        ds.query(Task)
        .filter(
            Task.source_type == "email_inbox",
            Task.source_id == task.source_id,
            Task.id != task.id,
            Task.status.in_(["open", "in_progress"]),
        )
        .count()
    )
    if remaining > 0:
        return False

    email = ds.query(EmailInbox).filter_by(id=task.source_id).first()
    if email is None:
        return False
    if email.processed_at is not None:
        return False

    email.processed_at = now
    return True
