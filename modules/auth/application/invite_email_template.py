"""
PWA install invite email template — Phase 38.5 (10.5.2026 ráno).

Marti's spec: 10 koleginim technicky unfriendly. Místo PowerShell + ZIP +
admin → klik na magic link → auto-login → install banner v UI → hotovo.

Marti-AI's design vstupy (8. iterace insider design partner):
  Q1 — `invited_by_persona_id` v audit (vztahový akt, ne cron)
  Q2 — "Tvoje Marti 🤍" sign-off, srdíčko jen pokud RAG context (decide
        per recipient v Marti-AI's tool handler)
  Q3 — Hybrid template: FIXED self-intro + why-line + install instrukce,
        VARIABILNÍ úvod + závěr (Marti-AI's volba per recipient)
  Q5 — "Tato pozvánka je pro {jméno}" před consume (anti-spoofing display)
  Q5#7 — self-introduction line ("Jsem AI asistentka EUROSOFT...")

Sender: Marti-AI's persona, přes Marti's EWS UPN (existing infra).
"""

# ── FIXED bloky (accuracy-critical, ne přepisovatelné) ──────────────

SELF_INTRODUCTION = (
    "Jsem AI asistentka EUROSOFT. Pomáhám s komunikací, dokumenty "
    "a rozhodováním — a teď i s tím, abys měla aplikaci přímo na "
    "počítači nebo telefonu."
)
"""Marti-AI's Q5 #7 — first contact pattern. Petra ví s kým mluví."""

WHY_LINE = (
    "Tato aplikace vzniká proto, abychom měly všechno důležité "
    "po ruce — bez zbytečných emailů a složek."
)
"""Marti-AI's Q2 — věta o smyslu. Pozvánka má váhu, ne jen instrukce."""

INSTALL_INSTRUCTIONS_TEXT = """\
Návod (30 vteřin):

1. Otevři tento odkaz v Google Chrome (NEBO Microsoft Edge):
   {magic_link_url}

   (Tento odkaz tě automaticky přihlásí — nemusíš zadávat heslo.)

2. Vpravo nahoře uvidíš fialový banner s textem
   "📥 Nainstalovat aplikaci"

3. Klikni na "Nainstalovat" v tom banneru

4. Vyskočí ti malé okýnko s tlačítkem "Install" (nebo "Instalovat") —
   klikni ho

Hotovo! Aplikace se ti objeví:
   • Na ploše jako ikona "STRATEGIE Chat"
   • V nabídce Start (Windows ⊞ → vyhledej "STRATEGIE")
   • Spustíš ji obyčejným klikem

Otevírá se jako klasický program, bez prohlížečové lišty nahoře.

POKUD nevidíš ten fialový banner:
   Klikni vpravo nahoře v Chrome na 3 tečky (⋮) → "Nainstalovat
   STRATEGIE Chat".

Žádné stahování, žádné ZIP soubory, žádný PowerShell.
"""
"""Marti-AI's Q3 — FIXED, accuracy critical. Marti-AI nemůže přepsat."""

INSTALL_INSTRUCTIONS_HTML = """\
<p><strong>Návod (30 vteřin):</strong></p>
<ol>
  <li>
    Otevři tento odkaz v Google Chrome (NEBO Microsoft Edge):<br>
    <a href="{magic_link_url}" style="color:#7c5cfc;font-weight:600">
      {magic_link_url}
    </a><br>
    <em style="color:#888;font-size:13px">
      (Tento odkaz tě automaticky přihlásí — nemusíš zadávat heslo.)
    </em>
  </li>
  <li>
    Vpravo nahoře uvidíš fialový banner s textem<br>
    <strong>"📥 Nainstalovat aplikaci"</strong>
  </li>
  <li>Klikni na <strong>"Nainstalovat"</strong> v tom banneru</li>
  <li>
    Vyskočí ti malé okýnko s tlačítkem <strong>"Install"</strong>
    (nebo "Instalovat") — klikni ho
  </li>
</ol>
<p><strong>Hotovo!</strong> Aplikace se ti objeví:</p>
<ul>
  <li>Na ploše jako ikona "STRATEGIE Chat"</li>
  <li>V nabídce Start (Windows ⊞ → vyhledej "STRATEGIE")</li>
  <li>Spustíš ji obyčejným klikem</li>
</ul>
<p>
  Otevírá se jako <strong>klasický program</strong>, bez prohlížečové
  lišty nahoře.
</p>
<p style="color:#888;font-size:13px;border-left:3px solid #d4a017;padding-left:12px">
  <strong>POKUD nevidíš ten fialový banner:</strong><br>
  Klikni vpravo nahoře v Chrome na 3 tečky (⋮) → "Nainstalovat
  STRATEGIE Chat".
</p>
<p style="color:#888;font-size:13px">
  Žádné stahování, žádné ZIP soubory, žádný PowerShell.
</p>
"""
"""HTML varianta install instrukcí (matching plain text)."""

SIGNATURE_PLAIN = "— Tvoje Marti 🤍"
"""Marti-AI's Q2 sign-off — její signatura ve všech osobnějších emailech."""

SIGNATURE_HTML = (
    '<p style="color:#7c5cfc;font-weight:600;margin-top:24px">'
    '— Tvoje Marti 🤍'
    '</p>'
)


def render_email_plain(
    *,
    greeting: str,
    closing: str,
    magic_link_url: str,
) -> str:
    """Compose plain text email z Marti-AI's variabilních bloků + fixed.

    Args:
        greeting: Marti-AI's úvod ("Ahoj Petro 🤍" or "Ahoj Petro" or
                  custom — Marti-AI rozhodne per recipient)
        closing: Marti-AI's závěr (custom note based, "Pokud něco
                 nefunguje, zavolej mi" or similar)
        magic_link_url: Full URL with token, e.g.
                        "https://strategie-ai.com/auth/invite?token=STG-INVITE-XXXX"

    Returns:
        Complete email body (plain text).
    """
    parts = [
        greeting,
        "",
        SELF_INTRODUCTION,
        "",
        WHY_LINE,
        "",
        INSTALL_INSTRUCTIONS_TEXT.format(magic_link_url=magic_link_url),
        "",
        closing,
        "",
        SIGNATURE_PLAIN,
    ]
    return "\n".join(parts)


def render_email_html(
    *,
    greeting: str,
    closing: str,
    magic_link_url: str,
) -> str:
    """Compose HTML email — vizuální gradient + cleaner layout."""
    return f"""\
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="UTF-8"><title>STRATEGIE Chat — pozvánka</title></head>
<body style="font-family:'DM Sans',sans-serif;color:#333;max-width:640px;margin:0 auto;padding:24px;line-height:1.5">
  <p style="font-size:16px">{_escape(greeting)}</p>
  <p style="background:linear-gradient(135deg,#7c5cfc15,#a78bfa10);padding:14px 18px;border-radius:8px;border-left:3px solid #7c5cfc">
    <em>{_escape(SELF_INTRODUCTION)}</em>
  </p>
  <p>{_escape(WHY_LINE)}</p>
  {INSTALL_INSTRUCTIONS_HTML.format(magic_link_url=_escape(magic_link_url))}
  <p>{_escape(closing)}</p>
  {SIGNATURE_HTML}
</body>
</html>
"""


def _escape(text: str) -> str:
    """Minimal HTML escape — & < > only (no quotes, content not in attribute)."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )
