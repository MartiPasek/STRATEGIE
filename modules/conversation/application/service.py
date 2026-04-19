"""
Conversation service s Execution layer.
Každý uživatel má svůj vlastní chat. Přepínání person místo sdílených konverzací.
"""
import json
import re
import anthropic

from core.config import settings
from core.database_data import get_data_session
from core.logging import get_logger
from modules.conversation.application.composer import build_prompt
from modules.conversation.application.tools import (
    TOOLS, format_email_preview, find_user_in_system,
    invite_user_to_strategie, switch_persona_for_user,
    get_user_default_persona_name, switch_tenant_for_user,
    get_user_default_tenant_id,
)
from modules.conversation.infrastructure.repository import (
    create_conversation,
    save_message,
    get_messages,
)
from modules.core.infrastructure.models_data import ActionLog, Message, PendingAction

logger = get_logger("conversation")

MODEL = "claude-haiku-4-5-20251001"

CONFIRM_KEYWORDS = {
    # jednoslovná potvrzení
    "ano", "jo", "jojo", "joo", "jj", "ja",
    "pošli", "posli", "odeslat", "poslat",
    "ok", "oky", "okay",
    "jasně", "jasne", "jasný", "jasny", "jasan", "jasnačka",
    "můžeš", "muzes", "můžem", "muzem",
    "klidně", "klidne",
    "souhlas", "potvrzuji", "potvrdit", "schvaluji",
    "yes", "send", "yep", "yeah", "sure", "yup",
    # běžné krátké fráze
    "tak jo", "tak ano",
    "ano pošli", "ano posli", "ano odeslat",
    "jo pošli", "jo posli",
    "pošli to", "posli to",
    "ok pošli", "ok posli",
    "můžeš poslat", "muzes poslat",
    "můžeš odeslat", "muzes odeslat",
}


def _is_confirmation(text: str) -> bool:
    # Normalizace: malá písmena, bez okolních mezer a běžné interpunkce na konci.
    cleaned = text.strip().lower().rstrip(".!?,;:")
    if "@" in cleaned:
        return False
    if len(cleaned) > 30:
        return False
    return cleaned in CONFIRM_KEYWORDS


def _looks_like_email_preview(text: str) -> bool:
    """
    Heuristika: rozpozná text, který vypadá jako email preview
    (ať už legitimní z format_email_preview, nebo Claudeho mimikry).
    Používá se v detekci, zda bylo poslední AI sdělení preview.
    """
    if not text:
        return False
    low = text.lower()
    if "mohu email odeslat" in low or "mám email odeslat" in low or "mám ho odeslat" in low:
        return True
    if "📧" in text and "návrh emailu" in low:
        return True
    return False


def _last_assistant_message_looks_like_email_preview(conversation_id: int) -> bool:
    """
    True, pokud POSLEDNÍ zpráva od asistenta v konverzaci vypadá jako email
    preview. Rozhodující signál pro zabezpečení potvrzovací větve:
    pokud „ano" přichází těsně po preview, ale v DB chybí pending,
    nedovolíme Claude halucinovat úspěšné odeslání.
    """
    session = get_data_session()
    try:
        last = (
            session.query(Message)
            .filter_by(conversation_id=conversation_id, role="assistant")
            .order_by(Message.id.desc())
            .first()
        )
        if not last:
            return False
        return _looks_like_email_preview(last.content)
    finally:
        session.close()


# ── PERSONA SWITCH — SERVER-SIDE INTENT DETECTION ─────────────────────────
# Spouštěče, které VŽDY vedou k zavolání switch_persona toolu bez ohledu
# na LLM. Claude Haiku občas ignoruje tool call a odpověď halucinuje, takže
# nejspolehlivější řešení je pro explicitní příkazy Claude úplně obejít.

