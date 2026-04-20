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


# ── PROJECT SWITCH — SERVER-SIDE INTENT DETECTION ─────────────────────────
# „přepni do projektu Skoda", „jdi na projekt Reorg Q2", „switch to project X"
# Klicovy rozdil od tenant switche: MUSI obsahovat slovo "projekt" / "project".
# Detekce projektu MA prednost pred tenant switchem — slovo "projekt" je
# specificke (kdyby bylo jen "do EUROSOFTu", padlo by to do tenant detekce).

_PROJECT_SWITCH_PATTERNS = [
    re.compile(r"^\s*p[rř]epni\s+(?:(?:m[eě]|mi|mne|si|se)\s+)?(?:do|na|k)\s+projektu?\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*p[rř]epnout\s+(?:(?:m[eě]|mi|mne|si|se)\s+)?(?:do|na|k)\s+projektu?\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*jdi\s+(?:do|na|k)\s+projektu?\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*chci\s+(?:do|na|k)\s+projektu?\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*otev[rř]i\s+projekt\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*switch\s+to\s+project\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*go\s+to\s+project\s+(.+?)\s*[.!?]?\s*$", re.IGNORECASE),
]

# Vycisti aktualni projekt (vrat na "bez projektu") — vselijake formulace
_PROJECT_CLEAR_PATTERNS = [
    re.compile(r"^\s*p[rř]epni\s+(?:(?:m[eě]|mi|mne|si|se)\s+)?bez\s+projektu\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*p[rř]epni\s+(?:(?:m[eě]|mi|mne|si|se)\s+)?(?:do|na)\s+(?:[zž][aá]dn[ée]ho?|nic)\s*(?:projektu)?\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*vy[cč]isti\s+projekt\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*opus[tť]\s+projekt\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*[zž][aá]dn[ýíé]\s+projekt\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*bez\s+projektu\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*clear\s+project\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*no\s+project\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*leave\s+project\s*[.!?]?\s*$", re.IGNORECASE),
]


def _detect_project_switch(text: str) -> str | None:
    """Vrati extrahovany cilovy projekt, nebo None."""
    if not text:
        return None
    if len(text.strip().split()) > 8:
        return None
    for pat in _PROJECT_SWITCH_PATTERNS:
        m = pat.match(text)
        if m:
            return m.group(1).strip() or None
    return None


