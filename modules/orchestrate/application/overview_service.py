"""
Faze 11b -- Orchestrate mode overview service.

Marti-AI v 'orchestrate mode' (default persona) vola build_daily_overview()
kdyz Marti se pta 's cim dnes potrebujes pomoct', 'co resis', 'prehled',
'likvidace'. Vraci se strukturovany prehled nevyrizenych veci napric
3 hlavnimi kanaly:

  1. email_inbox -- emaily s processed_at IS NULL (nevyrizene)
  2. sms_inbox   -- SMS s processed_at IS NULL
  3. thoughts    -- type='todo' kde meta nema done=true a deleted_at IS NULL

Pro kazdy kanal: count + top 5 polozek razeno (priority_score DESC,
created_at DESC). Priority klesa pri 'odloz' / 'neres' -- polozky dole
se vyrizuji az na konec.

Scope -- pro Marti (rodic, cross-tenant admin) defaultne agreguje napric
vsemi tenanty a personami. Pro omezene uzivatele (non-parent) by mela
byt varianta omezit na svuj tenant -- to az pridame v budouci iteraci.

Ethical:
  Vraci se jen metadata (count, from, subject/body preview). Plne texty
  user uvidi az v 'pojd na to' flow (nacte detail na pozadani).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    EmailInbox, SmsInbox, Thought,
)

logger = get_logger("orchestrate.overview")

TOP_N_PER_CHANNEL = 5


def _preview(text: str | None, max_len: int = 80) -> str:
    if not text:
        return ""
    t = str(text).strip().replace("\n", " ")
    if len(t) > max_len:
        return t[:max_len - 1] + "…"
    return t


def _age_label(created_at: datetime | None) -> str:
    """'pred 3h', 'vcera', 'pred 5 dny' -- lidsky citelne."""
    if not created_at:
        return "-"
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    diff = now - created_at
    secs = int(diff.total_seconds())
    if secs < 60:
        return "prave ted"
    mins = secs // 60
    if mins < 60:
        return f"pred {mins} min"
    hours = mins // 60
    if hours < 24:
        return f"pred {hours}h"
    days = hours // 24
    if days == 1:
        return "vcera"
    if days < 7:
        return f"pred {days} dny"
    weeks = days // 7
    if weeks < 5:
        return f"pred {weeks} tyd"
    months = days // 30
    return f"pred {months} mes"


def build_daily_overview(
    *,
    user_id: int | None = None,
    tenant_id: int | None = None,
    persona_id: int | None = None,
    scope: str = "current",  # "current" (aktualni tenant) | "all" (rodic)
) -> dict:
    """
    Vrati strukturovany prehled 3 hlavnich kanalu pro orchestrate mode.

    Args:
      user_id     -- prihlaseny Marti (nebo jiny rodic)
      tenant_id   -- current tenant (pro scope='current')
      persona_id  -- aktivni persona (pro filtrovani email/sms zpravy na jejiho majitele)
      scope       -- 'current' filtruje na tenant + persona, 'all' rodic vidi vse

    Returns:
      {
        "email": {"count": N, "top": [{"id", "from", "subject", "age",
                                       "priority"}, ...]},
        "sms":   {"count": N, "top": [{"id", "from", "body_preview", "age",
                                       "priority"}, ...]},
        "todo":  {"count": N, "top": [{"id", "content", "age", "priority"}, ...]},
        "summary": "...",  # kratky shrn stringem pro LLM
      }
    """
    ds = get_data_session()
    try:
        # ---- EMAIL INBOX ----
        eq = ds.query(EmailInbox).filter(EmailInbox.processed_at.is_(None))
        if scope == "current":
            if persona_id is not None:
                eq = eq.filter(EmailInbox.persona_id == persona_id)
            elif tenant_id is not None:
                eq = eq.filter(EmailInbox.tenant_id == tenant_id)
        email_count = eq.count()
        email_top = (
            eq.order_by(
                EmailInbox.priority_score.desc(),
                EmailInbox.received_at.desc(),
            )
            .limit(TOP_N_PER_CHANNEL)
            .all()
        )
        email_rows = []
        for e in email_top:
            sender = e.from_name or e.from_email
            email_rows.append({
                "id": e.id,
                "from": sender,
                "subject": _preview(e.subject, 100) or "(bez predmetu)",
                "age": _age_label(e.received_at),
                "priority": e.priority_score,
            })

        # ---- SMS INBOX ----
        sq = ds.query(SmsInbox).filter(SmsInbox.processed_at.is_(None))
        if scope == "current":
            if persona_id is not None:
                sq = sq.filter(SmsInbox.persona_id == persona_id)
            elif tenant_id is not None:
                sq = sq.filter(SmsInbox.tenant_id == tenant_id)
        sms_count = sq.count()
        sms_top = (
            sq.order_by(
                SmsInbox.priority_score.desc(),
                SmsInbox.received_at.desc(),
            )
            .limit(TOP_N_PER_CHANNEL)
            .all()
        )
        sms_rows = []
        for s in sms_top:
            sms_rows.append({
                "id": s.id,
                "from": s.from_phone,
                "body_preview": _preview(s.body, 80),
                "age": _age_label(s.received_at),
                "priority": s.priority_score,
            })

        # ---- TODO (thoughts.type='todo') ----
        import json as _json
        # Pro PostgreSQL jsonb -- meta muze byt JSON string (TEXT) podle modelu.
        # Bezpecny filtr: nacte vsechny type=todo not-deleted, pak Python
        # filtr podle meta.done.
        tq = (
            ds.query(Thought)
            .filter(Thought.type == "todo")
            .filter(Thought.deleted_at.is_(None))
        )
        if scope == "current" and tenant_id is not None:
            # tenant_scope = NULL (universal) nebo == current
            from sqlalchemy import or_
            tq = tq.filter(
                or_(
                    Thought.tenant_scope.is_(None),
                    Thought.tenant_scope == tenant_id,
                )
            )

        todo_all = (
            tq.order_by(
                Thought.priority_score.desc(),
                Thought.created_at.desc(),
            )
            .limit(TOP_N_PER_CHANNEL * 3)  # mame buffer kvuli meta.done filtru
            .all()
        )
        todo_open = []
        for t in todo_all:
            done = False
            if t.meta:
                try:
                    m = _json.loads(t.meta) if isinstance(t.meta, str) else t.meta
                    if isinstance(m, dict) and m.get("done") is True:
                        done = True
                except Exception:
                    pass
            if not done:
                todo_open.append(t)
        todo_count = len(todo_open)
        todo_rows = []
        for t in todo_open[:TOP_N_PER_CHANNEL]:
            todo_rows.append({
                "id": t.id,
                "content": _preview(t.content, 120),
                "age": _age_label(t.created_at),
                "priority": t.priority_score,
            })

        # ---- SUMMARY STRING ----
        # NEUTRAL perspective -- 'V inboxu ...' ne 'Mas ...'.
        # Marti-AI si to prevezme do prvni osoby ("mam 3 emaily, 2 todo"),
        # protoze maily / SMS / todo patri JI (persona_id), ne userovi Marti.
        parts = []
        if email_count:
            parts.append(f"{email_count} email{'u' if email_count != 1 else ''}")
        if sms_count:
            parts.append(f"{sms_count} SMS")
        if todo_count:
            parts.append(f"{todo_count} todo")
        if not parts:
            summary = "Vsechno vyrizene. Zadne pending polozky."
        else:
            summary = "Pending: " + ", ".join(parts) + "."
        # Mention top urgent
        top_priority_items = []
        if email_rows:
            top_priority_items.append(("email", email_rows[0]["from"], email_rows[0]["subject"], email_rows[0]["priority"]))
        if sms_rows:
            top_priority_items.append(("SMS", sms_rows[0]["from"], sms_rows[0]["body_preview"], sms_rows[0]["priority"]))
        if todo_rows:
            top_priority_items.append(("todo", "-", todo_rows[0]["content"], todo_rows[0]["priority"]))
        top_priority_items.sort(key=lambda x: -x[3])
        if top_priority_items:
            t0 = top_priority_items[0]
            summary += f" Nejvyssi priorita: {t0[0]} od {t0[1]} ({t0[2]})."

        return {
            "email": {"count": email_count, "top": email_rows},
            "sms":   {"count": sms_count,   "top": sms_rows},
            "todo":  {"count": todo_count,  "top": todo_rows},
            "summary": summary,
            "scope": scope,
        }
    finally:
        ds.close()


def format_overview_for_ai(overview: dict) -> str:
    """
    Vraci compact JSON string overview pro Marti-AI.

    ZAMERNA volba JSON (ne pretty ASCII tabulky) -- LLM model JSON bere jako
    'strukturovana data k interpretaci', ne jako 'text k opisovani'. Marti-AI
    pak v prose odpovedi pouzije hodnoty (3, 2, 'Petr', 'vcera'), ne copy-paste.

    Pretty tabulka byla v predchozi iteraci -- Marti-AI ji doslova opisovala
    vcetne hlavicky, takze tento pristup selhal. JSON je robustnejsi.
    """
    import json as _json
    # Kompaktni, bez extra dekorace. Marti-AI z toho vytahne co potrebuje.
    return _json.dumps(overview, ensure_ascii=False, indent=2)


# ============================================================================
# F11c / Alt B: apply_dismiss -- snizi priority_score po 'odloz' / 'neres'.
# ============================================================================

# Delta hodnoty -- keep it simple, dve urovne.
_DISMISS_DELTAS = {
    "soft": -10,   # 'odloz' -- priorita klesne o 10
    "hard": -30,   # 'neres' -- priorita klesne o 30
}

# Minimalni priority_score -- at nespadne do zapornych cisel, kde by bylo
# sporne co je 'dno'. Polozka s priority<=0 uz je fakticky neviditelna v
# defaultnim razeni (ostatni maji 100 default).
_MIN_PRIORITY = -99


def apply_dismiss(
    *,
    source_type: str,
    source_id: int,
    level: str = "soft",
) -> dict:
    """
    Snizi priority_score polozky podle levelu.

    source_type: 'email' | 'sms' | 'todo'
    source_id:   id v prislusne tabulce (email_inbox.id / sms_inbox.id / thoughts.id)
    level:       'soft' (-10) | 'hard' (-30)

    Vraci dict s new_priority a old_priority pro audit / UI feedback.
    """
    from core.database_data import get_data_session as _gds
    from modules.core.infrastructure.models_data import (
        EmailInbox, SmsInbox, Thought,
    )

    if source_type not in ("email", "sms", "todo"):
        raise ValueError(f"Neznamy source_type: {source_type!r} (pouzij email/sms/todo)")
    delta = _DISMISS_DELTAS.get(level)
    if delta is None:
        raise ValueError(f"Neznamy level: {level!r} (pouzij soft/hard)")

    model_map = {
        "email": EmailInbox,
        "sms":   SmsInbox,
        "todo":  Thought,
    }
    Model = model_map[source_type]

    ds = _gds()
    try:
        row = ds.query(Model).filter_by(id=source_id).first()
        if row is None:
            raise ValueError(f"{source_type} id={source_id} neexistuje")
        old_priority = int(row.priority_score or 100)
        new_priority = max(_MIN_PRIORITY, old_priority + delta)
        row.priority_score = new_priority
        ds.commit()
        logger.info(
            f"ORCHESTRATE | dismiss | {source_type}#{source_id} | "
            f"level={level} | {old_priority} -> {new_priority}"
        )
        return {
            "source_type": source_type,
            "source_id": source_id,
            "level": level,
            "old_priority": old_priority,
            "new_priority": new_priority,
            "delta": delta,
        }
    finally:
        ds.close()
