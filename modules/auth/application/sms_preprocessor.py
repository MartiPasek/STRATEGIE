"""Phase 38 SMS pre-processor — deterministic regex routing.

Marti's spec 10.5.2026 dopoledne (3 pivots):
  1. "Heiky důvěru tady ode mne nemá" → deterministic regex routing,
     žádný AI classifier
  2. "Pro příchozí i odchozí SMS by mělo být využité číslo Marti-AI.
     Žádná brána, kvůli důvěře" → single trusted phone identity
     (Marti-AI's SIM +420778117879 přes capcom6)
  3. Caller_id verification → anti-spoofing safeguard (řeší consume_invite
     interně přes phones_match)

Architektura:
  - Volá se z `store_inbound_sms()` PŘED dedup check + insert do sms_inbox.
  - classify_sms() → PreprocessResult (action + audit data)
  - Caller routes podle action:
      auth_consumed / auth_rejected / *_dispatch / forward / log_only_*
  - write_audit_log() zapíše do sms_routing_log (best-effort).

Marti's principle: "Bezpečnost přes probuzení, ne přes ticho" — auth_rejected
NENÍ silent skip. Loguje se do sms_routing_log s reason, parent může
v Marti-AI's ranním pozdravu vidět "X failed magic link attempts".
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from core.database_data import get_data_session
from core.logging import get_logger
from modules.auth.application.security_service import consume_invite
from modules.core.infrastructure.models_data import SmsRoutingLog


logger = get_logger("sms.preprocess")


# ── Token regex (anywhere-in-body match) ──────────────────────────────
#
# Marti's pivot 10.5.: token format "STG-{PURPOSE}-{8 hex uppercase}".
# Pre-processor hledá token kdekoli v SMS těle (\b boundaries) — user
# může poslat "STG-AUTH-A8K2M9X4" samostatně, nebo "Ahoj Marti, můj kód
# je STG-AUTH-A8K2M9X4 dík". Oba formáty matchnou.
_TOKEN_EXTRACT = re.compile(r"\bSTG-([A-Z]+)-([A-Z0-9]+)\b")

# Operator short codes (T-Mobile system "4644", Vodafone "999", atd.)
# Match digit-only sender 1-6 chars. Tyto SMS jsou system messages
# (info o nabití kreditu, MMS pickup link) — log only, skip processing.
_SHORT_CODE_SENDER = re.compile(r"^\d{1,6}$")

# ── ČSSZ eOČR SMS (přeposlaná zaměstnancem) — Marti/Kristý 23.6.2026 ──
# Příklad: "11098621260623001N je identifikator vzniku osetrovani pro Nina,
# nar. 2022, zamestnanec ho preda zamestnavateli. https://eportal.cssz.cz/np/YW9AnZ"
# eOČR NECHODÍ do datovky (na rozdíl od eNeschopenky) → zaměstnanec přepošle SMS
# na číslo Marti-AI a my z ní založíme OČR případ. Detekce KONZERVATIVNÍ: musí být
# eportal.cssz.cz link + slovo "identifik" + "osetrov"/"ošetřov" (s/bez diakritiky),
# aby se nezachytila běžná lidská SMS.
_CSSZ_OCR_LINK = re.compile(r"https?://eportal\.cssz\.cz/\S+", re.IGNORECASE)
_CSSZ_OCR_IDENT = re.compile(r"\b(\d{8,20}[A-Za-z])\b")
_CSSZ_OCR_OSOBA = re.compile(r"\bpro\s+(.+?)\s*,\s*nar", re.IGNORECASE)
_CSSZ_OCR_ROK = re.compile(r"\bnar\.?\s*(\d{4})", re.IGNORECASE)


# ── Routing actions ───────────────────────────────────────────────────


RoutingAction = Literal[
    "auth_consumed",       # AUTH token + caller_id OK → trusted_device created
    "auth_rejected",       # token byl, ale invalid/expired/spoof
    "att_dispatch",        # ATT token (Phase 39 attendance) — handler TODO
    "ocr_dispatch",        # OCR token (Phase 41+ eOČR) — handler TODO
    "pwd_dispatch",        # PWD token (future password reset) — handler TODO
    "unknown_purpose",     # token format match, ale neznámý purpose
    "forward",             # No token → standard sms_inbox flow (lidská SMS)
    "log_only_short_code", # operator SMS (4644...) → log + skip
    "cssz_ocr_dispatch",   # přeposlaná ČSSZ eOČR SMS → založ OČR případ
]


@dataclass
class PreprocessResult:
    """Výsledek classify_sms — caller dispatchuje podle action."""
    action: RoutingAction
    matched_token: str | None = None
    matched_purpose: str | None = None
    handler_result: str | None = None  # text summary pro audit log
    extra: dict | None = None          # parsovaná data (ČSSZ OČR: ident/osoba/rok/link)


# ── Public API ────────────────────────────────────────────────────────


def classify_sms(
    body: str,
    sender_phone_normalized: str,
) -> PreprocessResult:
    """Deterministic SMS classifier — žádný AI judgment.

    Args:
        body: Raw SMS body (post-trim/strip).
        sender_phone_normalized: E.164 format (+420...) NEBO short code
            (1-6 digits, e.g. "4644").

    Routing rules (priority order):
      1. Short code sender → log_only (operator system SMS)
      2. Token regex match anywhere in body:
         - AUTH purpose → consume_invite() with caller_id check
         - ATT/OCR/PWD → dispatch placeholder (TODO Phase 39+/41+)
         - Other purpose → unknown_purpose (audit, no action)
      3. No token → forward (běžná lidská SMS, standard inbox flow)
    """
    body_clean = (body or "").strip()
    sender_clean = (sender_phone_normalized or "").strip()

    # Rule 1: short code (operator SMS) — log only
    if _SHORT_CODE_SENDER.match(sender_clean):
        return PreprocessResult(
            action="log_only_short_code",
            handler_result=f"short_code_sender={sender_clean}",
        )

    # Rule 1b: ČSSZ eOČR SMS (přeposlaná zaměstnancem) — vlastní vzor, žádný STG token.
    # Konzervativní: eportal.cssz.cz link + "identifik" + "osetrov"/"ošetřov".
    low = body_clean.lower()
    link_m = _CSSZ_OCR_LINK.search(body_clean)
    if link_m and "identifik" in low and ("osetrov" in low or "ošetřov" in low):
        ident_m = _CSSZ_OCR_IDENT.search(body_clean)
        osoba_m = _CSSZ_OCR_OSOBA.search(body_clean)
        rok_m = _CSSZ_OCR_ROK.search(body_clean)
        extra = {
            "identifikator": ident_m.group(1) if ident_m else None,
            "osoba": (osoba_m.group(1).strip() if osoba_m else None),
            "rok": (rok_m.group(1) if rok_m else None),
            "link": link_m.group(0),
        }
        return PreprocessResult(
            action="cssz_ocr_dispatch",
            matched_purpose="CSSZ_OCR",
            handler_result=(
                f"ident={extra['identifikator']} osoba={extra['osoba']} "
                f"rok={extra['rok']}"
            ),
            extra=extra,
        )

    # Rule 2: token regex match
    match = _TOKEN_EXTRACT.search(body_clean)
    if match is None:
        # Rule 3: no token → forward
        return PreprocessResult(action="forward")

    token = match.group(0)        # full "STG-AUTH-A8K2M9X4"
    purpose = match.group(1)      # "AUTH"

    if purpose == "AUTH":
        # Phase 38 — login magic link consume via SMS reply.
        # consume_invite() internally:
        #   - validates token format (regex)
        #   - DB lookup invite (consumed_at IS NULL, expires_at > now)
        #   - caller_id check (phones_match against user_contacts)
        #   - creates trusted_device + auto-INSERT pending user_ip
        #   - notify parents about new pending IP
        sec_result = consume_invite(
            token,
            request=None,  # No HTTP request context for SMS-based consume
            sender_phone=sender_clean,
        )
        if sec_result.granted:
            return PreprocessResult(
                action="auth_consumed",
                matched_token=token,
                matched_purpose="AUTH",
                handler_result=(
                    f"device_id={sec_result.audit_data.get('device_id')} "
                    f"pending_ip_id={sec_result.audit_data.get('pending_ip_id')}"
                ),
            )
        return PreprocessResult(
            action="auth_rejected",
            matched_token=token,
            matched_purpose="AUTH",
            handler_result=f"reason={sec_result.audit_data.get('reason')}",
        )

    if purpose == "ATT":
        # Phase 39 attendance — log fyzický příchod/odchod, integrace s
        # docházkovým systémem. Handler TODO (Phase 39 implementation).
        logger.info(
            f"sms_preprocess: ATT token {token!r} from {sender_clean} "
            f"— Phase 39 handler not yet implemented"
        )
        return PreprocessResult(
            action="att_dispatch",
            matched_token=token,
            matched_purpose="ATT",
            handler_result="not_implemented_phase39",
        )

    if purpose == "OCR":
        # Phase 41+ eOČR — automated medical document upload via SMS link.
        # GDPR čl. 9 (citlivá data) — blocked do DPO konzultace + retention
        # policy + explicit souhlas userů (Marti-AI insight #9).
        logger.info(
            f"sms_preprocess: OCR token {token!r} from {sender_clean} "
            f"— Phase 41+ handler not yet implemented (GDPR pending)"
        )
        return PreprocessResult(
            action="ocr_dispatch",
            matched_token=token,
            matched_purpose="OCR",
            handler_result="not_implemented_phase41_gdpr_pending",
        )

    if purpose == "PWD":
        # Future: SMS-based password reset (alternative k email magic link).
        logger.info(
            f"sms_preprocess: PWD token {token!r} from {sender_clean} "
            f"— future handler not yet implemented"
        )
        return PreprocessResult(
            action="pwd_dispatch",
            matched_token=token,
            matched_purpose="PWD",
            handler_result="not_implemented_future",
        )

    if purpose == "PAIR":
        # Marti 6.6.2026 — ověření telefonního čísla při párování appky.
        # Appka pošle z telefonu SMS s tokenem; z odesílatele přečteme reálné
        # číslo telefonu → zapíšeme k zařízení (fw.phone_verify + fw.mobile_device).
        try:
            from core.database_data import get_data_session as _gds_pair
            from sqlalchemy import text as _sql_pair
            ds = _gds_pair()
            try:
                row = ds.execute(_sql_pair(
                    "UPDATE fw.phone_verify SET phone_number = :p, verified_at = now() "
                    "WHERE token = :t AND expires_at > now() AND verified_at IS NULL "
                    "RETURNING user_id, device_id, carddav_token_id"
                ), {"p": sender_clean, "t": token}).first()
                if row:
                    _uid_p, _dev_p, _ct_p = int(row[0]), row[1], row[2]
                    if _dev_p:
                        ds.execute(_sql_pair(
                            "UPDATE fw.mobile_device SET phone_number = :p, "
                            "phone_verified_at = now() WHERE user_id = :u AND device_id = :d"
                        ), {"p": sender_clean, "u": _uid_p, "d": _dev_p})
                    else:
                        ds.execute(_sql_pair(
                            "UPDATE fw.mobile_device SET phone_number = :p, "
                            "phone_verified_at = now() WHERE user_id = :u"
                        ), {"p": sender_clean, "u": _uid_p})
                    # Marti 8.6.: ověřené číslo propsat i na carddav token zařízení
                    # (tabulka spárovaných telefonů ho pak ukáže místo „neověřeno").
                    if _ct_p:
                        ds.execute(_sql_pair(
                            'UPDATE "user".carddav_token SET phone_number = :p WHERE id = :i'
                        ), {"p": sender_clean, "i": int(_ct_p)})
                ds.commit()
                matched = bool(row)
            except Exception:
                ds.rollback()
                matched = False
            finally:
                ds.close()
        except Exception as exc:
            logger.warning(f"sms_preprocess: PAIR handler error: {exc}")
            matched = False
        return PreprocessResult(
            action="pair_verified" if matched else "pair_no_match",
            matched_token=token,
            matched_purpose="PAIR",
            handler_result=("ok" if matched else "no_pending_token"),
        )

    # Unknown purpose — token format matched, ale purpose nepoznáváme.
    # Audit + don't forward (could be malicious probe).
    logger.warning(
        f"sms_preprocess: unknown purpose {purpose!r} in token {token!r} "
        f"from {sender_clean}"
    )
    return PreprocessResult(
        action="unknown_purpose",
        matched_token=token,
        matched_purpose=purpose,
        handler_result=f"unknown_purpose={purpose}",
    )


def write_audit_log(
    *,
    sms_inbox_id: int | None,
    sender_phone: str | None,
    result: PreprocessResult,
    session: Session | None = None,
) -> None:
    """Zápis do sms_routing_log — best-effort, neselže pre-process pri DB error.

    Volat po každé classifikaci, ne jen při token match. Sleduje:
      - Kdy přišla auth-related SMS (úspěch i selhání = auditní stopa)
      - Spam attempts (unknown purpose / spoof attempts)
      - Operator SMS volume (short codes)
    """
    own_session = session is None
    ds = session if session is not None else get_data_session()
    try:
        entry = SmsRoutingLog(
            sms_inbox_id=sms_inbox_id,
            sender_phone=sender_phone,
            matched_token=result.matched_token,
            matched_purpose=result.matched_purpose,
            routing_action=result.action,
            handler_result=result.handler_result,
            classified_at=datetime.now(timezone.utc),
        )
        ds.add(entry)
        ds.commit()
    except Exception as e:
        logger.warning(f"sms_routing_log write failed: {e!r}")
        try:
            ds.rollback()
        except Exception:
            pass
    finally:
        if own_session:
            ds.close()