def _detect_project_clear(text: str) -> bool:
    """True, pokud user chce z projektu odejit (bez projektu)."""
    if not text:
        return False
    if len(text.strip().split()) > 5:
        return False
    for pat in _PROJECT_CLEAR_PATTERNS:
        if pat.match(text):
            return True
    return False


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

    if tool_name == "list_project_members":
        from modules.projects.application.service import (
            list_projects_for_user as _list_projs2,
            list_project_members as _list_pm,
            NotProjectMember,
        )
        from modules.core.infrastructure.models_core import User as _UMa, Project as _Prja
        from core.database_core import get_core_session as _gcsa
        import unicodedata as _uda

        if not user_id:
            return "❌ Nejsi přihlášen."

        project_id = tool_input.get("project_id")
        project_name = tool_input.get("project_name")

        def _n(s):
            if not s: return ""
            nn = _uda.normalize("NFKD", s.strip().lower())
            return "".join(c for c in nn if _uda.category(c) != "Mn")

        if project_name:
            needle = _n(project_name)
            user_projects = _list_projs2(user_id)
            matches = [p for p in user_projects if needle in _n(p["name"])]
            if not matches:
                return f'❌ Projekt obsahující "{project_name}" nenalezen.'
            if len(matches) > 1:
                exact = [p for p in matches if _n(p["name"]) == needle]
                matches = exact if len(exact) == 1 else matches
                if len(matches) > 1:
                    names = ", ".join(p["name"] for p in matches[:5])
                    return f'❌ "{project_name}" je ambiguous: {names}. Upřesni.'
            project_id = matches[0]["id"]
        elif not project_id:
            csa = _gcsa()
            try:
                u = csa.query(_UMa).filter_by(id=user_id).first()
                project_id = u.last_active_project_id if u else None
            finally:
                csa.close()
            if not project_id:
                return (
                    "❌ Nemáš aktivní projekt a nezadal/a jsi konkrétní. "
                    "Zavolej list_projects a zeptej se uživatele, který projekt myslel."
                )

        # Jmeno projektu pro header
        csb = _gcsa()
        try:
            proj = csb.query(_Prja).filter_by(id=project_id).first()
            proj_name = proj.name if proj else f"#{project_id}"
        finally:
            csb.close()

        try:
            members = _list_pm(user_id=user_id, project_id=project_id)
        except NotProjectMember as e:
            return f"❌ {e}"

        if not members:
            return f'V projektu **{proj_name}** zatím nikdo není (ani owner? divné — zkontroluj DB).'

        lines = [f"V projektu **{proj_name}** je {len(members)} členů:"]
        selection_items = []
        for idx, m in enumerate(members, 1):
            is_self = (m.get("user_id") == user_id)
            self_mark = " ← to jsi ty" if is_self else ""
            email_part = f" — {m['email']}" if m.get("email") else ""
            lines.append(f"  **{idx}.** {m['full_name']} ({m['role']}){email_part}{self_mark}")
            selection_items.append({
                "index": idx,
                "user_id": m["user_id"],
                "name": m["full_name"],
                "email": m.get("email") or "",
            })
        _save_pending_action(conversation_id, "select_from_list_users", {
            "items": selection_items,
        })
        lines.append(
            '\nNapiš jen **číslo** a řeknu ti o tom členovi víc — '
            'nebo mě popros "odeber ho z projektu".'
        )
        return "\n".join(lines)

    if tool_name in ("add_project_member", "remove_project_member"):
        from modules.projects.application.service import (
            add_project_member as _add_member,
            remove_project_member as _rm_member,
            list_projects_for_user as _list_projs,
            ProjectError, NotProjectMember,
        )
        from modules.core.infrastructure.models_core import User as _UM, Project as _Proj
        from core.database_core import get_core_session as _gcs2
        import unicodedata as _ud

        def _norm(s):
            if not s: return ""
            n = _ud.normalize("NFKD", s.strip().lower())
            return "".join(c for c in n if _ud.category(c) != "Mn")

        if not user_id:
            return "❌ Nejsi přihlášen — neznám tvůj kontext."

        target_uid = tool_input.get("target_user_id")
        project_id = tool_input.get("project_id")
        project_name = tool_input.get("project_name")
        role = tool_input.get("role") or "member"

        # Resolve project — project_name (fuzzy) MA prednost pred project_id;
        # pokud nic, fallback na user.last_active_project_id
        if project_name:
            needle = _norm(project_name)
            user_projects = _list_projs(user_id)
            matches = [p for p in user_projects if needle in _norm(p["name"])]
            if not matches:
                return (
                    f"❌ Projekt obsahující \"{project_name}\" jsem v tvém tenantu nenašel/a. "
                    f"Zavolej list_projects a vyber si jméno z dostupných."
                )
            if len(matches) > 1:
                # Zkus presny match
                exact = [p for p in matches if _norm(p["name"]) == needle]
                if len(exact) == 1:
                    matches = exact
                else:
                    names = ", ".join(p["name"] for p in matches[:5])
                    return (
                        f"❌ \"{project_name}\" odpovídá víc projektům: {names}. "
                        f"Upřesni jméno (přesněji)."
                    )
            project_id = matches[0]["id"]
        elif not project_id:
            cs2 = _gcs2()
            try:
                u = cs2.query(_UM).filter_by(id=user_id).first()
                project_id = u.last_active_project_id if u else None
            finally:
                cs2.close()
            if not project_id:
                return (
                    "❌ Neřekl/a jsi do kterého projektu a ani nemáš aktivní. "
                    "Zavolej list_projects a zeptej se uživatele kam."
                )

        # Najdi jmeno projektu + target user pro pekny vystup
        cs3 = _gcs2()
        try:
            proj = cs3.query(_Proj).filter_by(id=project_id).first()
            proj_name = proj.name if proj else f"#{project_id}"
            target_user = cs3.query(_UM).filter_by(id=target_uid).first()
            target_name = " ".join(filter(None, [target_user.first_name, target_user.last_name])).strip() if target_user else f"#{target_uid}"
        finally:
            cs3.close()

        try:
            if tool_name == "add_project_member":
                result = _add_member(
                    user_id=user_id, project_id=project_id,
                    target_user_id=target_uid, role=role,
                )
                if result.get("added"):
                    return f"✅ Přidal/a jsem **{target_name}** do projektu **{proj_name}** ({role})."
                return f"ℹ️ **{target_name}** už členem projektu **{proj_name}** je."
            else:
                result = _rm_member(
                    user_id=user_id, project_id=project_id,
                    target_user_id=target_uid,
                )
                if result.get("removed"):
                    return f"✅ Odebral/a jsem **{target_name}** z projektu **{proj_name}**."
                return f"ℹ️ **{target_name}** v projektu **{proj_name}** ani nebyl/a."
        except NotProjectMember as e:
            return f"❌ {e}"
        except ProjectError as e:
            return f"❌ {e}"
        except Exception as e:
            return f"❌ Operace selhala: {e}"

    if tool_name == "list_conversations":
        from modules.conversation.infrastructure.repository import list_conversations as _list_conv
        from modules.core.infrastructure.models_core import User as _UserModel
        from core.database_core import get_core_session as _get_cs
        from datetime import datetime, timezone
        if not user_id:
            return "❌ Nejsi přihlášen — neznám tvůj kontext."
        # Active tenant z DB (single source of truth)
        cs = _get_cs()
        try:
            u = cs.query(_UserModel).filter_by(id=user_id).first()
            active_tenant_id = u.last_active_tenant_id if u else None
        finally:
            cs.close()
        items = _list_conv(user_id=user_id, tenant_id=active_tenant_id, limit=20)
        if not items:
            return (
                'V tomto tenantu zatím nemáš žádné aktivní konverzace.\n\n'
                'Nahoře v menu „+ Nová" můžeš začít první.'
            )

        def _rel(dt_str):
            if dt_str is None:
                return "bez aktivity"
            try:
                from datetime import datetime as _dt
                dt = _dt.fromisoformat(dt_str.replace("Z", "+00:00"))
                diff = datetime.now(timezone.utc) - dt
                mins = int(diff.total_seconds() // 60)
                if mins < 1: return "právě teď"
                if mins < 60: return f"před {mins} min"
                hours = mins // 60
                if hours < 24: return f"před {hours} h"
                days = hours // 24
                if days == 1: return "včera"
                if days < 30: return f"před {days} dny"
                return dt.strftime("%d.%m.%Y")
            except Exception:
                return "—"

        lines = [f"V tomto tenantu máš {len(items)} aktivních konverzací:"]
        selection_items = []
        for idx, it in enumerate(items, 1):
            title = it.get("title") or f"Konverzace #{it['id']}"
            activity = _rel(it.get("last_message_at"))
            mark = " ← právě otevřená" if it["id"] == conversation_id else ""
            lines.append(f"  **{idx}.** {title} ({activity}){mark}")
            selection_items.append({
                "index": idx,
                "conversation_id": it["id"],
                "title": title,
            })
        _save_pending_action(conversation_id, "select_from_list_conversations", {
            "items": selection_items,
        })
        lines.append(
            '\nNapiš mi jen **číslo** (např. "2") a otevřu ti tu konverzaci.'
        )
        return "\n".join(lines)

    if tool_name == "list_users":
        from modules.conversation.application.tools import list_users_in_tenant
        if not user_id:
            return "❌ Nejsi přihlášen — neznám tvůj tenant kontext."
        result = list_users_in_tenant(requester_user_id=user_id)
        if not result.get("found"):
            return "❌ Nemáš aktivní tenant — nemůžu vypsat lidi."
        users = result.get("users", [])
        if not users:
            return f"V tenantu **{result.get('tenant_name') or '—'}** nikdo aktivní není."
        tname = result.get("tenant_name") or "—"
        lines = [f"V tenantu **{tname}** je {result.get('total', len(users))} aktivních lidí:"]
        # Ulož seznam do pending_actions pro cislovanou selekci.
        # User pak muze odpovedet jen cislem (napr. "3") a my vime, koho myslel.
        selection_items = []
        for idx, u in enumerate(users, 1):
            name = u.get("display_name") or u.get("full_name") or "—"
            role = u.get("role") or "member"
            role_label = u.get("role_label")
            email = u.get("preferred_email") or "(bez emailu)"
            self_mark = " ← to jsi ty" if u.get("is_requester") else ""
            label_part = f", {role_label}" if role_label else ""
            lines.append(f"  **{idx}.** {name} ({role}{label_part}) — {email}{self_mark}")
            selection_items.append({
                "index": idx,
                "user_id": u.get("user_id"),
                "name": name,
                "email": email,
            })
        _save_pending_action(conversation_id, "select_from_list_users", {
            "items": selection_items,
        })
        if result.get("has_more"):
            lines.append(f"\n(zobrazeno prvních {len(users)}, celkem {result['total']})")
        lines.append(
            '\nNapiš mi jen **číslo** (např. "3") a řeknu ti o tom člověku víc — '
            'nebo mě rovnou popros "pošli email Ondrovi".'
        )
        return "\n".join(lines)

    if tool_name == "list_projects":
        from modules.projects.application.service import list_projects_for_user
        from datetime import datetime, timezone
        if not user_id:
            return "❌ Nejsi přihlášen — neznám tvůj tenant kontext."
        items = list_projects_for_user(user_id)
        if not items:
            return (
                'V tomto tenantu zatím nejsou žádné aktivní projekty.\n\n'
                'Můžeš si nějaký vytvořit nahoře v menu "● Projekty → + Nový projekt".'
            )

        def _rel(dt):
            if dt is None:
                return "bez aktivity"
            try:
                if isinstance(dt, str):
                    from datetime import datetime as _dt
                    dt = _dt.fromisoformat(dt.replace("Z", "+00:00"))
                diff = datetime.now(timezone.utc) - dt
                mins = int(diff.total_seconds() // 60)
                if mins < 1: return "právě teď"
                if mins < 60: return f"před {mins} min"
                hours = mins // 60
                if hours < 24: return f"před {hours} h"
                days = hours // 24
                if days == 1: return "včera"
                if days < 30: return f"před {days} dny"
                return dt.strftime("%d.%m.%Y")
            except Exception:
                return "—"

        # Najdi aktualni projekt usera, abychom ho v seznamu zvyraznili
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import User as _User
        cs = get_core_session()
        try:
            u = cs.query(_User).filter_by(id=user_id).first()
            current_pid = u.last_active_project_id if u else None
        finally:
            cs.close()

        lines = [f"V tomto tenantu máš {len(items)} aktivních projektů:"]
        # Ulož pro cislovanou selekci (user odpovi jen "3", my vime na ktery projekt).
        selection_items = []
        for idx, p in enumerate(items, 1):
            mark = " ← právě v něm" if p["id"] == current_pid else ""
            activity = p.get("last_activity_at") or p.get("created_at")
            lines.append(f"  **{idx}.** {p['name']} ({_rel(activity)}){mark}")
            selection_items.append({
                "index": idx,
                "project_id": p["id"],
                "name": p["name"],
            })
        _save_pending_action(conversation_id, "select_from_list_projects", {
            "items": selection_items,
        })
        if current_pid is None:
            lines.append("\nMomentálně pracuješ **bez projektu**.")
        lines.append(
            '\nNapiš mi jen **číslo** (např. "2") a přepnu tě tam — '
            'nebo řekni "přepni do projektu <jméno>".'
        )
        return "\n".join(lines)

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
        first_name = tool_input.get("first_name") or None
        last_name = tool_input.get("last_name") or None
        gender = tool_input.get("gender") or None
        # legacy fallback, pokud Claude pošle stary "name"
        legacy_name = tool_input.get("name") or None
        result = invite_user_to_strategie(
            email=email,
            invited_by_user_id=user_id or 1,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            name=legacy_name,
        )
        # Jméno pro zobrazení bez české deklinace (nominativ) — Marti-AI
        # pak může odpověď uživateli zformulovat gramaticky správně sama.
        full_name = " ".join(filter(None, [first_name, last_name])).strip()
        display = full_name or first_name or email
        if result["success"] and result["email_sent"]:
            return (
                f"✅ Pozvánka odeslána.\n"
                f"Jméno: {display}\n"
                f"Email: {email}"
            )
        return (
            f"⚠️ Pozvánka vytvořena, ale email se nepodařilo odeslat.\n"
            f"Jméno: {display}\n"
            f"Email: {email}"
        )

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
        # Načti aktivní tenant + projekt uživatele, ať se konverzace správně
        # přiřadí (Marti přepnut v EUROSOFTu, projekt Škoda -> nová konverzace
        # patří do EUROSOFT/Škoda, ne do Osobní/bez projektu).
        active_tenant_id: int | None = None
        active_project_id: int | None = None
        if user_id:
            from modules.core.infrastructure.models_core import User
            from core.database_core import get_core_session
            cs = get_core_session()
            try:
                u = cs.query(User).filter_by(id=user_id).first()
                if u:
                    active_tenant_id = u.last_active_tenant_id
                    active_project_id = u.last_active_project_id
            finally:
                cs.close()
        # project_id parametr funkce má prioritu (explicitní volba klienta),
        # jinak fallback na user.last_active_project_id.
        effective_project_id = project_id if project_id is not None else active_project_id
        conversation_id = create_conversation(
            user_id=user_id,
            tenant_id=active_tenant_id,
            project_id=effective_project_id,
        )

    if _is_confirmation(user_message):
        pending = _get_pending_action(conversation_id)
        if pending:
            # Skutečná pending akce existuje — vykonej a potvrď.
            save_message(conversation_id, role="user", content=user_message,
                         author_type="human", author_user_id=user_id)
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
            save_message(conversation_id, role="user", content=user_message,
                         author_type="human", author_user_id=user_id)
            reply = (
                "❌ Žádný email nebyl systémově připraven k odeslání.\n\n"
                "Napiš znovu explicitně, co mám poslat, např.:\n"
                "„pošli email m.pasek@eurosoft.com — Ahoj Marti, …"
            )
            save_message(conversation_id, role="assistant", content=reply)
            return conversation_id, reply, None
        # Jinak (ano bez pendingu a bez email kontextu) = běžné potvrzení,
        # nechej to dojít k Claude standardní cestou.

    save_message(conversation_id, role="user", content=user_message,
                 author_type="human", author_user_id=user_id)

    # ── ČÍSLOVANÁ SELEKCE z předchozího seznamu ───────────────────────
    # Pokud je user_message jen číslo (případně s tečkou) a v pending_actions
    # je uložen "select_from_list_*", provedeme akci podle indexu.
    # Patternu odpovídá: "3", "3.", " 2 ", "č. 1" atp.
    _selection_match = re.match(r"^\s*(?:č\.\s*)?(\d{1,3})\.?\s*$", user_message, re.IGNORECASE)
    if _selection_match:
        pending = _get_pending_action(conversation_id)
        if pending and pending.get("type") in (
            "select_from_list_projects",
            "select_from_list_users",
            "select_from_list_conversations",
            "select_user_action",
        ):
            try:
                wanted = int(_selection_match.group(1))
            except ValueError:
                wanted = None
            # select_user_action uklada volby pod klicem "actions", ostatni pod "items"
            items = pending.get("items") if pending.get("type") != "select_user_action" else pending.get("actions", [])
            picked = next((it for it in items if it.get("index") == wanted), None)
            if picked is None:
                reply = (
                    f"❌ Číslo {wanted} mimo rozsah seznamu (mám {len(items)} položek). "
                    f"Zkus znovu."
                )
                save_message(conversation_id, role="assistant", content=reply,
                             message_type="system")
                return conversation_id, reply, None

            if pending["type"] == "select_from_list_projects":
                from modules.projects.application.service import switch_project_by_query, switch_project_for_user
                project_id = picked["project_id"]
                # Pouzijeme switch_project_for_user (validuje membership) primo na ID
                try:
                    result = switch_project_for_user(user_id=user_id, project_id=project_id)
                    name = result.get("project_name") or picked["name"]
                    reply = (
                        f"✅ Přepnuto do projektu {name}.\n\n"
                        f"Od této zprávy s tebou pracuju v tomto projektovém kontextu."
                    )
                except Exception as e:
                    reply = f"❌ Nelze přepnout: {e}"
                _delete_pending_action(conversation_id)
                save_message(conversation_id, role="assistant", content=reply,
                             message_type="system")
                return conversation_id, reply, None

            if pending["type"] == "select_from_list_users":
                name = picked["name"]
                email = picked["email"]
                target_uid = picked["user_id"]
                # Uloz pending pro nasledujici cislovanou akci nad timto userem.
                _save_pending_action(conversation_id, "select_user_action", {
                    "user_id": target_uid,
                    "name": name,
                    "email": email,
                    "actions": [
                        {"index": 1, "key": "email"},
                        {"index": 2, "key": "dm"},
                        {"index": 3, "key": "free"},
                    ],
                })
                reply = (
                    f'Vybral jsi **{name}** — {email}.\n\n'
                    f'Co chceš dál?\n'
                    f'  **1.** Pošli email\n'
                    f'  **2.** Otevři DM (přepne do záložky "Lidé")\n'
                    f'  **3.** Něco jiného (řekni co)\n\n'
                    f'Napiš jen číslo nebo přímo co potřebuješ.'
                )
                save_message(conversation_id, role="assistant", content=reply,
                             message_type="system")
                return conversation_id, reply, None

            if pending["type"] == "select_from_list_conversations":
                target_cid = picked["conversation_id"]
                title = picked["title"]
                _delete_pending_action(conversation_id)
                # Pro otevreni konverzace nic neukladame (user ji fyzicky otevre
                # ve frontu). Vratime specialni dict v extras slotu — router
                # z neho vycte switch_to_conversation_id a preda do response.
                reply = f"Otevírám konverzaci: **{title}**."
                save_message(conversation_id, role="assistant", content=reply,
                             message_type="system")
                return conversation_id, reply, {"switch_to_conversation_id": target_cid}

            if pending["type"] == "select_user_action":
                # User vybral 1/2/3 po selekci z list_users.
                action_key = picked.get("key")
                target_uid = pending.get("user_id")
                target_name = pending.get("name") or "—"
                target_email = pending.get("email") or "(bez emailu)"
                _delete_pending_action(conversation_id)

                if action_key == "email":
                    # Nech Claude pokracovat v emailu — ulozime kontext jako
                    # system zpravu do historie, aby si Claude zapamatoval cil.
                    reply = (
                        f'OK, napíšu email **{target_name}** ({target_email}).\n\n'
                        f'Co má být předmětem a co chceš do těla napsat?'
                    )
                    save_message(conversation_id, role="assistant", content=reply,
                                 message_type="system")
                    # Hint pro Claude na dalsi turn — system-role v user zprave
                    # (stejny pattern jako tenant switch marker): user-role, ai type.
                    marker = (
                        f'[KONTEXT] Píšeš email pro: {target_name}, adresa: {target_email}. '
                        f'V dalším tahu user dodá obsah — zavolej send_email s touhle adresou.'
                    )
                    save_message(conversation_id, role="user", content=marker,
                                 author_type="ai", message_type="system")
                    return conversation_id, reply, None
                if action_key == "dm":
                    reply = f"Otevírám DM s **{target_name}**."
                    save_message(conversation_id, role="assistant", content=reply,
                                 message_type="system")
                    return conversation_id, reply, {"switch_to_dm_user_id": target_uid}
                # "free" = pust mu neco uzivatelsky, ale bez kontextu
                reply = (
                    f'OK, {target_name} je vybraný/á. Řekni co potřebuješ '
                    f'(zeptat se na něj, poslat email, apod.).'
                )
                save_message(conversation_id, role="assistant", content=reply,
                             message_type="system")
                return conversation_id, reply, None

    # ── Explicitní PROJECT switch ──────────────────────────────────────
    # „přepni do projektu Skoda", „bez projektu", „opust projekt".
    # MUSI byt PRED tenant switchem — slovo "projekt" je specificke.
    # Bez nej by „přepni do EUROSOFTu" padlo do tenant detekce.
    if user_id:
        if _detect_project_clear(user_message):
            from modules.projects.application.service import clear_project_for_user
            result = clear_project_for_user(user_id)
            if result.get("already_clear"):
                reply = "✅ Už jsi bez projektu."
            else:
                reply = "✅ Opustil jsi projekt. Pracuješ teď bez projektu."
            save_message(conversation_id, role="assistant", content=reply,
                         message_type="system")
            return conversation_id, reply, None

        project_target = _detect_project_switch(user_message)
        if project_target:
            from modules.projects.application.service import switch_project_by_query
            logger.info(
                f"PROJECT | switch_intent | user={user_id} | target={project_target!r}"
            )
            result = switch_project_by_query(user_id=user_id, query=project_target)
            if result.get("found"):
                name = result["project_name"]
                if result.get("already_active"):
                    reply = f"✅ Už jsi v projektu {name}."
                else:
                    reply = (
                        f"✅ Přepnuto do projektu {name}.\n\n"
                        f"Od této zprávy s tebou pracuju v tomto projektovém kontextu."
                    )
            elif result.get("ambiguous"):
                lines = ["Mám víc projektů odpovídajících tvému zadání:"]
                for i, c in enumerate(result["candidates"], 1):
                    lines.append(f"  {i}. {c['name']}")
                lines.append("\nUveď přesnější jméno.")
                reply = "\n".join(lines)
            elif result.get("no_projects"):
                reply = (
                    '❌ V tomto tenantu zatím nejsou žádné aktivní projekty.\n\n'
                    'Vlevo nahoře v "● Projekty" si můžeš nějaký vytvořit.'
                )
            else:
                reply = (
                    f'❌ Projekt "{project_target}" jsem nenašel/a v tomto tenantu.\n\n'
                    f'Klikni na "● Projekty" v hlavičce a uvidíš seznam dostupných.'
                )
            save_message(conversation_id, role="assistant", content=reply,
                         message_type="system")
            return conversation_id, reply, None

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
            # Tenant switch je systémové oznámení, ne AI text.
            save_message(conversation_id, role="assistant", content=reply,
                         message_type="system")
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
            # Fallback chain: persona ne → tenant → projekt. Důvod: lidi mixují
            # předložky („přepni na EUROSOFT", „přepni na TISAX") a nemusí
            # vědět, jestli mluví o personu, tenantu nebo projektu. Zkusíme
            # všechny tři škatulky, ať se chování chová "smart".
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
                # Poslední fallback: zkus projekt v aktuálním tenantu.
                project_fallback = None
                if user_id:
                    from modules.projects.application.service import switch_project_by_query
                    project_fallback = switch_project_by_query(user_id=user_id, query=switch_target)
                if project_fallback and project_fallback.get("found"):
                    pname = project_fallback["project_name"]
                    if project_fallback.get("already_active"):
                        reply = f"✅ Už jsi v projektu {pname}."
                    else:
                        reply = (
                            f"✅ Přepnuto do projektu {pname}.\n\n"
                            f"Od této zprávy s tebou pracuju v tomto projektovém kontextu."
                        )
                elif project_fallback and project_fallback.get("ambiguous"):
                    lines = ["Mám víc projektů odpovídajících tvému zadání:"]
                    for i, c in enumerate(project_fallback["candidates"], 1):
                        lines.append(f"  {i}. {c['name']}")
                    lines.append("\nUveď přesnější jméno.")
                    reply = "\n".join(lines)
                else:
                    reply = (
                        f"❌ Nenašel/a jsem '{switch_target}' — ani jako personu, "
                        f"ani jako tenant, ani jako projekt.\n\n"
                        f"Zkus přesnější jméno."
                    )
        # Persona / tenant / project switch je systémové oznámení, ne AI text.
        save_message(conversation_id, role="assistant", content=reply,
                     message_type="system")
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