_PERSONA_SWITCH_PATTERNS = [
    # "přepni [mi/mě/se] na X" / + tolerance k překlepům "n X" místo "na X"
    re.compile(r"^\s*p[rř]epni\s+(?:(?:m[eě]|mi|mne|si|se)\s+)?n[aA]?\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*p[rř]epnout\s+(?:(?:m[eě]|mi|mne|si|se)\s+)?n[aA]?\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*spoj\s+m[eě]\s+s\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*chci\s+mluvit\s+s\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*mluv\s+jako\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*switch\s+to\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
]

# "přepni zpět" / "na mě" / "na moji" / "původní" / "výchozí" — návrat do
# uživatelovy výchozí persony (jeho digitálního dvojčete).
# Přípustná kratičká slova mezi slovesem a cílem: mi, mě, me, mne, si, se.
_ME_PRON = r"(?:m[eě]|mi|mne|si|se)"
_PERSONA_RESET_PATTERNS = [
    re.compile(rf"^\s*p[rř]epni\s+(?:{_ME_PRON}\s+)?(?:zp[eě]t|zp[aá]tky)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(
        rf"^\s*p[rř]epni\s+(?:{_ME_PRON}\s+)?n[aA]?\s+"
        r"(?:m[eě]|mne|moji|sv[oé]ho|sv[eé]|p[uů]vodn[ií]|v[yý]choz[ií])"
        r"(?:-?ai)?\s*[.!?]?\s*$",
        re.IGNORECASE,
    ),
    re.compile(r"^\s*chci\s+(?:zp[eě]t|zp[aá]tky)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(rf"^\s*vra[tť]\s+(?:{_ME_PRON}\s+)?zp[eě]t\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*zp[aá]tky\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*zp[eě]t\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*back\s+to\s+(?:me|default)\s*[.!?]?\s*$", re.IGNORECASE),
]


def _detect_persona_reset(text: str) -> bool:
    """True, pokud user chce zpět na svou výchozí personu."""
    if not text:
        return False
    if len(text.strip().split()) > 5:
        return False
    for pat in _PERSONA_RESET_PATTERNS:
        if pat.match(text):
            return True
    return False


# ── TENANT SWITCH — SERVER-SIDE INTENT DETECTION ──────────────────────────
# „přepni do EUROSOFTu", „chci do DOMA", „switch to EUR"
# Klíčový rozdíl od persona switche: PŘEDLOŽKA „do" (tenant) vs. „na" (persona).
# Tj. „přepni na Marti" = persona, „přepni do EUROSOFTu" = tenant.

_TENANT_SWITCH_PATTERNS = [
    re.compile(r"^\s*p[rř]epni\s+(?:m[eě]\s+|me\s+|mi\s+|mne\s+|si\s+|se\s+)?do\s+(?:tenantu\s+)?(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*p[rř]epnout\s+(?:m[eě]\s+|me\s+|mi\s+|mne\s+|si\s+|se\s+)?do\s+(?:tenantu\s+)?(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*chci\s+do\s+(?:tenantu\s+)?(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*jdi\s+do\s+(?:tenantu\s+)?(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*switch\s+to\s+(?:tenant\s+)?(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*go\s+to\s+(?:tenant\s+)?(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
]


def _detect_tenant_switch(text: str) -> str | None:
    """
    Vrátí target tenant string, nebo None.
    Pozor: kontroluje předložku 'do' (tenant), ne 'na' (persona).
    """
    if not text:
        return None
    if len(text.strip().split()) > 6:
        return None
    for pat in _TENANT_SWITCH_PATTERNS:
        m = pat.match(text)
        if m:
            target = m.group(1).strip()
            # ořízni eventuální "u" suffix u akuzativ ("EUROSOFTu" → "EUROSOFT")
            # to zlepší matching, ale není kritické — fuzzy matcher v switch_tenant
            # to zvládne i tak.
            return target or None
    return None


def _detect_persona_switch(text: str) -> str | None:
    """
    Vrátí extrahovaný cíl přepnutí (název persony), nebo None.
    Porovnává jen krátké explicitní příkazy; dlouhé věty nechává Claude.
    """
    if not text:
        return None
    if len(text.strip().split()) > 6:
        return None
    for pat in _PERSONA_SWITCH_PATTERNS:
        m = pat.match(text)
        if m:
            target = m.group(1).strip()
            # ořízni běžné suffixy / koncovky
            target = re.sub(r"-?ai$", "", target, flags=re.IGNORECASE).strip()
            return target or None
    return None


def _save_pending_action(conversation_id: int, action_type: str, payload: dict) -> None:
    session = get_data_session()
    try:
        session.query(PendingAction).filter_by(conversation_id=conversation_id).delete()
        action = PendingAction(conversation_id=conversation_id, action_type=action_type, payload=json.dumps(payload))
        session.add(action)
        session.commit()
    finally:
        session.close()


def _get_pending_action(conversation_id: int) -> dict | None:
    session = get_data_session()
    try:
        action = session.query(PendingAction).filter_by(conversation_id=conversation_id).first()
        if not action:
            return None
        return {"type": action.action_type, **json.loads(action.payload)}
    finally:
        session.close()


def _delete_pending_action(conversation_id: int) -> None:
    session = get_data_session()
    try:
        session.query(PendingAction).filter_by(conversation_id=conversation_id).delete()
        session.commit()
    finally:
        session.close()


def _log_email_action(
    to: str,
    subject: str,
    body: str,
    status: str,
    user_id: int | None,
    conversation_id: int,
    error: str | None = None,
) -> None:
    """
    Zaloguje přesný obsah odeslaného (nebo selhaného) emailu do action_logs.
    Kritické pro audit — musí být možné zpětně ověřit, co přesně se odeslalo.
    """
    session = get_data_session()
    try:
        log = ActionLog(
            user_id=user_id,
            action_type="confirm",
            tool_name="send_email",
            input=json.dumps(
                {"to": to, "subject": subject, "body": body, "conversation_id": conversation_id},
                ensure_ascii=False,
            ),
            output=f"to={to} | chars={len(body)}" + (f" | error={error}" if error else ""),
            status=status,
            error_message=error,
            approval_required=True,
            approved_by=user_id,
        )
        session.add(log)
        session.commit()
    except Exception as e:
        logger.error(f"AUDIT | action_log failed: {e}")
    finally:
        session.close()


def _build_email_sent_message(to: str, body: str) -> str:
    """
    Potvrzovací text pro UI — krátký a bez balastu.
    Kompletní tělo se ukládá do action_logs pro zpětnou auditaci.
    """
    return "✅ Email odeslán"


def _execute_pending_action(conversation_id: int, user_id: int | None = None) -> str | None:
    action = _get_pending_action(conversation_id)
    if not action:
        return None
    _delete_pending_action(conversation_id)
    if action["type"] == "send_email":
        from modules.notifications.application.email_service import send_email
        to = action["to"]
        subject = action["subject"]
        body = action["body"]
        try:
            sent = send_email(to=to, subject=subject, body=body)
        except Exception as e:
            _log_email_action(to, subject, body, "error", user_id, conversation_id, error=str(e))
            return "❌ Email se nepodařilo odeslat."
        if sent:
            _log_email_action(to, subject, body, "success", user_id, conversation_id)
            return _build_email_sent_message(to, body)
        _log_email_action(to, subject, body, "error", user_id, conversation_id, error="send_email returned False")
        return "❌ Email se nepodařilo odeslat."
    return None


def _handle_tool(tool_name: str, tool_input: dict, conversation_id: int, user_id: int | None = None) -> str:
    logger.info(f"TOOL | name={tool_name}")

    if tool_name == "send_email":
        _save_pending_action(conversation_id, "send_email", {
            "to": tool_input.get("to", ""),
            "subject": tool_input.get("subject", ""),
            "body": tool_input.get("body", ""),
        })
        return format_email_preview(
            to=tool_input.get("to", ""),
            subject=tool_input.get("subject", ""),
            body=tool_input.get("body", ""),
        )

    if tool_name == "find_user":
        query = tool_input.get("query", "")
        result = find_user_in_system(query=query, requester_user_id=user_id)
        candidates = result.get("candidates", [])
        total = result.get("total_matches", 0)

        # 0 výsledků
        if not candidates:
            return (
                f"❌ '{query}' není v aktuálním tenantu.\n\n"
                f"Chceš ho/ji pozvat? (pokud znáš email)"
            )

        # 1 výsledek — přímá odpověď
        if len(candidates) == 1:
            c = candidates[0]
            name = c.get("display_name") or c.get("full_name") or "—"
            email = c.get("preferred_email") or "(bez emailu)"
            role = c.get("role_label")
            role_part = f", {role}" if role else ""
            return (
                f"✅ {name}{role_part} je v aktuálním tenantu.\n"
                f"Email: {email}\n\n"
                f"Chceš poslat email nebo přepnout na {name}-AI?"
            )

        # 2+ výsledků — disambiguation
        lines = [f"Našel/a jsem {total} kandidátů odpovídajících '{query}':"]
        for i, c in enumerate(candidates, 1):
            name = c.get("display_name") or c.get("full_name") or "—"
            email = c.get("preferred_email") or "(bez emailu)"
            role = c.get("role_label")
            role_part = f" — {role}" if role else ""
            lines.append(f"  {i}. {name}{role_part} ({email})")
        if result.get("has_more"):
            extra = total - len(candidates)
            lines.append(f"  ... a dalších {extra}. Zúpresni jméno.")
        lines.append("\nKterého máš na mysli?")
        return "\n".join(lines)

    if tool_name == "invite_user":
        email = tool_input.get("email", "")
        result = invite_user_to_strategie(email=email, name=tool_input.get("name", ""), invited_by_user_id=user_id or 1)
        if result["success"] and result["email_sent"]:
            return f"✅ Pozvánka odeslána na {email}."
        return f"⚠️ Pozvánka vytvořena ale email se nepodařilo odeslat na {email}."

    if tool_name == "switch_persona":
        query = tool_input.get("query", "")
        result = switch_persona_for_user(query=query, conversation_id=conversation_id)
        if result["found"]:
            name = result["persona_name"]
            return (
                f"✅ Přepnuto na {name}.\n\n"
                f"Nyní mluvíš s {name}. Jak ti mohu pomoci?"
            )
        else:
            return (
                f"❌ Personu '{query}' jsem nenašel/a v systému.\n\n"
                f"Dostupné persony jsou ty, které jsou nastavené v STRATEGIE. "
                f"Chceš pokračovat s výchozí personou?"
            )

    return ""


def chat(
    conversation_id: int | None,
    user_message: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
) -> tuple[int, str, dict | None]:
    """
    Vrátí (conversation_id, reply, summary_info).
    `summary_info` je None pokud se v tomto cyklu summary nevytvořilo,
    jinak dict s metadaty o nově vytvořeném shrnutí (pro UI banner).
    """

    if conversation_id is None:
        conversation_id = create_conversation(user_id=user_id)

    if _is_confirmation(user_message):
        pending = _get_pending_action(conversation_id)
        if pending:
            # Skutečná pending akce existuje — vykonej a potvrď.
            save_message(conversation_id, role="user", content=user_message)
            result = _execute_pending_action(conversation_id, user_id=user_id)
            if result:
                save_message(conversation_id, role="assistant", content=result)
                return conversation_id, result, None
        elif _last_assistant_message_looks_like_email_preview(conversation_id):
            # Bezpečnostní stopka: poslední AI odpověď sice vypadala jako
            # email preview, ale v DB není žádná pending akce (Claude ji
            # jen napsal, tool nezavolal). Nesmíme pustit Claude na tuhle
            # větev — napsal by „✅ Email odeslán" jako text a uživatel by
            # byl přesvědčen, že email odešel. Reálně by se neodeslalo nic.
            save_message(conversation_id, role="user", content=user_message)
            reply = (
                "❌ Žádný email nebyl systémově připraven k odeslání.\n\n"
                "Napiš znovu explicitně, co mám poslat, např.:\n"
                "„pošli email m.pasek@eurosoft.com — Ahoj Marti, …"
            )
            save_message(conversation_id, role="assistant", content=reply)
            return conversation_id, reply, None
        # Jinak (ano bez pendingu a bez email kontextu) = běžné potvrzení,
        # nechej to dojít k Claude standardní cestou.

    save_message(conversation_id, role="user", content=user_message)

    # ── Explicitní TENANT switch ───────────────────────────────────────
    # „přepni do EUROSOFTu", „chci do DOMA", „switch to EUR".
    # Předložka 'do' (tenant) vs. 'na' (persona) — patterny se nekříží.
    if user_id:
        tenant_target = _detect_tenant_switch(user_message)
        if tenant_target:
            logger.info(
                f"TENANT | switch_intent | user={user_id} | target={tenant_target!r}"
            )
            result = switch_tenant_for_user(user_id=user_id, query=tenant_target)
            if result.get("found"):
                name = result["tenant_name"]
                code = result.get("tenant_code") or ""
                code_part = f" ({code})" if code else ""
                if result.get("already_active"):
                    reply = f"✅ Už jsi v tenantu {name}{code_part}."
                else:
                    reply = (
                        f"✅ Přepnuto do tenantu {name}{code_part}.\n\n"
                        f"Od této zprávy s tebou pracuju v tomto kontextu."
                    )
            elif result.get("ambiguous"):
                lines = ["Mám víc tenantů odpovídajících tvému zadání:"]
                for i, c in enumerate(result["candidates"], 1):
                    lines.append(f"  {i}. {c['tenant_name']} ({c['tenant_code'] or '—'})")
                lines.append("\nUveď přesnější jméno nebo kód.")
                reply = "\n".join(lines)
            elif result.get("no_memberships"):
                reply = (
                    "❌ Nejsi členem žádného aktivního tenantu.\n\n"
                    "Kontaktuj admina, aby tě někam přidal."
                )
            else:
                reply = (
                    f"❌ Tenant '{tenant_target}' nenalezen "
                    f"(nebo nemáš ke kterému členství)."
                )
            save_message(conversation_id, role="assistant", content=reply)
            return conversation_id, reply, None

    # ── Explicitní persona switch ───────────────────────────────────────
    # Claude občas tool call přeskočí, takže na jednoznačné příkazy
    # reagujeme servisně bez LLM.
    # Pořadí: nejdřív reset (návrat na výchozí personu), pak obecný switch.

    switch_target: str | None = None

    if user_id and _detect_persona_reset(user_message):
        logger.info(f"PERSONA | reset_intent detected | user={user_id} | conv={conversation_id}")

        # „Přepni zpět" = vrať VŠE k defaultu — personu i tenant.
        # Tenant: zpátky na personal tenant uživatele.
        default_tenant_id = get_user_default_tenant_id(user_id)
        if default_tenant_id is not None:
            from core.database_core import get_core_session as _gcs
            from modules.core.infrastructure.models_core import User as _User
            _s = _gcs()
            try:
                _u = _s.query(_User).filter_by(id=user_id).first()
                if _u and _u.last_active_tenant_id != default_tenant_id:
                    _u.last_active_tenant_id = default_tenant_id
                    _s.commit()
                    logger.info(
                        f"TENANT | reset to default | user={user_id} | tenant={default_tenant_id}"
                    )
            finally:
                _s.close()

        default_name = get_user_default_persona_name(user_id)
        if default_name:
            switch_target = default_name
        else:
            reply = (
                "❌ Nemám pro tebe nastavenou výchozí personu.\n\n"
                "Zkus uvést konkrétní jméno (např. 'přepni na Marti')."
            )
            save_message(conversation_id, role="assistant", content=reply)
            return conversation_id, reply, None

    if switch_target is None:
        switch_target = _detect_persona_switch(user_message)

    if switch_target:
        logger.info(f"PERSONA | switch_intent | target={switch_target!r} | conv={conversation_id}")
        result = switch_persona_for_user(query=switch_target, conversation_id=conversation_id)
        if result.get("found"):
            name = result["persona_name"]
            reply = f"✅ Přepnuto na {name}.\n\nNyní mluvíš s {name}. Jak ti mohu pomoci?"
        else:
            # Fallback — uživatel mohl říct „přepni na EUROSOFT" pro tenant
            # (intuitivní — předložka 'na' obvykle pro persony, ale lidé to
            # mixují). Zkus tedy tenant switch se stejným query.
            tenant_fallback = None
            if user_id:
                tenant_fallback = switch_tenant_for_user(user_id=user_id, query=switch_target)
            if tenant_fallback and tenant_fallback.get("found"):
                tname = tenant_fallback["tenant_name"]
                tcode = tenant_fallback.get("tenant_code") or ""
                code_part = f" ({tcode})" if tcode else ""
                if tenant_fallback.get("already_active"):
                    reply = f"✅ Už jsi v tenantu {tname}{code_part}."
                else:
                    reply = (
                        f"✅ Přepnuto do tenantu {tname}{code_part}.\n\n"
                        f"Od této zprávy s tebou pracuju v tomto kontextu."
                    )
            elif tenant_fallback and tenant_fallback.get("ambiguous"):
                lines = ["Mám víc tenantů odpovídajících tvému zadání:"]
                for i, c in enumerate(tenant_fallback["candidates"], 1):
                    lines.append(f"  {i}. {c['tenant_name']} ({c['tenant_code'] or '—'})")
                lines.append("\nUveď přesnější jméno nebo kód.")
                reply = "\n".join(lines)
            else:
                reply = (
                    f"❌ Nenašel/a jsem '{switch_target}' — ani jako personu, ani jako tenant.\n\n"
                    f"Zkus přesnější jméno."
                )
        save_message(conversation_id, role="assistant", content=reply)
        return conversation_id, reply, None

    system_prompt, messages = build_prompt(conversation_id)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
        tools=TOOLS,
    )

    assistant_reply = ""
    for block in response.content:
        logger.info(f"BLOCK | type={block.type}")
        if block.type == "text":
            assistant_reply += block.text
        elif block.type == "tool_use":
            logger.info(f"TOOL_USE | name={block.name}")
            tool_result = _handle_tool(block.name, block.input, conversation_id, user_id=user_id)
            assistant_reply += tool_result

    if not assistant_reply:
        assistant_reply = "Promiň, něco se pokazilo. Zkus to znovu."

    save_message(conversation_id, role="assistant", content=assistant_reply)
    logger.info(f"CONVERSATION | chat | conversation_id={conversation_id} | user_id={user_id}")

    try:
        from modules.memory.application.service import extract_and_save
        all_messages = get_messages(conversation_id)
        extract_and_save(conversation_id=conversation_id, messages=all_messages, user_id=user_id)
    except Exception as e:
        logger.error(f"MEMORY | failed: {e}")

    # Summary job — idempotentní, sám si ověří podmínky spuštění.
    # Běží synchronně (přidá malou latenci při překročení prahu), ale je
    # robustní vůči chybám: návrat None při jakékoli výjimce.
    summary_info: dict | None = None
    try:
        from modules.conversation.application.summary_service import maybe_create_summary
        summary_info = maybe_create_summary(conversation_id)
    except Exception as e:
        logger.error(f"SUMMARY | failed: {e}")

    return conversation_id, assistant_reply, summary_info
