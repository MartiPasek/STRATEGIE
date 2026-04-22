"""
Task executor -- spusti AI tool loop nad konkretnim taskem.

Flow:
  1. Atomic claim: UPDATE tasks SET status='in_progress' WHERE id=X AND status='open'
     - chrani pred soubeznym zpracovanim dvema workery / UI akc
  2. Vytvori skrytou Conversation (conversation_type='task_execution')
     - je filtrovana z bezneho sidebar listingu (ktery bere conversation_type='ai')
     - ulozi jeji id do task.execution_conversation_id pro audit a UI drilldown
  3. Postaví task prompt z title + description + source context (SMS body)
  4. Zavola existujici chat() ze conversation service:
     - Claude dostane vsechny tools (find_user, send_email (CONFIRM), send_sms
       (CONFIRM), list_*, RAG, ...)
     - Persona pro tool loop = task.persona_id
  5. Reply od AI uklada do task.result_summary a mark_task_done()
     - cascade: pokud je to posledni open task nad SMS, sms.processed_at = now
  6. Pri vyjimce: task.status='failed', task.error=str(e) -- worker muze retry

CONFIRM akce (send_email, send_sms):
  AI muze behem tasku chtit odeslat mail/SMS -- to vytvori pending_action v
  task conversation, reply obsahuje preview + vyzvu k potvrzeni. MVP:
  task se uzavre jako 'done' s result_summary = tim preview. User pak v UI
  uvidi navrh a v Commit 7 ho potvrdi / zamitne primo v task karte
  (UI zavola POST /api/v1/conversation/.../confirm nebo podobne).

Race conditions:
  - Worker picks up same task twice -> druhy se odpali na claim-check (status
    uz je 'in_progress', UPDATE vrati 0 rows) a logne "skip, already claimed".
  - UI dela mark-done zatimco worker bezi -> v DB vyhrava posledni commit;
    audit log je OK, task bude `done` a `result_summary` z toho, kdo commitl
    jako posledni. Worst case je replaced summary.
"""
from datetime import datetime, timezone

from sqlalchemy import update

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    Task, Conversation, SmsInbox, EmailInbox,
)
from modules.tasks.application import service as task_service

logger = get_logger("tasks.executor")


# ── Helpers ────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _atomic_claim(task_id: int) -> Task | None:
    """
    Atomicky oznaci task jako in_progress, vraci Task pokud se podarilo
    claim. Jinak None (task uz neexistuje nebo ho popadli jinde).

    Pouzije UPDATE ... WHERE status='open' -- row-level lock v PG zajisti,
    ze paralelne spustene workery se nemuzou stretnout.
    """
    ds = get_data_session()
    try:
        now = _now()
        result = ds.execute(
            update(Task)
            .where(Task.id == task_id, Task.status == "open")
            .values(
                status="in_progress",
                started_at=now,
                attempts=Task.attempts + 1,
            )
        )
        ds.commit()
        if result.rowcount == 0:
            # Task bud neexistuje, nebo uz ma status != 'open' (jiny worker,
            # manual cancel, cokoli).
            return None
        # Nactu aktualizovany task back -- kvuli attempts counteru a dalsim
        # polim ktere mohly byt zmenene.
        task = ds.query(Task).filter_by(id=task_id).first()
        return task
    finally:
        ds.close()


