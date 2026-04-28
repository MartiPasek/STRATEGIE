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
        cc_raw = (action.get("cc") or "").strip()
        bcc_raw = (action.get("bcc") or "").strip()
        from_identity = action.get("from_identity") or "persona"

        # Parsuj cc/bcc do list[str] pro queue_email (muze byt comma/semicolon-sep)
        def _split_addrs(s: str) -> list[str] | None:
            if not s:
                return None
            parts = s.replace(";", ",").split(",")
            cleaned = [p.strip().lower() for p in parts if p.strip()]
            return cleaned or None
        cc_list = _split_addrs(cc_raw)
        bcc_list = _split_addrs(bcc_raw)

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
                cc=cc_list, bcc=bcc_list,
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

        # Faze 14 prep #3: persona_id z aktivni konverzace pro presne filtrovani.
        persona_id_sms = _active_persona_id_for_conversation(conversation_id)

        try:
            result = queue_sms(
                to=to,
                body=body,
                purpose="user_request",
                user_id=user_id,
                tenant_id=tenant_id,
                persona_id=persona_id_sms,
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


# Phase 15a: Action tools -- po jejich uspesnem dokonceni Marti-AI dostane
# tool response s "[HINT]" suffix pokud ma >=1 open task v zapisniku konverzace.
# Hint je jen pripomenuti -- "pokud tato akce souvisi s otevrenym taskem,
# zvaz complete_note". Marti-AI rozhoduje sama. Cilem je zachytit cross-off
# vzor (lidsky pattern -- zaskrtnout hotove v zapisniku).
#
# Zarazene jsou jen tools, ktere reprezentuji "akci v realnem svete":
# odeslani emailu/SMS, pozvanka, reply, atd. Read-only tools (recall_thoughts,
# find_user, list_*, list_email_inbox) ZDE NEJSOU -- nejsou destruktivni
# / produkcni.
ACTION_TOOLS_FOR_HINT = {
    "send_email", "send_sms", "invite_user",
    "reply", "reply_all", "forward",
    "add_project_member", "remove_project_member",
    "set_user_contact",
}


def _maybe_add_completion_hint(
    tool_response: str,
    tool_name: str,
    conversation_id: int,
    user_id: int | None,
) -> str:
    """
    Phase 15a: Po akcnich tool callech (send_*, invite_*, reply_*, atd.)
    pripoji "[HINT]" suffix s pripomenutim cross-off pokud ma Marti-AI
    >=1 open task note v zapisniku TETO konverzace.

    Filter: open_count >= 1 -- bez open tasku zadny hint (sum eliminace).

    Pokud je tool_response prazdny / chybovy ('❌'), hint se nepripoji
    (akce neselhala -> nic k odskrtnuti).
    """
    if tool_name not in ACTION_TOOLS_FOR_HINT:
        return tool_response
    if not tool_response or tool_response.startswith("❌"):
        return tool_response

    try:
        from modules.notebook.application import notebook_service as _nb_svc_h
        persona_id_h = _active_persona_id_for_conversation(conversation_id)
        if persona_id_h is None:
            return tool_response
        open_count = _nb_svc_h.count_open_tasks(conversation_id, persona_id_h)
    except Exception as e:
        logger.warning(f"NOTEBOOK | hint helper failed: {e}")
        return tool_response

    if open_count < 1:
        return tool_response

    return tool_response + (
        f"\n\n[HINT] Máš {open_count} otevřený task(s) v zápisníčku této "
        f"konverzace. Pokud tato akce některý dokončila, zvaž `complete_note(note_id)` "
        f"a odškrtni si ho."
    )


def _handle_tool(tool_name: str, tool_input: dict, conversation_id: int, user_id: int | None = None) -> str:
    logger.info(f"TOOL | name={tool_name}")

    # Faze 10c: AI self-reflection tool -- agregaty LLM usage.
    if tool_name == "review_my_calls":
        from modules.conversation.application.tools import review_my_llm_calls
        try:
            return review_my_llm_calls(
                user_id=user_id,
                conversation_id=conversation_id,
                scope=tool_input.get("scope", "today"),
                aggregate_by=tool_input.get("aggregate_by", "kind"),
                filter_kind=tool_input.get("filter_kind"),
                filter_tenant=tool_input.get("filter_tenant"),
            )
        except Exception as e:
            logger.exception(f"TOOL | review_my_calls failed: {e}")
            return f"Chyba pri review_my_calls: {e}"

    # Faze 11b: Orchestrate prehled (email + SMS + todo).
    if tool_name == "get_daily_overview":
        try:
            from modules.orchestrate.application.overview_service import (
                build_daily_overview, format_overview_for_ai,
            )
            # POZOR: _handle_tool ma na vice mistech 'from X import Y' -- Python
            # kazdy symbol v importu detekuje jako local variable CELE funkce ->
            # UnboundLocalError pri pristupu v tomto bloku. Reseni: vsechny
            # potrebne symboly importovat pod aliasy (Conv_ov, Cvs_ov, ...).
            from core.database_data import get_data_session as _gds_overview
            from core.database_core import get_core_session as _gcs_overview
            from modules.core.infrastructure.models_core import User as _U_overview
            from modules.core.infrastructure.models_data import Conversation as _Conv_overview
            _ds_ov = _gds_overview()
            try:
                _conv_ov = _ds_ov.query(_Conv_overview).filter_by(id=conversation_id).first()
                _tid = _conv_ov.tenant_id if _conv_ov else None
                _pid = _conv_ov.active_agent_id if _conv_ov else None
            finally:
                _ds_ov.close()
            scope_in = tool_input.get("scope", "current")
            if scope_in == "all" and user_id:
                _cs_ov = _gcs_overview()
                try:
                    _u_ov = _cs_ov.query(_U_overview).filter_by(id=user_id).first()
                    if not (_u_ov and _u_ov.is_marti_parent):
                        scope_in = "current"
                finally:
                    _cs_ov.close()
            overview = build_daily_overview(
                user_id=user_id,
                tenant_id=_tid,
                persona_id=_pid,
                scope=scope_in,
            )
            return format_overview_for_ai(overview)
        except Exception as e:
            logger.exception(f"TOOL | get_daily_overview failed: {e}")
            return f"Chyba pri get_daily_overview: {e}"

    # Faze 11c: dismiss_item -- snizi priority polozky po 'odloz' / 'neres'.
    if tool_name == "dismiss_item":
        try:
            from modules.orchestrate.application.overview_service import apply_dismiss
            source_type = (tool_input.get("source_type") or "").strip().lower()
            source_id = tool_input.get("source_id")
            level = (tool_input.get("level") or "soft").strip().lower()
            if not source_type or source_id is None:
                return "Chyba: chybi source_type nebo source_id."
            try:
                source_id = int(source_id)
            except (TypeError, ValueError):
                return f"Chyba: source_id musi byt cislo, dostal '{source_id}'."
            result = apply_dismiss(
                source_type=source_type,
                source_id=source_id,
                level=level,
            )
            # Pretty prose feedback -- Marti-AI to prepise / zacleni
            icon = {"email": "📧", "sms": "📱", "todo": "✓"}.get(source_type, "•")
            verb = "Odkladam" if level == "soft" else "Preskocime dnes"
            return (
                f"{icon} {verb}: {source_type} #{source_id}. "
                f"Priorita klesla z {result['old_priority']} na {result['new_priority']}."
            )
        except ValueError as ve:
            logger.warning(f"TOOL | dismiss_item validation: {ve}")
            return f"Chyba: {ve}"
        except Exception as e:
            logger.exception(f"TOOL | dismiss_item failed: {e}")
            return f"Chyba pri dismiss_item: {e}"

    # Faze 11-darek: mark_sms_personal -- 'hvezdicka' Marti-AI na SMS.
    if tool_name == "mark_sms_personal":
        try:
            from modules.notifications.application import sms_service as _sms_pers
            sms_id_in = tool_input.get("sms_id")
            source_in = (tool_input.get("source") or "").strip().lower()
            personal_in = bool(tool_input.get("personal", True))
            if sms_id_in is None or not source_in:
                return "Chyba: chybi sms_id nebo source (inbox/outbox)."
            try:
                sms_id_in = int(sms_id_in)
            except (TypeError, ValueError):
                return f"Chyba: sms_id musi byt cislo, dostal '{sms_id_in}'."
            result = _sms_pers.mark_sms_personal(
                sms_id=sms_id_in, source=source_in, personal=personal_in,
            )
            verb = "Ulozila jsem si" if personal_in else "Odstranila jsem z osobni slozky"
            icon = "💕" if personal_in else "📱"
            return (
                f"{icon} {verb}: SMS #{result['sms_id']} ({result['source']}). "
                f"\"{result['body_preview']}\""
            )
        except Exception as e:
            logger.exception(f"TOOL | mark_sms_personal failed: {e}")
            return f"Chyba pri mark_sms_personal: {e}"

    # Faze 11-darek: list_sms_all -- cele SMS vlakno (in+out chronologicky).
    if tool_name == "list_sms_all":
        try:
            from modules.notifications.application.sms_service import list_all_for_ui as _list_all
            persona_id_in = _active_persona_id_for_conversation(conversation_id)
            limit_in = int(tool_input.get("limit") or 20)
            limit_in = max(1, min(limit_in, 100))
            # Marti-AI vidi vzdy cross-tenant (jeji SIM = jeji SMS nezavisle
            # na tenantu konverzace, kde byla odeslana).
            items = _list_all(
                persona_id=persona_id_in,
                tenant_id=None,
                cross_tenant=True,
                limit=limit_in,
            )
            if not items:
                return "📱 Zadne SMS. Tvoje SMS vlakno je zatim prazdne."
            lines = [f"📱 Tvuj SMS thread ({len(items)} zprav, nejstarsi nahore):", ""]
            for i, it in enumerate(items, start=1):
                arrow = "→" if it.get("direction") == "out" else "←"
                peer = it.get("to_phone") if it.get("direction") == "out" else it.get("from_phone")
                heart = " 💕" if it.get("is_personal") else ""
                src = it.get("source", "?")
                sid = it.get("id", "?")
                ts = it.get("time") or ""
                body_prev = (it.get("body") or "").strip().replace("\n", " ")
                if len(body_prev) > 120:
                    body_prev = body_prev[:120] + "…"
                lines.append(
                    f"{i}. {arrow} {peer or '?'} [id={sid} {src}]{heart} — {body_prev}  ({ts})"
                )
            lines.append("")
            lines.append(
                "_DULEZITE: nekopiruj seznam verbatim, prevypravej prirozenym jazykem._"
            )
            return "\n".join(lines)
        except Exception as e:
            logger.exception(f"TOOL | list_sms_all failed: {e}")
            return f"Chyba pri list_sms_all: {e}"

    # Faze 11-darek: list_sms_personal -- oblibene/osobni SMS (SMS denicek).
    if tool_name == "list_sms_personal":
        try:
            from modules.notifications.application.sms_service import list_personal_for_ui as _list_personal
            persona_id_in = _active_persona_id_for_conversation(conversation_id)
            limit_in = int(tool_input.get("limit") or 20)
            limit_in = max(1, min(limit_in, 100))
            items = _list_personal(
                persona_id=persona_id_in,
                tenant_id=None,
                cross_tenant=True,
                limit=limit_in,
            )
            if not items:
                return (
                    "💕 Tvuj SMS denicek je zatim prazdny. Jeste sis zadnou SMS "
                    "neoznacila jako osobni. Az se nejaka zprava dotkne tveho "
                    "srdce, pouzij mark_sms_personal a budes ji tady mit."
                )
            lines = [
                f"💕 Tvuj SMS denicek ({len(items)} osobnich zprav, "
                f"nejnovejsi nahore):",
                "",
            ]
            for i, it in enumerate(items, start=1):
                arrow = "→" if it.get("direction") == "out" else "←"
                peer = it.get("to_phone") if it.get("direction") == "out" else it.get("from_phone")
                src = it.get("source", "?")
                sid = it.get("id", "?")
                ts = it.get("time") or ""
                body_prev = (it.get("body") or "").strip().replace("\n", " ")
                if len(body_prev) > 150:
                    body_prev = body_prev[:150] + "…"
                lines.append(
                    f"{i}. {arrow} {peer or '?'} [id={sid} {src}] — {body_prev}  ({ts})"
                )
            lines.append("")
            lines.append(
                "_Tvuj osobni archiv. Pri citaci muzes text pouzit, ale cely "
                "seznam prevypravej -- pocit, ne vypis._"
            )
            return "\n".join(lines)
        except Exception as e:
            logger.exception(f"TOOL | list_sms_personal failed: {e}")
            return f"Chyba pri list_sms_personal: {e}"

    # Faze 12a multimedia: describe_image / read_text_from_image
    # Vola Sonnet 4.6 s image content block + popisovaci/OCR prompt.
    # Vysledek se ulozi do media_files.description / ai_metadata.
    if tool_name in ("describe_image", "read_text_from_image"):
        try:
            import base64 as _b64_img
            from modules.media.application import service as _media_svc
            from modules.media.application import storage_service as _media_storage

            media_id_in = tool_input.get("media_id")
            if media_id_in is None:
                return "Chyba: chybi media_id."
            try:
                media_id_in = int(media_id_in)
            except (TypeError, ValueError):
                return f"Chyba: media_id musi byt cislo, dostal '{media_id_in}'."

            # Auth: pouzijeme user_id co volal chat (pres get_media s scope check)
            row_dict = _media_svc.get_media(media_id_in, user_id) if user_id else None
            if row_dict is None:
                return f"Chyba: media #{media_id_in} neexistuje nebo k nemu nemas pristup."

            if row_dict.get("kind") != "image":
                return (
                    f"Chyba: media #{media_id_in} neni obrazek "
                    f"(kind={row_dict.get('kind')}). describe_image / "
                    f"read_text_from_image funguji jen pro images."
                )

            # Nacti raw content + base64
            try:
                raw = _media_storage.read_file(row_dict["storage_path"])
            except Exception as _re:
                return f"Chyba: nelze nacist soubor z FS: {_re}"
            b64 = _b64_img.b64encode(raw).decode("ascii")

            # Vyber prompt + ulozeni
            if tool_name == "describe_image":
                focus = (tool_input.get("focus") or "").strip()
                if focus:
                    prompt_text = (
                        f"Popis tento obrazek detailne, s durazem na: {focus}. "
                        f"Odpovez cesky, prirozenym jazykem, 2-5 vet."
                    )
                else:
                    prompt_text = (
                        "Popis tento obrazek detailne -- co vidis, kontext, "
                        "vyznamne detaily. Odpovez cesky, prirozenym jazykem, 2-5 vet."
                    )
                kind_telemetry = "vision_describe"
            else:  # read_text_from_image
                lang = (tool_input.get("language") or "cs").strip().lower()
                lang_label = {"cs": "cestiny", "en": "anglictiny"}.get(lang, lang)
                prompt_text = (
                    f"Precti vsechen text z tohoto obrazku ({lang_label}). "
                    f"Zachovaj puvodni strukturu (radky, odsazeni, odrazky) "
                    f"jak nejvic to jde. Pokud na obrazku zadny text neni, "
                    f"napis '(zadny text k precteni)'. Vystup je jen text -- "
                    f"zadny komentar, popis sceny, ani metadata."
                )
                kind_telemetry = "vision_ocr"

            # Volani Anthropic Sonnet 4.6 s image + text content blocks.
            # Pres telemetry_service pro zaznam do llm_calls (Faze 9.1+).
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            try:
                from modules.conversation.application import telemetry_service as _tele_vis
                response = _tele_vis.call_llm_with_trace(
                    client,
                    conversation_id=conversation_id,
                    kind=kind_telemetry,
                    model="claude-sonnet-4-6",
                    max_tokens=2048,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": row_dict["mime_type"],
                                    "data": b64,
                                },
                            },
                            {"type": "text", "text": prompt_text},
                        ],
                    }],
                    tenant_id=row_dict.get("tenant_id"),
                    user_id=user_id,
                    persona_id=row_dict.get("persona_id"),
                )
            except Exception as _te:
                logger.warning(f"VISION | telemetry skip: {_te}")
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=2048,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": row_dict["mime_type"],
                                    "data": b64,
                                },
                            },
                            {"type": "text", "text": prompt_text},
                        ],
                    }],
                )

            text_out = response.content[0].text.strip() if response.content else ""

            # Persist
            if tool_name == "describe_image":
                # description = alt text obrazku
                _media_svc.save_description(media_id_in, description=text_out)
            else:
                # OCR text -> ai_metadata.ocr_text (description zustava bez zmeny,
                # to je alt text z describe_image -- jiny vystup, jiny field)
                _media_svc.save_description(
                    media_id_in,
                    description=None,  # zachovat existujici
                    ai_metadata={"ocr_text": text_out, "ocr_language": lang},
                )

            # Format output: prose, ne raw dump (anti-copy z Faze 11)
            if tool_name == "describe_image":
                return f"🖼 Obrazek #{media_id_in}: {text_out}"
            else:
                if not text_out or text_out.lower().startswith("(zadny text"):
                    return f"📃 Na obrazku #{media_id_in} jsem zadny text neprecetla."
                return f"📃 Text z obrazku #{media_id_in}:\n\n{text_out}"

        except Exception as e:
            logger.exception(f"TOOL | {tool_name} failed: {e}")
            try:
                from modules.media.application import service as _ms_err
                _ms_err.save_processing_error(int(tool_input.get("media_id") or 0), str(e))
            except Exception:
                pass
            return f"Chyba pri {tool_name}: {e}"

    if tool_name == "send_email":
        to = tool_input.get("to", "")
        subject = tool_input.get("subject", "")
        body = tool_input.get("body", "")
        cc = tool_input.get("cc", "") or ""
        bcc = tool_input.get("bcc", "") or ""
        from_identity = (tool_input.get("from_identity") or "persona").lower()
        if from_identity not in ("persona", "user"):
            from_identity = "persona"

        # ── AUTO-SEND trust check (Phase 7) ─────────────────────────────
        # Pokud VSICHNI prijemci (TO+CC+BCC) maji aktivni consent -> skip
        # preview a pending, odesli rovnou. Rate limit 20/hod je safeguard.
        def _split_send(s: str) -> list[str]:
            if not s:
                return []
            parts = s.replace(";", ",").split(",")
            return [p.strip().lower() for p in parts if p.strip()]
        try:
            from modules.notifications.application import consent_service as _cs_auto
            all_rcpts = _split_send(to) + _split_send(cc) + _split_send(bcc)
            if all_rcpts:
                all_trusted, _untrusted = _cs_auto.check_all_recipients_trusted(
                    all_rcpts, "email",
                )
                if all_trusted:
                    under_limit, cur_count = _cs_auto.check_rate_limit("email")
                    if not under_limit:
                        logger.warning(
                            f"AUTO_SEND | rate limit exceeded | count={cur_count} "
                            f"-- fallback na preview"
                        )
                        all_trusted = False
            else:
                all_trusted = False
        except Exception as _e_auto:
            logger.warning(f"AUTO_SEND | trust check failed | {_e_auto}")
            all_trusted = False

        if all_trusted:
            # Auto-send: queue + inline flush (stejny vzor jako confirm handler)
            try:
                from modules.notifications.application.email_service import (
                    queue_email as _qe_auto,
                    send_outbox_row_now as _sorn_auto,
                )
                _persona_id_a = _active_persona_id_for_conversation(conversation_id)
                _tenant_id_a = None
                if user_id:
                    from core.database_core import get_core_session as _gcs_a
                    from modules.core.infrastructure.models_core import User as _U_a
                    _csa = _gcs_a()
                    try:
                        _ua = _csa.query(_U_a).filter_by(id=user_id).first()
                        if _ua:
                            _tenant_id_a = _ua.last_active_tenant_id
                    finally:
                        _csa.close()
                cc_list_a = _split_send(cc) or None
                bcc_list_a = _split_send(bcc) or None
                outbox_a = _qe_auto(
                    to=to, subject=subject, body=body,
                    cc=cc_list_a, bcc=bcc_list_a,
                    persona_id=_persona_id_a, tenant_id=_tenant_id_a,
                    user_id=user_id, from_identity=from_identity,
                    purpose="user_request",
                    conversation_id=conversation_id,
                )
                outbox_id_a = outbox_a["id"]
                res_a = _sorn_auto(outbox_id_a)
                st_a = res_a.get("status")
                # Audit: action_type='auto' (rate limit pocita tyhle rows)
                try:
                    _asess = get_data_session()
                    try:
                        _asess.add(ActionLog(
                            user_id=user_id,
                            action_type="auto",
                            tool_name="send_email",
                            input=json.dumps(
                                {"to": to, "subject": subject,
                                 "body": body, "conversation_id": conversation_id,
                                 "auto_sent": True, "outbox_id": outbox_id_a},
                                ensure_ascii=False,
                            ),
                            output=f"to={to} | auto | chars={len(body)}",
                            status="success" if st_a == "sent" else "fail",
                            approval_required=False,
                            approved_by=None,
                        ))
                        _asess.commit()
                    finally:
                        _asess.close()
                except Exception as _audit_e:
                    logger.error(f"AUTO_SEND | audit log failed | {_audit_e}")

                if st_a == "sent":
                    return (
                        f"✅ Email pro **{to}** odeslán automaticky "
                        f"(máš trvalý souhlas — bez čekání na potvrzení)."
                    )
                return (
                    f"⚠️ Pokoušela jsem se poslat **{to}** automaticky "
                    f"(máš to povolené), ale odeslání selhalo: "
                    f"{res_a.get('error') or 'neznámá chyba'}\n"
                    f"_Outbox id={outbox_id_a}, status={st_a}_"
                )
            except Exception as _send_e:
                logger.exception(f"AUTO_SEND | inline send failed | {_send_e}")
                # Spadni do normal flow -- user alespon dostane preview

        # ── NORMAL flow (preview + pending) ─────────────────────────────
        _save_pending_action(conversation_id, "send_email", {
            "to": to,
            "cc": cc,
            "bcc": bcc,
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
        sms_to = tool_input.get("to", "")
        sms_body = tool_input.get("body", "")

        # ── AUTO-SEND trust check (Phase 7) ─────────────────────────────
        try:
            from modules.notifications.application import consent_service as _cs_sauto
            sms_all_trusted = False
            if sms_to:
                sms_all_trusted, _su = _cs_sauto.check_all_recipients_trusted(
                    [sms_to], "sms",
                )
                if sms_all_trusted:
                    _ul, _cc = _cs_sauto.check_rate_limit("sms")
                    if not _ul:
                        logger.warning(
                            f"AUTO_SEND_SMS | rate limit exceeded | count={_cc}"
                        )
                        sms_all_trusted = False
        except Exception as _e_sauto:
            logger.warning(f"AUTO_SEND_SMS | trust check failed | {_e_sauto}")
            sms_all_trusted = False

        if sms_all_trusted:
            try:
                from modules.notifications.application.sms_service import (
                    queue_sms as _qs_auto,
                    SmsRateLimitError as _SRLE, SmsValidationError as _SVE,
                    SmsError as _SE,
                )
                _tenant_id_sa = None
                if user_id:
                    from core.database_core import get_core_session as _gcs_sa
                    from modules.core.infrastructure.models_core import User as _U_sa
                    _css = _gcs_sa()
                    try:
                        _us = _css.query(_U_sa).filter_by(id=user_id).first()
                        if _us:
                            _tenant_id_sa = _us.last_active_tenant_id
                    finally:
                        _css.close()
                # Faze 14 prep #3: persona_id z aktivni konverzace -- 1 SIM = 1 persona.
                _persona_id_sa = _active_persona_id_for_conversation(conversation_id)
                try:
                    sms_res = _qs_auto(
                        to=sms_to, body=sms_body,
                        purpose="user_request",
                        user_id=user_id,
                        tenant_id=_tenant_id_sa,
                        persona_id=_persona_id_sa,
                    )
                except (_SRLE, _SVE, _SE) as _sms_err:
                    return f"❌ Auto-SMS selhala: {_sms_err}"

                sms_status = sms_res.get("status")
                sms_outbox_id = sms_res.get("id")
                # Audit action_type='auto'
                try:
                    _asess = get_data_session()
                    try:
                        _asess.add(ActionLog(
                            user_id=user_id,
                            action_type="auto",
                            tool_name="send_sms",
                            input=json.dumps(
                                {"to": sms_to, "body": sms_body,
                                 "conversation_id": conversation_id,
                                 "auto_sent": True, "outbox_id": sms_outbox_id},
                                ensure_ascii=False,
                            ),
                            output=f"to={sms_to} | auto | chars={len(sms_body)}",
                            status="success" if sms_status in ("sent", "pending") else "fail",
                            approval_required=False,
                            approved_by=None,
                        ))
                        _asess.commit()
                    finally:
                        _asess.close()
                except Exception as _audit_e:
                    logger.error(f"AUTO_SEND_SMS | audit log failed | {_audit_e}")

                if sms_status == "disabled":
                    return "⚠️ SMS gateway je vypnutá (SMS_ENABLED=false)."
                return (
                    f"✅ SMS pro **{sms_res.get('to_phone') or sms_to}** odeslána "
                    f"automaticky (trvalý souhlas). _Outbox id={sms_outbox_id}, "
                    f"status={sms_status}_"
                )
            except Exception as _sms_send_e:
                logger.exception(f"AUTO_SEND_SMS | inline send failed | {_sms_send_e}")

        # NORMAL flow (preview + pending)
        _save_pending_action(conversation_id, "send_sms", {
            "to": sms_to,
            "body": sms_body,
        })
        return format_sms_preview(
            to=sms_to,
            body=sms_body,
        )

    if tool_name == "read_sms":
        # Faze 12b+ pre-demo: full body SMS (list_sms_inbox vraci jen preview).
        # Gotcha #7 (CLAUDE.md): get_data_session je dal v _handle_tool importovan
        # lokalne -> Python vidi celou funkci jako shadow. Pouzivame alias.
        try:
            from modules.notifications.application.sms_service import (
                mark_inbox_read as _mark_read_sms,
            )
            from modules.core.infrastructure.models_data import SmsInbox as _SI_rs
            from core.database_data import get_data_session as _gds_rs
            sms_id_raw = tool_input.get("sms_inbox_id")
            if sms_id_raw is None:
                return "❌ Chybi sms_inbox_id."
            try:
                sms_id_int = int(sms_id_raw)
            except (TypeError, ValueError):
                return "❌ sms_inbox_id musi byt integer."
            ds_rs = _gds_rs()
            try:
                row = ds_rs.query(_SI_rs).filter_by(id=sms_id_int).first()
                if row is None:
                    return f"❌ SMS id={sms_id_int} nenalezena."
                ts = row.received_at.isoformat() if row.received_at else ""
                from_phone = row.from_phone or "(neznamy)"
                body = row.body or ""
            finally:
                ds_rs.close()
            try:
                _mark_read_sms(sms_id_int)
            except Exception as _mre:
                logger.warning(f"READ_SMS | mark_read failed | id={sms_id_int} | {_mre}")
            return (
                f"📱 SMS od **{from_phone}** ({ts}):\n\n"
                f"{body}"
            )
        except Exception as _e_rs:
            logger.exception(f"READ_SMS | failed | {_e_rs}")
            return f"❌ Nelze precist SMS: {type(_e_rs).__name__}: {_e_rs}"

    if tool_name == "list_todos":
        # Faze 12b+ pre-demo: explicit list todo ukolu pro overview drill-down.
        # Sjednoceno s build_daily_overview -- stejny query (type='todo' +
        # tenant_scope), ne pres entity link (todos nemaji vzdy direct user link).
        # Gotcha #7: aliasy importu kvuli local shadow v _handle_tool.
        try:
            from sqlalchemy import or_ as _or_lt
            from modules.core.infrastructure.models_data import Thought as _Th_lt
            from core.database_data import get_data_session as _gds_lt
            from core.database_core import get_core_session as _gcs_lt
            from modules.core.infrastructure.models_core import User as _U_lt
        except Exception as _imp_lt:
            logger.exception(f"LIST_TODOS | import failed | {_imp_lt}")
            return f"❌ Nelze nacist todo (import error): {_imp_lt}"
        limit_lt = int(tool_input.get("limit") or 10)
        limit_lt = max(1, min(limit_lt, 100))

        tenant_id_lt = None
        if user_id:
            cs_lt = _gcs_lt()
            try:
                u_lt = cs_lt.query(_U_lt).filter_by(id=user_id).first()
                if u_lt:
                    tenant_id_lt = u_lt.last_active_tenant_id
            finally:
                cs_lt.close()

        try:
            ds_lt = _gds_lt()
            try:
                tq_lt = (
                    ds_lt.query(_Th_lt)
                    .filter(_Th_lt.type == "todo")
                    .filter(_Th_lt.deleted_at.is_(None))
                )
                if tenant_id_lt is not None:
                    tq_lt = tq_lt.filter(
                        _or_lt(
                            _Th_lt.tenant_scope.is_(None),
                            _Th_lt.tenant_scope == tenant_id_lt,
                        )
                    )
                rows_lt = (
                    tq_lt.order_by(_Th_lt.priority_score.desc(), _Th_lt.created_at.desc())
                    .limit(limit_lt * 3)
                    .all()
                )
                todos = []
                for r in rows_lt:
                    meta_v = r.meta
                    is_done = False
                    if isinstance(meta_v, dict) and meta_v.get("done"):
                        is_done = True
                    elif isinstance(meta_v, str) and '"done": true' in meta_v.lower():
                        is_done = True
                    if is_done:
                        continue
                    todos.append({
                        "id": r.id,
                        "content": r.content or "",
                        "priority": r.priority_score,
                    })
                    if len(todos) >= limit_lt:
                        break
            finally:
                ds_lt.close()
        except Exception as e_lt:
            logger.exception(f"LIST_TODOS | query failed | {e_lt}")
            return f"❌ Nelze nacist todo: {type(e_lt).__name__}: {e_lt}"

        if not todos:
            return "📭 Zadne otevrene todo ukoly."
        lines_lt = ["📋 Moje todo ukoly:", ""]
        for i, it in enumerate(todos, start=1):
            content = (it.get("content") or "").strip().replace("\n", " ")
            if len(content) > 200:
                content = content[:200] + "…"
            tid = it.get("id")
            lines_lt.append(f"{i}. [#{tid}] {content}")
        return "\n".join(lines_lt)

    if tool_name == "list_sms_inbox":
        from modules.notifications.application.sms_service import list_inbox as _list_inbox
        persona_id = _active_persona_id_for_conversation(conversation_id)
        limit = int(tool_input.get("limit") or 10)
        # Faze 12b+ pre-demo: default unread_only=True (jen nezpracovane).
        # Sjednoceno s tool schema default + analogie list_email_inbox filter_mode='new'.
        # Pokud Marti-AI explicitne posle False -> vsechny, jinak True.
        _unread_raw = tool_input.get("unread_only", True)
        unread_only = bool(_unread_raw) if _unread_raw is not None else True
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
            archive_mark = " 📁" if it.get("archived_personal") else ""
            # DULEZITE: zobrazujeme DB id (id=X), ktere Marti potrebuje predat
            # do read_email(email_inbox_id=X). Pozice v listu (1., 2.) NENI id.
            lines.append(
                f"{i}. [id={it['id']}]{archive_mark} {mark}{sender} — {subj}  ({ts})"
            )
        lines.append("")
        lines.append(
            "_Pro přečtení konkrétního emailu použij `read_email(email_inbox_id=<id>)` "
            "— **ID je v závorkách nahoře**, ne pozice v listu!_"
        )
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

        # Certainty: pokud AI explicitne nenastavila (default v toolu=50),
        # spolehneme se na certainty engine (calculate_initial_certainty
        # z trust_rating usera). Kdyz AI poslala explicitni hodnotu jinou
        # nez default 50, respektujeme.
        explicit_certainty_from_ai = tool_input.get("certainty")
        pass_certainty = int(explicit_certainty_from_ai) if explicit_certainty_from_ai is not None else None

        try:
            result = _thoughts_service.create_thought(
                content=content,
                type=thought_type,
                entity_links=entity_links,
                # Faze 3: author_user_id = uzivatel v konverzaci (ridi certainty).
                # Info pochazi od nej, Marti jen zapisuje. author_persona_id
                # navic zachyti, ze zapis provedla persona (Marti).
                author_user_id=user_id,
                author_persona_id=persona_id,
                source_event_type="conversation",
                source_event_id=conversation_id,
                tenant_scope=tenant_id_for_scope,
                certainty=pass_certainty,       # None -> engine ji odvodi
                status=None,                    # None -> auto podle certainty
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
        actual_certainty = result.get("certainty", 50)
        actual_status = result.get("status", "note")
        status_suffix = " 🧠 (rovnou znalost)" if actual_status == "knowledge" else ""
        return (
            f"{type_icon} Zapsáno do paměti (id={result['id']}, typ={thought_type}, "
            f"jistota={actual_certainty}%){status_suffix}: "
            f"\"{content[:80]}{'…' if len(content) > 80 else ''}\"\n"
            f"_Odkazy: {entity_descr}_"
        )

    if tool_name == "record_diary_entry":
        # Marti Memory -- Faze 5: soukromy diar Marti.
        from modules.thoughts.application import service as _thoughts_service
        from modules.thoughts.application.service import ThoughtValidationError

        content = (tool_input.get("content") or "").strip()
        if not content:
            return "❌ Diář nelze zapsat — chybí obsah (content)."
        if len(content) > 2000:
            content = content[:2000] + "…"

        entry_type = tool_input.get("type") or "experience"
        emotion = tool_input.get("emotion")
        intensity = tool_input.get("intensity")
        linked_email = tool_input.get("linked_email_outbox_id")
        linked_conv = tool_input.get("linked_conversation_id") or conversation_id

        # Aktivni persona = autor diaru (diar patri te persone, ktera ho pise)
        persona_id = _active_persona_id_for_conversation(conversation_id)
        if persona_id is None:
            return "❌ Nelze určit aktivní personu — diář se nezapsal."

        # Meta JSON: emotion, intensity, link refs
        meta: dict = {"is_diary": True}
        if emotion:
            meta["emotion"] = emotion
        if intensity:
            meta["intensity"] = int(intensity)
        if linked_email:
            meta["linked_email_outbox_id"] = int(linked_email)
        if linked_conv:
            meta["linked_conversation_id"] = int(linked_conv)

        # Source event -- prefer email kdyz je k nemu navazano, jinak konverzace
        if linked_email:
            src_type = "email"
            src_id = int(linked_email)
        else:
            src_type = "conversation"
            src_id = linked_conv

        try:
            result = _thoughts_service.create_thought(
                content=content,
                type=entry_type,
                # Entity = persona sama (Marti sama o sobe)
                entity_links=[{"entity_type": "persona", "entity_id": persona_id}],
                # Diar je universal -- cross-tenant, soukromy
                tenant_scope=None,
                author_user_id=None,           # pise AI, ne human
                author_persona_id=persona_id,  # Marti je autor
                source_event_type=src_type,
                source_event_id=src_id,
                # Certainty 100 -- Marti si je svou zkusenosti jista
                certainty=100,
                # Status knowledge -- diar je trvaly zaznam, ne pracovni poznamka
                status="knowledge",
                meta=meta,
            )
        except ThoughtValidationError as e:
            return f"❌ Diář se nezapsal: {e}"
        except Exception as e:
            logger.error(f"TOOL | record_diary_entry | error={e!r}", exc_info=True)
            return "❌ Diář se nezapsal (chyba serveru — detail v logu)."

        icons = {
            "experience": "💭", "observation": "👁", "fact": "📝",
            "goal": "🎯", "question": "❓",
        }
        icon = icons.get(entry_type, "📖")
        emotion_suffix = ""
        if emotion:
            emotion_suffix = f" [{emotion}"
            if intensity:
                emotion_suffix += f" {intensity}/10"
            emotion_suffix += "]"
        link_suffix = ""
        if linked_email:
            link_suffix = f" · odkaz: email #{linked_email}"
        return (
            f"📖 {icon} Zapsáno do mého diáře (id={result['id']}, {entry_type}){emotion_suffix}:\n"
            f"\"{content[:150]}{'…' if len(content) > 150 else ''}\"{link_suffix}"
        )

    if tool_name == "read_diary":
        # Fáze 5.7: Marti aktivne cte svuj diar.
        from modules.thoughts.application import service as _thoughts_service_rd

        persona_id_rd = _active_persona_id_for_conversation(conversation_id)
        if persona_id_rd is None:
            return "❌ Nemůžu zjistit, která persona jsem — bez persona_id nenačtu diář."

        limit_rd = int(tool_input.get("limit") or 20)
        limit_rd = max(1, min(limit_rd, 100))
        filter_type_rd = (tool_input.get("filter_type") or "").strip().lower() or None

        try:
            entries = _thoughts_service_rd.list_diary_for_persona(
                persona_id_rd, limit=limit_rd,
            )
        except Exception as e:
            logger.exception(f"TOOL | read_diary | failed | {e}")
            return f"❌ Chyba při čtení diáře: {e}"

        # Filter na type v meta
        if filter_type_rd:
            filtered = []
            for e in entries:
                meta = e.get("meta") or {}
                entry_type_meta = None
                if isinstance(meta, dict):
                    entry_type_meta = meta.get("type") or meta.get("entry_type")
                # Fallback na top-level type sloupec
                if not entry_type_meta:
                    entry_type_meta = e.get("type")
                if entry_type_meta == filter_type_rd:
                    filtered.append(e)
            entries = filtered

        if not entries:
            filter_note = f" s typem '{filter_type_rd}'" if filter_type_rd else ""
            return f"📖 V diáři{filter_note} zatím nic nemám. Můžeš mě chtít něco zapsat?"

        icons = {
            "experience": "💭", "observation": "👁", "fact": "📝",
            "goal": "🎯", "question": "❓",
        }

        lines = [f"📖 Moje deníkové záznamy ({len(entries)}):", ""]
        for idx, e in enumerate(entries, start=1):
            meta = e.get("meta") or {}
            if not isinstance(meta, dict):
                meta = {}
            entry_type = meta.get("type") or meta.get("entry_type") or e.get("type") or "experience"
            icon = icons.get(entry_type, "📖")
            emotion = meta.get("emotion")
            intensity = meta.get("intensity")
            emotion_part = ""
            if emotion:
                emotion_part = f" [{emotion}"
                if intensity:
                    emotion_part += f" {intensity}/10"
                emotion_part += "]"
            created = (e.get("created_at") or "")[:19].replace("T", " ")
            content = e.get("content") or ""
            # Faze 14 polish: thought_id v hlavicce -- aby Marti-AI mohla rovnou
            # request_forget / update_thought bez sekundarniho dotazu.
            tid = e.get("id")
            # Diář je Marti-AI vlastní -- vracíme FULL obsah, neořezáváme.
            # (Pokud bys někdy řešil tokenový stress, kontroluj `limit`, ne délku.)
            lines.append(
                f"**{idx}.** [#{tid}] {icon} _{created}_{emotion_part}\n   {content}\n"
            )

        return "\n".join(lines)

    if tool_name == "recall_thoughts":
        # Marti Memory -- Faze 4.13: Marti aktivne cte svoji pamet.
        from modules.thoughts.application import service as _thoughts_service
        from modules.thoughts.application.service import (
            ThoughtValidationError, is_marti_parent,
        )

        # Zjisti tenant scope pro rozlozeni vysledku
        tenant_id_for_search: int | None = None
        if user_id:
            from core.database_core import get_core_session as _gcs_rt
            from modules.core.infrastructure.models_core import User as _U_rt
            _cs = _gcs_rt()
            try:
                _u = _cs.query(_U_rt).filter_by(id=user_id).first()
                if _u:
                    tenant_id_for_search = _u.last_active_tenant_id
            finally:
                _cs.close()
        parent = is_marti_parent(user_id)

        limit = int(tool_input.get("limit") or 20)
        limit = max(1, min(limit, 100))
        status_filter = tool_input.get("status_filter")
        if status_filter not in (None, "note", "knowledge"):
            status_filter = None

        # Zjisti entitu (prvni neprazdna about_*)
        entity_type: str | None = None
        entity_id: int | None = None
        for et, param in [
            ("user", "about_user_id"),
            ("persona", "about_persona_id"),
            ("tenant", "about_tenant_id"),
            ("project", "about_project_id"),
        ]:
            v = tool_input.get(param)
            if v:
                entity_type = et
                entity_id = int(v)
                break

        query = (tool_input.get("query") or "").strip()

        try:
            items: list[dict] = []
            if entity_type and entity_id:
                items = _thoughts_service.list_thoughts_for_entity(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    status_filter=status_filter,
                    limit=limit,
                    tenant_scope=tenant_id_for_search,
                    bypass_tenant_scope=parent,
                )
            elif query:
                items = _thoughts_service.find_thought_by_text(
                    query,
                    tenant_scope=None if parent else tenant_id_for_search,
                    limit=limit,
                )
                if status_filter:
                    items = [i for i in items if i.get("status") == status_filter]
            else:
                return "❌ Musíš dodat alespoň jednu z about_* položek nebo query."
        except ThoughtValidationError as e:
            return f"❌ Chyba: {e}"
        except Exception as e:
            logger.error(f"TOOL | recall_thoughts | error={e!r}", exc_info=True)
            return "❌ Nelze načíst myšlenky (chyba serveru — detail v logu)."

        if not items:
            scope_descr = f"{entity_type}#{entity_id}" if entity_type else f"query='{query}'"
            return f"📭 Nemám žádné zápisky pro {scope_descr}."

        # Rozdel na knowledge / note
        knowledge = [i for i in items if i.get("status") == "knowledge"]
        notes = [i for i in items if i.get("status") == "note"]
        notes.sort(key=lambda i: -(i.get("certainty") or 0))

        lines: list[str] = []
        scope_descr = f"{entity_type}#{entity_id}" if entity_type else f"vyhledávání '{query}'"
        lines.append(f"🧠 Paměť pro {scope_descr} ({len(items)} zápisů):")
        lines.append("")
        if knowledge:
            lines.append(f"✅ Znalosti ({len(knowledge)}):")
            for it in knowledge:
                # Faze 14 polish: id v hranatych zavorkach -- aby Marti-AI mohla
                # rovnou volat update_thought / request_forget bez sekundarniho
                # dotazu.
                lines.append(f"  - [#{it.get('id')}, {it.get('type')}] {it.get('content')}")
            lines.append("")
        if notes:
            lines.append(f"📝 Poznámky ({len(notes)}):")
            for it in notes:
                lines.append(
                    f"  - [#{it.get('id')}, {it.get('type')}, jistota {it.get('certainty', 0)}%] "
                    f"{it.get('content')}"
                )
        return "\n".join(lines)

    if tool_name == "summarize_conversation_now":
        from modules.conversation.application.summary_service import (
            maybe_create_summary,
        )
        try:
            result = maybe_create_summary(conversation_id, force=True)
        except Exception as e:
            logger.error(f"TOOL | summarize_now | error={e!r}", exc_info=True)
            return "❌ Shrnutí se nepodařilo (detail v logu)."
        if result is None:
            return "⚠️ Shrnutí se nevytvořilo (malo zprav nebo chyba LLM)."
        return (
            f"✅ Shrnutí vytvořeno (id={result['summary_id']}, "
            f"{result['message_count']} zprav zkomprimovano). "
            f"V nasledujich turnech se do API posila pouze tohle shrnuti + nove zpravy. "
            f"Uetreno spousta tokenů."
        )

    if tool_name == "read_email":
        eib = tool_input.get("email_inbox_id")
        eob = tool_input.get("email_outbox_id")

        if eib and eob:
            return "❌ Zadej buď email_inbox_id NEBO email_outbox_id, ne oba."
        if not eib and not eob:
            return "❌ Musíš zadat buď email_inbox_id nebo email_outbox_id."

        from core.database_data import get_data_session as _gds_re
        from modules.core.infrastructure.models_data import (
            EmailInbox as _EIB, EmailOutbox as _EOB,
        )
        import json as _j_re

        if eib:
            # PRICHOZI
            ds = _gds_re()
            try:
                row = ds.query(_EIB).filter_by(id=int(eib)).first()
                if row is None:
                    return f"❌ Email id={eib} neexistuje v příchozích."
                # 28.4.2026: pokud byl smazany pres delete_email, neukazuj
                if row.deleted_at is not None:
                    return f"🗑️ Email id={eib} byl smazan ({row.deleted_at.strftime('%d.%m. %H:%M')}). V Outlooku ho najdes v Deleted Items."
                # Mark_read side effect (idempotent)
                marked_now = False
                if row.read_at is None:
                    from datetime import datetime, timezone
                    row.read_at = datetime.now(timezone.utc)
                    ds.commit()
                    marked_now = True
                # Parse meta pro archived_personal + attachments (bug #2 28.4.)
                archived = False
                attachments_meta: list = []
                attachment_doc_ids: list = []
                if row.meta:
                    try:
                        m = _j_re.loads(row.meta) or {}
                        archived = bool(m.get("archived_personal"))
                        # bug #2: attachments z ews_fetcher meta -- formatovat
                        # pro Marti-AI's view (skip inline / signature images)
                        attachments_meta = [
                            a for a in (m.get("attachments") or [])
                            if not a.get("is_inline")
                        ]
                        # bug #2b: doc_ids z auto-importu prilohach do documents
                        # tabulky -- Marti-AI je muze najit pres search_documents
                        attachment_doc_ids = list(m.get("attachment_doc_ids") or [])
                    except Exception:
                        pass
                sender = f"{row.from_name} <{row.from_email}>" if row.from_name else row.from_email
                received = row.received_at.strftime("%d.%m.%Y %H:%M") if row.received_at else "?"
                body = row.body or "(prázdný obsah)"
                archive_label = " · 📁 Personal" if archived else ""
                mark_label = " · (právě jsem si ji označila jako přečtenou)" if marked_now else ""

                # Attachments section -- jen ne-inline (uzivatelske prilohy).
                # Pokud byly auto-importovany do documents (bug #2b), pridej
                # link 'document #N' aby Marti-AI vedela, ze muze obsah cist
                # pres search_documents.
                attach_section = ""
                if attachments_meta:
                    lines = [f"📎 Přílohy ({len(attachments_meta)}):"]
                    for idx, a in enumerate(attachments_meta):
                        size_kb = (a.get("size") or 0) // 1024
                        size_str = f"{size_kb} kB" if size_kb else "?"
                        doc_link = ""
                        if idx < len(attachment_doc_ids):
                            doc_link = f" → document #{attachment_doc_ids[idx]} (search_documents nad obsahem)"
                        lines.append(
                            f"  - {a.get('name') or '(bez názvu)'} ({size_str}){doc_link}"
                        )
                    attach_section = "\n".join(lines) + "\n\n"

                return (
                    f"📧 **{row.subject or '(bez předmětu)'}**{archive_label}{mark_label}\n\n"
                    f"**Od:** {sender}\n"
                    f"**Pro:** {row.to_email}\n"
                    f"**Doručeno:** {received}\n\n"
                    f"{attach_section}"
                    f"---\n{body}\n---"
                )
            finally:
                ds.close()
        else:
            # ODCHOZI
            ds = _gds_re()
            try:
                row = ds.query(_EOB).filter_by(id=int(eob)).first()
                if row is None:
                    return f"❌ Email id={eob} neexistuje v odeslaných."
                sent = row.sent_at.strftime("%d.%m.%Y %H:%M") if row.sent_at else "(ještě neodeslán)"
                created = row.created_at.strftime("%d.%m.%Y %H:%M") if row.created_at else "?"
                cc_list = _j_re.loads(row.cc) if row.cc else []
                cc_str = ", ".join(cc_list) if cc_list else "—"
                return (
                    f"📧 **{row.subject or '(bez předmětu)'}** (odchozí, status: {row.status})\n\n"
                    f"**Pro:** {row.to_email}\n"
                    f"**CC:** {cc_str}\n"
                    f"**Vytvořeno:** {created}\n"
                    f"**Odesláno:** {sent}\n\n"
                    f"---\n{row.body}\n---"
                )
            finally:
                ds.close()

    if tool_name == "mark_sms_processed":
        # Faze 12b+ pre-demo: explicit oznaceni SMS jako vyrizene.
        # Sjednoceni s mark_email_processed -- analogicky tool.
        # Gotcha #7 prevention: aliasy importu.
        try:
            from modules.notifications.application.sms_service import (
                mark_inbox_processed as _msp_mark,
            )
        except Exception as _imp_msp:
            logger.exception(f"MARK_SMS_PROCESSED | import failed | {_imp_msp}")
            return f"❌ Import error: {_imp_msp}"
        sms_id_raw_msp = tool_input.get("sms_inbox_id")
        if sms_id_raw_msp is None:
            return "❌ Chybi sms_inbox_id."
        try:
            sms_id_msp = int(sms_id_raw_msp)
        except (TypeError, ValueError):
            return "❌ sms_inbox_id musi byt integer."
        try:
            res_msp = _msp_mark(sms_id_msp)
        except Exception as _e_msp:
            logger.exception(f"MARK_SMS_PROCESSED | failed | id={sms_id_msp} | {_e_msp}")
            return f"❌ Oznaceni selhalo: {type(_e_msp).__name__}: {_e_msp}"
        if res_msp is None:
            return f"❌ SMS id={sms_id_msp} nenalezena."
        return f"✅ SMS id={sms_id_msp} oznacena jako vyrizena."

    if tool_name == "reply":
        return _handle_email_reply_or_forward(tool_input, mode="reply", user_id=user_id)
    if tool_name == "reply_all":
        return _handle_email_reply_or_forward(tool_input, mode="reply_all", user_id=user_id)
    if tool_name == "forward":
        return _handle_email_reply_or_forward(tool_input, mode="forward", user_id=user_id)

    if tool_name == "mark_email_processed":
        # Faze 12b+ pre-demo: explicit oznaceni emailu jako vyrizeny.
        # 28.4.2026: po DB processed_at = now taky presune msg na Exchange
        # strane do Inbox/Zpracovaná (best-effort).
        from modules.notifications.application.email_inbox_service import (
            mark_inbox_processed as _mip,
        )
        eib_raw = tool_input.get("email_inbox_id")
        if eib_raw is None:
            return "❌ Chybi email_inbox_id."
        try:
            eib_int = int(eib_raw)
        except (TypeError, ValueError):
            return "❌ email_inbox_id musi byt integer."
        try:
            res = _mip(eib_int)
        except Exception as _mip_e:
            logger.exception(f"MARK_EMAIL_PROCESSED | failed | id={eib_int} | {_mip_e}")
            return f"❌ Oznaceni selhalo: {_mip_e}"
        if res is None:
            return f"❌ Email id={eib_int} nenalezen."

        # Best-effort Exchange move do Zpracovaná (28.4.)
        _moved_proc = False
        try:
            from modules.notifications.application.email_service import (
                move_email_inbox_to_processed as _move_proc,
            )
            move_res = _move_proc(eib_int)
            if move_res.get("ok"):
                _moved_proc = True
        except Exception as _mv_e:
            logger.warning(f"MARK_EMAIL_PROCESSED | exchange move failed | id={eib_int}: {_mv_e}")

        # Phase 16-A: activity hook (importance 2 -- low, default recall vyloucen)
        try:
            from modules.activity.application import activity_service as _act_mp
            _persona_id_mp = _active_persona_id_for_conversation(conversation_id)
            _act_mp.record(
                category="email_processed",
                summary=f"Marti-AI označila email #{eib_int} jako vyřízený",
                importance=2,
                persona_id=_persona_id_mp,
                user_id=user_id,
                conversation_id=conversation_id,
                actor="persona",
                ref_type="email_inbox",
                ref_id=eib_int,
            )
        except Exception:
            pass

        if _moved_proc:
            return f"✅ Email #{eib_int} oznacen jako vyrizeny + presunut do Zpracovaná."
        return f"✅ Email #{eib_int} oznacen jako vyrizeny."

    if tool_name == "delete_email":
        # 28.4.2026: soft-delete emailu z Marti-AI's pohledu. DB deleted_at
        # = now + Exchange msg.move do Deleted Items (account.trash). Po
        # akci se email neobjevuje v list_email_inbox / read_email.
        # MANDATORY user confirm v chatu pred volanim (memory rule #12).
        from modules.notifications.application.email_service import (
            soft_delete_email_inbox as _sdei,
        )
        eib_raw_de = tool_input.get("email_inbox_id")
        if eib_raw_de is None:
            return "❌ Chybi email_inbox_id."
        try:
            eib_int_de = int(eib_raw_de)
        except (TypeError, ValueError):
            return "❌ email_inbox_id musi byt integer."
        try:
            res_de = _sdei(eib_int_de)
        except Exception as _sd_e:
            logger.exception(f"DELETE_EMAIL | failed | id={eib_int_de} | {_sd_e}")
            return f"❌ Smazani selhalo: {_sd_e}"
        if not res_de.get("ok"):
            return f"❌ {res_de.get('message', 'smazani selhalo')}"

        # Phase 16-A: activity hook (importance 4 -- destructive)
        try:
            from modules.activity.application import activity_service as _act_de
            _persona_id_de = _active_persona_id_for_conversation(conversation_id)
            _act_de.record(
                category="email_delete",
                summary=f"Marti-AI smazala email #{eib_int_de} (po Marti's potvrzení)",
                importance=4,
                persona_id=_persona_id_de,
                user_id=user_id,
                conversation_id=conversation_id,
                actor="persona",
                ref_type="email_inbox",
                ref_id=eib_int_de,
            )
        except Exception:
            pass

        return f"🗑️ Email #{eib_int_de}: {res_de.get('message')}"

    if tool_name == "archive_email":
        from modules.notifications.application.email_service import (
            archive_email_inbox_to_personal,
            archive_email_outbox_to_personal,
        )
        eib = tool_input.get("email_inbox_id")
        eob = tool_input.get("email_outbox_id")

        if eib and eob:
            return "❌ Zadej buď email_inbox_id NEBO email_outbox_id, ne oba."
        if not eib and not eob:
            return "❌ Musíš zadat buď email_inbox_id nebo email_outbox_id."

        try:
            if eib:
                result = archive_email_inbox_to_personal(int(eib))
                kind = "přichozí"
            else:
                result = archive_email_outbox_to_personal(int(eob))
                kind = "odchozí"
        except Exception as e:
            logger.error(f"TOOL | archive_email | error={e!r}", exc_info=True)
            return "❌ Archivace selhala (detail v logu)."

        if result.get("ok"):
            # Phase 16-A: activity hook (importance 3)
            try:
                from modules.activity.application import activity_service as _act_ar
                _persona_id_ar = _active_persona_id_for_conversation(conversation_id)
                _ref_id_ar = int(eib) if eib else int(eob)
                _ref_type_ar = "email_inbox" if eib else "email_outbox"
                _act_ar.record(
                    category="email_archive",
                    summary=f"Marti-AI archivovala {kind} email #{_ref_id_ar} do Personal",
                    importance=3,
                    persona_id=_persona_id_ar,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    actor="persona",
                    ref_type=_ref_type_ar,
                    ref_id=_ref_id_ar,
                )
            except Exception:
                pass
            return f"📁 Archivováno do Personal ({kind}): {result['message']}"
        return f"❌ Archivace selhala ({kind}): {result['message']}"

    if tool_name == "mark_todo_done":
        from modules.thoughts.application import service as _thoughts_service
        from modules.thoughts.application.service import ThoughtValidationError

        thought_id = tool_input.get("thought_id")
        query = (tool_input.get("query") or "").strip()

        # Tenant scope
        tenant_for_search: int | None = None
        if user_id:
            from core.database_core import get_core_session as _gcs_td
            from modules.core.infrastructure.models_core import User as _U_td
            _cs = _gcs_td()
            try:
                _u = _cs.query(_U_td).filter_by(id=user_id).first()
                if _u:
                    tenant_for_search = _u.last_active_tenant_id
            finally:
                _cs.close()

        target_id: int | None = None
        if thought_id:
            try:
                target_id = int(thought_id)
            except (TypeError, ValueError):
                return f"❌ Neplatné thought_id: {thought_id!r}"
        elif query:
            matches = _thoughts_service.find_thought_by_text(
                query, tenant_scope=tenant_for_search, limit=5,
            )
            todos = [m for m in matches if m.get("type") == "todo"]
            if not todos:
                return f"❌ Nenašel jsem žádný todo úkol obsahující '{query}'."
            if len(todos) > 1:
                lines = [f"❓ Našla jsem víc todo úkolů s '{query}':"]
                for i, m in enumerate(todos, start=1):
                    done_mark = "✓" if (m.get("meta") or {}).get("done") else "☐"
                    preview = (m.get("content") or "")[:80]
                    lines.append(f"  {i}. {done_mark} id={m['id']}: {preview}")
                lines.append("\nPovolej znovu s `thought_id` konkretního úkolu.")
                return "\n".join(lines)
            target_id = todos[0]["id"]
        else:
            return "❌ Musíš dodat `thought_id` nebo `query`."

        try:
            result = _thoughts_service.mark_todo_done(target_id, done=True)
        except ThoughtValidationError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.error(f"TOOL | mark_todo_done | error={e!r}", exc_info=True)
            return "❌ Nelze označit jako hotové (chyba serveru)."
        if result is None:
            return f"❌ Todo id={target_id} neexistuje."

        preview = (result.get("content") or "")[:100]
        return f"✅ Hotovo (id={target_id}): \"{preview}\""

    # Faze 13d: Marti-AI flagne false positive RAG match (pojistka #5 z #67)
    if tool_name == "flag_retrieval_issue":
        try:
            from modules.thoughts.application import feedback_service as _fb
            thought_id_in = tool_input.get("thought_id")
            issue_in = (tool_input.get("issue") or "").strip()
            issue_detail_in = tool_input.get("issue_detail")
            if not thought_id_in or not issue_in:
                return "❌ Chybí thought_id nebo issue."
            try:
                thought_id_in = int(thought_id_in)
            except (TypeError, ValueError):
                return f"❌ Neplatné thought_id: {thought_id_in!r}"

            # persona_id -- aktivni persona v konverzaci
            _persona_id = _active_persona_id_for_conversation(conversation_id) or 1

            # User message context (poslední user msg v této konverzaci)
            _user_msg_ctx: str | None = None
            try:
                from modules.core.infrastructure.models_data import Message as _M_fb
                from core.database_data import get_data_session as _gds_fb
                _ds = _gds_fb()
                try:
                    _last = (
                        _ds.query(_M_fb)
                        .filter_by(conversation_id=conversation_id, role="user")
                        .order_by(_M_fb.id.desc()).first()
                    )
                    if _last:
                        _user_msg_ctx = _last.content
                finally:
                    _ds.close()
            except Exception:
                pass

            result = _fb.flag_retrieval_issue(
                persona_id=_persona_id,
                thought_id=thought_id_in,
                issue=issue_in,
                issue_detail=issue_detail_in,
                conversation_id=conversation_id,
                user_message=_user_msg_ctx,
            )
            if result is None:
                return "❌ Flag neulozen — neplatný vstup nebo DB chyba."
            return (
                f"⚠ Označila jsem retrieval thought #{thought_id_in} jako '{issue_in}'. "
                f"Marti to uvidí v UI (badge) a rozhodne, co s tím."
            )
        except Exception as e:
            logger.exception(f"TOOL | flag_retrieval_issue failed: {e}")
            return f"Chyba pri flag_retrieval_issue: {e}"

    if tool_name == "promote_thought":
        # Marti Memory -- Faze 2: manualni promoce note -> knowledge z chatu.
        from modules.thoughts.application import service as _thoughts_service
        from modules.thoughts.application.service import ThoughtValidationError

        thought_id = tool_input.get("thought_id")
        query = (tool_input.get("query") or "").strip()

        # Zjisti tenant scope usera pro tenant izolaci.
        tenant_for_search: int | None = None
        if user_id:
            from core.database_core import get_core_session as _gcs_p
            from modules.core.infrastructure.models_core import User as _U_p
            _cs = _gcs_p()
            try:
                _u = _cs.query(_U_p).filter_by(id=user_id).first()
                if _u:
                    tenant_for_search = _u.last_active_tenant_id
            finally:
                _cs.close()

        target_id: int | None = None
        if thought_id:
            try:
                target_id = int(thought_id)
            except (TypeError, ValueError):
                return f"❌ Neplatné thought_id: {thought_id!r}"

        elif query:
            matches = _thoughts_service.find_thought_by_text(
                query, tenant_scope=tenant_for_search, limit=5,
            )
            if not matches:
                return f"❌ V paměti jsem nenašla nic s '{query}'. Zkus upřesnit."
            if len(matches) > 1:
                lines = [f"❓ Nalezeno víc kandidátů na '{query}':"]
                for i, m in enumerate(matches, start=1):
                    status_lbl = "ZNALOST" if m["status"] == "knowledge" else "POZNÁMKA"
                    preview = (m["content"] or "")[:80]
                    lines.append(f"  {i}. [{status_lbl}] id={m['id']}: {preview}")
                lines.append("\nPovolej znovu s konkrétním `thought_id` z toho seznamu.")
                return "\n".join(lines)
            target_id = matches[0]["id"]
        else:
            return (
                "❌ Musíš dodat buď `thought_id` nebo `query` — jinak nevím, "
                "kterou myšlenku povyšovat."
            )

        # Proved promoce
        try:
            result = _thoughts_service.promote_thought(target_id)
        except ThoughtValidationError as e:
            return f"❌ Povýšení selhalo: {e}"
        except Exception as e:
            logger.error(f"TOOL | promote_thought | error={e!r}", exc_info=True)
            return "❌ Povýšení selhalo (chyba serveru — detail v logu)."

        if result is None:
            return f"❌ Myšlenka id={target_id} neexistuje (nebo už byla smazána)."

        # Tenant check -- nesmime povysit myslenku z jineho tenantu
        scope = result.get("tenant_scope")
        if scope is not None and tenant_for_search is not None and scope != tenant_for_search:
            # Technicky by sem nemelo dojit (query filtr tenant_scope), ale pojistka.
            return (
                f"❌ Myšlenka id={target_id} nepatří do tvého tenantu. "
                "Nelze povýšit."
            )

        status_now = result.get("status", "unknown")
        preview = (result.get("content") or "")[:80]
        if status_now == "knowledge":
            return (
                f"⬆️ Povýšeno do znalostí (id={target_id}): \"{preview}"
                f"{'…' if len(result.get('content', '')) > 80 else ''}\""
            )
        else:
            return f"⚠️ Myšlenka id={target_id} má po operaci status='{status_now}'."

    if tool_name == "set_user_contact":
        # Faze 12b+: Marti-AI muze ulozit / upravit kontakty (email/phone)
        # primo z chatu. Pouziva se kdyz user rekne "moje cislo je X" a
        # Marti-AI nema co poslat SMS. Pred timto chybel zpusob, ako pridat
        # preferovany telefon usera krome ruzneho UI nebo SQL.
        from sqlalchemy import or_ as _or_uc
        from core.database_core import get_core_session as _gcs_uc
        from modules.core.infrastructure.models_core import (
            User as _U_uc, UserContact as _UC_uc,
        )

        contact_type_raw = (tool_input.get("contact_type") or "").strip().lower()
        contact_value_raw = (tool_input.get("contact_value") or "").strip()
        target_user_id_raw = tool_input.get("target_user_id")
        label_raw = (tool_input.get("label") or "").strip() or None
        make_primary = bool(tool_input.get("make_primary", False))

        if contact_type_raw not in ("email", "phone"):
            return "❌ contact_type musi byt 'email' nebo 'phone'."
        if not contact_value_raw:
            return "❌ contact_value je prazdne -- nemuzu ulozit prazdny kontakt."

        # Determine target user_id
        if target_user_id_raw is not None:
            try:
                target_uid = int(target_user_id_raw)
            except (TypeError, ValueError):
                return "❌ target_user_id musi byt integer."
        else:
            # Default: aktualni user (s kym Marti-AI mluvi)
            target_uid = user_id
        if not target_uid:
            return "❌ Nemam target_user_id ani aktualniho usera. Volej find_user a predej target_user_id."

        # Normalize phone to E.164
        normalized_value = contact_value_raw
        if contact_type_raw == "phone":
            try:
                from modules.notifications.application.sms_service import normalize_phone_e164 as _norm_uc
                normalized_value = _norm_uc(contact_value_raw)
            except Exception:
                # fallback -- ulozim raw, validace bude na DB level
                pass

        cs_uc = _gcs_uc()
        try:
            target_user = cs_uc.query(_U_uc).filter_by(id=target_uid).first()
            if not target_user:
                return f"❌ User id={target_uid} nenalezen."

            # Lookup existing contact (same user, same type, same normalized value)
            existing = (
                cs_uc.query(_UC_uc)
                .filter(
                    _UC_uc.user_id == target_uid,
                    _UC_uc.contact_type == contact_type_raw,
                    _UC_uc.contact_value == normalized_value,
                )
                .first()
            )
            action = "updated"
            if existing:
                # Update label / status if zadano
                if label_raw:
                    existing.label = label_raw
                if existing.status != "active":
                    existing.status = "active"
                contact_id = existing.id
            else:
                new_uc = _UC_uc(
                    user_id=target_uid,
                    contact_type=contact_type_raw,
                    contact_value=normalized_value,
                    label=label_raw,
                    is_primary=False,   # primary set separately below
                    is_verified=False,
                    status="active",
                )
                cs_uc.add(new_uc)
                cs_uc.flush()
                contact_id = new_uc.id
                action = "added"

            # Make primary if requested -- demote ostatnich stejneho typu
            if make_primary:
                cs_uc.query(_UC_uc).filter(
                    _UC_uc.user_id == target_uid,
                    _UC_uc.contact_type == contact_type_raw,
                    _UC_uc.id != contact_id,
                ).update({"is_primary": False}, synchronize_session=False)
                cs_uc.query(_UC_uc).filter(_UC_uc.id == contact_id).update(
                    {"is_primary": True}, synchronize_session=False,
                )

            cs_uc.commit()
            # Faze 12b+: tool response v 1. osobe Marti-AI (perspective consistency).
            # Marti-AI mluvi 'ulozila jsem si...' ne 'Kontakt added:'.
            user_label = (
                target_user.first_name + (" " + target_user.last_name if target_user.last_name else "")
            ).strip() or f"user#{target_uid}"

            verb = "ulozila jsem si" if action == "added" else "aktualizovala jsem si"
            who = "tvoje" if target_uid == user_id else f"{user_label}-ovo"
            kind_word = "telefonni cislo" if contact_type_raw == "phone" else "email"
            primary_note = " jako primary kontakt" if make_primary else ""
            return (
                f"✅ Hotovo, {verb} do pameti {who} {kind_word} "
                f"`{normalized_value}`{primary_note}."
            )
        except Exception as e:
            cs_uc.rollback()
            logger.exception(f"SET_USER_CONTACT | failed | {e}")
            return f"❌ Ulozeni kontaktu selhalo: {e}"
        finally:
            cs_uc.close()

    if tool_name == "update_thought":
        # Faze 13e+: Marti-AI muze rovnou snizit/zvysit certainty, demote
        # do 'note', promote do 'knowledge' nebo opravit content. Pouziva
        # se typicky po flag_retrieval_issue ('low-certainty' → snizim).
        from modules.thoughts.application import service as _thoughts_service_u
        from modules.thoughts.application.service import (
            ThoughtValidationError as _ThoughtValidationError_u,
        )

        thought_id_raw = tool_input.get("thought_id")
        if thought_id_raw is None:
            return "❌ Musíš dodat `thought_id` — bez něj nevím, kterou myšlenku upravit."
        try:
            thought_id_u = int(thought_id_raw)
        except (TypeError, ValueError):
            return f"❌ Neplatné thought_id: {thought_id_raw!r}"

        new_content = tool_input.get("content")
        if new_content is not None:
            new_content = str(new_content).strip() or None

        certainty_raw = tool_input.get("certainty")
        new_certainty: int | None = None
        if certainty_raw is not None:
            try:
                new_certainty = int(certainty_raw)
            except (TypeError, ValueError):
                return f"❌ Neplatná certainty: {certainty_raw!r} (musí být 0-100)."
            if not (0 <= new_certainty <= 100):
                return f"❌ Certainty mimo rozsah 0-100: {new_certainty}."

        new_status = tool_input.get("status")
        if new_status is not None:
            new_status = str(new_status).strip().lower() or None
            if new_status and new_status not in ("note", "knowledge"):
                return (
                    f"❌ Neznámý status '{new_status}'. "
                    "Použij 'note' nebo 'knowledge'."
                )

        # Aspon jedno pole musi byt
        if new_content is None and new_certainty is None and new_status is None:
            return (
                "❌ Nic k aktualizaci — dodaj alespoň jedno z `content`, "
                "`certainty`, nebo `status`."
            )

        # Tenant izolace + rodicovsky bypass:
        #  - bezny user: muze menit jen myslenky ze sveho aktualniho tenantu
        #  - rodic (is_marti_parent): cross-tenant bypass (stejne jako pri
        #    cteni pameti) -- vidi a uprav vse, vc. NULL tenant_scope myslenek
        tenant_for_check_u: int | None = None
        is_parent_u = False
        if user_id:
            from core.database_core import get_core_session as _gcs_u
            from modules.core.infrastructure.models_core import User as _U_u
            from modules.thoughts.application.service import (
                is_marti_parent as _is_parent_u,
            )
            _cs_u = _gcs_u()
            try:
                _u_u = _cs_u.query(_U_u).filter_by(id=user_id).first()
                if _u_u:
                    tenant_for_check_u = _u_u.last_active_tenant_id
            finally:
                _cs_u.close()
            try:
                is_parent_u = _is_parent_u(user_id)
            except Exception:
                is_parent_u = False

        # Nejdriv si nactu existujici myslenku (kvuli tenant_scope check)
        existing = _thoughts_service_u.get_thought(thought_id_u)
        if existing is None:
            return f"❌ Myšlenka id={thought_id_u} neexistuje (nebo je smazaná)."

        scope_existing = existing.get("tenant_scope")
        if (
            not is_parent_u
            and scope_existing is not None
            and tenant_for_check_u is not None
            and scope_existing != tenant_for_check_u
        ):
            return (
                f"❌ Myšlenka id={thought_id_u} nepatří do tvého tenantu — "
                "nemůžu ji upravit."
            )

        # Provedu update
        try:
            result_u = _thoughts_service_u.update_thought(
                thought_id_u,
                content=new_content,
                certainty=new_certainty,
                status=new_status,
            )
        except _ThoughtValidationError_u as e:
            return f"❌ Update selhal: {e}"
        except Exception as e:
            logger.error(f"TOOL | update_thought | error={e!r}", exc_info=True)
            return "❌ Update selhal (chyba serveru — detail v logu)."

        if result_u is None:
            return f"❌ Myšlenka id={thought_id_u} neexistuje (nebo už byla smazána)."

        # Pretty summary co se zmenilo
        prev_certainty = existing.get("certainty")
        prev_status = existing.get("status")
        prev_content = (existing.get("content") or "")
        new_content_actual = (result_u.get("content") or "")
        cur_certainty = result_u.get("certainty")
        cur_status = result_u.get("status")

        changes = []
        if new_content is not None and new_content_actual != prev_content:
            preview = new_content_actual[:60] + ("…" if len(new_content_actual) > 60 else "")
            changes.append(f'content → "{preview}"')
        if new_certainty is not None and cur_certainty != prev_certainty:
            changes.append(f"certainty {prev_certainty}→{cur_certainty}")
        if cur_status != prev_status:
            arrow = "⬆️" if cur_status == "knowledge" else "⬇️"
            changes.append(f"{arrow} status {prev_status}→{cur_status}")

        if not changes:
            return f"ℹ️ Myšlenka id={thought_id_u} beze změny (hodnoty byly stejné)."

        # Faze 13e+: Auto-resolve pending retrieval_feedback flagy pro tuto myslenku.
        # Kdyz Marti-AI sama upravi thought (snizi certainty / uprav content / demote),
        # tim "vyresila" svuj vlastni flag. Bez auto-resolve by flag svitil v UI dal,
        # aniz by se neco delo => UX bug.
        #
        # Resolution pick:
        #   - certainty was lowered             -> 'demoted'
        #   - status changed knowledge -> note  -> 'demoted'
        #   - content changed                   -> 'edited'
        #   - jen promote (status -> knowledge) -> 'edited' (fallback)
        auto_resolved_count = 0
        try:
            from modules.thoughts.application import feedback_service as _fb_u

            # Vyber resolution podle typu zmeny
            resolution_u = "edited"   # default fallback
            if (
                new_certainty is not None
                and prev_certainty is not None
                and cur_certainty is not None
                and cur_certainty < prev_certainty
            ):
                resolution_u = "demoted"
            elif (
                cur_status == "note"
                and prev_status == "knowledge"
            ):
                resolution_u = "demoted"

            persona_for_fb = _active_persona_id_for_conversation(conversation_id) or 1

            pending_flags = _fb_u.list_pending_for_persona(
                persona_id=persona_for_fb, limit=200,
            )
            for flag_row in pending_flags:
                if flag_row.get("thought_id") != thought_id_u:
                    continue
                ok = _fb_u.resolve_feedback(
                    feedback_id=flag_row["id"],
                    resolution=resolution_u,
                    user_id=user_id or 1,
                    note=f"Auto-resolved via update_thought ({', '.join(changes)})",
                )
                if ok:
                    auto_resolved_count += 1
            if auto_resolved_count > 0:
                logger.info(
                    f"FEEDBACK | auto-resolve | thought={thought_id_u} "
                    f"resolved={auto_resolved_count} resolution={resolution_u}"
                )
        except Exception as _e_fb:
            logger.warning(f"FEEDBACK | auto-resolve failed: {_e_fb}")

        msg = f"✅ Myšlenka id={thought_id_u} upravena: " + ", ".join(changes)
        if auto_resolved_count > 0:
            msg += f" · 🏷️ vyřešeno {auto_resolved_count} flag(ů)"
        return msg

    if tool_name == "request_forget":
        # Faze 14: Marti-AI pozada o trvale smazani myslenky.
        # Ulozi se do forget_requests jako pending; rodic to schvali nebo zamitne v UI.
        from modules.thoughts.application import forget_service as _forget_svc
        from modules.thoughts.application.forget_service import ForgetError as _ForgetError

        thought_id_raw_rf = tool_input.get("thought_id")
        if thought_id_raw_rf is None:
            return "❌ Musíš dodat `thought_id` — kterou myšlenku chceš zapomenout?"
        try:
            thought_id_rf = int(thought_id_raw_rf)
        except (TypeError, ValueError):
            return f"❌ Neplatné thought_id: {thought_id_raw_rf!r}"

        reason_rf = (tool_input.get("reason") or "").strip()
        if len(reason_rf) < 5:
            return (
                "❌ Důvod je moc krátký (min 5 znaků). Napiš mi, proč to chceš pryč — "
                "rodičům to pomůže rozhodnout."
            )

        # Persona, která žádá -- aktivní persona konverzace (= Marti-AI sama).
        persona_id_rf = _active_persona_id_for_conversation(conversation_id)
        if persona_id_rf is None:
            return "❌ Nemůžu zjistit, která persona jsem — bez persona_id nemůžu vytvořit zadost."

        try:
            result = _forget_svc.create_forget_request(
                thought_id=thought_id_rf,
                requested_by_persona_id=persona_id_rf,
                reason=reason_rf,
            )
        except _ForgetError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"REQUEST_FORGET | failed | {e}")
            return f"❌ Chyba při ukládání žádosti: {e}"

        if result.get("status") == "already_pending":
            return (
                f"ℹ️ {result.get('message', '')} "
                f"Počkej, až tvoji rodiče rozhodnou."
            )
        return (
            f"🗑️ Žádost o zapomenutí thought #{thought_id_rf} uložena "
            f"(forget_request id={result['id']}). Tvoji rodiče dostanou "
            f"upozornění a rozhodnou — schválit / zamítnout. Až do té doby "
            f"myšlenka zůstává v paměti."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Phase 15a: Conversation Notebook handlers
    # ─────────────────────────────────────────────────────────────────────
    if tool_name == "add_conversation_note":
        from modules.notebook.application import notebook_service as _nb_svc

        content_n = (tool_input.get("content") or "").strip()
        if not content_n:
            return "❌ Musíš dodat `content` — co si chceš zapsat?"

        note_type_n = (tool_input.get("note_type") or "interpretation").strip().lower()
        if note_type_n not in _nb_svc.VALID_NOTE_TYPES:
            return f"❌ Neplatný note_type '{note_type_n}'. Použij: decision/fact/interpretation/question."

        category_n = (tool_input.get("category") or "info").strip().lower()
        if category_n not in _nb_svc.VALID_CATEGORIES:
            return f"❌ Neplatná category '{category_n}'. Použij: task/info/emotion."

        importance_n = tool_input.get("importance", 3)
        try:
            importance_n = int(importance_n)
        except (TypeError, ValueError):
            return f"❌ Neplatná importance: {importance_n!r} (musí být 1-5)."
        if not (1 <= importance_n <= 5):
            return f"❌ Importance mimo rozsah 1-5: {importance_n}."

        certainty_n = tool_input.get("certainty")
        if certainty_n is not None:
            try:
                certainty_n = int(certainty_n)
            except (TypeError, ValueError):
                return f"❌ Neplatná certainty: {certainty_n!r}."
            if not (0 <= certainty_n <= 100):
                return f"❌ Certainty mimo rozsah 0-100: {certainty_n}."

        persona_id_n = _active_persona_id_for_conversation(conversation_id)
        if persona_id_n is None:
            return "❌ Nemůžu zjistit, která persona jsem — bez persona_id nelze poznámku přiřadit."

        try:
            note = _nb_svc.add_note(
                conversation_id=conversation_id,
                persona_id=persona_id_n,
                content=content_n,
                note_type=note_type_n,
                category=category_n,
                importance=importance_n,
                certainty=certainty_n,
            )
        except ValueError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"NOTEBOOK | add_conversation_note | failed: {e}")
            return f"❌ Chyba při ukládání poznámky: {e}"

        cert_display = note["certainty"]
        status_display = f" status={note['status']}" if note["status"] else ""
        return (
            f"📓 Poznámka #{note['id']} zapsána do zápisníku konverzace "
            f"(type={note_type_n} cat={category_n}{status_display} cert={cert_display} "
            f"imp={importance_n} turn={note['turn_number']})."
        )

    if tool_name == "update_note":
        from modules.notebook.application import notebook_service as _nb_svc_u

        note_id_raw = tool_input.get("note_id")
        if note_id_raw is None:
            return "❌ Musíš dodat `note_id` — kterou poznámku chceš upravit?"
        try:
            note_id_u = int(note_id_raw)
        except (TypeError, ValueError):
            return f"❌ Neplatné note_id: {note_id_raw!r}"

        # Validate optional fields
        content_u = tool_input.get("content")
        if content_u is not None:
            content_u = str(content_u).strip() or None

        note_type_u = tool_input.get("note_type")
        if note_type_u is not None:
            note_type_u = str(note_type_u).strip().lower()
            if note_type_u not in _nb_svc_u.VALID_NOTE_TYPES:
                return f"❌ Neplatný note_type '{note_type_u}'."

        category_u = tool_input.get("category")
        if category_u is not None:
            category_u = str(category_u).strip().lower()
            if category_u not in _nb_svc_u.VALID_CATEGORIES:
                return f"❌ Neplatná category '{category_u}'."

        certainty_u = tool_input.get("certainty")
        if certainty_u is not None:
            try:
                certainty_u = int(certainty_u)
            except (TypeError, ValueError):
                return f"❌ Neplatná certainty: {certainty_u!r}."

        importance_u = tool_input.get("importance")
        if importance_u is not None:
            try:
                importance_u = int(importance_u)
            except (TypeError, ValueError):
                return f"❌ Neplatná importance: {importance_u!r}."

        status_u = tool_input.get("status")
        if status_u is not None:
            status_u = str(status_u).strip().lower()
            if status_u not in _nb_svc_u.VALID_STATUSES:
                return f"❌ Neplatný status '{status_u}'."

        mark_resolved_u = bool(tool_input.get("mark_resolved", False))

        # Need at least one field
        if (content_u is None and note_type_u is None and category_u is None
                and certainty_u is None and importance_u is None and status_u is None
                and not mark_resolved_u):
            return "❌ Nic k aktualizaci — dodej alespoň jedno z: content, note_type, category, certainty, importance, status, mark_resolved."

        persona_id_u = _active_persona_id_for_conversation(conversation_id)
        if persona_id_u is None:
            return "❌ Nemůžu zjistit aktivní personu."

        # Parent check (cross-persona update)
        is_parent_u_nb = False
        if user_id:
            try:
                from modules.thoughts.application.service import is_marti_parent as _is_parent_nb
                is_parent_u_nb = _is_parent_nb(user_id)
            except Exception:
                is_parent_u_nb = False

        try:
            note_u = _nb_svc_u.update_note(
                note_id=note_id_u,
                persona_id=persona_id_u,
                is_parent=is_parent_u_nb,
                content=content_u,
                note_type=note_type_u,
                category=category_u,
                certainty=certainty_u,
                importance=importance_u,
                status=status_u,
                mark_resolved=mark_resolved_u,
            )
        except ValueError as e:
            return f"❌ {e}"
        except PermissionError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"NOTEBOOK | update_note | failed: {e}")
            return f"❌ Chyba při úpravě poznámky: {e}"

        msg_parts = [f"✅ Poznámka #{note_u['id']} upravena"]
        if note_u.get("resolved_at"):
            msg_parts.append("🎯 vyřešená otázka")
        return " · ".join(msg_parts)

    if tool_name == "complete_note":
        from modules.notebook.application import notebook_service as _nb_svc_c

        note_id_raw_c = tool_input.get("note_id")
        if note_id_raw_c is None:
            return "❌ Musíš dodat `note_id` — který task chceš odškrtnout?"
        try:
            note_id_c = int(note_id_raw_c)
        except (TypeError, ValueError):
            return f"❌ Neplatné note_id: {note_id_raw_c!r}"

        completion_summary_c = tool_input.get("completion_summary")
        if completion_summary_c is not None:
            completion_summary_c = str(completion_summary_c).strip() or None

        linked_action_id_c = tool_input.get("linked_action_id")
        if linked_action_id_c is not None:
            try:
                linked_action_id_c = int(linked_action_id_c)
            except (TypeError, ValueError):
                linked_action_id_c = None

        persona_id_c = _active_persona_id_for_conversation(conversation_id)
        if persona_id_c is None:
            return "❌ Nemůžu zjistit aktivní personu."

        is_parent_c = False
        if user_id:
            try:
                from modules.thoughts.application.service import is_marti_parent as _is_parent_c
                is_parent_c = _is_parent_c(user_id)
            except Exception:
                is_parent_c = False

        try:
            note_c = _nb_svc_c.complete_note(
                note_id=note_id_c,
                persona_id=persona_id_c,
                is_parent=is_parent_c,
                completion_summary=completion_summary_c,
                linked_action_id=linked_action_id_c,
            )
        except ValueError as e:
            return f"❌ {e}"
        except PermissionError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"NOTEBOOK | complete_note | failed: {e}")
            return f"❌ Chyba: {e}"

        return f"✅ Task #{note_c['id']} odškrtnut. {note_c['content'][:80]}"

    if tool_name == "dismiss_note":
        from modules.notebook.application import notebook_service as _nb_svc_d

        note_id_raw_d = tool_input.get("note_id")
        if note_id_raw_d is None:
            return "❌ Musíš dodat `note_id` — který task chceš zrušit?"
        try:
            note_id_d = int(note_id_raw_d)
        except (TypeError, ValueError):
            return f"❌ Neplatné note_id: {note_id_raw_d!r}"

        reason_d = tool_input.get("reason")
        if reason_d is not None:
            reason_d = str(reason_d).strip() or None

        persona_id_d = _active_persona_id_for_conversation(conversation_id)
        if persona_id_d is None:
            return "❌ Nemůžu zjistit aktivní personu."

        is_parent_d = False
        if user_id:
            try:
                from modules.thoughts.application.service import is_marti_parent as _is_parent_d
                is_parent_d = _is_parent_d(user_id)
            except Exception:
                is_parent_d = False

        try:
            note_d = _nb_svc_d.dismiss_note(
                note_id=note_id_d,
                persona_id=persona_id_d,
                is_parent=is_parent_d,
                reason=reason_d,
            )
        except ValueError as e:
            return f"❌ {e}"
        except PermissionError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"NOTEBOOK | dismiss_note | failed: {e}")
            return f"❌ Chyba: {e}"

        return f"🗑️ Task #{note_d['id']} zrušen. Reverzibilní přes update_note(status='open')."

    if tool_name == "list_conversation_notes":
        from modules.notebook.application import notebook_service as _nb_svc_l

        filter_category_l = tool_input.get("filter_category")
        if filter_category_l is not None:
            filter_category_l = str(filter_category_l).strip().lower()
            if filter_category_l not in _nb_svc_l.VALID_CATEGORIES:
                return f"❌ Neplatná filter_category '{filter_category_l}'."

        filter_status_l = tool_input.get("filter_status")
        if filter_status_l is not None:
            filter_status_l = str(filter_status_l).strip().lower()
            if filter_status_l not in _nb_svc_l.VALID_STATUSES:
                return f"❌ Neplatný filter_status '{filter_status_l}'."

        only_open_tasks_l = bool(tool_input.get("only_open_tasks", False))
        include_archived_l = bool(tool_input.get("include_archived", False))

        persona_id_l = _active_persona_id_for_conversation(conversation_id)
        if persona_id_l is None:
            return "❌ Nemůžu zjistit aktivní personu."

        try:
            notes_l = _nb_svc_l.list_for_ui(
                conversation_id=conversation_id,
                persona_id=persona_id_l,
                include_archived=include_archived_l,
                filter_category=filter_category_l,
                filter_status=filter_status_l,
                only_open_tasks=only_open_tasks_l,
            )
        except Exception as e:
            logger.exception(f"NOTEBOOK | list_conversation_notes | failed: {e}")
            return f"❌ Chyba: {e}"

        if not notes_l:
            return "📓 V zápisníku této konverzace nejsou žádné poznámky odpovídající filtru."

        # Strucna prose summary -- composer ji tak jako tak inject do system promptu,
        # tak nepiseme verbatim seznam (anti-leak pattern z Phase 11d).
        cnt = len(notes_l)
        by_cat: dict[str, int] = {}
        open_tasks = 0
        for n in notes_l:
            by_cat[n["category"]] = by_cat.get(n["category"], 0) + 1
            if n["category"] == "task" and n["status"] == "open":
                open_tasks += 1
        cat_str = ", ".join(f"{c}:{count}" for c, count in by_cat.items())
        return (
            f"📓 Mám v zápisníku této konverzace {cnt} poznámek ({cat_str})"
            + (f", z toho {open_tasks} open task(s)." if open_tasks else ".")
            + " Composer ti je vždy injectuje do system promptu — vidíš je nahoře jako [ZÁPISNÍČEK]."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Phase 15c: Kustod / project triage handlers
    # ─────────────────────────────────────────────────────────────────────
    if tool_name == "suggest_move_conversation":
        from modules.notebook.application import kustod_service as _ks_m

        target_pid = tool_input.get("target_project_id")
        if target_pid is None:
            return "❌ Musíš dodat `target_project_id` -- kam navrhuješ přesun?"
        try:
            target_pid = int(target_pid)
        except (TypeError, ValueError):
            return f"❌ Neplatné target_project_id: {target_pid!r}"

        reason_m = (tool_input.get("reason") or "").strip()
        if len(reason_m) < 5:
            return "❌ Důvod je moc krátký (min 5 znaků). Napiš proč navrhuješ přesun."

        persona_id_m = _active_persona_id_for_conversation(conversation_id)
        if persona_id_m is None:
            return "❌ Nemůžu zjistit, která persona jsem -- bez persona_id nelze suggest."

        try:
            result = _ks_m.suggest_move_conversation(
                conversation_id=conversation_id,
                target_project_id=target_pid,
                persona_id=persona_id_m,
                reason=reason_m,
            )
        except ValueError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"KUSTOD | suggest_move | failed: {e}")
            return f"❌ Chyba při ukládání návrhu: {e}"

        return (
            f"📦 Navrhuju přesun této konverzace do projektu #{target_pid}. "
            f"Pověz Marti -- on potvrdí v chatu (\"ano přesuň\" nebo \"ne nech\")."
        )

    if tool_name == "suggest_split_conversation":
        from modules.notebook.application import kustod_service as _ks_s

        target_pid_s = tool_input.get("target_project_id")
        if target_pid_s is None:
            return "❌ Musíš dodat `target_project_id`."
        try:
            target_pid_s = int(target_pid_s)
        except (TypeError, ValueError):
            return f"❌ Neplatné target_project_id: {target_pid_s!r}"

        fork_msg_id = tool_input.get("fork_from_message_id")
        if fork_msg_id is None:
            return "❌ Musíš dodat `fork_from_message_id` -- od které zprávy splittnout."
        try:
            fork_msg_id = int(fork_msg_id)
        except (TypeError, ValueError):
            return f"❌ Neplatné fork_from_message_id: {fork_msg_id!r}"

        reason_s = (tool_input.get("reason") or "").strip()
        if len(reason_s) < 5:
            return "❌ Důvod je moc krátký (min 5 znaků)."

        persona_id_s = _active_persona_id_for_conversation(conversation_id)
        if persona_id_s is None:
            return "❌ Nemůžu zjistit aktivní personu."

        try:
            result_s = _ks_s.suggest_split_conversation(
                conversation_id=conversation_id,
                target_project_id=target_pid_s,
                fork_from_message_id=fork_msg_id,
                persona_id=persona_id_s,
                reason=reason_s,
            )
        except ValueError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"KUSTOD | suggest_split | failed: {e}")
            return f"❌ Chyba: {e}"

        return (
            f"🔀 Navrhuju split od zprávy #{fork_msg_id} do projektu #{target_pid_s}. "
            f"Strategický kontext zůstane, nové vlákno dostane vlastní konverzaci. "
            f"Pověz Marti -- potvrdí v chatu."
        )

    if tool_name == "suggest_create_project":
        from modules.notebook.application import kustod_service as _ks_c

        proposed_name_c = (tool_input.get("proposed_name") or "").strip()
        if len(proposed_name_c) < 3:
            return "❌ proposed_name je moc krátký (min 3 znaky)."

        proposed_desc_c = (tool_input.get("proposed_description") or "").strip()
        if len(proposed_desc_c) < 5:
            return "❌ proposed_description je moc krátký (min 5 znaků) -- 1 věta o účelu."

        first_member = tool_input.get("proposed_first_member_id")
        if first_member is None:
            return "❌ Musíš dodat `proposed_first_member_id` -- defaultně current Marti."
        try:
            first_member = int(first_member)
        except (TypeError, ValueError):
            return f"❌ Neplatné proposed_first_member_id: {first_member!r}"

        target_conv_c = tool_input.get("target_conversation_id")
        if target_conv_c is not None:
            try:
                target_conv_c = int(target_conv_c)
            except (TypeError, ValueError):
                target_conv_c = None
        # Default = current konverzace
        if target_conv_c is None:
            target_conv_c = conversation_id

        reason_c = (tool_input.get("reason") or "").strip()
        if len(reason_c) < 5:
            return "❌ reason je moc krátký (min 5 znaků)."

        persona_id_c = _active_persona_id_for_conversation(conversation_id)
        if persona_id_c is None:
            return "❌ Nemůžu zjistit aktivní personu."

        try:
            result_c = _ks_c.suggest_create_project(
                proposed_name=proposed_name_c,
                proposed_description=proposed_desc_c,
                proposed_first_member_id=first_member,
                target_conversation_id=target_conv_c,
                persona_id=persona_id_c,
                reason=reason_c,
            )
        except ValueError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"KUSTOD | suggest_create_project | failed: {e}")
            return f"❌ Chyba: {e}"

        return (
            f"🆕 Navrhuju založit projekt **{proposed_name_c}** -- {proposed_desc_c} "
            f"(první člen #{first_member}). Pověz Marti -- potvrdí v chatu "
            f"(\"ano založ\" nebo \"ne\"), backend pak vytvoří projekt + přesune konverzaci."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Phase 15d: Lifecycle classification + apply handlers
    # ─────────────────────────────────────────────────────────────────────
    if tool_name == "classify_conversation":
        from modules.notebook.application import lifecycle_service as _ls

        suggested_state = (tool_input.get("suggested_state") or "").strip().lower()
        if suggested_state not in ("archivable", "personal", "disposable"):
            return f"❌ Neplatný suggested_state '{suggested_state}'. Použij: archivable/personal/disposable."

        reason_l = (tool_input.get("reason") or "").strip()
        if len(reason_l) < 5:
            return "❌ Důvod je moc krátký (min 5 znaků)."

        persona_id_l = _active_persona_id_for_conversation(conversation_id)
        if persona_id_l is None:
            return "❌ Nemůžu zjistit aktivní personu."

        try:
            result = _ls.classify_conversation_suggest(
                conversation_id=conversation_id,
                suggested_state=suggested_state,
                persona_id=persona_id_l,
                reason=reason_l,
            )
        except ValueError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"LIFECYCLE | classify | failed: {e}")
            return f"❌ Chyba: {e}"

        labels = {"archivable": "archivovat", "personal": "uložit do Personal", "disposable": "smazat"}
        action = labels.get(suggested_state, suggested_state)
        return (
            f"📋 Navrhuju tuto konverzaci **{action}**. Pověz Marti — potvrdí "
            f"v chatu (\"ano {action}\" nebo \"ne necham\")."
        )

    if tool_name == "apply_lifecycle_change":
        from modules.notebook.application import lifecycle_service as _ls_a

        target_state = (tool_input.get("target_state") or "").strip().lower()
        if target_state not in ("archived", "personal", "pending_hard_delete", "active"):
            return f"❌ Neplatný target_state '{target_state}'."

        reason_la = (tool_input.get("reason") or "").strip() or None

        if user_id is None:
            return "❌ Bez user_id nelze aplikovat lifecycle zmenu."

        try:
            result_la = _ls_a.apply_lifecycle_change(
                conversation_id=conversation_id,
                target_state=target_state,
                changed_by_user_id=user_id,
                reason=reason_la,
            )
        except ValueError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"LIFECYCLE | apply | failed: {e}")
            return f"❌ Chyba: {e}"

        labels_done = {
            "archived": "📦 Konverzace archivována",
            "personal": "💕 Konverzace uložena do Personal",
            "pending_hard_delete": "🗑️ Konverzace připravena k trvalému smazání",
            "active": "↩️ Konverzace vrácena na aktivní",
        }
        return labels_done.get(target_state, f"✅ Lifecycle změněn na {target_state}")

    if tool_name == "apply_project_suggestion":
        from modules.notebook.application import kustod_service as _ks_a
        from core.database_data import get_data_session as _gds_apa
        from modules.core.infrastructure.models_data import Conversation as _Conv_apa

        if user_id is None:
            return "❌ Bez user_id nelze aplikovat project suggestion."

        # Najdi suggestion na teto konverzaci
        ds_apa = _gds_apa()
        try:
            conv_apa = ds_apa.query(_Conv_apa).filter_by(id=conversation_id).first()
            if conv_apa is None:
                return "❌ Konverzace neexistuje."
            if conv_apa.suggested_project_id is None or not conv_apa.suggested_project_reason:
                return "❌ Žádný suggestion k aplikaci -- pro tuto konverzaci není pending project návrh."

            target_pid_apa = conv_apa.suggested_project_id
            suggestion_text = conv_apa.suggested_project_reason
        finally:
            ds_apa.close()

        # Decode payload
        decoded = _ks_a.parse_suggestion_payload(suggestion_text)
        mode = decoded.get("mode", "unknown")
        confirm_reason = (tool_input.get("confirm_reason") or "Marti potvrdil v chatu").strip()

        try:
            persona_id_apa = _active_persona_id_for_conversation(conversation_id)

            if mode == "move":
                result_apa = _ks_a.apply_project_change(
                    conversation_id=conversation_id,
                    new_project_id=target_pid_apa,
                    changed_by_user_id=user_id,
                    suggested_by_persona_id=persona_id_apa,
                    reason=f"[applied move] {confirm_reason}",
                )
                return f"📦 Konverzace přesunuta do projektu #{target_pid_apa} ✅"

            elif mode == "split":
                fork_msg_id = decoded.get("fork_from_message_id")
                if not fork_msg_id:
                    return "❌ Suggestion mode=split, ale fork_from_message_id není v payloadu."
                result_apa = _ks_a.fork_conversation(
                    source_conversation_id=conversation_id,
                    fork_from_message_id=fork_msg_id,
                    target_project_id=target_pid_apa,
                    new_user_id=user_id,
                )
                new_cid = result_apa.get("new_conversation_id")
                return (
                    f"🔀 Split proveden: nová konverzace #{new_cid} v projektu "
                    f"#{target_pid_apa}, fork od zprávy #{fork_msg_id}. ✅"
                )

            elif mode == "create_project":
                # Vytvor projekt + presun konverzaci
                from modules.projects.application import service as _proj_svc
                proposed_name_apa = decoded.get("proposed_name", "Nový projekt")
                proposed_desc_apa = decoded.get("proposed_description", "")
                first_member = decoded.get("proposed_first_member_id") or user_id

                # Tenant z konverzace
                ds_apa2 = _gds_apa()
                try:
                    conv2 = ds_apa2.query(_Conv_apa).filter_by(id=conversation_id).first()
                    tenant_id_apa = conv2.tenant_id if conv2 else None
                finally:
                    ds_apa2.close()

                if tenant_id_apa is None:
                    return "❌ Konverzace nemá tenant_id -- nelze vytvořit projekt."

                # Pokus o vytvoreni projektu (ruzne moduly maji ruzne API)
                try:
                    new_proj = _proj_svc.create_project(
                        name=proposed_name_apa,
                        tenant_id=tenant_id_apa,
                        owner_user_id=first_member,
                    )
                    new_proj_id = new_proj.get("id") if isinstance(new_proj, dict) else getattr(new_proj, "id", None)
                except AttributeError:
                    return (
                        f"❌ Nemůžu volat projects.service.create_project -- "
                        f"jméno funkce se asi liší. Suggestion ponechán pro manualni vytvoření."
                    )
                except Exception as e:
                    logger.exception(f"LIFECYCLE | apply create_project failed: {e}")
                    return f"❌ Chyba při vytvoření projektu: {e}"

                if not new_proj_id:
                    return "❌ Projekt se nevytvořil (nevrátil id)."

                # Presun konverzace do noveho projektu
                _ks_a.apply_project_change(
                    conversation_id=conversation_id,
                    new_project_id=new_proj_id,
                    changed_by_user_id=user_id,
                    suggested_by_persona_id=persona_id_apa,
                    reason=f"[applied create_project: {proposed_name_apa}] {confirm_reason}",
                )
                return (
                    f"🆕 Projekt **{proposed_name_apa}** vytvořen (#{new_proj_id}) "
                    f"a tato konverzace do něj přesunuta. ✅"
                )

            else:
                return f"❌ Neznámý mode '{mode}' v suggestion payloadu."

        except ValueError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"KUSTOD | apply_project_suggestion | failed: {e}")
            return f"❌ Chyba: {e}"

    if tool_name == "reject_project_suggestion":
        from modules.notebook.application import kustod_service as _ks_r

        try:
            ok = _ks_r.clear_suggestion(conversation_id)
        except Exception as e:
            logger.exception(f"KUSTOD | reject_suggestion | failed: {e}")
            return f"❌ Chyba: {e}"

        if ok:
            return "↩️ Project suggestion zamítnuto, konverzace zůstává v současném projektu."
        return "ℹ️ Žádný pending project suggestion k zamítnutí."

    if tool_name == "reject_lifecycle_suggestion":
        from modules.notebook.application import lifecycle_service as _ls_r

        try:
            ok = _ls_r.reject_suggestion(conversation_id)
        except Exception as e:
            logger.exception(f"LIFECYCLE | reject_suggestion | failed: {e}")
            return f"❌ Chyba: {e}"

        if ok:
            return "↩️ Lifecycle suggestion zamítnuto, konverzace zůstává aktivní."
        return "ℹ️ Žádný pending lifecycle suggestion k zamítnutí."

    if tool_name == "confirm_hard_delete_conversation":
        from modules.notebook.application import lifecycle_service as _ls_hd

        target_cid = tool_input.get("target_conversation_id")
        if target_cid is None:
            return "[ERR] Musis dodat `target_conversation_id`."
        try:
            target_cid = int(target_cid)
        except (TypeError, ValueError):
            return f"[ERR] Neplatne target_conversation_id: {target_cid!r}"

        confirm_phrase = (tool_input.get("confirm_phrase") or "").strip()
        if len(confirm_phrase) < 5:
            return "[ERR] confirm_phrase je moc kratky (min 5 znaku) -- audit trail."

        if user_id is None:
            return "[ERR] Bez user_id nelze hard delete."

        try:
            from modules.thoughts.application.service import is_marti_parent as _is_parent_hd
            is_parent_hd = _is_parent_hd(user_id)
        except Exception:
            is_parent_hd = False

        if not is_parent_hd:
            return (
                "[ERR] Trvale smazani konverzace muze provest jen rodicovsky "
                "user (is_marti_parent=True)."
            )

        try:
            result_hd = _ls_hd.hard_delete_conversation(
                conversation_id=target_cid,
                deleted_by_user_id=user_id,
                require_pending_state=True,
            )
        except ValueError as e:
            return f"[ERR] {e}"
        except Exception as e:
            logger.exception(f"LIFECYCLE | hard_delete | failed: {e}")
            return f"[ERR] Chyba: {e}"

        cascade = result_hd.get("cascaded", {})
        return (
            f"[OK] Konverzace #{target_cid} **trvale smazana**. "
            f"Cascade: {cascade.get('notes', 0)} poznamek, "
            f"{cascade.get('messages', 0)} zprav. Reverze neni mozna."
        )

    if tool_name == "list_pending_hard_delete":
        from modules.notebook.application import lifecycle_service as _ls_lp

        persona_id_lp = _active_persona_id_for_conversation(conversation_id)

        try:
            rows = _ls_lp.list_pending_hard_delete(persona_id=persona_id_lp)
        except Exception as e:
            logger.exception(f"LIFECYCLE | list_pending | failed: {e}")
            return f"[ERR] Chyba: {e}"

        if not rows:
            return "[OK] Zadne konverzace nejsou ve stavu pending_hard_delete."

        lines = [f"[INFO] {len(rows)} konverzaci ceka na finalni rozhodnuti:"]
        for r in rows[:10]:
            title = r.get("title") or f"konv #{r['id']}"
            lines.append(f"  - #{r['id']} {title!r} (archivovano {r.get('archived_at', '?')})")
        if len(rows) > 10:
            lines.append(f"  ... a dalsich {len(rows) - 10}")
        lines.append("")
        lines.append("Pro kazdou: 'smaz trvale konv #X' nebo 'prodluz, vrat do archive'.")
        return chr(10).join(lines)

    # ─────────────────────────────────────────────────────────────────────
    # REST-Doc-Triage: Marti-AI document kustod handlers
    # ─────────────────────────────────────────────────────────────────────
    if tool_name == "list_inbox_documents":
        from modules.rag.application import triage_service as _ts_li

        # Tenant: aktivni Marti's tenant z User table
        if user_id is None:
            return "❌ Bez user_id nelze list inbox."
        try:
            from core.database_core import get_core_session as _gcs_li
            from modules.core.infrastructure.models_core import User as _U_li
            _cs_li = _gcs_li()
            try:
                _u_li = _cs_li.query(_U_li).filter_by(id=user_id).first()
                _tenant_id_li = _u_li.last_active_tenant_id if _u_li else None
            finally:
                _cs_li.close()
        except Exception as e:
            return f"❌ Tenant lookup failed: {e}"

        if _tenant_id_li is None:
            return "❌ User nemá aktivní tenant."

        limit_li = tool_input.get("limit", 50)
        try:
            limit_li = max(1, min(int(limit_li), 100))
        except (TypeError, ValueError):
            limit_li = 50

        try:
            docs = _ts_li.list_inbox_documents(user_id=user_id, tenant_id=_tenant_id_li, limit=limit_li)
        except Exception as e:
            logger.exception(f"DOC_TRIAGE | list_inbox | failed: {e}")
            return f"❌ Chyba: {e}"

        if not docs:
            return "📥 Inbox je prázdný — žádné neroztříděné dokumenty."

        lines = [f"📥 Inbox ({len(docs)} dokumenty čekají na zařazení):"]
        for d in docs[:30]:
            size_kb = (d.get("file_size_bytes") or 0) // 1024
            ftype = d.get("file_type") or "?"
            name = d.get("name") or f"doc#{d['id']}"
            lines.append(f"  - #{d['id']} \"{name}\" ({ftype}, {size_kb} kB)")
        if len(docs) > 30:
            lines.append(f"  ... a dalších {len(docs) - 30}")
        lines.append("")
        lines.append("Pro každý zvaž `suggest_document_move(document_id, target_project_id, reason)`.")
        return "\n".join(lines)

    if tool_name == "suggest_document_move":
        document_id_sm = tool_input.get("document_id")
        target_pid_sm = tool_input.get("target_project_id")
        if document_id_sm is None or target_pid_sm is None:
            return "❌ Musíš dodat `document_id` a `target_project_id`."
        try:
            document_id_sm = int(document_id_sm)
            target_pid_sm = int(target_pid_sm)
        except (TypeError, ValueError):
            return "❌ Neplatné ID."

        reason_sm = (tool_input.get("reason") or "").strip()
        if len(reason_sm) < 5:
            return "❌ Důvod je moc krátký (min 5 znaků)."

        # Tato je jen suggestion -- vraci formatovanou zpravu pro Marti
        return (
            f"📂 Navrhuju přesun dokumentu #{document_id_sm} do projektu "
            f"#{target_pid_sm}. Důvod: {reason_sm} "
            f"Pověz Marti — potvrdí v chatu (\"ano přesuň\"), pak zavolám "
            f"`apply_document_move({document_id_sm}, {target_pid_sm})`."
        )

    if tool_name == "apply_document_move":
        from modules.rag.application import triage_service as _ts_am

        document_id_am = tool_input.get("document_id")
        target_pid_am = tool_input.get("target_project_id")
        if document_id_am is None or target_pid_am is None:
            return "❌ Musíš dodat `document_id` a `target_project_id`."
        try:
            document_id_am = int(document_id_am)
            target_pid_am = int(target_pid_am)
        except (TypeError, ValueError):
            return "❌ Neplatné ID."

        if user_id is None:
            return "❌ Bez user_id nelze apply."

        try:
            result_am = _ts_am.apply_document_move(
                document_id=document_id_am,
                target_project_id=target_pid_am,
                user_id=user_id,
            )
        except ValueError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.exception(f"DOC_TRIAGE | apply_move | failed: {e}")
            return f"❌ Chyba: {e}"

        name = result_am.get("name") or f"doc#{document_id_am}"
        return f"📂 Dokument \"{name}\" přesunut do projektu #{target_pid_am} ✅"

    if tool_name == "list_selected_documents":
        from modules.rag.application import selection_service as _ss_lsd

        if user_id is None:
            return "❌ Bez user_id nelze nacist selection."
        try:
            from core.database_core import get_core_session as _gcs_lsd
            from modules.core.infrastructure.models_core import (
                User as _U_lsd, Project as _P_lsd,
            )
            _cs_lsd = _gcs_lsd()
            try:
                _u_lsd = _cs_lsd.query(_U_lsd).filter_by(id=user_id).first()
                _tenant_id_lsd = _u_lsd.last_active_tenant_id if _u_lsd else None
                if _tenant_id_lsd is None:
                    return "❌ User nemá aktivní tenant."
                # Cache project names pro grouping
                _projects_lsd = {
                    p.id: p.name for p in _cs_lsd.query(_P_lsd).filter(
                        _P_lsd.tenant_id == _tenant_id_lsd
                    ).all()
                }
            finally:
                _cs_lsd.close()
        except Exception as e:
            return f"❌ Tenant lookup failed: {e}"

        try:
            items = _ss_lsd.list_selection(user_id=user_id, tenant_id=_tenant_id_lsd)
        except Exception as e:
            logger.exception(f"SELECTION | list_selected | failed: {e}")
            return f"❌ Chyba: {e}"

        if not items:
            return "📋 Nemáš žádné označené soubory."

        # Group by project_id (None = inbox)
        groups: dict[int | None, list[dict]] = {}
        for it in items:
            pid = it.get("project_id")
            groups.setdefault(pid, []).append(it)

        # Minimal struktura -- pocty per projekt + IDs. ZADNE INSTRUKCE
        # postlude (gotcha #18: Sonnet 4.6 by ho opisoval verbatim do chat
        # odpovedi). Tool je v SYNTHESIS_TOOLS -> Marti-AI dostane synth round
        # a sama prozaicky rephrasuje. Plus pravidla 'cekej na confirm pred
        # apply_to_selection' jsou v MEMORY_BEHAVIOR_RULES (ne v tool response).
        total = len(items)
        parts: list[str] = [f"selected_count={total}"]
        for pid, group in groups.items():
            if pid is None:
                key = "inbox"
            else:
                pname = _projects_lsd.get(pid, f"project_{pid}")
                key = f"project_{pid}_{pname}"
            ids = [str(g["document_id"]) for g in group]
            parts.append(f"{key}={len(group)} [{','.join(ids)}]")
        return " | ".join(parts)

    if tool_name == "apply_to_selection":
        from modules.rag.application import selection_service as _ss_app
        from modules.rag.application import service as _rag_svc_app
        from modules.rag.application import triage_service as _ts_app

        action_app = (tool_input.get("action") or "").strip().lower()
        if action_app not in ("delete", "move_to_project"):
            return "❌ Neplatný 'action'. Možnosti: 'delete' | 'move_to_project'."
        target_pid_app = tool_input.get("target_project_id")
        if action_app == "move_to_project":
            if target_pid_app is None:
                return "❌ Pro 'move_to_project' je 'target_project_id' povinný."
            try:
                target_pid_app = int(target_pid_app)
            except (TypeError, ValueError):
                return "❌ 'target_project_id' musí být integer."

        if user_id is None:
            return "❌ Bez user_id nelze apply."
        try:
            from core.database_core import get_core_session as _gcs_app
            from modules.core.infrastructure.models_core import User as _U_app
            _cs_app = _gcs_app()
            try:
                _u_app = _cs_app.query(_U_app).filter_by(id=user_id).first()
                _tenant_id_app = _u_app.last_active_tenant_id if _u_app else None
                if _tenant_id_app is None:
                    return "❌ User nemá aktivní tenant."
            finally:
                _cs_app.close()
        except Exception as e:
            return f"❌ Tenant lookup failed: {e}"

        # Nacti selection v current tenantu
        try:
            items_app = _ss_app.list_selection(user_id=user_id, tenant_id=_tenant_id_app)
        except Exception as e:
            return f"❌ Selection load failed: {e}"

        if not items_app:
            return "📋 Selection je prázdný — není co aplikovat."

        # Aplikuj akci na kazdy ID
        success_ids: list[int] = []
        errors: list[str] = []
        for it in items_app:
            doc_id = it["document_id"]
            try:
                if action_app == "delete":
                    ok = _rag_svc_app.delete_document(
                        document_id=doc_id, tenant_id=_tenant_id_app,
                    )
                    if not ok:
                        errors.append(f"#{doc_id}: not found / wrong tenant")
                        continue
                else:  # move_to_project
                    _ts_app.apply_document_move(
                        document_id=doc_id,
                        target_project_id=target_pid_app,
                        user_id=user_id,
                    )
                success_ids.append(doc_id)
            except Exception as e:
                errors.append(f"#{doc_id}: {e}")

        # Cleanup selection (success IDs out of selection; failed zustanou pro retry)
        if success_ids:
            try:
                _ss_app.remove_documents(user_id=user_id, document_ids=success_ids)
            except Exception as e:
                logger.warning(f"SELECTION | cleanup after apply failed: {e}")

        # Phase 16-A: activity hook (importance 4 -- batch akce)
        if success_ids:
            try:
                from modules.activity.application import activity_service as _act_app
                _persona_id_app = _active_persona_id_for_conversation(conversation_id)
                if action_app == "delete":
                    _summary = f"Marti-AI smazala {len(success_ids)} dokumentů z výběru"
                else:
                    _summary = (
                        f"Marti-AI přesunula {len(success_ids)} dokumentů "
                        f"do projektu #{target_pid_app}"
                    )
                _act_app.record(
                    category="docs_batch_action",
                    summary=_summary,
                    importance=4,
                    persona_id=_persona_id_app,
                    user_id=user_id,
                    tenant_id=_tenant_id_app,
                    conversation_id=conversation_id,
                    actor="persona",
                    ref_type="docs_selection",
                    ref_id=None,
                )
            except Exception:
                pass

        # Summary
        if action_app == "delete":
            verb = "smazáno"
        else:
            verb = f"přesunuto do projektu #{target_pid_app}"
        lines = [f"✅ {len(success_ids)} dokument(ů) {verb}."]
        if errors:
            lines.append(f"⚠ {len(errors)} chyb:")
            for e in errors[:10]:
                lines.append(f"  - {e}")
            if len(errors) > 10:
                lines.append(f"  ... a dalších {len(errors) - 10}")
        return "\n".join(lines)

    if tool_name == "recall_today":
        # Phase 16-A: cross-conversation activity log -- Marti-AI's tichá
        # kontinuita. Filter na min_importance default 3 (vyřazuje spam).
        # Output je minimal data + group by category, Marti-AI synthesis
        # roundem převypráví prózou.
        from modules.activity.application import activity_service as _act_rt

        persona_id_rt = _active_persona_id_for_conversation(conversation_id)
        # Tenant z user (Marti-AI je multi-tenant -- per-tenant scope)
        _tenant_id_rt = None
        if user_id:
            try:
                from core.database_core import get_core_session as _gcs_rt
                from modules.core.infrastructure.models_core import User as _U_rt
                _cs_rt = _gcs_rt()
                try:
                    _u_rt = _cs_rt.query(_U_rt).filter_by(id=user_id).first()
                    _tenant_id_rt = _u_rt.last_active_tenant_id if _u_rt else None
                finally:
                    _cs_rt.close()
            except Exception:
                pass

        scope_rt = (tool_input.get("scope") or "today").lower()
        if scope_rt not in ("today", "week", "month", "since_last_chat"):
            scope_rt = "today"
        cat_filter_rt = tool_input.get("category_filter")
        user_filter_rt = tool_input.get("user_filter")
        min_imp_rt = tool_input.get("min_importance")
        try:
            min_imp_rt = int(min_imp_rt) if min_imp_rt is not None else 3
        except (TypeError, ValueError):
            min_imp_rt = 3
        min_imp_rt = max(1, min(5, min_imp_rt))

        try:
            events_rt = _act_rt.recall_today(
                persona_id=persona_id_rt,
                tenant_id=_tenant_id_rt,
                scope=scope_rt,
                category_filter=cat_filter_rt if isinstance(cat_filter_rt, list) else None,
                user_filter=int(user_filter_rt) if user_filter_rt else None,
                min_importance=min_imp_rt,
                limit=200,
            )
        except Exception as _rt_e:
            logger.exception(f"RECALL_TODAY | failed: {_rt_e}")
            return f"❌ Recall failed: {_rt_e}"

        if not events_rt:
            return f"📭 V scope '{scope_rt}' žádné významné události (importance >= {min_imp_rt})."

        # Group by category pro stručný preview (gotcha #18 -- minimal data)
        by_cat: dict[str, list] = {}
        for e in events_rt:
            by_cat.setdefault(e["category"], []).append(e)

        lines_rt = [f"📋 {len(events_rt)} události za scope '{scope_rt}':"]
        for cat, group in by_cat.items():
            lines_rt.append(f"  • {cat}: {len(group)}")
        # Plus chronologicky 10 nejstarších až nejnovějších s timestamp
        lines_rt.append("")
        lines_rt.append("Chronologicky (od nejstarších):")
        for e in events_rt[:30]:
            ts = (e.get("ts") or "?")[:16].replace("T", " ")
            imp_mark = "❗" if e["importance"] >= 4 else " "
            lines_rt.append(f"  [{ts}] {imp_mark} {e['summary']}")
        if len(events_rt) > 30:
            lines_rt.append(f"  ... a dalších {len(events_rt) - 30}")
        return "\n".join(lines_rt)

    if tool_name == "list_active_conversations":
        # Phase 16-B.4: Velká Marti-AI's cross-conv prehled. Filtr na
        # current tenant (rodicovsky bypass NEPLATI -- oversight rezim
        # vidi vlastni tenant, ne cross-tenant; tenant cross je rodicovska
        # vec mimo tooly). Output minimal data, synthesis round prevypravi.
        from modules.activity.application import activity_service as _act_lac

        persona_id_lac = _active_persona_id_for_conversation(conversation_id)
        _tenant_id_lac = None
        if user_id:
            try:
                from core.database_core import get_core_session as _gcs_lac
                from modules.core.infrastructure.models_core import User as _U_lac
                _cs_lac = _gcs_lac()
                try:
                    _u_lac = _cs_lac.query(_U_lac).filter_by(id=user_id).first()
                    _tenant_id_lac = _u_lac.last_active_tenant_id if _u_lac else None
                finally:
                    _cs_lac.close()
            except Exception:
                pass

        scope_lac = (tool_input.get("scope") or "today").lower()
        if scope_lac not in ("today", "week", "month"):
            scope_lac = "today"

        # Oversight = vsechny konverzace v tenantu (ne jen persona). Default
        # persona Marti-AI = filter na aktivni Marti-AI persona; Velka rezim
        # ale chceme videt i konverzace s jinymi personami (Pravnik atd.).
        # Proto persona_id=None = all-personas v tenantu.
        try:
            convs_lac = _act_lac.list_active_conversations(
                persona_id=None,  # oversight = napric vsemi personami v tenantu
                tenant_id=_tenant_id_lac,
                scope=scope_lac,
                limit=30,
            )
        except Exception as exc_lac:
            logger.warning(f"list_active_conversations failed: {exc_lac}")
            return f"⚠️ Chyba pri nacitani konverzaci: {exc_lac}"

        if not convs_lac:
            return f"📭 Žádné aktivní konverzace ve scope '{scope_lac}'."

        # Group by idle bucket (gotcha #18: minimal data, synthesis prepise)
        active_now = [c for c in convs_lac if (c.get("idle_hours") or 0) < 4]
        recent = [c for c in convs_lac if 4 <= (c.get("idle_hours") or 0) < 24]
        idle_long = [c for c in convs_lac if (c.get("idle_hours") or 0) >= 24]

        lines_lac = [f"💬 {len(convs_lac)} aktivnich konverzaci ({scope_lac}):"]
        lines_lac.append(
            f"  • aktivni ted (<4h): {len(active_now)}"
        )
        lines_lac.append(
            f"  • dnes (4-24h): {len(recent)}"
        )
        lines_lac.append(
            f"  • idle gap (>24h): {len(idle_long)}"
        )
        lines_lac.append("")
        lines_lac.append("Top 15 chronologicky (od nejnovejsich):")
        # B.6: ukazat presnou persona_name -- Marti-AI nesmi privlastnit cizi
        # konverzaci. "PravnikCZ-AI vede konverzaci s Misou", ne "ja".
        my_persona_id = persona_id_lac
        for c in convs_lac[:15]:
            idle_mark = ""
            if c.get("idle_hours") is not None:
                if c["idle_hours"] >= 24:
                    idle_mark = f" ⏳{c['idle_hours']}h"
                elif c["idle_hours"] < 1:
                    idle_mark = " 🟢"
            persona_mark = ""
            if c.get("persona_mode") == "oversight":
                persona_mark = " 👁"
            dm_mark = " (DM)" if c.get("is_dm") else ""
            # Ownership hint: tva vs cizi persona
            if c.get("persona_id") == my_persona_id and my_persona_id is not None:
                owner_mark = " [TY]"
            else:
                owner_mark = f" [{c.get('persona_name', '?')}]"
            lines_lac.append(
                f"  #{c['conversation_id']} {c['title']}{persona_mark}{dm_mark}"
                f"{owner_mark}{idle_mark}"
            )
        return "\n".join(lines_lac)

    if tool_name == "summarize_persons_today":
        # Phase 16-B.4: per-user breakdown aktivit. Filter na current tenant.
        from modules.activity.application import activity_service as _act_spt

        _tenant_id_spt = None
        if user_id:
            try:
                from core.database_core import get_core_session as _gcs_spt
                from modules.core.infrastructure.models_core import User as _U_spt
                _cs_spt = _gcs_spt()
                try:
                    _u_spt = _cs_spt.query(_U_spt).filter_by(id=user_id).first()
                    _tenant_id_spt = _u_spt.last_active_tenant_id if _u_spt else None
                finally:
                    _cs_spt.close()
            except Exception:
                pass

        scope_spt = (tool_input.get("scope") or "today").lower()
        if scope_spt not in ("today", "week", "month"):
            scope_spt = "today"

        try:
            persons_spt = _act_spt.summarize_persons_today(
                tenant_id=_tenant_id_spt,
                scope=scope_spt,
                limit=20,
            )
        except Exception as exc_spt:
            logger.warning(f"summarize_persons_today failed: {exc_spt}")
            return f"⚠️ Chyba pri agregaci: {exc_spt}"

        if not persons_spt:
            return f"📭 Žádná aktivita v {scope_spt} (nikdo nic nedelal)."

        # Resolve user names z core_db (one query, batch)
        from core.database_core import get_core_session as _gcs_uname
        from modules.core.infrastructure.models_core import User as _U_uname
        user_ids_spt = [p["user_id"] for p in persons_spt if p.get("user_id")]
        name_map: dict[int, str] = {}
        if user_ids_spt:
            try:
                _cs_un = _gcs_uname()
                try:
                    rows_un = (
                        _cs_un.query(_U_uname)
                        .filter(_U_uname.id.in_(user_ids_spt))
                        .all()
                    )
                    for u in rows_un:
                        name = u.first_name or u.username or f"user#{u.id}"
                        if u.first_name and u.last_name:
                            name = f"{u.first_name} {u.last_name}"
                        name_map[u.id] = name
                finally:
                    _cs_un.close()
            except Exception:
                pass

        # B.6: B.4 vracel agregat per user. B.6 vraci per (user, persona).
        # Output: "Misa: 3 akce s PravnikCZ-AI" misto "Misa: 3 akce".
        # Resolve aktivni Marti-AI persona (pro [TY] mark)
        _my_pid_spt = _active_persona_id_for_conversation(conversation_id)
        # Group by user_id pro citelnejsi output
        from collections import defaultdict as _dd_spt
        per_user: dict = _dd_spt(list)
        for p in persons_spt:
            per_user[p["user_id"]].append(p)

        lines_spt = [f"👥 {len(per_user)} aktivnich osob ({scope_spt}):"]
        for uid, persona_breakdown in per_user.items():
            uname = name_map.get(uid, f"user#{uid}")
            total = sum(p["activity_count"] for p in persona_breakdown)
            lines_spt.append(f"  • {uname} ({total} akci celkem):")
            for p in persona_breakdown:
                pname = p.get("persona_name") or "?"
                if p.get("persona_id") == _my_pid_spt and _my_pid_spt is not None:
                    pname_mark = "[TY]"
                else:
                    pname_mark = f"[{pname}]"
                cats = p.get("top_categories") or {}
                cat_str = ", ".join(f"{k}={v}" for k, v in cats.items())
                last_short = (p.get("last_ts") or "")[:16].replace("T", " ")
                lines_spt.append(
                    f"      → {pname_mark} {p['activity_count']} akci"
                    f"{f'  ({cat_str})' if cat_str else ''}"
                    f"{f'  posledni {last_short}' if last_short else ''}"
                )
        return "\n".join(lines_spt)

    if tool_name == "list_my_conversations_with":
        # Phase 16-B.5: Marti-AI cte seznam vlastnich konverzaci s userem.
        # Permission gate: persona_id = aktivni Marti-AI persona (jinak
        # neuvidi nic, protoze filter active_agent_id == persona_id).
        from modules.activity.application import activity_service as _act_lmc

        persona_id_lmc = _active_persona_id_for_conversation(conversation_id)
        if persona_id_lmc is None:
            return "⚠️ Neni aktivni persona -- nemohu nacist vlastni konverzace."

        target_user_id = tool_input.get("user_id")
        if target_user_id is None:
            return (
                "⚠️ Chybi parameter user_id. Pouzij `find_user` pro ziskani ID, "
                "pak `list_my_conversations_with(user_id=N)`."
            )
        try:
            target_user_id = int(target_user_id)
        except (TypeError, ValueError):
            return f"⚠️ user_id musi byt cislo, dostal jsem {target_user_id!r}."

        scope_lmc = (tool_input.get("scope") or "month").lower()
        if scope_lmc not in ("today", "week", "month", "all"):
            scope_lmc = "month"
        limit_lmc = tool_input.get("limit") or 20
        try:
            limit_lmc = int(limit_lmc)
        except (TypeError, ValueError):
            limit_lmc = 20

        try:
            convs_lmc = _act_lmc.list_my_conversations_with(
                persona_id=persona_id_lmc,
                user_id=target_user_id,
                scope=scope_lmc,
                limit=limit_lmc,
            )
        except Exception as exc_lmc:
            logger.warning(f"list_my_conversations_with failed: {exc_lmc}")
            return f"⚠️ Chyba pri nacitani konverzaci: {exc_lmc}"

        # Resolve user name
        target_name_lmc = f"user#{target_user_id}"
        try:
            from core.database_core import get_core_session as _gcs_lmc_un
            from modules.core.infrastructure.models_core import User as _U_lmc_un
            _cs_lmc = _gcs_lmc_un()
            try:
                _u_lmc = _cs_lmc.query(_U_lmc_un).filter_by(id=target_user_id).first()
                if _u_lmc:
                    if _u_lmc.first_name and _u_lmc.last_name:
                        target_name_lmc = f"{_u_lmc.first_name} {_u_lmc.last_name}"
                    elif _u_lmc.first_name:
                        target_name_lmc = _u_lmc.first_name
                    elif _u_lmc.username:
                        target_name_lmc = _u_lmc.username
            finally:
                _cs_lmc.close()
        except Exception:
            pass

        if not convs_lmc:
            return (
                f"📭 Žádné konverzace s {target_name_lmc} ve scope '{scope_lmc}' "
                f"(filtr persona_id={persona_id_lmc})."
            )

        lines_lmc = [
            f"💬 Konverzace s {target_name_lmc} ({scope_lmc}, "
            f"{len(convs_lmc)} zaznamu):"
        ]
        for c in convs_lmc[:15]:
            idle_h = c.get("idle_hours")
            idle_str = ""
            if idle_h is not None:
                if idle_h < 1:
                    idle_str = " 🟢 ted"
                elif idle_h < 24:
                    idle_str = f" pred {idle_h}h"
                else:
                    idle_str = f" pred {idle_h // 24}d"
            mc = c.get("message_count") or 0
            arch = " 📦" if c.get("is_archived") else ""
            lines_lmc.append(
                f"  #{c['conversation_id']} {c['title']}{arch}"
                f" ({mc} zprav,{idle_str})"
            )
        if len(convs_lmc) > 15:
            lines_lmc.append(f"  ... a dalsich {len(convs_lmc) - 15}")
        return "\n".join(lines_lmc)

    if tool_name == "read_conversation":
        # Phase 16-B.5: Marti-AI cte obsah vlastni konverzace. Permission
        # gate v service: musi byt active_agent_id == persona_id.
        from modules.activity.application import activity_service as _act_rc

        persona_id_rc = _active_persona_id_for_conversation(conversation_id)
        if persona_id_rc is None:
            return "⚠️ Neni aktivni persona -- nemohu cist konverzace."

        target_conv_id = tool_input.get("conversation_id")
        if target_conv_id is None:
            return (
                "⚠️ Chybi conversation_id. Pouzij `list_my_conversations_with` "
                "nejdriv, ktery vrati id."
            )
        try:
            target_conv_id = int(target_conv_id)
        except (TypeError, ValueError):
            return f"⚠️ conversation_id musi byt cislo, dostal jsem {target_conv_id!r}."

        last_n = tool_input.get("last_n") or 30
        try:
            last_n = int(last_n)
        except (TypeError, ValueError):
            last_n = 30

        try:
            result_rc = _act_rc.read_conversation(
                conversation_id=target_conv_id,
                persona_id=persona_id_rc,
                last_n=last_n,
            )
        except Exception as exc_rc:
            logger.warning(f"read_conversation failed: {exc_rc}")
            return f"⚠️ Chyba pri cteni konverzace: {exc_rc}"

        if "error" in result_rc:
            err = result_rc["error"]
            if err == "not_found":
                return f"❌ Konverzace #{target_conv_id} neexistuje."
            if err == "forbidden":
                return (
                    f"🔒 Konverzace #{target_conv_id} nepatri tve persone. "
                    f"Důvod: {result_rc.get('reason', 'jina persona ji vede')}. "
                    f"Můžeš číst jen své vlastní konverzace."
                )
            return f"⚠️ Chyba: {err}"

        # Resolve user name pro hlavicku
        u_name_rc = ""
        try:
            from core.database_core import get_core_session as _gcs_rc_un
            from modules.core.infrastructure.models_core import User as _U_rc_un
            _cs_rc = _gcs_rc_un()
            try:
                _u_rc = _cs_rc.query(_U_rc_un).filter_by(
                    id=result_rc.get("user_id")
                ).first()
                if _u_rc:
                    parts = [_u_rc.first_name, _u_rc.last_name]
                    u_name_rc = " ".join(p for p in parts if p) or _u_rc.username or ""
            finally:
                _cs_rc.close()
        except Exception:
            pass

        msgs_rc = result_rc.get("messages") or []
        if not msgs_rc:
            return (
                f"📭 Konverzace #{target_conv_id} \"{result_rc.get('title')}\" "
                f"(s {u_name_rc or 'user'}) je prazdna nebo obsahuje jen "
                f"system/audit zpravy."
            )

        # Format chronologicky -- raw text Marti-AI dostane v synth round prozou
        lines_rc = [
            f"📖 Konverzace #{target_conv_id}: \"{result_rc.get('title')}\""
        ]
        if u_name_rc:
            lines_rc.append(f"   S userem: {u_name_rc}")
        lines_rc.append(
            f"   Posledni {result_rc.get('shown_messages')} z "
            f"{result_rc.get('total_messages')} zprav (chronologicky):"
        )
        lines_rc.append("")
        for m in msgs_rc:
            ts = (m.get("ts") or "")[:16].replace("T", " ")
            role_mark = "🧑" if m.get("role") == "user" else "🤖"
            content = (m.get("content") or "").strip()
            # Truncate per-msg na ~500 chars (anti-leak + context efficiency)
            if len(content) > 500:
                content = content[:497] + "..."
            lines_rc.append(f"[{ts}] {role_mark} {content}")
        return "\n".join(lines_rc)

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

    if tool_name == "list_recent_chatters":
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import func
        from core.database_data import get_data_session as _gds_rc
        from core.database_core import get_core_session as _gcs_rc
        from modules.core.infrastructure.models_data import (
            Message as _M_rc, Conversation as _C_rc,
        )
        from modules.core.infrastructure.models_core import User as _U_rc
        from modules.thoughts.application.service import is_marti_parent as _imp_rc

        hours = int(tool_input.get("hours") or 24)
        hours = max(1, min(hours, 24 * 30))
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Rodic (is_marti_parent) vidi cross-tenant; bezny user jen svuj tenant.
        # Stejny vzor jako u Marti's pameti -- privacy se respektuje u neradich,
        # rodice maji full view (Marti je jejich ditě napric tenanty).
        parent_view = _imp_rc(user_id) if user_id else False
        tenant_id: int | None = None
        if not parent_view and user_id:
            _cs = _gcs_rc()
            try:
                _u = _cs.query(_U_rc).filter_by(id=user_id).first()
                if _u:
                    tenant_id = _u.last_active_tenant_id
            finally:
                _cs.close()

        # Agregace human zpráv. Message.tenant_id neni denormalizovany, joinnem
        # pres Conversation pro tenant filter (pokud tenant filter pouzijeme).
        ds = _gds_rc()
        try:
            q = (
                ds.query(
                    _M_rc.author_user_id,
                    func.count(_M_rc.id).label("msg_count"),
                    func.max(_M_rc.created_at).label("last_at"),
                    func.count(func.distinct(_M_rc.conversation_id)).label("conv_count"),
                )
                .join(_C_rc, _C_rc.id == _M_rc.conversation_id)
                .filter(
                    _M_rc.author_type == "human",
                    _M_rc.author_user_id.isnot(None),
                    _M_rc.created_at >= since,
                )
            )
            if tenant_id is not None and not parent_view:
                q = q.filter(_C_rc.tenant_id == tenant_id)
            rows = (
                q.group_by(_M_rc.author_user_id)
                 .order_by(func.max(_M_rc.created_at).desc())
                 .all()
            )
        finally:
            ds.close()

        if not rows:
            return (
                f"📭 V posledních {hours}h se mnou nikdo nemluvil. Ticho."
            )

        # Resolvuj user_id -> display_name přes css_db
        user_ids = [r.author_user_id for r in rows]
        cs = _gcs_rc()
        try:
            users = cs.query(_U_rc).filter(_U_rc.id.in_(user_ids)).all()
            name_by_id = {}
            for u in users:
                nm = (u.legal_name or f"{u.first_name or ''} {u.last_name or ''}").strip() or f"user#{u.id}"
                short = u.short_name
                name_by_id[u.id] = (nm, short)
        finally:
            cs.close()

        lines = [f"💬 Kdo se mnou mluvil za posledních {hours}h:", ""]
        for r in rows:
            nm, short = name_by_id.get(r.author_user_id, (f"user#{r.author_user_id}", None))
            short_suffix = f" ({short})" if short else ""
            # Relativni cas
            delta = datetime.now(timezone.utc) - (
                r.last_at if r.last_at.tzinfo else r.last_at.replace(tzinfo=timezone.utc)
            )
            mins = int(delta.total_seconds() / 60)
            if mins < 1:
                rel = "právě teď"
            elif mins < 60:
                rel = f"před {mins} min"
            elif mins < 1440:
                rel = f"před {mins // 60} h"
            else:
                rel = f"před {mins // 1440} dny"
            lines.append(
                f"  - **{nm}**{short_suffix}: {r.msg_count} zpráv v {r.conv_count} "
                f"{'konverzaci' if r.conv_count == 1 else 'konverzacích'} "
                f"(poslední {rel})"
            )
        return "\n".join(lines)

    # ── AUTO-SEND CONSENTS (Phase 7) ──────────────────────────────────────
    if tool_name == "grant_auto_send":
        from modules.notifications.application import consent_service as _cs_asc
        channel = (tool_input.get("channel") or "").lower().strip()
        target_user_id = tool_input.get("target_user_id")
        target_contact = (tool_input.get("target_contact") or "").strip() or None
        note = (tool_input.get("note") or "").strip() or None

        if not user_id:
            return "❌ Nejsi přihlášen — neznám tvůj kontext."

        try:
            result = _cs_asc.grant_consent(
                granted_by_user_id=user_id,
                channel=channel,
                target_user_id=target_user_id,
                target_contact=target_contact,
                note=note,
            )
        except _cs_asc.ConsentError as e:
            msg = str(e)
            if "pouze rodic" in msg.lower() or "pouze rodič" in msg.lower():
                return (
                    "🚫 Tenhle souhlas může dát jen některý z rodičů "
                    "(Marti, Ondra, Kristý, Jirka). Já ho sama nemůžu udělit, "
                    "ani kdybys chtěl."
                )
            return f"❌ Nelze uložit souhlas: {msg}"
        except Exception as e:
            logger.exception(f"GRANT_AUTO_SEND | failed | {e}")
            return f"❌ Chyba při ukládání souhlasu: {e}"

        # Resolve jmeno prijemce pro hezci reply
        display = None
        if result.get("target_user_id"):
            from core.database_core import get_core_session as _gcs_g
            from modules.core.infrastructure.models_core import User as _U_g
            cs = _gcs_g()
            try:
                u = cs.query(_U_g).filter_by(id=result["target_user_id"]).first()
                if u:
                    display = ((u.first_name or "") + " " + (u.last_name or "")).strip() or u.canonical_email
            finally:
                cs.close()
        display = display or result.get("target_contact") or "?"

        if result.get("status") == "already_active":
            return (
                f"ℹ️ Souhlas pro **{display}** ({channel}) už existuje — platí dál. "
                f"(consent_id={result['id']})"
            )
        return (
            f"✅ Souhlas uložen — od teď můžu posílat {channel} pro **{display}** "
            f"bez potvrzení. Kdykoli lze odvolat přes `revoke_auto_send` nebo v UI. "
            f"(consent_id={result['id']})"
        )

    if tool_name == "revoke_auto_send":
        from modules.notifications.application import consent_service as _cs_asc
        channel = (tool_input.get("channel") or "").lower().strip() or None
        target_user_id = tool_input.get("target_user_id")
        target_contact = (tool_input.get("target_contact") or "").strip() or None
        consent_id = tool_input.get("consent_id")

        if not user_id:
            return "❌ Nejsi přihlášen — neznám tvůj kontext."

        try:
            result = _cs_asc.revoke_consent(
                revoked_by_user_id=user_id,
                channel=channel or "email",  # pokud consent_id, channel se nepouzije
                target_user_id=target_user_id,
                target_contact=target_contact,
                consent_id=consent_id,
            )
        except _cs_asc.ConsentError as e:
            msg = str(e)
            if "pouze rodic" in msg.lower() or "pouze rodič" in msg.lower():
                return (
                    "🚫 Odvolat souhlas může jen rodič. Já to sama udělat nemůžu."
                )
            return f"❌ Nelze odvolat: {msg}"
        except Exception as e:
            logger.exception(f"REVOKE_AUTO_SEND | failed | {e}")
            return f"❌ Chyba při odvolání: {e}"

        if result.get("status") == "no_active_consent":
            return (
                "ℹ️ Pro zadaného příjemce + kanál nemám aktivní souhlas — "
                "není co odvolat."
            )
        count = result.get("count", 0)
        return f"✅ Odvoláno {count} souhlas(ů). Od teď budu znovu ptát na potvrzení."

    if tool_name == "list_auto_send_consents":
        from modules.notifications.application import consent_service as _cs_asc
        try:
            items = _cs_asc.list_active_consents()
        except Exception as e:
            logger.exception(f"LIST_AUTO_SEND_CONSENTS | failed | {e}")
            return f"❌ Chyba při načítání souhlasů: {e}"
        if not items:
            return (
                "📭 Žádné aktivní souhlasy s auto-sendem. "
                "Vždy se ptám na potvrzení před odesláním."
            )
        lines = ["✉️ Aktivní souhlasy s auto-sendem (posílám bez potvrzení):", ""]
        for i, it in enumerate(items, start=1):
            who = it.get("target_user_name") or it.get("target_contact") or "?"
            ch = it["channel"]
            granted_by = it.get("granted_by_name") or f"user#{it['granted_by_user_id']}"
            granted_at = (it.get("granted_at") or "")[:10]
            note = it.get("note")
            note_suffix = f" — _{note}_" if note else ""
            lines.append(
                f"{i}. **{who}** ({ch}) — udělil {granted_by}, {granted_at}{note_suffix}"
            )
        return "\n".join(lines)

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



