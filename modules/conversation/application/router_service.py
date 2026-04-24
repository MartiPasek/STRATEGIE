"""
Router service -- Fáze 9.1 multi-mode Marti-AI.

Před hlavním chat() voláním klasifikuje vstupní zprávu do jednoho ze 4 módů:
  - personal : rodinné, osobní, emoční (rodiče, diář, preference, vzpomínky)
  - project  : práce na konkrétním projektu (project_id)
  - work     : obecný pracovní kontext tenantu
  - system   : admin / systémové operace (backup, restore, správa)

Router dostává:
  - text zprávy
  - UI state (active_project_id, active_tenant_id, tenant_type, is_parent, ...)
  - posledních 2-3 zpráv pro kontext (detekce mode shiftu)

Router vrací strukturovaný dict:
  {
    "mode": "personal" | "project" | "work" | "system",
    "confidence": 0.0-1.0,
    "project_id": int | None,
    "reason": "...",
    "secondary_hints": [...]  # pro budoucí multi-label
  }

UI STATE jako PRIOR (Bayesian):
  - active_project_id je set  -> strong prior toward "project"
  - tenant_type='personal'    -> prior toward "personal"
  - is_parent + admin keyword -> possibly "system"

Text zprávy je evidence. Low confidence classifier -> UI wins.
High confidence + contradicting UI -> override (e.g., "co je k večeři"
v aktivním projektu -> personal override).

Model: claude-haiku-4-5-20251001 (levny, rychly, dostatecny pro klasifikaci).
Náklad: ~$0.0003 per call. Bez dopadu na Tier 2 Sonnet TPM bucket.

Fallback při selhání: vrátí mode='personal' s confidence=0. Chat muze pokracovat
v dnešním chování (full Marti-AI with memory block).
"""
from __future__ import annotations
import json
from typing import Any

import anthropic

from core.config import settings
from core.logging import get_logger

logger = get_logger("conversation.router")

ROUTER_MODEL = "claude-haiku-4-5-20251001"
ROUTER_MAX_OUTPUT_TOKENS = 300  # JSON response, stačí bohatě

VALID_MODES = {"personal", "project", "work", "system"}
DEFAULT_MODE = "personal"  # bezpečný fallback — víc kontextu, nic neshodí


ROUTER_SYSTEM_PROMPT = """Jsi router pro AI asistentku Marti-AI. Tvoje jediná práce je klasifikovat vstupní zprávu uživatele do jednoho ze 4 módů podle kontextu konverzace.

MÓDY:

**personal** — rodinné, osobní, emocionální
  Příklady: "co dělá Ondra", "zapiš si, že mám rád kafe", "jaký je tvůj diář",
  "zeptej se maminky", "co je k večeři", "pamatuješ si naši dovolenou"
  Signály: zmínka rodinných příslušníků, emocionální tón, osobní preference,
  diář, paměť obecně, vzpomínky.

**project** — konkrétní projekt (vrať i project_id pokud ho znáš nebo je v UI)
  Příklady: "jak vypadá TISAX", "stav úkolu", "kdo je v projektu STRATEGIE",
  "uprav dokument", "připrav report", "co je rozpracované"
  Signály: název projektu, pracovní úkoly, dokumenty, review, milníky.

**work** — obecný pracovní kontext tenantu (bez konkrétního projektu)
  Příklady: "kdo je v týmu", "jaké máme projekty", "pozvi Ondru", "pošli email klientovi",
  "co je nového v firmě"
  Signály: obecné pracovní dotazy, správa lidí/projektů v tenantu.

**system** — admin / systémové operace
  Příklady: "zálohuj databáze", "restart", "vymaž testovací usery", "jak funguje backup",
  "nastav autosend consent", "kolik konverzací je v systému"
  Signály: admin keywordy (backup, restart, delete, setup, config).

=== UI STATE JAKO PRIOR ===

Input ti dává UI state. Ten je **STRONG PRIOR** — přemýšlej o něm jako o kormidle:

- `active_project_id` je set  -> prior = "project" (zachovej dokud text jasně neříká jinak)
- `tenant_type` = "personal"  -> prior = "personal"
- `active_tenant_id` bez projektu (pracovní tenant) -> prior = "work"
- `is_parent` = true + admin keyword -> zvažuj "system"

=== JAK SE ROZHODNOUT ===

1. Podívej se na UI state -> to je tvůj **default mode**.
2. Přečti si text zprávy -> je tam SILNÝ signál jiného módu?
3. Pokud SILNÝ signál -> override (třeba: aktivní projekt, ale user píše "co máš v deníku" -> personal).
4. Pokud text je ambiguous (např. "jak to vypadá?") -> **UI prior vyhrává**, vrať default mode s high confidence.
5. Pokud vůbec nevíš -> vrať "personal", confidence 0.3 (bezpečný fallback).

=== VÝSTUPNÍ FORMÁT ===

VRAŤ POUZE validní JSON, bez jakéhokoli dalšího textu, bez markdown, bez ```:

{"mode": "personal", "confidence": 0.9, "project_id": null, "reason": "stručné vysvětlení v jedné větě", "secondary_hints": []}

Pole:
- `mode`: jeden z ["personal", "project", "work", "system"]
- `confidence`: 0.0-1.0 (jak si jsi jistý)
- `project_id`: integer pokud mode="project" a znáš ID, jinak null
- `reason`: jedna věta česky, proč jsi takhle klasifikoval
- `secondary_hints`: list[str], budoucí multi-label (dnes můžeš nechat prázdný [])
"""