def _create_execution_conversation(task: Task) -> int:
    """
    Vytvori skrytou conversation pro tento task. Vraci conversation.id.

    conversation_type='task_execution' zajisti, ze se konverzace nezobrazi
    v sidebaru (`list_conversations_for_user` filtruje type='ai').
    """
    ds = get_data_session()
    try:
        conv = Conversation(
            user_id=None,              # AI autonomne -- zadny lidsky vlastnik
            tenant_id=task.tenant_id,
            project_id=None,
            conversation_type="task_execution",
            active_agent_id=task.persona_id,
            title=f"[task #{task.id}] {(task.title or '')[:80]}",
            created_by_user_id=task.created_by_user_id,
        )
        ds.add(conv)
        ds.commit()
        ds.refresh(conv)

        # Zapisme execution_conversation_id zpetne do tasku -- UI drilldown,
        # audit.
        t = ds.query(Task).filter_by(id=task.id).first()
        if t is not None:
            t.execution_conversation_id = conv.id
            ds.commit()

        logger.info(
            f"TASK EXECUTOR | hidden conv created | conv_id={conv.id} | "
            f"task_id={task.id} | tenant={task.tenant_id} | persona={task.persona_id}"
        )
        return conv.id
    finally:
        ds.close()


def _build_task_prompt(task: Task) -> str:
    """
    Postavi user-role zpravu, kterou dostane Claude jako prvni vstup.

    Format:
      - jasne instrukce co ma udelat (z task.title + task.description)
      - pokud task pochazi ze zpravy (SMS/email) -- originalni telo
      - explicitni pokyn: „po dokonceni napis kratke shrnuti co jsi udelal"
    """
    parts: list[str] = []
    parts.append(f"## Úkol\n{task.title}")
    if task.description:
        parts.append(f"\n### Detail\n{task.description}")

    # Pripojim original SMS telo pro kontext.
    if task.source_type == "sms_inbox" and task.source_id is not None:
        ds = get_data_session()
        try:
            sms = ds.query(SmsInbox).filter_by(id=task.source_id).first()
            if sms is not None:
                parts.append(
                    f"\n### Zdrojová zpráva (SMS od {sms.from_phone})\n"
                    f"> {sms.body}"
                )
        finally:
            ds.close()

    # Pripojim original email pro kontext (email_inbox source).
    # Formatujeme jako blockquote, aby byl zdroj jasne oddeleny od task
    # instrukce a AI videla "tohle mi prislo, reaguj na to".
    if task.source_type == "email_inbox" and task.source_id is not None:
        ds = get_data_session()
        try:
            email = ds.query(EmailInbox).filter_by(id=task.source_id).first()
            if email is not None:
                sender = f"{email.from_name} <{email.from_email}>" if email.from_name else email.from_email
                subj = email.subject or "(bez předmětu)"
                body_preview = (email.body or "(prázdný body)").strip()
                parts.append(
                    f"\n### Zdrojový email\n"
                    f"**Od:** {sender}\n"
                    f"**Pro:** {email.to_email}\n"
                    f"**Předmět:** {subj}\n\n"
                    f"**Tělo:**\n"
                    f"> " + body_preview.replace("\n", "\n> ")
                )
        finally:
            ds.close()

    # Instrukce na zaver -- rozlisit email vs. SMS/manual proto, ze u emailu
    # typicky chceme draft odpovedi (ne akci "poslat odpoved hned") -- user
    # ho potvrdi v UI.
    if task.source_type == "email_inbox":
        parts.append(
            "\n---\n"
            "Navrhni vhodnou odpověď na tento email. Piš přímo **tělo odpovědi** "
            "bez hlaviček (To/Subject/From) a bez uvozovacích vět typu „Tady je návrh:\" "
            "— co napíšeš, to user uvidí jako draft a může ho rovnou potvrdit k odeslání.\n\n"
            "Pokud je potřeba něco dohledat (informace, kontakt), použij dostupné nástroje. "
            "Pokud email nepotřebuje odpověď (reklama, info-only), napiš krátké shrnutí "
            "a uveď, proč odpověď nedává smysl."
        )
    else:
        parts.append(
            "\n---\n"
            "Proveď potřebné kroky (použij dostupné nástroje). "
            "Pokud navrhuješ odpověď, napiš ji v textu odpovědi — uživatel ji "
            "uvidí v task kartě a může ji potvrdit k odeslání.\n\n"
            "Na závěr stručně (1-2 věty) shrň, co jsi udělal."
        )
    return "\n".join(parts)