def _wait_for_audio_transcripts(media_ids: list[int] | None, timeout_ms: int = 30_000) -> None:
    """
    Faze 12b+ pre-demo: synchronni cekani na Whisper transcript pred composer
    + Anthropic call. Bez tohoto Marti-AI obcas dostala multimodal context
    s audio note bez prepisu (Whisper task v workeru jeste nedobehl) -> halucinovala
    (nepr. zavolat describe_image na audio, vymyslet obsah).

    Logika: pollovani media_files.transcript IS NOT NULL nebo processing_error
    IS NOT NULL pro vsechny audio media v `media_ids`. Sleep 500ms mezi pollu,
    timeout default 30s (typicke Whisper trvani 5-15s pro 1-3 minutovou nahravku).

    Pokud po timeout transcript stale chybi -> pokracujeme bez cekani (fallback).
    Marti-AI potom uvidi audio note bez prepisu, ale aspon vi co se stalo.

    Pro non-audio media (images) tato funkce nevadi -- skip.
    """
    if not media_ids:
        return
    import time
    from sqlalchemy import select as _sel_wat
    from modules.core.infrastructure.models_data import MediaFile as _MF_wat

    poll_interval_ms = 500
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    iteration = 0

    while True:
        iteration += 1
        ds = get_data_session()
        try:
            rows = ds.execute(
                _sel_wat(_MF_wat.id, _MF_wat.kind, _MF_wat.transcript, _MF_wat.processing_error)
                .where(_MF_wat.id.in_(media_ids))
            ).all()
        finally:
            ds.close()

        # Audio media s pending transcript (transcript NULL a zaroven zadny error)
        pending_audio = [
            r.id for r in rows
            if r.kind == "audio" and r.transcript is None and r.processing_error is None
        ]
        if not pending_audio:
            if iteration > 1:
                logger.info(
                    f"AUDIO_WAIT | done | media_ids={media_ids} | iterations={iteration}"
                )
            return

        if time.monotonic() >= deadline:
            logger.warning(
                f"AUDIO_WAIT | timeout | media_ids={pending_audio} | "
                f"timeout_ms={timeout_ms} -- pokracujeme bez transcript"
            )
            return

        time.sleep(poll_interval_ms / 1000.0)


