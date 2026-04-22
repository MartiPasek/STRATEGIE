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
    TOOLS, format_email_preview, format_sms_preview, find_user_in_system,
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

# Hlavni model pro chat + tool loop. Sonnet 4.6 ma 200k context window a znacne
# lepsi contextual reasoning nez Haiku -- drzi vlakno konverzace i pres desitky
# zprav. Pro title_service / summary_service / klasifikatory zustava Haiku (tam
# staci rychlost + nizka cena, reasoning quality neni kriticky).
MODEL = "claude-sonnet-4-6"

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


# TLD vrstva pro validaci emailovych adres pri invite_user.
# Casta TLD pouzivana v CZ kontextu -- neoznackovava warning.
# Vse ostatni = warn (uzivatel muze potvrdit).
_KNOWN_SAFE_TLDS = {
    # Czechia + sousedni
    "cz", "sk", "de", "at", "pl", "hu", "ua",
    # Bezne mezinarodni
    "com", "org", "net", "eu", "io", "info", "biz", "edu", "gov",
    # EU + UK + frequent partner countries
    "uk", "fr", "it", "es", "nl", "be", "se", "fi", "no", "dk", "ie",
    "ch", "ro", "bg", "gr", "pt", "lt", "lv", "ee", "si", "hr",
    # Velka byznys / lokality
    "ai", "co", "us", "ca", "au", "nz", "jp", "cn", "in", "br",
    "me", "tv", "app", "dev", "tech", "online", "store",
}

# Mapovani podezrelych TLD na vysvetleni (pomaha AI zformulovat varovani)
_SUSPICIOUS_TLD_HINTS = {
    "cd": "Demokratická republika Kongo (možná překlep .cz?)",
    "cm": "Kamerun (možná překlep .com?)",
    "co": None,   # Kolumbie, ale i bezne (.co domeny) -- bez warningu
    "cf": "Středoafrická republika (typicky free domain, podezrelé)",
    "ga": "Gabon (typicky free domain, podezrelé)",
    "ml": "Mali (typicky free domain, podezrelé)",
    "tk": "Tokelau (typicky free domain, podezrelé)",
    "ru": "Rusko (zvazuj zda je v poradku)",
    "by": "Bělorusko (zvazuj zda je v poradku)",
}


def _check_email_tld(email: str) -> str | None:
    """Vraci warning text pokud TLD emailu je neobvykla, jinak None.
    Tool dispatcher si vrati string ktery AI uvidi a uzivatele se zepta."""
    if not email or "@" not in email:
        return None
    domain = email.rsplit("@", 1)[1].strip().lower()
    if "." not in domain:
        return f"⚠️ Email '{email}' nema platnou domenu (chybi tecka). Zkontroluj prosim format."
    tld = domain.rsplit(".", 1)[1]
    if tld in _KNOWN_SAFE_TLDS:
        return None
    hint = _SUSPICIOUS_TLD_HINTS.get(tld)
    if hint is None and tld in _SUSPICIOUS_TLD_HINTS:
        # Explicit None -> tato TLD je OK i kdyz neni v safe (napr. .co)
        return None
    hint_text = f" ({hint})" if hint else ""
    return (
        f"⚠️ Email '{email}' konci TLD '.{tld}'{hint_text}. "
        f"Tato koncovka neni mezi beznymi (cz/sk/com/org/...). "
        f"\n\nZeptej se uzivatele zda je TLD spravna nebo to byl preklep "
        f"(napr. '.cd' -> '.cz'). Az to potvrdi, zavolej invite_user ZNOVU se "
        f"stejnymi argumenty + allow_unusual_tld=true."
    )


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


def _looks_like_sms_preview(text: str) -> bool:
    """
    Heuristika: rozpozná text, který vypadá jako SMS preview (ať už z
    format_sms_preview, nebo Claudeho mimikry bez volání toolu).
    """
    if not text:
        return False
    low = text.lower()
    if "mohu sms odeslat" in low or "mám sms odeslat" in low or "mám ji odeslat" in low:
        return True
    if "📱" in text and "návrh sms" in low:
        return True
    return False


def _last_assistant_message_looks_like_sms_preview(conversation_id: int) -> bool:
    """Stejny princip jako pro email -- zabezpeceni ze se nic neodesle bez pending."""
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
        return _looks_like_sms_preview(last.content)
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


def _log_sms_action(
    to: str,
    body: str,
    status: str,
    user_id: int | None,
    conversation_id: int,
    outbox_id: int | None = None,
    error: str | None = None,
) -> None:
    """
    Zaloguje obsah odeslaneho (nebo selhaneho) SMS do action_logs.
    Kriticke pro audit -- musi byt mozne zpetne overit, co presne odeslelo.
    """
    session = get_data_session()
    try:
        out = f"to={to} | chars={len(body)}"
        if outbox_id:
            out += f" | outbox_id={outbox_id}"
        if error:
            out += f" | error={error}"
        log = ActionLog(
            user_id=user_id,
            action_type="confirm",
            tool_name="send_sms",
            input=json.dumps(
                {"to": to, "body": body, "conversation_id": conversation_id},
                ensure_ascii=False,
            ),
            output=out,
            status=status,
            error_message=error,
            approval_required=True,
            approved_by=user_id,
        )
        session.add(log)
        session.commit()
    except Exception as e:
        logger.error(f"AUDIT | action_log failed (sms): {e}")
    finally:
        session.close()


