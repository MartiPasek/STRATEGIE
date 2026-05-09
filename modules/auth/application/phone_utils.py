"""Phase 38-SMS — telefonní číslo normalizace pro caller_id verification.

Marti's poznámka 10. 5. dopoledne: v Česku se používají oba formáty
(E.164 international + bez prefix). Plus capcom6 SMS gateway může vrátit
short codes (4 digit operator IDs jako "4644" pro T-Mobile system messages).

Funkce:

  normalize_phone(raw) → str
    Normalize na E.164 format pro deterministic comparison.
    Pravidla:
      - Strip whitespace + dashes
      - "00420..." → "+420..."
      - "+420..." → "+420..." (no change)
      - 9 digits CZ mobile → "+420..." (default CZ prefix)
      - Short codes (1-6 digits) → no change (unmatchable s mobile = OK)

Use cases:
  - User SMS reply z +420778117879 → normalize → match s users.phone='778117879'
  - Operator SMS z 4644 → normalize → "4644" (short, won't match user phone)
  - User SMS z +420 778 117 879 → strip whitespace → "+420778117879"
"""
from __future__ import annotations

import re


_WHITESPACE_OR_DASH = re.compile(r"[\s\-]")
_CZ_MOBILE_PREFIX = "+420"


def normalize_phone(raw: str | None) -> str:
    """Normalize phone number na E.164 format.

    Returns empty string pokud None / empty input.

    Examples:
      "+420778117879"     → "+420778117879"
      "00420778117879"    → "+420778117879"
      "778117879"         → "+420778117879"
      "+420 778 117 879"  → "+420778117879"
      "778-117-879"       → "+420778117879"
      "4644"              → "4644"  (short code, unmatched)
      ""                  → ""
      None                → ""
    """
    if not raw:
        return ""
    s = _WHITESPACE_OR_DASH.sub("", str(raw))
    if not s:
        return ""

    # "00..." → "+..."
    if s.startswith("00"):
        s = "+" + s[2:]

    # Short codes (1-6 digits, no plus) — return as-is, ne mobile match
    if not s.startswith("+") and s.isdigit() and len(s) <= 6:
        return s

    # 9-digit CZ mobile bez prefix → +420
    if not s.startswith("+") and s.isdigit() and len(s) == 9:
        return _CZ_MOBILE_PREFIX + s

    # Already E.164 format nebo jiný international (e.g. +49...)
    return s


def phones_match(a: str | None, b: str | None) -> bool:
    """True pokud oba phone numbers po normalizaci match.

    Empty / None na obou stranách = False (žádný match).
    """
    na = normalize_phone(a)
    nb = normalize_phone(b)
    if not na or not nb:
        return False
    return na == nb