# ── Public API ─────────────────────────────────────────────────────────────

def execute_task(task_id: int) -> dict:
    """
    Zpracuje jeden task -- claim, spusti AI, ulozi vysledek.

    Vraci:
      {"status": "claimed" | "done" | "failed" | "skipped", "task_id": X, ...}
      - "skipped"  -- task neni open (uz ho nekdo popadl / nezskal)
      - "done"     -- AI dokoncila a vratila reply
      - "failed"   -- exception behem exekuce

    Thread-safe diky atomic claim. Muzes volat paralelne ze workeru
    (i kdyz pro MVP worker bude single-threaded polling).
    """
    task = _atomic_claim(task_id)
    if task is None:
        logger.info(f"TASK EXECUTOR | skip | task_id={task_id} | uz neni open")
        return {"status": "skipped", "task_id": task_id}

    logger.info(
        f"TASK EXECUTOR | claimed | task_id={task_id} | "
        f"attempt={task.attempts} | source={task.source_type}:{task.source_id}"
    )

    try:
        conv_id = _create_execution_conversation(task)
        prompt = _build_task_prompt(task)

        # Import uvnitr funkce kvuli cyklickym importum (conversation modul
        # casem muze importovat z tasks, kdyz pridame AI tool `create_task`).
        from modules.conversation.application.service import chat

        _, reply, _summary = chat(
            conversation_id=conv_id,
            user_message=prompt,
            user_id=None,                       # AI agent, bez human kontextu
            tenant_id=task.tenant_id,
            project_id=None,
            preferred_persona_id=task.persona_id,
        )

        # Mark done + cascade na sms_inbox.processed_at.
        # user_id=None znamena "system/AI complete" -- mark_task_done to
        # neblokuje (tenant assert se preskoci).
        task_service.mark_task_done(
            user_id=None,
            task_id=task_id,
            result_summary=reply,
        )

        logger.info(
            f"TASK EXECUTOR | done | task_id={task_id} | "
            f"reply_len={len(reply) if reply else 0}"
        )
        return {
            "status": "done",
            "task_id": task_id,
            "execution_conversation_id": conv_id,
            "result_preview": (reply or "")[:200],
        }

    except Exception as e:
        # Failed -- uloz error, dovol retry pozdeji (worker si tasky failed
        # muze brat jen pri explicitnim retry, automaticky ne, ať nejsme v
        # nekonecne smycce pri persistentni chybe).
        _mark_task_failed(task_id, str(e))
        logger.error(
            f"TASK EXECUTOR | failed | task_id={task_id} | error={e!r}",
            exc_info=True,
        )
        return {"status": "failed", "task_id": task_id, "error": str(e)}


def _mark_task_failed(task_id: int, error: str) -> None:
    """Zapise status=failed + error. Volane jen z executoru pri vyjimce."""
    ds = get_data_session()
    try:
        t = ds.query(Task).filter_by(id=task_id).first()
        if t is None:
            return
        t.status = "failed"
        t.error = error[:4000]   # ochrana pred obrovskymi error tracebacks
        t.completed_at = _now()
        ds.commit()
    finally:
        ds.close()


def fetch_open_task_ids(limit: int = 10) -> list[int]:
    """
    Vrati seznam task_id, ktere jsou ve stavu 'open', serazene podle priority
    (high -> normal -> low) a pak podle created_at (oldest first).

    Worker to vola pri kazdem poll cyklu.
    """
    ds = get_data_session()
    try:
        # CASE WHEN pro custom sort (PG/SQLAlchemy-agnosticky zpusob).
        from sqlalchemy import case
        priority_order = case(
            {"high": 0, "normal": 1, "low": 2},
            value=Task.priority,
            else_=1,
        )
        rows = (
            ds.query(Task.id)
            .filter(Task.status == "open")
            .order_by(priority_order, Task.created_at.asc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
        return [r[0] for r in rows]
    finally:
        ds.close()
