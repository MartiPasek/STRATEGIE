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


def _resolve_tenant_for_auto_reply(task: Task) -> int | None:
    """
    Faze 13 cleanup: pri auto-reply z SMS task se queue_sms volalo s
    tenant_id=task.tenant_id, ale task.tenant_id casto NULL (zvlast pri
    SMS auto-reply v ranni rade 25.4.2026 -- rows 7-17 v sms_outbox bez
    tenant_id, neviditelne v UI).

    Fallback chain:
      1. task.tenant_id (primary)
      2. Conversation.tenant_id pres task.execution_conversation_id
      3. Marti's (user_id=1) last_active_tenant_id (rodicovsky default)
      4. None (last resort -- bude potreba backfill SQL)
    """
    if task.tenant_id:
        return task.tenant_id

    # Try execution_conversation
    if task.execution_conversation_id:
        try:
            ds = get_data_session()
            try:
                conv = (
                    ds.query(Conversation)
                    .filter_by(id=task.execution_conversation_id)
                    .first()
                )
                if conv and conv.tenant_id:
                    return conv.tenant_id
            finally:
                ds.close()
        except Exception as _e:
            logger.warning(f"AUTO_REPLY | resolve via conversation failed: {_e}")

    # Fallback: Marti's last_active_tenant_id (rodic = primary owner)
    try:
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import User
        cs = get_core_session()
        try:
            marti = cs.query(User).filter_by(id=1).first()
            if marti and marti.last_active_tenant_id:
                return marti.last_active_tenant_id
        finally:
            cs.close()
    except Exception as _e:
        logger.warning(f"AUTO_REPLY | resolve via Marti fallback failed: {_e}")

    return None


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
    elif task.source_type == "sms_inbox":
        # SMS-specific instrukce -- task executor sam zaridi odeslani.
        # AI MA NAPSAT JEN TELO ODPOVEDI, NIC VICE. Nesmi volat send_sms tool
        # -- jinak vznikne dvojity send (AI volani + executor auto-reply hook).
        parts.append(
            "\n---\n"
            "**DŮLEŽITÉ — jak odpovídat na tento SMS task:**\n"
            "Tvoje odpověď (final message) = **přesné tělo SMS, které se odešle**. "
            "Napiš ho stručně, přirozeně, v SMS stylu — žádné hlavičky, žádné "
            "uvozovací věty typu „Tady je návrh:\" nebo „Odpověď:\".\n\n"
            "**NEPOUŽÍVEJ nástroj `send_sms`** — SMS task executor odešle SMS "
            "automaticky na základě tvé final odpovědi. Pokud bys volala send_sms, "
            "SMS se pošle 2x (jednou tebou, jednou executorem). Nevolej ani "
            "`send_email` — toto je SMS task.\n\n"
            "Můžeš volat informační tooly (find_user, recall_thoughts, list_sms_inbox) "
            "pro získání kontextu, pokud je potřeba.\n\n"
            "Pravidla SMS: max 2-3 věty, ~300 znaků. Pokud dotaz vyžaduje dlouhou "
            "odpověď, napiš krátké shrnutí + „detaily pošlu mailem\" nebo podobně."
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

        # High watermark pred chatem -- pouzito pro detekci, ze AI behem
        # tasku uz odeslala SMS/email (abychom nedelali duplicitni auto-reply).
        from modules.core.infrastructure.models_data import ActionLog as _AL_hw
        _ds_hw = get_data_session()
        try:
            _hw = _ds_hw.query(_AL_hw).order_by(_AL_hw.id.desc()).first()
            pre_chat_log_id = _hw.id if _hw else 0
        finally:
            _ds_hw.close()

        # Import uvnitr funkce kvuli cyklickym importum (conversation modul
        # casem muze importovat z tasks, kdyz pridame AI tool `create_task`).
        from modules.conversation.application.service import chat

        # Faze 10b: source rozlisi typ LLM volani v llm_calls.kind
        # -> dashboard umi delit 'user_chat' vs 'task_email' vs 'task_sms'.
        if task.source_type == "email_inbox":
            _src = "email_suggest"
        elif task.source_type == "sms_inbox":
            _src = "sms_task"
        else:
            _src = "task_other"

        _, reply, _summary = chat(
            conversation_id=conv_id,
            user_message=prompt,
            user_id=None,                       # AI agent, bez human kontextu
            tenant_id=task.tenant_id,
            project_id=None,
            preferred_persona_id=task.persona_id,
            source=_src,
        )

        # ── AUTO-REPLY pro trusted SMS sendery (Phase 7 extension) ────────
        # Pokud task pochazi z prichozi SMS, sender ma aktivni auto_send_consent
        # pro SMS a jsme pod rate limitem (20/hod) -> odpoved odesleme rovnou,
        # bez user manualniho kliknuti. Reply zustava ulozeny v task.result_summary
        # jako audit. Email necham jako opt-in draft (uzivatelska preference).
        auto_replied = False
        if task.source_type == "sms_inbox" and reply and reply.strip():
            try:
                _ds = get_data_session()
                try:
                    _sms = _ds.query(SmsInbox).filter_by(id=task.source_id).first()
                    _from = _sms.from_phone if _sms else None
                finally:
                    _ds.close()

                if _from:
                    # DEDUP: pokud AI behem chat() sama odeslala SMS na stejne cislo
                    # (pres send_sms tool -- ten muze sam spustit auto-send), tak
                    # nesmime poslat znovu. Filtrujeme action_logs vytvorene po
                    # pre_chat_log_id kde tool_name=send_sms a input obsahuje _from.
                    from modules.core.infrastructure.models_data import ActionLog as _AL_dup
                    _dup_ds = get_data_session()
                    try:
                        _dup_rows = (
                            _dup_ds.query(_AL_dup)
                            .filter(
                                _AL_dup.id > pre_chat_log_id,
                                _AL_dup.tool_name == "send_sms",
                                _AL_dup.status == "success",
                            )
                            .all()
                        )
                        _already_sent = False
                        _from_digits = "".join(c for c in _from if c.isdigit() or c == "+")
                        for _row in _dup_rows:
                            _inp = _row.input or ""
                            # Match podle telefonu -- nezavisle na formatu (number/escape)
                            if _from in _inp or _from_digits in _inp:
                                _already_sent = True
                                break
                    finally:
                        _dup_ds.close()

                    if _already_sent:
                        logger.info(
                            f"AUTO_REPLY_SMS | skipped (AI already sent) | "
                            f"task_id={task_id} | to={_from}"
                        )

                    from modules.notifications.application import consent_service as _csvc
                    _trust, _ = _csvc.check_all_recipients_trusted([_from], "sms")
                    _under_limit, _cnt = _csvc.check_rate_limit("sms")
                    if _trust and _under_limit and not _already_sent:
                        # Strip mozny preambul AI typu "Tady je odpoved:" -- reply
                        # je v SMS formatu primo (AI uz ma pokyn psat primo telo).
                        from modules.notifications.application.sms_service import (
                            queue_sms as _qs_reply, SmsError as _SE_reply,
                        )

                        # Faze 14 prep #2 polish: defensive outbox dedup check.
                        # Chrani pred race conditions, ktere _already_sent (action_logs)
                        # nezachyti -- zejmena restart API mid-task, paralelni
                        # worker po manual retry, nebo edge cases. Historicke
                        # rows 7+8 a 9+10 v sms_outbox (23.4. 12:37, 12:38) byly
                        # presne tenhle case (3-4s gap, identicky body).
                        # Window 30s je velkorysy ale defensive -- legit duplicate
                        # send (user posila dvakrat to same vedome) je nepravdepodobny
                        # u auto-reply.
                        from modules.core.infrastructure.models_data import (
                            SmsOutbox as _SmsOutbox_dup,
                        )
                        from datetime import timedelta as _timedelta_dup
                        _dup_existing = None
                        _dedup_ds = get_data_session()
                        try:
                            _dedup_cutoff = _now() - _timedelta_dup(seconds=30)
                            _dup_existing = (
                                _dedup_ds.query(_SmsOutbox_dup)
                                .filter(
                                    _SmsOutbox_dup.to_phone == _from,
                                    _SmsOutbox_dup.body == reply,
                                    _SmsOutbox_dup.created_at >= _dedup_cutoff,
                                    _SmsOutbox_dup.status.in_(["pending", "sent"]),
                                )
                                .first()
                            )
                        finally:
                            _dedup_ds.close()

                        if _dup_existing:
                            logger.warning(
                                f"AUTO_REPLY_SMS | duplicate detected, skipping | "
                                f"task_id={task_id} | to={_from} | "
                                f"existing_outbox_id={_dup_existing.id} | "
                                f"existing_created={_dup_existing.created_at}"
                            )
                            # Skip send -- audit log neni potreba (fakticky
                            # neproslo nase ruka). auto_replied zustava False.

                        # Hlavni queue_sms branch -- pouze kdyz neni duplicate.
                        # Pri _dup_existing celou tuto sekci preskakujeme,
                        # audit log se taky nedela (zadne send neproslo).
                        if not _dup_existing:
                            try:
                                # Faze 13 cleanup: resolve tenant_id pres helper.
                                # task.tenant_id je casto NULL u SMS auto-reply --
                                # zpusobilo to 11 NULL rows v sms_outbox (25.4. ranni
                                # vlna), neviditelne v UI Vsechny/Odeslane.
                                _eff_tenant_id = _resolve_tenant_for_auto_reply(task)
                                _res = _qs_reply(
                                    to=_from, body=reply,
                                    purpose="user_request",
                                    user_id=None,
                                    tenant_id=_eff_tenant_id,
                                    persona_id=task.persona_id,
                                )
                                # Audit action_type='auto' (pocita se do rate limitu)
                                try:
                                    import json as _json_auto
                                    from modules.core.infrastructure.models_data import ActionLog as _AL_auto
                                    _alog_s = get_data_session()
                                    try:
                                        _alog_s.add(_AL_auto(
                                            user_id=None,
                                            action_type="auto",
                                            tool_name="send_sms",
                                            input=_json_auto.dumps(
                                                {"to": _from, "body": reply,
                                                 "auto_reply": True,
                                                 "task_id": task_id,
                                                 "outbox_id": _res.get("id")},
                                                ensure_ascii=False,
                                            ),
                                            output=f"to={_from} | auto_reply | task={task_id}",
                                            status="success" if _res.get("status") in ("sent", "pending") else "fail",
                                            approval_required=False,
                                        ))
                                        _alog_s.commit()
                                    finally:
                                        _alog_s.close()
                                except Exception as _ae:
                                    logger.error(f"AUTO_REPLY_SMS | audit failed | {_ae}")
                                auto_replied = True
                                logger.info(
                                    f"AUTO_REPLY_SMS | sent | task_id={task_id} | "
                                    f"to={_from} | outbox_id={_res.get('id')}"
                                )
                            except _SE_reply as _se:
                                logger.warning(
                                    f"AUTO_REPLY_SMS | queue failed | task_id={task_id} | "
                                    f"to={_from} | err={_se}"
                                )
                    else:
                        logger.info(
                            f"AUTO_REPLY_SMS | skipped | task_id={task_id} | "
                            f"trusted={_trust} under_limit={_under_limit} cnt={_cnt}"
                        )
            except Exception as _are:
                logger.exception(f"AUTO_REPLY_SMS | check failed | task_id={task_id} | {_are}")

        # Mark done + cascade na sms_inbox.processed_at.
        # user_id=None znamena "system/AI complete" -- mark_task_done to
        # neblokuje (tenant assert se preskoci).
        task_service.mark_task_done(
            user_id=None,
            task_id=task_id,
            result_summary=(reply + "\n\n_[auto-reply odeslán]_") if auto_replied else reply,
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