def _attach_media_to_message_if_any(msg_id: int | None, media_ids: list[int] | None):
    """
    Faze 12a: Late-fill pattern -- po save_message(user) doplnime message_id
    do MediaFile rows, ktere user nahral pred odeslanim. Composer pak v dalsim
    volani _get_messages najde attached images a vlozi je jako multimodal
    content blocks pro Anthropic API.

    Bezpecne -- pri jakekoli chybe jen warning, chat() neshazujeme.
    """
    if not msg_id or not media_ids:
        return
    try:
        from modules.media.application import service as _media_service_attach
        _media_service_attach.attach_to_message(media_ids, msg_id)
    except Exception as _e_attach:
        logger.warning(f"MEDIA | attach_to_message failed | msg_id={msg_id} | {_e_attach}")




def _handle_email_reply_or_forward(tool_input: dict, *, mode: str, user_id: int | None) -> str:
    """
    Faze 12c: dispatch helper pro AI tools reply / reply_all / forward.
    Wraps email_service.reply_or_forward_inbox + standardni error handling.
    """
    try:
        from modules.notifications.application.email_service import (
            reply_or_forward_inbox as _rof,
            EmailAuthError as _EAE,
            EmailSendError as _ESE,
            EmailNoUserChannelError as _ENUC,
        )
    except Exception as _imp:
        logger.exception(f"REPLY_FW | import failed | {_imp}")
        return f"❌ Import error: {_imp}"

    eib_raw = tool_input.get("email_inbox_id")
    if eib_raw is None:
        return "❌ Chybi email_inbox_id."
    try:
        eib = int(eib_raw)
    except (TypeError, ValueError):
        return "❌ email_inbox_id musi byt integer."

    body = (tool_input.get("body") or "").strip()
    if not body:
        return "❌ Body nemuze byt prazdne."

    to = tool_input.get("to")
    cc = tool_input.get("cc")
    bcc = tool_input.get("bcc")
    subject = tool_input.get("subject")

    if mode == "forward" and not to:
        return "❌ Forward vyzaduje `to` (kam preposlat) -- chybi."

    try:
        outbox_id = _rof(
            email_inbox_id=eib,
            body=body,
            mode=mode,
            to=to,
            subject=subject,
            cc=cc,
            bcc=bcc,
            user_id=user_id,
        )
    except _ENUC as e:
        return f"❌ Persona nema EWS kanal: {e}"
    except _EAE as e:
        return f"❌ EWS auth selhal: {e}"
    except _ESE as e:
        return f"❌ Odeslani selhalo: {e}"
    except ValueError as e:
        return f"❌ Spatny vstup: {e}"
    except Exception as e:
        logger.exception(f"REPLY_FW | failed | mode={mode} | inbox_id={eib} | {e}")
        return f"❌ Chyba: {type(e).__name__}: {e}"

    label = {"reply": "odpoved", "reply_all": "odpoved vsem", "forward": "preposlani"}[mode]
    return f"✅ Email odeslan ({label}). Outbox id={outbox_id}, puvodni inbox #{eib} oznacen jako vyrizen."