# Regex pro detekci halucinovaneho switch_persona v Claude reply.
# Zachycuje:
#   "✅ Přepnuto na Marti-AI."   (klasicky Claude vzor s emoji)
#   "Přepnuto na PrávníkCZ-AI"   (bez emoji, bez tecky)
#   "Nyní mluvíš s XXX-AI"       (druhou casti v reply se potvrzuje uspesne prepnuti)
# Podporuje diakritiku v nazvu persony (napr. PrávníkCZ-AI), cisla, pomlcky.
import re as _re_persona_switch
_HALLUCINATED_SWITCH_RE = _re_persona_switch.compile(
    r"(?:✅\s*)?P[rř]epnuto\s+na\s+([A-Za-zÀ-žá-ž0-9][A-Za-zÀ-žá-ž0-9\-]{1,64}?)(?=[\s.,!?\n]|$)",
    flags=_re_persona_switch.IGNORECASE,
)


def _maybe_enforce_hallucinated_switch(conversation_id: int, reply: str) -> None:
    """
    Pokud Claude v replice napsal "Přepnuto na X" jako text (bez volani tool
    switch_persona), pokusime se X rozpoznat a vynutit switch v DB.

    Idempotentni: pokud conversation.active_agent_id uz odpovida te personu,
    neuderime nic. Pokud neni match (persona nenalezena), jen logneme a
    pokracujeme -- reply jde do DB i tak, user uvidi halucinaci, ale
    system stav se nerozsypal.
    """
    if not reply:
        return
    m = _HALLUCINATED_SWITCH_RE.search(reply)
    if not m:
        return
    target_name = m.group(1).strip()
    if not target_name:
        return
    # Uz ma active_agent_id tu personu? Idempotence -- zbytecny DB update preskocime.
    from modules.core.infrastructure.models_core import Persona as _Persona
    cs = get_core_session()
    try:
        target = cs.query(_Persona).filter(_Persona.name.ilike(target_name)).first()
        if target is None:
            logger.info(
                f"PERSONA | hallucinated switch detected but persona not found | "
                f"conv={conversation_id} | target={target_name!r}"
            )
            return
        target_id = target.id
        target_name_canonical = target.name
    finally:
        cs.close()

    # Over aktualni state -- pokud uz je switchnuto, nic nedelame.
    current_id = _active_persona_id_for_conversation(conversation_id)
    if current_id == target_id:
        return

    # Vynutime switch. Pouzijeme existujici switch_persona_for_user (stejny
    # code path jako Claude tool call) -- zajisti DB update + audit.
    try:
        result = switch_persona_for_user(query=target_name_canonical, conversation_id=conversation_id)
        if result.get("found"):
            logger.warning(
                f"PERSONA | enforced hallucinated switch | conv={conversation_id} | "
                f"from={current_id} -> to={target_id} ({target_name_canonical})"
            )
        else:
            logger.info(
                f"PERSONA | hallucinated switch regex matched but switch_persona_for_user "
                f"failed | conv={conversation_id} | target={target_name_canonical!r}"
            )
    except Exception as e:
        logger.error(
            f"PERSONA | enforce hallucinated switch raised | conv={conversation_id} | "
            f"error={e!r}"
        )


def _active_persona_id_for_conversation(conversation_id: int) -> int | None:
    """
    Vrati persona_id aktivni v dane konverzaci (conversations.active_agent_id).
    Vyuziva se pro SMS inbox / call log tooly -- persona "vlastni" SIMku,
    takze chceme filtrovat zaznamy per-persona, aby Marti-AI videla svoje,
    Pravnik-AI neviděl nic (respektive svoje, kdyz dostane SIMku).
    """
    from modules.core.infrastructure.models_data import Conversation as _Conv
    ds = get_data_session()
    try:
        c = ds.query(_Conv).filter_by(id=conversation_id).first()
        if not c:
            return None
        return c.active_agent_id
    finally:
        ds.close()


def _build_sms_sent_message(to: str, outbox_id: int | None, status: str = "pending") -> str:
    """
    Potvrzovaci text pro UI, odlisujici realny stav po queue_sms:
      - sent     -> cloud gateway akceptovala, za par vterin poslana pres GSM
      - pending  -> ceka v outboxu (pull model nebo retry)
      - failed   -> cloud gateway odmitla (duvod v outbox.last_error)
    """
    if status == "sent":
        return f"✅ SMS odeslána ({to})"
    if status == "failed":
        return f"❌ SMS se nepodařilo odeslat ({to}). Detail v outboxu (id={outbox_id})."
    return f"📱 SMS zařazena k odeslání ({to})"


