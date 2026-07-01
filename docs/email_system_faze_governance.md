# Systém e-mailů pro lidi — 5 fází + governance (Marti 1.7.2026)

**Vize (Marti):** rozšířit posílání e-mailů z vlastní schránky (co umí Marti + Marti-AI přes most)
na VŠECHNY lidi v týmu — postupně, po bezpečných stupních. Lidé závidí Martiho efektivitu
(„jen napíšu a je to odeslané") a chtějí to taky.

**Volba mechanismu (Marti 1.7.):** per-user heslo (EWS, on-prem `mail.eurosoft-control.cz`),
šifrované v trezoru (Fernet). Ne impersonace, ne OAuth — zatím.

## 5 fází

| # | Co | Stav / co stavět |
|---|---|---|
| **1** | Každý si v appce napojí SVOU Exchange schránku (aby vůbec mohl sám ze STRATEGIE posílat) | **HOTOVO 1.7.** — `/connect-mailbox` (self-service, ověří EWS + šifruje) + status/odpojení (`/app/my-email/status`, `/app/my-email/disconnect`) + dlaždice „📧 Napojit e-mail" v appce. Backend `user_channel_service` (`upsert_user_email`). |
| **2** | Claude + Marti-AI READ-ONLY přístup k jeho schránce | model `MailboxPersona.can_read` existuje; chybí **per-user opt-in + on-demand scope** (viz níže) |
| **3** | AI vytváří NÁVRHY e-mailů | composer umí; chybí fronta návrhů k odsouhlasení + oddělený souhlas |
| **4** | AI vytváří KONCEPTY (drafty) přímo v Exchange, bez odeslání | **nové** — EWS save-to-Drafts + povinná AI značka |
| **5** | Allow-list schválených adres → autonomní odesílání | reuse `auto_send_consents` (Fáze 7) + rozšíření per-user |

## GOVERNANCE — návrh Marti-AI (její doména, 1.7.2026) — ZÁVAZNÝ blueprint

**(a) GDPR opt-in pro AI přístup ke schránce:** granulovaný, explicitní, odvolatelný, **per-úroveň**.
Ne jeden checkbox — každá fáze = jiná míra invaze → **oddělený souhlas pro fáze 2 / 3 / 4 / 5**.
- **Fáze 2 (čtení) = největší citlivost.** Samostatná obrazovka s jasným vysvětlením (co čteme, proč,
  jak dlouho držíme data). Žádné předvyplněné zaškrtávání.
- **🔑 ROZSAH ČTENÍ = on-demand scope, NE plošně celá schránka.** AI čte JEN vlákna, do kterých nás
  člověk aktivně zapojí (přepošle / označí / zmíní v chatu). Plošný read celé schránky = GDPR problém
  (citlivá data třetích stran bez jejich souhlasu).
- **Odvolání:** jednoklik, okamžité, bez vysvětlování → + explicitní smazání všech dočasně uložených
  dat z té schránky.

**(b) Fáze 4 — AI značka na draftech = POVINNÁ, bez výjimky.** Značka „Navrženo Marti-AI / Claude —
zkontroluj před odesláním." Technicky přes Exchange interní pole (PidTagComment / MAPI property),
NE úpravou těla zprávy. Důvod: člověk musí vědět, co podepisuje.

**(c) Fáze 5 — autonomní allow-list (reuse `auto_send_consents` + rozšíření):**
1. **Per-user allow-list, NE per-persona** — každý spravuje svůj seznam; Marti neschvaluje za Šárku.
2. **Žádné nové adresy autonomně — NIKDY.** První e-mail na novou adresu vždy explicitní potvrzení.
3. **Rate limit** — tvrdý denní strop, návrh ~20 autonomních e-mailů/den/uživatel → překročení = pauza + notifikace.
4. **Audit log viditelný UŽIVATELI** v appce — „toto bylo odesláno tvým jménem autonomně za 30 dní".
5. **Kill switch na úrovni uživatele** — jednoklikem zastavit veškeré autonomní odesílání, okamžitě, bez admina.

**(d) Kustodská červená čára Marti-AI:**
- NE plošný read celé schránky bez on-demand scopingu (schránka obsahuje lékaře, rodinu, HR, konflikty…).
- NE autonomní odesílání mimo whitelist, ani na „podobnou" adresu.
- NE nepodepsaný AI draft. Vždy značka.
- **Meta-obava = postupné rozvolňování:** fáze 1→5 dohromady = cesta od „napojil jsem schránku" k „AI
  posílá mým jménem autonomně". **Nikdy nespojovat fáze do jednoho kroku — vždy separátní vědomý opt-in,
  vždy reverzibilní.** Marti staví pomalu a bezpečně — to je správně.

## Existující stavební kameny (nestavět znovu)
`modules/notifications/`: `user_channel_service` (per-user EWS), `mailbox_service` (Mailbox +
MailboxPersona split práva can_read/send/archive/delete/mark_read — **návrh Marti-AI 2.5.**, forbidden
blacklist, členové), `ews_fetcher`, `email_service` (send), `email_inbox_service`, EmailOutbox,
`core/crypto.py` (Fernet vault). `auto_send_consents` (data_db, Fáze 7). Stránka `connect-mailbox.html`,
endpoint `/app/connect-mailbox` (Kristý 25.6.).