def _format_recent_messages(recent):
    """
    Naformátuje posledních pár zpráv jako kontext pro router.
    Omezíme na posledních 3-5 zpráv a krátí obsah, ať prompt nebobtná.
    """
    if not recent:
        return "(žádná předchozí historie)"
    lines = []
    for m in recent[-5:]:
        role = m.get("role", "?")
        content = (m.get("content") or "").strip()
        if len(content) > 200:
            content = content[:200] + "..."
        role_label = "Uživatel" if role == "user" else "Marti-AI" if role == "assistant" else role
        lines.append(f"{role_label}: {content}")
    return "\n".join(lines)


def _format_ui_state(ui_state):
    """
    Naformátuje UI state jako čitelný blok pro Haiku.
    """
    if not ui_state:
        return "(žádný UI stav neznámý)"
    parts = []
    for key in [
        "active_tenant_id", "active_tenant_name", "tenant_type",
        "active_project_id", "active_project_name",
        "active_persona_id", "active_persona_name",
        "user_id", "user_name", "is_parent",
    ]:
        if key in ui_state and ui_state[key] is not None:
            parts.append(f"  {key}: {ui_state[key]}")
    return "\n".join(parts) if parts else "(UI state prázdný)"


def _parse_router_output(raw):
    """
    Parsuje JSON z Haiku odpovědi. Robustní — tolerujeme případy kdy
    Haiku zabalí JSON do markdown bloku nebo přidá trailing text.
    Vrací None při nemožnosti parsovat.
    """
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl != -1:
            text = text[first_nl + 1:]
        if text.rstrip().endswith("```"):
            text = text.rsplit("```", 1)[0]
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def _validate_and_normalize(raw_dict, ui_state):
    """
    Validuje pole, nastaví defaults, normalizuje hodnoty.
    """
    mode = (raw_dict.get("mode") or DEFAULT_MODE).lower().strip()
    if mode not in VALID_MODES:
        logger.warning(f"ROUTER | invalid mode '{mode}' -> fallback '{DEFAULT_MODE}'")
        mode = DEFAULT_MODE

    try:
        confidence = float(raw_dict.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    project_id = raw_dict.get("project_id")
    if project_id is not None:
        try:
            project_id = int(project_id)
        except (TypeError, ValueError):
            project_id = None

    if mode == "project" and project_id is None and ui_state:
        ui_pid = ui_state.get("active_project_id")
        if ui_pid:
            try:
                project_id = int(ui_pid)
            except (TypeError, ValueError):
                pass

    reason = str(raw_dict.get("reason") or "")[:500]
    secondary = raw_dict.get("secondary_hints") or []
    if not isinstance(secondary, list):
        secondary = []
    secondary = [str(s)[:100] for s in secondary[:5]]

    return {
        "mode": mode,
        "confidence": round(confidence, 3),
        "project_id": project_id,
        "reason": reason,
        "secondary_hints": secondary,
    }


def classify_mode(
    message,
    ui_state=None,
    recent_messages=None,
    *,
    conversation_id=None,
    tenant_id=None,
    user_id=None,
    persona_id=None,
    is_auto=False,
):
    """
    Hlavni entrypoint. Klasifikuje vstupni zpravu do jednoho ze 4 modu.

    Args:
      message: text od uzivatele (posledni zprava v konverzaci)
      ui_state: dict s UI kontextem -- active_project_id, tenant_type, is_parent, ...
      recent_messages: poslednich par zprav konverzace
      conversation_id: pokud zadano, router zapise svuj LLM call do llm_calls
                       tabulky (kind='router') pro Faze 9.1 Dev View.
                       Pri None (legacy / unit testy) se nezapisuje.

    Returns:
      Dict { "mode", "confidence", "project_id", "reason", "secondary_hints" }

    Failure mode: pri jakekoli chybe vraci fallback s mode='personal', conf=0.
    """
    fallback = {
        "mode": DEFAULT_MODE,
        "confidence": 0.0,
        "project_id": None,
        "reason": "fallback: router selhal nebo nevolan",
        "secondary_hints": [],
    }

    if not message or not message.strip():
        logger.info("ROUTER | empty message -> fallback personal")
        return fallback

    ui_text = _format_ui_state(ui_state)
    history_text = _format_recent_messages(recent_messages)

    user_prompt = (
        f"=== UI STATE ===\n{ui_text}\n\n"
        f"=== POSLEDNI ZPRAVY V KONVERZACI ===\n{history_text}\n\n"
        f"=== AKTUALNI ZPRAVA K KLASIFIKACI ===\n{message.strip()}\n\n"
        "Klasifikuj. Vrat pouze JSON podle formatu v system promptu."
    )

    # Faze 9.1 telemetry -- jen pokud je conversation_id (pouzivat z composeru)
    _telemetry = None
    _t_start = 0
    if conversation_id is not None:
        try:
            from modules.conversation.application import telemetry_service as _telemetry
            _t_start = _telemetry.now_ms()
        except Exception as e:
            logger.warning(f"ROUTER | telemetry import selhal: {e}")
            _telemetry = None

    def _record(response_json, prompt_tokens, output_tokens, error):
        if _telemetry is None or conversation_id is None:
            return
        try:
            _telemetry.record_chat_call(
                conversation_id=conversation_id,
                kind="router",
                model=ROUTER_MODEL,
                request_json=_telemetry.build_request_json(
                    model=ROUTER_MODEL,
                    system=ROUTER_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                    max_tokens=ROUTER_MAX_OUTPUT_TOKENS,
                ),
                response_json=response_json,
                prompt_tokens=prompt_tokens,
                output_tokens=output_tokens,
                latency_ms=_telemetry.now_ms() - _t_start,
                error=error,
                tenant_id=tenant_id,
                user_id=user_id,
                persona_id=persona_id,
                is_auto=is_auto,
            )
        except Exception as te:
            logger.warning(f"ROUTER | telemetry zapis selhal: {te}")

    try:
        if not settings.anthropic_api_key:
            logger.warning("ROUTER | anthropic_api_key missing -> fallback")
            return fallback

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=ROUTER_MODEL,
            max_tokens=ROUTER_MAX_OUTPUT_TOKENS,
            system=ROUTER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIError as e:
        logger.warning(f"ROUTER | API error | {e} -> fallback")
        _record(None, None, None, str(e))
        return fallback
    except Exception as e:
        logger.exception(f"ROUTER | unexpected | {e} -> fallback")
        _record(None, None, None, str(e))
        return fallback

    # Zapis do llm_calls pri uspechu
    _prompt_tokens = getattr(response.usage, "input_tokens", None) if hasattr(response, "usage") else None
    _output_tokens = getattr(response.usage, "output_tokens", None) if hasattr(response, "usage") else None
    _resp_json = None
    if _telemetry is not None:
        try:
            _resp_json = _telemetry.serialize_anthropic_response(response)
        except Exception as e:
            logger.warning(f"ROUTER | response serialize selhal: {e}")
    _record(_resp_json, _prompt_tokens, _output_tokens, None)

    # Extrahuj text z response content (prvni text block)
    raw_text = ""
    for block in response.content:
        if block.type == "text":
            raw_text += block.text
    raw_text = raw_text.strip()

    parsed = _parse_router_output(raw_text)
    if parsed is None:
        logger.warning(
            f"ROUTER | unparseable output | raw='{raw_text[:200]}' -> fallback"
        )
        return fallback

    result = _validate_and_normalize(parsed, ui_state)
    logger.info(
        f"ROUTER | mode={result['mode']} | conf={result['confidence']} | "
        f"project_id={result['project_id']} | reason='{result['reason'][:80]}'"
    )
    return result


# -- PRIOR-ONLY HELPER (bez LLM call) -----------------------------------------
# Uzitecne pro testy a fallback scenare, kdy je ANTHROPIC_API_KEY nedostupny.

def infer_prior_mode(ui_state):
    """
    Deterministicka klasifikace jen z UI state, bez volani LLM.
    Vraci stejnou strukturu jako classify_mode(), ale pouze podle UI priors.
    """
    if not ui_state:
        return {
            "mode": DEFAULT_MODE,
            "confidence": 0.3,
            "project_id": None,
            "reason": "prior-only: prazdny UI state",
            "secondary_hints": [],
        }

    project_id = ui_state.get("active_project_id")
    tenant_type = ui_state.get("tenant_type") or ""
    tenant_id = ui_state.get("active_tenant_id")

    if project_id:
        try:
            pid = int(project_id)
        except (TypeError, ValueError):
            pid = None
        return {
            "mode": "project",
            "confidence": 0.7,
            "project_id": pid,
            "reason": "prior-only: UI ma aktivni projekt",
            "secondary_hints": [],
        }

    if tenant_type == "personal":
        return {
            "mode": "personal",
            "confidence": 0.7,
            "project_id": None,
            "reason": "prior-only: osobni tenant",
            "secondary_hints": [],
        }

    if tenant_id:
        return {
            "mode": "work",
            "confidence": 0.5,
            "project_id": None,
            "reason": "prior-only: pracovni tenant bez projektu",
            "secondary_hints": [],
        }

    return {
        "mode": DEFAULT_MODE,
        "confidence": 0.3,
        "project_id": None,
        "reason": "prior-only: zadny kontext, fallback personal",
        "secondary_hints": [],
    }