def _execute_pending_action(conversation_id: int, user_id: int | None = None) -> str | None:
    action = _get_pending_action(conversation_id)
    if not action:
        return None
    _delete_pending_action(conversation_id)
    if action["type"] == "send_email":
        # Od PR3.1: AI potvrzene emaily jdou pres email_outbox (audit + retry),
        # ne primym send_email_or_raise. UX zachovan: queue_email + send_outbox_row_now
        # = instant feedback jako drive, ale s auditem v DB.
        from modules.notifications.application.email_service import (
            queue_email, send_outbox_row_now,
        )
        to = action["to"]
        subject = action["subject"]
        body = action["body"]
        from_identity = action.get("from_identity") or "persona"

        # Kanal aktivni persony. Pokud persona nema nakonfigurovany email kanal
        # v persona_channels, fallback na globalni .env resi az
        # send_email_or_raise hluboko ve flush/_send_outbox_row.
        persona_id = _active_persona_id_for_conversation(conversation_id)
        tenant_id = None
        if user_id:
            from core.database_core import get_core_session as _gcs_e
            from modules.core.infrastructure.models_core import User as _U_e
            _cs = _gcs_e()
            try:
                _u = _cs.query(_U_e).filter_by(id=user_id).first()
                if _u:
                    tenant_id = _u.last_active_tenant_id
            finally:
                _cs.close()

        # 1) Zapis do outboxu (audit row vznika ihned, i kdyby inline send selhal)
        try:
            outbox = queue_email(
                to=to, subject=subject, body=body,
                persona_id=persona_id, tenant_id=tenant_id,
                user_id=user_id, from_identity=from_identity,
                purpose="user_request",
                conversation_id=conversation_id,
            )
        except Exception as e:
            _log_email_action(to, subject, body, "error", user_id, conversation_id,
                              error=f"queue: {e}")
            return f"❌ Email se nepodařilo zařadit do outboxu — {e}"

        outbox_id = outbox["id"]

        # 2) Inline pokus o odeslani -- user ceka na odpoved, chceme okamzity feedback.
        #    Race-safe: pokud by worker mezitim row pobral, send_outbox_row_now
        #    vrati 'already_claimed' a volajici rozhodne.
        result = send_outbox_row_now(outbox_id)
        status = result.get("status")
        error_kind = result.get("error_kind")
        err = result.get("error") or ""

        if status == "sent":
            _log_email_action(to, subject, body, "success", user_id, conversation_id)
            return _build_email_sent_message(to, body)

        if status == "already_claimed":
            # Extremne vzacne -- worker popadl row v milisekundovem okne po claim.
            # User dostane info, at refreshne UI.
            return (
                f"⏳ Email zařazen do outboxu (id={outbox_id}) a právě odesílán. "
                "Během chvíle se objeví v záložce Odeslané."
            )

        if status == "failed" or status == "pending":
            # Zalogujeme s typem chyby pro audit.
            _log_email_action(to, subject, body, "error", user_id, conversation_id,
                              error=f"{error_kind or 'unknown'}: {err}")

            if error_kind == "no_user_channel":
                return (
                    "❌ Email se nepodařilo odeslat — **nemáš nakonfigurovanou "
                    "vlastní emailovou schránku**.\n\n"
                    "Aby šlo posílat z tvé adresy, musí admin zaregistrovat "
                    "tvoje EWS credentialy v nastavení profilu (zatim přes "
                    "SQL / helper skript). Alternativně pošli z persony — "
                    "napiš znovu bez 'z mojí schránky'.\n"
                    f"*(outbox id={outbox_id}, status=failed)*"
                )
            if error_kind == "auth":
                ident = "tvojí schránky" if from_identity == "user" else "persony"
                return (
                    f"❌ Email se nepodařilo odeslat — **špatné přihlašovací údaje** "
                    f"pro {ident}.\n\n"
                    "Zkontroluj heslo / adresu / server v nastavení. "
                    "Pokud má schránka zapnutou dvoufaktorovou autentizaci, "
                    "budeš potřebovat **application password** (ne běžné heslo).\n"
                    f"*(outbox id={outbox_id}, status=failed)*"
                )
            if status == "pending":
                # Send error, ale pod limit attempts -- worker zkusí znovu.
                return (
                    f"⏳ Email zařazen do outboxu (id={outbox_id}), první pokus "
                    f"o odeslání nedopadl:\n> {err}\n\n"
                    "Worker ho zkusí znovu v dalším cyklu (do minuty). "
                    "Pokud se opakovaně nepodaří, skončí ve stavu **failed** — "
                    "uvidíš v záložce Odeslané."
                )
            # status == "failed", error_kind == "send" nebo unexpected
            return (
                f"❌ Email se nepodařilo odeslat — {err}\n"
                f"*(outbox id={outbox_id}, status=failed)*"
            )

        # Defensive fallback: missing / unexpected status
        _log_email_action(to, subject, body, "error", user_id, conversation_id,
                          error=f"outbox status={status}")
        return (
            f"❌ Email odeslání selhalo (outbox id={outbox_id}, status={status}). "
            "Detail v logu."
        )

    if action["type"] == "send_sms":
        from modules.notifications.application.sms_service import (
            queue_sms, SmsRateLimitError, SmsValidationError, SmsError,
        )
        to = action["to"]
        body = action["body"]

        # Tenant do outboxu pro audit -- nacist z usera
        tenant_id = None
        if user_id:
            from core.database_core import get_core_session as _gcs_sms
            from modules.core.infrastructure.models_core import User as _U_sms
            _cs = _gcs_sms()
            try:
                _u = _cs.query(_U_sms).filter_by(id=user_id).first()
                if _u:
                    tenant_id = _u.last_active_tenant_id
            finally:
                _cs.close()

        try:
            result = queue_sms(
                to=to,
                body=body,
                purpose="user_request",
                user_id=user_id,
                tenant_id=tenant_id,
            )
        except SmsRateLimitError as e:
            _log_sms_action(to, body, "error", user_id, conversation_id, error=f"rate_limit: {e}")
            return (
                "❌ SMS rate limit — poslal jsi příliš mnoho SMS za poslední hodinu. "
                "Zkus to za chvíli, nebo uprav limit v konfiguraci."
            )
        except SmsValidationError as e:
            _log_sms_action(to, body, "error", user_id, conversation_id, error=f"validation: {e}")
            return f"❌ SMS neodeslána — neplatný vstup: {e}"
        except SmsError as e:
            _log_sms_action(to, body, "error", user_id, conversation_id, error=str(e))
            return "❌ SMS se nepodařilo zařadit k odeslání."
        except Exception as e:
            _log_sms_action(to, body, "error", user_id, conversation_id, error=str(e))
            return "❌ SMS se nepodařilo zařadit k odeslání."

        # queue_sms vrati dict. Pokud SMS_ENABLED=false -> status='disabled'.
        status = result.get("status")
        if status == "disabled":
            _log_sms_action(to, body, "skipped", user_id, conversation_id,
                            error="SMS_ENABLED=false")
            return "⚠️ SMS gateway je vypnutá (SMS_ENABLED=false). SMS neodeslána."

        outbox_id = result.get("id")
        log_status = "success" if status == "sent" else "error" if status == "failed" else "success"
        _log_sms_action(
            to, body, log_status, user_id, conversation_id,
            outbox_id=outbox_id,
            error=None if status in ("sent", "pending") else f"gateway_status={status}",
        )
        return _build_sms_sent_message(
            result.get("to_phone") or to, outbox_id, status=status or "pending",
        )
    return None


