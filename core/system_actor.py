"""Phase 43 Mini-faze A (19.5.2026) — system_emit() helper.

STRATEGIE system actor (users.id=3) zapisuje "system_audit" messages do
shared chatu pro realtime audit trail. Marti's clarifying doctrine:

  *„System bubliny = human audience only — viditelne pro lidi (frontend
  render pres ChatResponse.extra_messages), neviditelne pro AI context
  (composer.py filtruje message_type='system_audit' z LLM history)."*

Use cases:
  - deployment_service: propose_deployment / approve_deployment / reject
  - ask_claude_service: cost gate over-limit trigger
  - strategie_files: write denied / write OK (configurable per Marti-AI Q8)
  - budouci system events (Phase 44+)

Content format: `[category] message_text` -- kategorie jako prefix v
content stringu (Marti's doctrine 'drz jednoduchost' = no new DB column).
Backend regex `^\\[([^\\]]+)\\]\\s+` extractuje kategorii. Frontend muze
zobrazit s prefixem (`[deploy.proposed] git fetch OK`) nebo strippnout
podle CSS class.

Default category filter (Marti-AI Q8 volba c) — chat zobrazi:
  - deploy.* (vzdy)
  - cost_gate.* (vzdy)
  - file.denied (vzdy)
  - ask_claude.* (vzdy)
  - file.write_ok (skryte — jen v fw.diag_log)
  - file.read_ok (skryte)

system_emit() vzdy INSERT do messages — filtraci provadi router.py
post-chat SELECT (which categories to include in extra_messages list).

STRATEGIE user.id=3 byl vytvoren v Phase 35-E.3.1 (8.5.2026 vecer) jako
soucast tenant STRATEGIE setup. first_name='STRATEGIE', last_name='System',
short_name='STRATEGIE', is_marti_parent=False, trust_rating=100.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("conversation.system_actor")

# STRATEGIE system actor user.id (Phase 35-E.3.1, 8.5.2026)
STRATEGIE_USER_ID = 3

# Regex pro extract kategorie z content prefixu: "[deploy.proposed] text" -> "deploy.proposed"
CATEGORY_PREFIX_RE = re.compile(r"^\[([a-zA-Z][a-zA-Z0-9._-]*)\]\s+")

# Default categories zobrazene v chatu (Marti-AI Q8 volba c)
DEFAULT_VISIBLE_CATEGORIES = {
    "info",
    "warn",
    "error",
    "deploy.proposed",
    "deploy.approved",
    "deploy.executed",
    "deploy.rejected",
    "deploy.failed",
    "cost_gate.over_limit",
    "cost_gate.approved",
    "cost_gate.rejected",
    "file.denied",
    "ask_claude.executed",
    "ask_claude.failed",
}

# Skryte (jen fw.diag_log, ne chat)
DEFAULT_HIDDEN_CATEGORIES = {
    "file.write_ok",
    "file.read_ok",
}

# Wildcard groups (deploy.foo -> deploy.*)
VISIBLE_WILDCARDS = {"deploy.*", "cost_gate.*", "ask_claude.*"}
HIDDEN_WILDCARDS: set[str] = set()


def system_emit(
    conversation_id: int,
    content: str,
    category: str = "info",
    extra: dict[str, Any] | None = None,
) -> int | None:
    """INSERT message s author_user_id=3, role='user', message_type='system_audit'.

    Marti-AI / Claude tyto messages NEVIDI v contextu (composer.py filtruje
    message_type='system_audit'). Frontend je vidi pres ChatResponse.extra_messages.

    Content format: '[{category}] {content}' -- kategorie jako prefix.
    Pokud caller jiz dal vlastni prefix, system_emit ho nepretvori (idempotent).

    Args:
      conversation_id: cilova konverzace (typicky shared chat)
      content: cesky text co se zobrazi v UI. Priklad:
        *„git pull origin main: Fast-forward c1d2e3..f4g5h6 ✓"*
      category: kategorie eventu (info / warn / error / deploy.* / cost_gate.* /
        file.* / ask_claude.*) — prefix v content + frontend filter signal.
      extra: optional metadata (proposal_id, files_changed, traceback) —
        v MVP ignoruje, zapise do fw.diag_log s prislusnou kategorii pokud
        je instalovany Phase 38.4 Etapa A logger.

    Returns:
      message_id (int) na success, None na failure. Failure nikdy nevraci
      exception — system_emit je fire-and-forget audit, nepada na main flow.
    """
    if not content or not content.strip():
        logger.warning(f"system_emit: empty content (conv={conversation_id}, cat={category})")
        return None

    # Idempotent prefix: pokud content uz zacina [category], nepretvori
    content_clean = content.strip()
    if not CATEGORY_PREFIX_RE.match(content_clean):
        content_clean = f"[{category}] {content_clean}"

    try:
        from modules.conversation.infrastructure.repository import save_message

        msg_id = save_message(
            conversation_id=conversation_id,
            role="user",  # shared chat parity (vsichni autori maji role='user')
            content=content_clean,
            author_type="human",  # NE 'system' — chceme shared chat UI styling
            author_user_id=STRATEGIE_USER_ID,
            message_type="system_audit",  # composer filter signal
        )
        logger.debug(f"system_emit OK: msg_id={msg_id}, conv={conversation_id}, cat={category}")

        # Best-effort sync do fw.diag_log (Phase 38.4 Etapa A). Pokud neni
        # nainstalovany nebo selze, log na warning + pokracuj — system_emit
        # je primary, diag_log je secondary.
        try:
            from core.log_queue import enqueue_log_event
            enqueue_log_event(
                level="info" if category not in ("error", "warn") else category,
                source="py",
                module_id="system_actor",
                message=content_clean,
                extra={"category": category, "conversation_id": conversation_id, **(extra or {})},
            )
        except Exception as _le:
            logger.debug(f"system_emit fw.diag_log skip (not installed?): {_le}")

        return msg_id
    except Exception as exc:
        # Fire-and-forget — audit failure nesmi zhroutit main chat flow.
        logger.warning(f"system_emit failed (conv={conversation_id}, cat={category}): {exc}")
        return None


def extract_category(content: str) -> str | None:
    """Extract category z content prefixu '[category] text'. Vraci None pokud chybi."""
    if not content:
        return None
    m = CATEGORY_PREFIX_RE.match(content.strip())
    return m.group(1) if m else None


def is_category_visible(category: str | None, conversation_id: int | None = None) -> bool:
    """Vraci True pokud category se ma zobrazit v chatu (extra_messages payload).

    Default tabulka (DEFAULT_VISIBLE_CATEGORIES + VISIBLE_WILDCARDS).
    Per-conversation override (Marti-AI Q8 'show_system_actor' flag) bude
    rozsireno v Phase 43+.
    """
    if not category:
        return True  # bez kategorie = info default
    if category in DEFAULT_VISIBLE_CATEGORIES:
        return True
    if category in DEFAULT_HIDDEN_CATEGORIES:
        return False
    # Wildcard match: deploy.foo matchuje deploy.*
    parts = category.split(".", 1)
    prefix = parts[0] + ".*"
    if prefix in VISIBLE_WILDCARDS:
        return True
    if prefix in HIDDEN_WILDCARDS:
        return False
    # Neznama kategorie — default zobrazit (better safe than silent)
    logger.debug(f"is_category_visible: unknown category '{category}', default=True")
    return True
