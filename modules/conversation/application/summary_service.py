"""
Summary service — komprese starší části konverzace.

Spouštění (MVP):
  - po každé odpovědi AI v chat() volá `maybe_create_summary(conversation_id)`
  - funkce je idempotentní: sama ověří podmínky spuštění
  - pokud vytvoří summary, vrátí dict s metadaty; jinak None

Podmínky pro vytvoření:
  - od posledního summary (nebo od začátku konverzace) existuje alespoň
    `SUMMARY_THRESHOLD` nových zpráv

Pokrytí:
  - summary vždy pokrývá rozsah `from_message_id`..`to_message_id`
  - `from_message_id` = ID první zprávy po posledním summary (nebo 1. zpráva)
  - `to_message_id` = ID poslední zprávy v konverzaci v okamžiku volání
  - následné zprávy jsou „recentní detail" v Composeru (ne shrnuté)

Selhání: logujeme, nikdy nepropadne do chat handleru — konverzace nesmí
spadnout kvůli summary chybě.
"""
from datetime import datetime, timezone

import anthropic

from core.config import settings
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    Conversation,
    ConversationSummary,
    Message,
)

logger = get_logger("conversation.summary")

# Threshold: kdy zacit tvorit summary. Historie:
#   10 zprav   -- agresivni, nedostatek detailu (3 vety misto 10 zprav)
#   500 zprav  -- prakticky vypnute, ale dnes uz kontext (pamet + diar + tool
#                 schemas) rychle bobtna, takze u 30+ zprav to skripe i s
#                 Sonnet 4.6 a 450K TPM (Tier 2).
#   40 zprav (dnes) -- rozumny kompromis: u kratkych konverzaci se summary
#                 nevytvori (nikdy vice nez 10-20 zprav pri kratkem ukolu),
#                 u dlouhych dev sessions (40+) uleva.
# Pri zmene pouzivaj notifikaci v UI (SUMMARY_SUGGEST_AT) pro user awareness.
SUMMARY_THRESHOLD = 40

# Pro UI + Marti system prompt: nad timto poctem zprav zacnem signalizovat
# uzivateli, ze je konverzace dlouha a summary se blizi / uz bezi.
SUMMARY_SUGGEST_AT = 30
SUMMARY_MODEL = "claude-haiku-4-5-20251001"
# Output: zvyseno z 300 na 1500 tokenu. 3 vety byly nedostatecne pro e-mailova
# zadani / multi-step pokyny, kde zanikaly konkretni parametry (koho, co, kdy).
# 1500 tokenu = ~10-15 vet shrnuti, prostor i pro vyjmenovani klicovych entit.
SUMMARY_MAX_OUTPUT_TOKENS = 1500

SUMMARY_SYSTEM_PROMPT = (
    "Shrň následující konverzaci věcně a s KONKRÉTNÍMI DETAILY. "
    "Zachyť všechna jména, emaily, telefonní čísla, data, částky a rozhodnutí, "
    "o kterých se mluvilo. Uveď, co uživatel po AI chtěl, co AI slíbila a co "
    "ještě nebylo dokončeno (otevřené úkoly / pendingy). "
    "Neopakuj zdvořilosti ani malé fragmenty. "
    "Rozsah: ideálně 8-15 vět — raději detailněji než zkratkovitě."
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _get_range_to_summarize(
    conversation_id: int,
    min_count: int | None = None,
) -> tuple[int, int, list[Message]] | None:
    """
    Vrátí (from_message_id, to_message_id, messages) pro nové summary,
    nebo None pokud podmínky nejsou splněné.

    min_count: pocet zprav pro spusteni. Default SUMMARY_THRESHOLD.
    """
    if min_count is None:
        min_count = SUMMARY_THRESHOLD
    session = get_data_session()
    try:
        last_summary = (
            session.query(ConversationSummary)
            .filter_by(conversation_id=conversation_id)
            .order_by(ConversationSummary.id.desc())
            .first()
        )
        after_id = last_summary.to_message_id if last_summary else 0

        messages = (
            session.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.id > after_id,
            )
            .order_by(Message.id.asc())
            .all()
        )
        if len(messages) < min_count:
            return None

        # SQLAlchemy objekty odpoj od session, ať je můžeme vrátit a volající
        # nemusí řešit expired attributes po close().
        detached = [
            Message(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                author_type=m.author_type,
                author_user_id=m.author_user_id,
                created_at=m.created_at,
            )
            for m in messages
        ]
        return detached[0].id, detached[-1].id, detached
    finally:
        session.close()