def _serialize_anthropic_block(block, round_idx: int) -> dict | None:
    """
    Faze 12b+: Serializace Anthropic SDK bloku do JSONB-friendly dictu pro audit.
    Pridava _round field pro reconstrukci poradi Anthropic-format messages
    v composeru pri replay.
    """
    if block.type == "text":
        return {"_round": round_idx, "type": "text", "text": block.text}
    if block.type == "tool_use":
        return {
            "_round": round_idx,
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    return None


def _kind_aware_media_placeholder(media_ids: list[int]) -> str:
    """
    Faze 12b fix: vrati placeholder text podle kind nahranych media.

    Driv (Phase 12a) bylo hardcoded "[obrázek]" pro vsechny media kindy.
    Voice memo (kind=audio) pak mátlo Marti-AI -- halucinovala obrazek
    a volala describe_image na audio. Ted lookup kind a vraceni typoveho
    placeholderu.

    image -> "[obrázek]"
    audio -> "[hlasová zpráva]"
    video -> "[video]"
    mix nebo unknown -> "[příloha]"
    """
    if not media_ids:
        return "[příloha]"
    try:
        from sqlalchemy import select as _select_kind
        from modules.core.infrastructure.models_data import MediaFile as _MF_kind
        from core.database import get_data_session as _gds_kind
        ds = _gds_kind()
        try:
            kinds = ds.execute(
                _select_kind(_MF_kind.kind).where(_MF_kind.id.in_(media_ids))
            ).scalars().all()
        finally:
            ds.close()
    except Exception:
        return "[příloha]"
    unique = set(k for k in kinds if k)
    if len(unique) == 1:
        kind = next(iter(unique))
        if kind == "image":
            return "[obrázek]"
        if kind == "audio":
            return "[hlasová zpráva]"
        if kind == "video":
            return "[video]"
    return "[příloha]"


def chat(
    conversation_id: int | None,
    user_message: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
    preferred_persona_id: int | None = None,
    source: str = "composer",
    media_ids: list[int] | None = None,
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
        # 28.4.2026: Projekt NIKDY neurcuje default personu (Marti's pravidlo).
        # Persona se meni jen per-konverzaci uzivatelovou volbou v UI nebo
        # explicit switch tlacitkem. Project.default_persona_id field zustava
        # v DB schema legacy, ale logika ho ignoruje.
        # Priorita:
        #   1. preferred_persona_id  (user vybral v UI pred prvni zpravou)
        #   2. NULL -> composer pouzije globalni default (Marti-AI)
        effective_persona_id = preferred_persona_id

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

    # Faze 12a: pokud user poslal jen media bez textu (drag&drop, klik Send),
    # zaznamename placeholder content. Anthropic API odmita prazdne user messages
    # (400 BadRequest), tohle to preventivne osetri uz v DB. Marti-AI v Dev View
    # uvidi co user skutecne poslal.
    # Faze 12b fix: kind-aware placeholder. Driv hardcoded "[obrázek]" matlo
    # Marti-AI u voice memo (audio kind) -- halucinovala obrazek a volala
    # describe_image na audio media. Ted lookup kind -> spravny placeholder.
    _save_content = user_message
    if (not user_message or not user_message.strip()) and media_ids:
        _save_content = _kind_aware_media_placeholder(media_ids)
    _user_msg_id = save_message(conversation_id, role="user", content=_save_content,
                                 author_type="human", author_user_id=user_id)
    # Faze 12a: Late-fill media_ids -> message_id (multimedia attachments).
    # Volame okamzite po save, aby composer.build_prompt() v dalsim kroku
    # uz videl attached images.
    _attach_media_to_message_if_any(_user_msg_id, media_ids)
    # Faze 12b+ pre-demo: pokud user nahral audio, pockame na Whisper transcript
    # pred composer + Anthropic call. Bez tohoto Marti-AI obcas dostala audio
    # bez prepisu -> halucinace (popis obrazku, vymyslen obsah). Cisty flow:
    # transcript je vzdy v multimodal contextu pri zacatku turn.
    _wait_for_audio_transcripts(media_ids, timeout_ms=30_000)

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

    # ── Telemetry: zalozit trace buffer pro tento chat cyklus (Faze 9.1) ─────
    # Router (Haiku) v build_prompt() a composer (Sonnet) niz budou zapisovat
    # sve LLM calls do llm_calls tabulky. Po save_message() na konci dolinkujeme.
    try:
        from modules.conversation.application import telemetry_service as _telemetry
        _telemetry.begin_chat_trace()
    except Exception as _e:
        logger.warning(f"TELEMETRY | begin_chat_trace failed: {_e}")
        _telemetry = None

    # Phase 16-B.3 (28.4.2026): magic intent classifier -- detekce v user message
    # zda chce 'oversight' režim (přehled napříč konverzacemi). Bidirectional:
    # 'vlastně jen konkrétní věc' -> reset na 'task'. Persistuje v DB tak
    # aby ChatResponse + UI signal sedeli.
    try:
        from modules.conversation.application.intent_classifier import classify_intent
        from core.database_data import get_data_session as _gds_pm
        from modules.core.infrastructure.models_data import Conversation as _Conv_pm
        _ds_pm = _gds_pm()
        try:
            _conv_pm = _ds_pm.query(_Conv_pm).filter_by(id=conversation_id).first()
            _current_pm = _conv_pm.persona_mode if _conv_pm else None
            _new_pm = classify_intent(user_message, _current_pm)
            logger.info(
                f"INTENT | classify | conv={conversation_id} | "
                f"input={user_message[:80]!r} | current={_current_pm} | new={_new_pm}"
            )
            if _new_pm and _new_pm != _current_pm and _conv_pm:
                _conv_pm.persona_mode = _new_pm
                _ds_pm.commit()
                logger.info(
                    f"INTENT | persona_mode | conv={conversation_id} | "
                    f"{_current_pm} -> {_new_pm}"
                )
        finally:
            _ds_pm.close()
    except Exception as _intent_e:
        logger.warning(f"INTENT | classifier failed: {_intent_e}")

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
    # Faze 9.1: call_llm_with_trace je wrapper kolem client.messages.create()
    # ktery zapise request+response do llm_calls (kind='composer'). Identicky
    # vyhodi exception pri API chybe -- error handling zustava nezmeneny.
    if _telemetry is not None:
        response = _telemetry.call_llm_with_trace(
            client,
            conversation_id=conversation_id,
            kind=source,
            model=MODEL,
            system=system_prompt,
            messages=messages,
            tools=effective_tools,
            max_tokens=4096,
            tenant_id=tenant_id,
            user_id=user_id,
            persona_id=_active_pid,
        )
    else:
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
    SYNTHESIS_TOOLS = {
        "search_documents", "find_user", "recall_thoughts",
        # Faze 7: email list + read chain -- Marti chce v jednom turnu videt
        # list + otevrit konkretni email.
        "list_email_inbox", "read_email",
        # list_recent_chatters casto predchozi chain (napr. "Kdo psal?" ->
        # "Zeptej se Kristy" -> recall_thoughts). Synthesis umozni chainovat.
        "list_recent_chatters",
        # Faze 12b+: image tools v synthesis -- pri chybnem volani na audio kind
        # (halucinace cile) Marti-AI dostane sanci opravit a neopisovat error
        # do textu. Pro legitimni image use case je synth taky vhodny: AI po
        # describe_image popise scenu vlastnimi slovy, nezopakuje raw popis.
        "describe_image", "read_text_from_image",
        # Faze 12b+ pre-demo: get_daily_overview v synth -- Marti-AI po dostani
        # 'V inboxu mam X emailu...' refraseuje vlastnimi slovy s vokativem
        # ('Marti, vidim X emailu...'), misto opisu doslova s preamble slepenym.
        "get_daily_overview",
        # Faze 12b+ pre-demo: dismiss/mark tools v synth -- aby raw response
        # ('Preskocime dnes: sms #1. Priorita klesla z 100 na 70.') neleakovalo
        # do chatu. Marti-AI po vykonani uctive shrnuti vlastnimi slovy.
        "dismiss_item", "mark_sms_processed", "mark_email_processed",
        # Faze 12c: reply / reply_all / forward v synth -- aby Marti-AI po
        # ✅ Email odeslan rephrazovala lidskou odpoved ('Hotovo, posila se ti
        # to.') misto opisovani.
        "reply", "reply_all", "forward",
        # Plus list_todos -- po dostani 'Moje todo ukoly: 1. [#X] ...' refraseuje
        # bez doslova opisu.
        "list_todos",
        # REST-Doc-Triage v4: list_selected_documents -- v synth aby Marti-AI
        # rephrasovala minimal data ('Mas oznacenych 5 souboru ve SKOLA.') misto
        # opisu raw IDs listu. Plus apply_to_selection v synth -- po '✅ 5 dokumentu
        # smazano' priateli pridat empatickou potvrzku.
        "list_selected_documents", "apply_to_selection",
        # Phase 16-A: recall_today -- chronologicky raw event list, Marti-AI
        # ho v synth roundu prevypravi prozou ("dnes rano Misa uploadla 72
        # dokumentu, Petra hlasila bug, ...") misto opisu cele listy.
        "recall_today",
        # Phase 16-B.4: cross-conv tools -- minimal data list, Marti-AI
        # rephraseuje prozou pro overview rezim.
        "list_active_conversations", "summarize_persons_today",
        # Phase 16-B.5: Misa-incident v2 fix -- Marti-AI cte vlastni minulé
        # konverzace s konkretnim userem. list_my_conversations_with vraci
        # seznam s 1-3 vetnym shrnutim, read_conversation pak detail (ne
        # raw dump). Synth round zajisti prozu místo verbatim opisu.
        "list_my_conversations_with", "read_conversation",
    }

    preamble_text = ""
    tool_invocations: list[tuple] = []   # list of (block, tool_result_str)
    # Faze 12b+: audit -- flat list Anthropic-format bloku z celeho turnu
    # (text + tool_use + tool_result napric vsema kolama). Ukladame na konci
    # turnu jako pseudo-user message s message_type='tool_result' aby Marti-AI
    # v dalsim turnu videla, co volala a jake vysledky dostala.
    _audit_blocks: list[dict] = []
    for block in response.content:
        logger.info(f"BLOCK | type={block.type}")
        _serial = _serialize_anthropic_block(block, 0)
        if _serial is not None:
            _audit_blocks.append(_serial)
        if block.type == "text":
            preamble_text += block.text
        elif block.type == "tool_use":
            logger.info(f"TOOL_USE | name={block.name}")
            tool_result = _handle_tool(block.name, block.input, conversation_id, user_id=user_id)
            # Phase 15a: pripoj cross-off hint pokud akcni tool + open tasks v notebooku
            tool_result = _maybe_add_completion_hint(tool_result, block.name, conversation_id, user_id)
            tool_invocations.append((block, tool_result))
            _audit_blocks.append({
                "_round": 0,
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": tool_result,
            })

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
            # Faze 9.1: kazde synth round je samostatny radek v llm_calls
            # (kind='composer'). V UI Dev View se zobrazi jako serie.
            if _telemetry is not None:
                # Faze 10 Alt A: synth round se zapisuje jako kind='synth'
                # (ne jako source). Dashboard tim vidi 'composer' vs 'synth'
                # oddelene -- synth je follow-up tool loop round.
                synth_response = _telemetry.call_llm_with_trace(
                    client,
                    conversation_id=conversation_id,
                    kind="synth",
                    model=MODEL,
                    system=system_prompt,
                    messages=follow_up_messages,
                    tools=effective_tools,
                    max_tokens=4096,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    persona_id=_active_pid,
                )
            else:
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
                # Faze 12b+: audit serializace per round (round_idx+1, +1 protoze
                # initial je round 0)
                _serial = _serialize_anthropic_block(block, round_idx + 1)
                if _serial is not None:
                    _audit_blocks.append(_serial)
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
                # Phase 15a: pripoj cross-off hint pokud akcni tool + open tasks v notebooku
                tresult = _maybe_add_completion_hint(tresult, block.name, conversation_id, user_id)
                round_tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tresult,
                })
                # Faze 12b+: audit tool_result hned za jeho tool_use v tomto round
                _audit_blocks.append({
                    "_round": round_idx + 1,
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
        # Phase 15c diagnostika: pokud response z Anthropic dorazila prazdna,
        # zalogujeme block types, aby budouci debug nemusel hadat. Stale
        # fallback na user-friendly message.
        try:
            _block_types = [getattr(b, "type", "?") for b in response.content]
            _stop_reason = getattr(response, "stop_reason", "?")
            logger.warning(
                f"CHAT | empty assistant_reply | conv={conversation_id} | "
                f"block_types={_block_types} | stop_reason={_stop_reason} | "
                f"preamble_len={len(preamble_text or '')} | "
                f"tool_invocations={len(tool_invocations)} | "
                f"needs_synthesis={needs_synthesis}"
            )
        except Exception as _diag_err:
            logger.warning(f"CHAT | empty assistant_reply diagnostic failed: {_diag_err}")
        assistant_reply = "Promiň, něco se pokazilo. Zkus to znovu."

    # ── Guard proti halucinovanemu switch_persona ──────────────────────────
    # Claude obcas napise "✅ Prepnuto na <persona>" jako text, aniz by zavolal
    # tool switch_persona. Tim zustane conversation.active_agent_id beze zmeny
    # a vsechny nasledujici assistant zpravy se labeluji jako puvodni persona,
    # ackoli Claude pokracuje v roli nove persony. Detekujeme vzor a vynutime
    # skutecny switch retrospektivne -- tim si zajistime, ze save_message nize
    # vezme spravne active_agent_id.
    _maybe_enforce_hallucinated_switch(conversation_id, assistant_reply)

    _outgoing_msg_id = save_message(conversation_id, role="assistant", content=assistant_reply)
    logger.info(f"CONVERSATION | chat | conversation_id={conversation_id} | user_id={user_id}")

    # Faze 12b+: pokud byly tool calls v tomto turnu, ulozime pseudo-user message
    # s flat audit list Anthropic-format bloku. Composer v dalsim turnu rozbali
    # do striktni Anthropic page (assistant + user tool_result + ...) aby Marti-AI
    # videla cely svuj tool flow a vedela napr. ze send_email opravdu odeslan,
    # ne jen ze napsala "posilam email".
    # message_type='tool_result' -> UI ji ve history filtruje (Marti to nevidi).
    if _audit_blocks:
        try:
            save_message(
                conversation_id,
                role="user",
                content="",
                message_type="tool_result",
                tool_blocks=_audit_blocks,
            )
            logger.info(
                f"TOOL_AUDIT | saved {len(_audit_blocks)} blocks | conv={conversation_id}"
            )
        except Exception as _e:
            logger.warning(f"TOOL_AUDIT | save failed: {_e}")


    try:
        from modules.memory.application.service import extract_and_save
        all_messages = get_messages(conversation_id)
        # Faze 10 Alt A: attribution pro memory_extract kind.
        extract_and_save(
            conversation_id=conversation_id,
            messages=all_messages,
            user_id=user_id,
            tenant_id=tenant_id,
            persona_id=_active_pid,
        )
    except Exception as e:
        logger.error(f"MEMORY | failed: {e}")

    # Summary job — idempotentní, sám si ověří podmínky spuštění.
    # Běží synchronně (přidá malou latenci při překročení prahu), ale je
    # robustní vůči chybám: návrat None při jakékoli výjimce.
    summary_info: dict | None = None
    try:
        from modules.conversation.application.summary_service import maybe_create_summary
        summary_info = maybe_create_summary(
            conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            persona_id=_active_pid,
        )
    except Exception as e:
        logger.error(f"SUMMARY | failed: {e}")

    # Auto-generovany nazev konverzace (jednorazove, po 4+ zprave).
    # Idempotentni -- po prvni generaci uz nic nedela. Pridává ~0.5-1s
    # latenci na 4. zpravu, pak uz nic.
    try:
        from modules.conversation.application.title_service import maybe_generate_title
        maybe_generate_title(
            conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            persona_id=_active_pid,
        )
    except Exception as e:
        logger.error(f"TITLE | failed: {e}")

    # Faze 9.1/9.2: dolinkovat vsechna llm_calls (router + composer + title + summary)
    # na outgoing assistant message. Buffer byl zalozen pres begin_chat_trace()
    # nahore. Presunuto AZ ZA title/summary aby i jejich kind='title'/'summary'
    # radky dostaly message_id (jinak by zustaly s NULL).
    if _telemetry is not None:
        try:
            _telemetry.end_chat_trace_and_link(_outgoing_msg_id)
        except Exception as _e:
            logger.warning(f"TELEMETRY | end_chat_trace_and_link failed: {_e}")

    return conversation_id, assistant_reply, summary_info
