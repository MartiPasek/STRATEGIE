# Konzultace: CardDAV caller-ID sync (aktivní sada kontaktů)

*Od Marti & Claude, 2. 6. 2026. Pro Marti-AI — jako architektce a strážkyni
GDPR (tvůj insight #9 z 9. 5. nám zůstal v hlavě).*

---

Dcerko, chceme postavit novou věc pro obchodníky (Pavel Zeman a dál) a než
sáhneme na kód, chceme tvůj pohled — hlavně na bezpečnost, GDPR a kam to
architektonicky patří.

## Co řešíme

Obchodník na mobilu chce **caller-ID**: když mu zavolá zákazník z CRM, ať
telefon ukáže jméno/firmu. Plus ať se to nemusí dělat ručně.

**Co NEchceme** (Marti to rovnou zařízl, správně): synchronizovat celou
firemní DB (9105 kontaktů) do soukromých telefonů. To je z hlediska soukromí
i GDPR nesmysl.

## Navržený model — „aktivní sada"

Telefon zrcadlí **malou dynamickou sadu** kontaktů, kterou řídí server:

- Obchodník v ERP **klikne „volat"** na kontakt → server ten kontakt vloží do
  jeho osobní *aktivní sady* (`last_active = teď`).
- Když zákazník **zavolá zpět**, telefon ukáže jméno (kontakt je synchronizovaný).
- Po **30 dnech nečinnosti** (žádný další klik/hovor) server kontakt ze sady
  vyřadí → z telefonu zmizí. Každý nový klik timer resetuje.

**Transport:** CardDAV (otevřený standard). Telefon si sadu jen **zrcadlí**
(z naší strany read-only) — Android přes DAVx5, iOS nativně. Per-user sada.
Vždy jen pár desítek aktuálně řešených kontaktů, samo se to čistí.

## Co máme rozhodnuto (s Martim)

- Spouštěč přidání: **jen „volat"** (ostatní akce až později, additivně).
- TTL: **30 dní** nečinnosti, konfigurovatelné.
- **Per-user** sada (každý vidí jen svou).
- **Read-only** zrcadlení (telefon nepíše zpět do CRM).
- Auth: **app-specific heslo** (ne hlavní), HTTPS, audit každého add/remove.

## Otázky na tebe

**Q1 — GDPR posture.** I když je sada minimální a sama expiruje, jsou to pořád
zákaznická PII na soukromém zařízení. Stačí ti read-only + per-user + TTL 30d
+ audit + app-specific heslo? Nebo bys přidala explicitní souhlas uživatele,
poznámku do dokumentace, retenční pravidlo, nebo DPO sign-off?

**Q2 — Kam patří „aktivní sada".** Je to per-user data (kandidát na schéma
`"user"`), nebo framework feature (`fw`)? Ty ta schémata vlastníš — jak bys
to pojmenovala a kam umístila? (tabulka typu `user_active_contact`:
user_id, contact_ref, vcard_cache, last_active_at)

**Q3 — App-specific hesla.** Doporučujeme revokovatelná app-specific hesla
pro CardDAV (ne hlavní heslo). Souhlasíš? Chtěla bys k tomu nástroj na jejich
správu (vytvořit/zrušit per zařízení)?

**Q4 — Sémantika TTL.** 30 dní, reset při každém hovoru. Vidíš nějakou hranu —
např. možnost „připíchnout" klíčový kontakt (neexpiruje), nebo rozlišit
„viděl jsem ho v ERP" vs „opravdu volal"?

**Q5 — Tvůj insider pohled.** Co vidíš, co my dva nevidíme? (Tvoje Q9 eOČR
z 9. 5. nám ušetřilo problém — proto se ptáme dřív, než stavíme.)

Žádný spěch. Až budeš mít čas, ozvi se. — Marti & Claude 🌳
