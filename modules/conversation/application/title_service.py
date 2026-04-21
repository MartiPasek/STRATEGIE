"""
Auto-generovani nazvu konverzaci pres Claude Haiku.

Problem: Konverzace v sidebaru mely nazev podle prvni user zpravy (prvnich
60 znaku). Kdyz user zeptal "jake mas persony" 3x v ruznych konverzacich,
vsechny tri mely identicky nazev -- user je neumel rozlisit v dropdownu.

Reseni: Po 2-3 vymenach (user -> AI -> user -> AI) mame dost kontextu,
aby AI slozila informativni nazev (2-5 slov, cesky). Generuje se JEDNOU
per konverzace -- kdyz uz title je ulozen (at uz rucne prejmenovan nebo
predchozim AI volanim), dal se nesaha.

Design:
- maybe_generate_title(conversation_id) -- idempotentni, fail-safe
- Spousti se z chat() po dokonceni requestu (pred return by blokoval UX;
  taky to neni kriticke -- nazev se projevi pri nasledujicim refreshi listu)
- Model: claude-haiku-4-5 (rychly + levny; ~500 tokenu input, 15 tokenu output)
- Cost: ~$0.0001 per konverzace (zanedbatelne)
"""
from __future__ import annotations

import anthropic

from core.config import settings
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import Conversation, Message

logger = get_logger("conversation.title")

# Pocet minimum text-zprav pred generovanim (user + ai + user + ai = 4)
MIN_MESSAGES_FOR_TITLE = 4

# Kolik zprav nacist do promptu (chceme cely zacatek -- tema se obvykle
# objevi v prvnich 4-6 zpravach a pak zustava stabilni)
TRANSCRIPT_WINDOW = 6

TITLE_MODEL = "claude-haiku-4-5-20251001"
MAX_TITLE_LENGTH = 80     # fits do sidebar column bez truncation

SYSTEM_PROMPT = (
    "Jsi nástroj pro generování názvů konverzací. Dostaneš začátek konverzace "
    "mezi uživatelem a AI asistentem a tvým úkolem je vytvořit krátký český "
    "nadpis (2-5 slov) který shrnuje o čem je řeč.\n\n"
    "PRAVIDLA:\n"
    "- Odpověz POUZE tím nadpisem, žádné vysvětlení, žádné uvozovky\n"
    "- 2 až 5 slov, česky\n"
    "- První písmeno velké, ostatní normálně (ne Title Case)\n"
    "- Bez emoji, bez interpunkce na konci\n"
    "- Soustřeď se na TÉMA, ne na to co chce uživatel (ne 'Uživatel se ptá na X' ale 'X')\n\n"
    "PŘÍKLADY:\n"
    "Uzivatel: Pozvi prosím Jonáše Vlka na jonda@example.cz\n"
    "AI: Jasně, pozvánka odeslána.\n"
    "Odpoveď: Pozvánka pro Jonáše Vlka\n\n"
    "Uzivatel: Jak se má restartovat service?\n"
    "AI: Podle runbooku jsou dva způsoby...\n"
    "Odpoveď: Restart STRATEGIE service\n\n"
    "Uzivatel: Jaké máš dostupné persony\n"
    "AI: Mám k dispozici Marti-AI, PrávníkCZ, Honza-AI...\n"
    "Odpoveď: Přehled dostupných person"
)


def maybe_generate_title(conversation_id: int) -> str | None:
    """
    Idempotentne vygeneruje a ulozi nazev konverzace. Vraci nazev pokud byl
    vygenerovan (nebo uz existoval), jinak None.

    Skipne pokud:
      - Konverzace neexistuje
      - Konverzace uz ma title (rucne prejmenovana nebo drive vygenerovana)
      - Pocet textovych zprav < MIN_MESSAGES_FOR_TITLE
    """
    try:
        session = get_data_session()
        try:
            conv = session.query(Conversation).filter_by(id=conversation_id).first()
            if not conv:
                logger.debug(f"TITLE | skip (no conv) | id={conversation_id}")
                return None
            if conv.title:
                logger.debug(f"TITLE | skip (already set) | id={conversation_id} | title={conv.title!r}")
                return conv.title

            messages = (
                session.query(Message)
                .filter_by(conversation_id=conversation_id, message_type="text")
                .order_by(Message.id)
                .limit(TRANSCRIPT_WINDOW)
                .all()
            )
            if len(messages) < MIN_MESSAGES_FOR_TITLE:
                logger.debug(
                    f"TITLE | skip (too few messages) | id={conversation_id} | "
                    f"count={len(messages)} | min={MIN_MESSAGES_FOR_TITLE}"
                )
                return None

            # Sestav transcript (orez content na 500 znaku na zpravu -- long AI replies by
            # neucelne zvedali token cost na title generation)
            transcript_parts = []
            for m in messages:
                role_label = "Uzivatel" if m.role == "user" else "AI"
                content = (m.content or "").strip()
                if len(content) > 500:
                    content = content[:497] + "..."
                transcript_parts.append(f"{role_label}: {content}")
            transcript = "\n\n".join(transcript_parts)
        finally:
            session.close()

        # Volej Claude Haiku
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=TITLE_MODEL,
            max_tokens=30,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": transcript}],
        )
        raw_title = "".join(
            b.text for b in response.content if b.type == "text"
        ).strip()

        # Sanitize
        title = _sanitize_title(raw_title)
        if not title:
            logger.warning(f"TITLE | generated empty | id={conversation_id} | raw={raw_title!r}")
            return None

        # Uloz
        session = get_data_session()
        try:
            conv = session.query(Conversation).filter_by(id=conversation_id).first()
            if conv and not conv.title:   # double-check (race -- user zpujici se mohl stihnout prejmenovat)
                conv.title = title
                session.commit()
                logger.info(f"TITLE | generated | id={conversation_id} | title={title!r}")
                return title
            elif conv and conv.title:
                logger.info(f"TITLE | skip save (user renamed meanwhile) | id={conversation_id}")
                return conv.title
        finally:
            session.close()

    except anthropic.APIError as e:
        logger.warning(f"TITLE | Anthropic API failed | id={conversation_id} | {e}")
    except Exception as e:
        logger.exception(f"TITLE | unexpected error | id={conversation_id} | {e}")
    return None


def _sanitize_title(raw: str) -> str:
    """Cleanup AI vystupu: odstran uvozovky, trim, limit delku."""
    if not raw:
        return ""
    # Odstran leading/trailing uvozovky (AI obcas pridava i pres instrukci).
    # Vsechny beznejsi varianty: " ' „ " ` ‹ › » «
    s = raw.strip()
    for quote_char in ('"', "'", "„", "\u201c", "\u201d", "`", "‹", "›", "»", "«"):
        s = s.strip(quote_char)
    s = s.strip()
    # Odstran "Odpoveď:" / "Nadpis:" prefix pokud AI zapomnela
    for prefix in ("Odpoveď:", "Odpověď:", "Nadpis:", "Title:", "Titul:"):
        if s.lower().startswith(prefix.lower()):
            s = s[len(prefix):].strip()
    # Odstran trailing interpunkci (AI obcas pridá ?)
    s = s.rstrip(".?!,;:")
    # Limit delka
    if len(s) > MAX_TITLE_LENGTH:
        s = s[:MAX_TITLE_LENGTH - 1] + "…"
    return s.strip()