def _format_messages_for_llm(messages: list[Message]) -> str:
    """Složí zprávy do jednoduchého textu pro summary prompt."""
    lines: list[str] = []
    for m in messages:
        role_label = "Uživatel" if m.role == "user" else "Asistent"
        lines.append(f"{role_label}: {m.content}")
    return "\n\n".join(lines)


def _call_llm_for_summary(text: str) -> str:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=SUMMARY_MODEL,
        max_tokens=SUMMARY_MAX_OUTPUT_TOKENS,
        system=SUMMARY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    out = ""
    for block in response.content:
        if block.type == "text":
            out += block.text
    return out.strip()


def _save_summary(
    conversation_id: int,
    from_message_id: int,
    to_message_id: int,
    summary_text: str,
    tenant_id: int | None = None,
    project_id: int | None = None,
) -> int:
    session = get_data_session()
    try:
        row = ConversationSummary(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            project_id=project_id,
            summary_text=summary_text,
            from_message_id=from_message_id,
            to_message_id=to_message_id,
            created_at=_now_utc(),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id
    finally:
        session.close()


def _get_conversation_context(conversation_id: int) -> tuple[int | None, int | None]:
    """Vrátí (tenant_id, project_id) z konverzace — ať summary dědí kontext."""
    session = get_data_session()
    try:
        conv = session.query(Conversation).filter_by(id=conversation_id).first()
        if not conv:
            return None, None
        return conv.tenant_id, conv.project_id
    finally:
        session.close()


def maybe_create_summary(
    conversation_id: int,
    force: bool = False,
    min_messages: int | None = None,
) -> dict | None:
    """
    Hlavní entrypoint. Idempotentní.
    Vrátí info o vytvořeném summary, nebo None pokud nebyly splněny podmínky.

    force=True: ignoruje SUMMARY_THRESHOLD -- vytvori summary i u kratkych
    konverzaci. Pouziva se z AI toolu summarize_conversation_now, kdyz
    user explicitne pozada o zkraceni.

    min_messages: volitelne minimum (default SUMMARY_THRESHOLD). Pri force=True
    se bere default 2 (aby summary mohla vzniknout i z malo zprav).

    Tvar výstupu: {
        "summary_id": int,
        "from_message_id": int,
        "to_message_id": int,
        "message_count": int,
        "summary_text": str,
    }
    """
    try:
        effective_min = min_messages or (2 if force else SUMMARY_THRESHOLD)
        range_info = _get_range_to_summarize(conversation_id, min_count=effective_min)
        if range_info is None:
            return None
        from_id, to_id, messages = range_info

        text_block = _format_messages_for_llm(messages)
        summary_text = _call_llm_for_summary(text_block)
        if not summary_text:
            logger.warning(f"SUMMARY | empty output | conv={conversation_id}")
            return None

        tenant_id, project_id = _get_conversation_context(conversation_id)
        summary_id = _save_summary(
            conversation_id=conversation_id,
            from_message_id=from_id,
            to_message_id=to_id,
            summary_text=summary_text,
            tenant_id=tenant_id,
            project_id=project_id,
        )

        info = {
            "summary_id": summary_id,
            "from_message_id": from_id,
            "to_message_id": to_id,
            "message_count": len(messages),
            "summary_text": summary_text,
        }
        logger.info(
            f"SUMMARY | created | conv={conversation_id} | "
            f"range={from_id}..{to_id} | count={len(messages)} | "
            f"id={summary_id}"
        )
        return info
    except Exception as e:
        logger.exception(f"SUMMARY | failed | conv={conversation_id} | {e}")
        return None