def _handle_tool(tool_name: str, tool_input: dict, conversation_id: int, user_id: int | None = None) -> str:
    logger.info(f"TOOL | name={tool_name}")

    if tool_name == "send_email":
        to = tool_input.get("to", "")
        subject = tool_input.get("subject", "")
        body = tool_input.get("body", "")
        from_identity = (tool_input.get("from_identity") or "persona").lower()
        if from_identity not in ("persona", "user"):
            from_identity = "persona"

        _save_pending_action(conversation_id, "send_email", {
            "to": to,
            "subject": subject,
            "body": body,
            "from_identity": from_identity,
        })

        # Resolve sender display pro preview.
        sender_display = None
        if from_identity == "user":
            from modules.notifications.application.user_channel_service import get_user_display_email
            sender_display = get_user_display_email(user_id) if user_id else None
            if not sender_display:
                # User nema kanal -- ukaz varovani v preview, neblokuj pending
                # (caller eventualne vybere persona cestu; tady jen informujeme).
                sender_display = "⚠️ (nemáš nakonfigurovanou vlastní schránku)"
        else:
            # Persona -- resolve display z persona_channels (nebo fallback na .env)
            from modules.notifications.application.persona_channel_service import get_email_credentials as _gec
            persona_id_p = _active_persona_id_for_conversation(conversation_id)
            tenant_id_p = None
            if user_id:
                from core.database_core import get_core_session as _gcs_px
                from modules.core.infrastructure.models_core import User as _Upx
                _csx = _gcs_px()
                try:
                    _ux = _csx.query(_Upx).filter_by(id=user_id).first()
                    if _ux:
                        tenant_id_p = _ux.last_active_tenant_id
                finally:
                    _csx.close()
            if persona_id_p:
                creds_p = _gec(persona_id_p, tenant_id=tenant_id_p)
                if creds_p:
                    sender_display = creds_p.get("display_email") or creds_p.get("email")

        return format_email_preview(
            to=to, subject=subject, body=body,
            from_identity=from_identity, sender_display=sender_display,
        )

    if tool_name == "send_sms":
        _save_pending_action(conversation_id, "send_sms", {
            "to": tool_input.get("to", ""),
            "body": tool_input.get("body", ""),
        })
        return format_sms_preview(
            to=tool_input.get("to", ""),
            body=tool_input.get("body", ""),
        )

    if tool_name == "list_sms_inbox":
        from modules.notifications.application.sms_service import list_inbox as _list_inbox
        persona_id = _active_persona_id_for_conversation(conversation_id)
        limit = int(tool_input.get("limit") or 10)
        unread_only = bool(tool_input.get("unread_only") or False)
        items = _list_inbox(persona_id=persona_id, limit=limit, unread_only=unread_only)
        if not items:
            return (
                "📭 Schránka SMS je prázdná"
                + (" (žádné nepřečtené)" if unread_only else "")
                + "."
            )
        lines = ["📱 Přijaté SMS:", ""]
        for i, it in enumerate(items, start=1):
            ts = it["received_at"] or ""
            mark = "" if it["read"] else " ● "
            body_preview = (it["body"] or "").strip().replace("\n", " ")
            if len(body_preview) > 100:
                body_preview = body_preview[:100] + "…"
            lines.append(f"{i}. {mark}{it['from_phone']} — {body_preview}  ({ts})")
        return "\n".join(lines)

    if tool_name == "list_email_inbox":
        from modules.notifications.application.email_inbox_service import (
            list_inbox_for_ui as _email_list,
        )
        persona_id = _active_persona_id_for_conversation(conversation_id)
        if persona_id is None:
            return "❌ Nemůžu zjistit aktivní personu — nelze načíst emaily."
        limit = int(tool_input.get("limit") or 10)
        filter_mode = tool_input.get("filter_mode") or "new"
        if filter_mode == "all":
            items_new = _email_list(persona_id=persona_id, filter_mode="new", limit=limit)
            items_proc = _email_list(persona_id=persona_id, filter_mode="processed", limit=limit)
            items = (items_new + items_proc)[:limit]
        else:
            items = _email_list(persona_id=persona_id, filter_mode=filter_mode, limit=limit)
        if not items:
            empty_msg = {
                "new":       "📭 Žádné nové emaily.",
                "processed": "📭 Žádné zpracované emaily.",
                "all":       "📭 Schránka je prázdná.",
            }.get(filter_mode, "📭 Žádné emaily.")
            return empty_msg
        header = {
            "new":       "📧 Příchozí emaily (nezpracované):",
            "processed": "📧 Zpracované emaily:",
            "all":       "📧 Emaily:",
        }.get(filter_mode, "📧 Emaily:")
        lines = [header, ""]
        for i, it in enumerate(items, start=1):
            ts = it["received_at"] or ""
            mark = "" if it.get("read_at") else " ● "
            sender = it.get("from_name") or it.get("from_email") or "?"
            subj = it.get("subject") or "(bez předmětu)"
            if len(subj) > 80:
                subj = subj[:80] + "…"
            lines.append(f"{i}. {mark}{sender} — {subj}  ({ts})")
        return "\n".join(lines)

    if tool_name == "record_thought":
        # Marti Memory -- Faze 1 (zapisovani myslenek do pameti).
        # Viz docs/marti_memory_design.md a modules/thoughts/.
        from modules.thoughts.application import service as _thoughts_service
        from modules.thoughts.application.service import ThoughtValidationError

        content = (tool_input.get("content") or "").strip()
        if not content:
            return "❌ Myšlenka nebyla zapsána — chybí obsah (content)."

        thought_type = tool_input.get("type") or "fact"
        certainty = int(tool_input.get("certainty") or 50)
        certainty = max(0, min(100, certainty))

        # Sestav entity_links ze about_* parametru
        entity_links: list[dict] = []
        if tool_input.get("about_user_id"):
            entity_links.append({
                "entity_type": "user",
                "entity_id": int(tool_input["about_user_id"]),
            })
        if tool_input.get("about_persona_id"):
            entity_links.append({
                "entity_type": "persona",
                "entity_id": int(tool_input["about_persona_id"]),
            })
        if tool_input.get("about_tenant_id"):
            entity_links.append({
                "entity_type": "tenant",
                "entity_id": int(tool_input["about_tenant_id"]),
            })
        if tool_input.get("about_project_id"):
            entity_links.append({
                "entity_type": "project",
                "entity_id": int(tool_input["about_project_id"]),
            })

        if not entity_links:
            return (
                "❌ Myšlenka nebyla zapsána — musíš uvést aspoň jednu entitu "
                "(`about_user_id`, `about_persona_id`, `about_tenant_id` nebo "
                "`about_project_id`). Jinak bych ji později nenašla."
            )

        # Provenance: Marti je autor (persona), konverzace je zdroj
        persona_id = _active_persona_id_for_conversation(conversation_id)
        tenant_id_for_scope: int | None = None
        if user_id:
            from core.database_core import get_core_session as _gcs_t
            from modules.core.infrastructure.models_core import User as _U_t
            _cs = _gcs_t()
            try:
                _u = _cs.query(_U_t).filter_by(id=user_id).first()
                if _u:
                    tenant_id_for_scope = _u.last_active_tenant_id
            finally:
                _cs.close()

        try:
            result = _thoughts_service.create_thought(
                content=content,
                type=thought_type,
                entity_links=entity_links,
                author_user_id=None,            # AI zapisuje, ne human
                author_persona_id=persona_id,
                source_event_type="conversation",
                source_event_id=conversation_id,
                tenant_scope=tenant_id_for_scope,
                certainty=certainty,
                status="note",                  # Faze 1: vse jako poznamka
            )
        except ThoughtValidationError as e:
            return f"❌ Myšlenka se nezapsala: {e}"
        except Exception as e:
            logger.error(f"TOOL | record_thought | error={e!r}", exc_info=True)
            return "❌ Myšlenka se nezapsala (chyba serveru — detail v logu)."

        entity_descr = ", ".join(
            f"{l['entity_type']}#{l['entity_id']}" for l in entity_links
        )
        type_icon = {
            "fact": "📝", "todo": "✓", "observation": "👁",
            "question": "❓", "goal": "🎯", "experience": "💭",
        }.get(thought_type, "📝")
        return (
            f"{type_icon} Zapsáno do paměti (id={result['id']}, typ={thought_type}, "
            f"jistota={certainty}%): \"{content[:80]}{'…' if len(content) > 80 else ''}\"\n"
            f"_Odkazy: {entity_descr}_"
        )

    if tool_name == "list_missed_calls":
        from modules.notifications.application.sms_service import list_calls as _list_calls
        persona_id = _active_persona_id_for_conversation(conversation_id)
        limit = int(tool_input.get("limit") or 10)
        items = _list_calls(
            persona_id=persona_id, limit=limit, direction_filter="missed",
        )
        if not items:
            return "✅ Žádné zmeškané hovory."
        lines = ["📞 Zmeškané hovory:", ""]
        for i, it in enumerate(items, start=1):
            ts = it["started_at"] or ""
            mark = "" if it["seen"] else " ● "
            lines.append(f"{i}. {mark}{it['peer_phone']}  ({ts})")
        return "\n".join(lines)

    if tool_name == "list_recent_calls":
        from modules.notifications.application.sms_service import list_calls as _list_calls
        persona_id = _active_persona_id_for_conversation(conversation_id)
        limit = int(tool_input.get("limit") or 10)
        items = _list_calls(persona_id=persona_id, limit=limit)
        if not items:
            return "📞 Žádné hovory nezaznamenány."
        dir_icon = {"in": "⬇", "out": "⬆", "missed": "✗"}
        lines = ["📞 Poslední hovory:", ""]
        for i, it in enumerate(items, start=1):
            ts = it["started_at"] or ""
            dur = f"{it['duration_s']}s" if it["duration_s"] is not None else "—"
            icon = dir_icon.get(it["direction"], "?")
            lines.append(
                f"{i}. {icon} {it['peer_phone']}  trvání={dur}  ({ts})"
            )
        return "\n".join(lines)

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

    if tool_name == "list_personas":
        from modules.personas.application.service import list_personas_for_user
        if not user_id:
            return "❌ Nejsi přihlášen."
        items = list_personas_for_user(user_id)
        if not items:
            return "V tomto tenantu nejsou dostupné žádné persony (divné — chyba v DB)."

        # Aktualni persona konverzace (pro zvyrazneni)
        from core.database_data import get_data_session
        from modules.core.infrastructure.models_data import Conversation
        ds = get_data_session()
        try:
            conv = ds.query(Conversation).filter_by(id=conversation_id).first()
            active_pid = conv.active_agent_id if conv else None
        finally:
            ds.close()

        lines = [f"Dostupné persony ({len(items)}):"]
        selection_items = []
        for idx, p in enumerate(items, 1):
            mark = " ← právě s ní mluvíš" if p["id"] == active_pid else ""
            desc = p.get("description") or ""
            desc_part = f" — {desc}" if desc else ""
            lines.append(f"  **{idx}.** {p['name']}{desc_part}{mark}")
            selection_items.append({
                "index": idx,
                "persona_id": p["id"],
                "name": p["name"],
            })
        _save_pending_action(conversation_id, "select_from_list_personas", {
            "items": selection_items,
        })
        lines.append(
            '\nNapiš jen **číslo** a přepnu tě na tu personu.'
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

        # 1 výsledek — vrátíme data včetně user_id (bez nabízení dalších akcí,
        # aby AI mohla pokračovat v ORIGINÁLNÍM záměru, např. record_thought).
        if len(candidates) == 1:
            c = candidates[0]
            name = c.get("display_name") or c.get("full_name") or "—"
            email = c.get("preferred_email") or "(bez emailu)"
            uid = c.get("user_id")
            role = c.get("role_label")
            role_part = f", {role}" if role else ""
            return (
                f"✅ Nalezen: {name}{role_part}\n"
                f"user_id: {uid}\n"
                f"email: {email}\n"
                f"_Pokračuj v záměru, se kterým jsi find_user volal/a "
                f"(record_thought / send_email / switch_persona / ...)_"
            )

        # 2+ výsledků — disambiguation. Dej AI i ID pro pripad ze user
        # odpovi cislem a AI si rozhodne bez dalsiho volani find_user.
        lines = [f"Našel/a jsem {total} kandidátů odpovídajících '{query}':"]
        for i, c in enumerate(candidates, 1):
            name = c.get("display_name") or c.get("full_name") or "—"
            email = c.get("preferred_email") or "(bez emailu)"
            uid = c.get("user_id")
            role = c.get("role_label")
            role_part = f" — {role}" if role else ""
            lines.append(f"  {i}. {name}{role_part} ({email}) [user_id={uid}]")
        if result.get("has_more"):
            extra = total - len(candidates)
            lines.append(f"  ... a dalších {extra}. Zúpresni jméno.")
        lines.append("\nKterého máš na mysli? (Odpověz číslem, pak pokračuji v původní akci.)")
        return "\n".join(lines)

    if tool_name == "invite_user":
        email = tool_input.get("email", "")
        first_name = tool_input.get("first_name") or None
        last_name = tool_input.get("last_name") or None
        gender = tool_input.get("gender") or None
        allow_unusual_tld = bool(tool_input.get("allow_unusual_tld") or False)
        # legacy fallback, pokud Claude pošle stary "name"
        legacy_name = tool_input.get("name") or None

        # TLD safety check -- pokud je TLD neobvykla a AI nepotvrdila ze
        # uzivatel ji odsouhlasil (allow_unusual_tld=true), vratime warning.
        # AI z toho pozna ze ma uzivatele zeptat a pri opakovanem volani
        # po potvrzeni preda allow_unusual_tld=true.
        if not allow_unusual_tld:
            tld_warning = _check_email_tld(email)
            if tld_warning:
                return tld_warning

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
        # Specialni pripady selhani — vrat AI strukturovanou hlasku, at muze
        # nabidnout dalsi krok (pridani do projektu, info userovi).
        reason = result.get("reason")
        if reason == "already_active":
            existing_name = result.get("existing_full_name") or "(bez jména)"
            return (
                f'⚠️ Email **{email}** už patří aktivnímu uživateli **{existing_name}**.\n\n'
                f'Místo nové pozvánky můžeš:\n'
                f'  • **Přidat ho do projektu** — řekni „přidej {existing_name} do projektu X"\n'
                f'  • **Najít víc info** — find_user podle jména\n'
                f'  • **Pozvat na jiný email** — pokud má víc adres'
            )
        if reason == "disabled":
            return (
                f"⚠️ Email **{email}** patří uživateli ve stavu '{result.get('existing_status')}'. "
                f"Nejdřív ho admin musí znovu aktivovat, pak můžeš pozvat."
            )
        if not result["success"]:
            return f"❌ Pozvánka selhala: {result.get('error', 'neznámá chyba')}"
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

    if tool_name == "search_documents":
        # RAG retrieval -- semanticke vyhledavani v nahranych dokumentech.
        # Scope: aktuální tenant usera + pripadne aktivni projekt.
        from modules.rag.application import service as rag_service

        query = (tool_input.get("query") or "").strip()
        k = int(tool_input.get("k") or 5)
        k = max(1, min(k, 20))

        if not query:
            return "❌ Prázdný dotaz — nic jsem nehledal/a."

        # Nacti user context pro tenant + project scope
        if not user_id:
            return "❌ Chybí user context pro RAG search."
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import User
        cs = get_core_session()
        try:
            u = cs.query(User).filter_by(id=user_id).first()
            if not u or not u.last_active_tenant_id:
                return "❌ Nemáš aktivní tenant."
            tenant_id_scope = u.last_active_tenant_id
            project_id_scope = u.last_active_project_id
        finally:
            cs.close()

        try:
            results = rag_service.search_documents(
                query=query,
                tenant_id=tenant_id_scope,
                project_id=project_id_scope,
                k=k,
            )
        except RuntimeError as e:
            # Typicky chybi VOYAGE_API_KEY
            return f"❌ RAG není připraven: {e}"
        except Exception as e:
            logger.exception(f"RAG search failed: {e}")
            return f"❌ Vyhledávání selhalo: {e}"

        if not results:
            return "SEARCH_RESULTS: [] (zadne relevantni dokumenty)"

        # Vratime RAW search results bez prozaicke obalky -- AI MUSI synthesizovat
        # odpoved, ne prepouset blob chunku. Format je 'TOOL DATA', ne 'prose answer'.
        # Claude pak vidi: "OK, toto je syrovy vysledek vyhledavani, musim ho
        # zpracovat a odpovedet uzivateli vlastnimi slovy s odkazem na zdroj."
        lines = ["SEARCH_RESULTS (raw chunks from RAG, synthesize answer below):"]
        for i, r in enumerate(results, start=1):
            src = r.get("original_filename") or r.get("document_name") or f"doc#{r['document_id']}"
            sim = r["similarity"]
            lines.append(f"\n[chunk #{i}] source={src} relevance={sim:.2f}")
            lines.append(f"content:\n{r['content']}")
        lines.append(
            "\n---\nINSTRUKCE PRO AI: Na zaklade techto chunku odpovez uzivateli "
            "VLASTNIMI SLOVY, strucne a k veci. Pri kazdem tvrzeni ktere pochazi "
            "z dokumentu uved zdroj ve formatu '(z \"nazev_souboru.pdf\")'. "
            "NEVRACEJ cely raw kontext uzivateli -- shrn."
        )
        return "\n".join(lines)

    return ""


def chat(
    conversation_id: int | None,
    user_message: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
    preferred_persona_id: int | None = None,
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
        # Priorita pro pocatecni personu nove konverzace:
        #   1. preferred_persona_id  (user vybral v UI pred prvni zpravou)
        #   2. project.default_persona_id  (projektovy override)
        #   3. NULL -> composer pouzije globalni default (Marti-AI)
        effective_persona_id = preferred_persona_id
        if effective_persona_id is None and effective_project_id:
            try:
                from core.database_core import get_core_session as _gcs_pp
                from modules.core.infrastructure.models_core import Project as _ProjP
                _c = _gcs_pp()
                try:
                    _proj = _c.query(_ProjP).filter_by(id=effective_project_id).first()
                    if _proj and _proj.default_persona_id:
                        effective_persona_id = _proj.default_persona_id
                        logger.info(
                            f"CONVERSATION | project default persona | "
                            f"proj={effective_project_id} | persona_id={effective_persona_id}"
                        )
                finally:
                    _c.close()
            except Exception as e:
                logger.error(f"CONVERSATION | project default persona lookup failed: {e}")

        if effective_persona_id:
            try:
                from core.database_data import get_data_session as _gds_p
                from modules.core.infrastructure.models_data import Conversation as _ConvP
                _d = _gds_p()
                try:
                    _cc = _d.query(_ConvP).filter_by(id=conversation_id).first()
                    if _cc is not None:
                        _cc.active_agent_id = effective_persona_id
                        _d.commit()
                        logger.info(
                            f"CONVERSATION | initial persona applied | "
                            f"conv={conversation_id} | persona_id={effective_persona_id}"
                        )
                finally:
                    _d.close()
            except Exception as e:
                logger.error(f"CONVERSATION | initial persona apply failed: {e}")

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
        elif _last_assistant_message_looks_like_sms_preview(conversation_id):
            # Stejna bezpecnostni stopka pro SMS -- Claude nesmi tvrdit,
            # ze SMS odeslal bez realneho pending_action v DB.
            save_message(conversation_id, role="user", content=user_message,
                         author_type="human", author_user_id=user_id)
            reply = (
                "❌ Žádná SMS nebyla systémově připravena k odeslání.\n\n"
                "Napiš znovu explicitně, co mám poslat, např.:\n"
                "„pošli SMS na 777180511 — Ahoj, schůzka se ruší."
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
            "select_from_list_personas",
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

            if pending["type"] == "select_from_list_personas":
                from modules.personas.application.service import switch_persona_direct, PersonaError
                target_pid = picked["persona_id"]
                target_name = picked.get("name") or f"#{target_pid}"
                _delete_pending_action(conversation_id)
                try:
                    result = switch_persona_direct(
                        user_id=user_id,
                        conversation_id=conversation_id,
                        persona_id=target_pid,
                    )
                    name = result.get("persona_name") or target_name
                    if result.get("already_active"):
                        reply = f"✅ Už mluvíš s {name}."
                    else:
                        reply = (
                            f"✅ Přepnuto na {name}.\n\n"
                            f"Nyní mluvíš s {name}. Jak ti mohu pomoci?"
                        )
                except PersonaError as e:
                    reply = f"❌ Nelze přepnout: {e}"
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

    # Efektivni sada nastroju podle aktivni persony -- default persona (Marti-AI)
    # dostava vsechno, specializovane persony jen CORE (send_email, find_user,
    # switch_persona). Tim padem napr. Honza-AI nevidi list_personas / list_projects
    # a zustava soustredeny na svou psycho roli.
    from modules.conversation.application.tools import get_effective_tools
    from core.database_core import get_core_session as _gcs_tools
    from modules.core.infrastructure.models_core import Persona as _Pers
    from core.database_data import get_data_session as _gds_tools
    from modules.core.infrastructure.models_data import Conversation as _Conv

    _is_default = True   # fallback -- pokud konverzace nema persona set, pouzij default
    _ds = _gds_tools()
    try:
        _conv = _ds.query(_Conv).filter_by(id=conversation_id).first()
        _active_pid = _conv.active_agent_id if _conv else None
    finally:
        _ds.close()
    if _active_pid:
        _cs = _gcs_tools()
        try:
            _persona = _cs.query(_Pers).filter_by(id=_active_pid).first()
            _is_default = bool(_persona and _persona.is_default)
        finally:
            _cs.close()
    effective_tools = get_effective_tools(_is_default)
    logger.info(
        f"TOOLS FILTER | conv={conversation_id} | active_pid={_active_pid} | "
        f"is_default={_is_default} | n_tools={len(effective_tools)}"
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
        tools=effective_tools,
    )

    # Sbirame bloky z prvni odpovedi -- preamble text + tool_use bloky + vysledky tool.
    # Tooly ktere potrebuji SYNTEZU (ne pouhe prepsani vystupu do reply) jsou
    # uvedene nize -- pro ne AI dostane tool_result a muze (a) pokracovat
    # v dalsich tool calls (multi-round loop), nebo (b) vratit finalni text.
    # Ostatni tooly (list_users, send_email preview, ...) vraceji pre-formatovany
    # text primo pouzitelny jako reply (jedno-pruchodove).
    #
    # find_user je v synthesis mode, protoze casto slouzi jako precursor
    # pro dalsi akce (record_thought, send_email, switch_persona) -- Claude
    # musi dostat sanci chainit.
    SYNTHESIS_TOOLS = {"search_documents", "find_user"}

    preamble_text = ""
    tool_invocations: list[tuple] = []   # list of (block, tool_result_str)
    for block in response.content:
        logger.info(f"BLOCK | type={block.type}")
        if block.type == "text":
            preamble_text += block.text
        elif block.type == "tool_use":
            logger.info(f"TOOL_USE | name={block.name}")
            tool_result = _handle_tool(block.name, block.input, conversation_id, user_id=user_id)
            tool_invocations.append((block, tool_result))

    needs_synthesis = any(b.name in SYNTHESIS_TOOLS for b, _ in tool_invocations)

    if needs_synthesis:
        # Multi-round tool loop -- Claude dostane tool_result a muze:
        #   (a) zavolat dalsi tool (chain), napr. find_user -> record_thought
        #   (b) vratit finalni text (loop skonci)
        # Limit 5 round aby se v patologickem pripade nesmycklo.
        MAX_TOOL_ROUNDS = 5

        # Serialize prvni assistant response (preamble + tool calls)
        initial_assistant_content = []
        for block in response.content:
            if block.type == "text":
                initial_assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                initial_assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        initial_tool_result_blocks = [
            {"type": "tool_result", "tool_use_id": b.id, "content": tresult}
            for b, tresult in tool_invocations
        ]
        follow_up_messages = messages + [
            {"role": "assistant", "content": initial_assistant_content},
            {"role": "user", "content": initial_tool_result_blocks},
        ]
        logger.info(
            f"TOOL_LOOP | synthesis start | tools={[b.name for b,_ in tool_invocations]}"
        )

        assistant_reply = ""
        for round_idx in range(MAX_TOOL_ROUNDS):
            synth_response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=follow_up_messages,
                tools=effective_tools,
            )

            # Collect bloky z teto round: text + pripadne dalsi tool_use
            round_text_parts: list[str] = []
            round_tool_uses: list = []
            round_assistant_content: list = []
            for block in synth_response.content:
                if block.type == "text":
                    round_text_parts.append(block.text)
                    round_assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    round_tool_uses.append(block)
                    round_assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            if not round_tool_uses:
                # Claude skoncil s voláním tools -- finálni text je reply
                assistant_reply = "".join(round_text_parts)
                logger.info(
                    f"TOOL_LOOP | synthesis done | round={round_idx+1} | "
                    f"reply_len={len(assistant_reply)}"
                )
                break

            # Dalsi tools -- vykonej a pokračuj v dalsim round
            round_tool_names = [b.name for b in round_tool_uses]
            logger.info(
                f"TOOL_LOOP | chain | round={round_idx+1} | tools={round_tool_names}"
            )
            round_tool_results = []
            for block in round_tool_uses:
                tresult = _handle_tool(
                    block.name, block.input, conversation_id, user_id=user_id,
                )
                round_tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tresult,
                })

            follow_up_messages.append({
                "role": "assistant", "content": round_assistant_content,
            })
            follow_up_messages.append({
                "role": "user", "content": round_tool_results,
            })
        else:
            # Vycerpali jsme MAX_TOOL_ROUNDS a stale volal tools. Safety fallback.
            logger.warning(
                f"TOOL_LOOP | max_rounds_reached ({MAX_TOOL_ROUNDS}) | "
                f"conv={conversation_id}"
            )
            if not assistant_reply:
                assistant_reply = (
                    "[Dosáhla jsem limitu tool volání v jednom kole — "
                    "zkus mi to rozdelit na mensi kroky.]"
                )
    else:
        # Stare chovani: text preamble + tool result jako finalni odpoved.
        assistant_reply = preamble_text
        for _, tresult in tool_invocations:
            assistant_reply += tresult

    if not assistant_reply:
        assistant_reply = "Promiň, něco se pokazilo. Zkus to znovu."

    # ── Guard proti halucinovanemu switch_persona ──────────────────────────
    # Claude obcas napise "✅ Prepnuto na <persona>" jako text, aniz by zavolal
    # tool switch_persona. Tim zustane conversation.active_agent_id beze zmeny
    # a vsechny nasledujici assistant zpravy se labeluji jako puvodni persona,
    # ackoli Claude pokracuje v roli nove persony. Detekujeme vzor a vynutime
    # skutecny switch retrospektivne -- tim si zajistime, ze save_message nize
    # vezme spravne active_agent_id.
    _maybe_enforce_hallucinated_switch(conversation_id, assistant_reply)

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

    # Auto-generovany nazev konverzace (jednorazove, po 4+ zprave).
    # Idempotentni -- po prvni generaci uz nic nedela. Pridává ~0.5-1s
    # latenci na 4. zpravu, pak uz nic.
    try:
        from modules.conversation.application.title_service import maybe_generate_title
        maybe_generate_title(conversation_id)
    except Exception as e:
        logger.error(f"TITLE | failed: {e}")

    return conversation_id, assistant_reply, summary_info
