# Demo průvodce — ISO 27001 / TISAX modul (prezentace certifikační firmě)

> oblast: `iso27001` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Demo průvodce — ISO 27001 / TISAX modul (prezentace certifikační firmě)

> **Verze:** 1.0 · **Datum:** 21. 6. 2026 · **Pro:** Marti (prezentující) · **Klasifikace:** Interní
> **Příběh (přerámováno 21.6.):** Tohle není „software na získání certifikátu". Je to **zákazníkova
> pravá ruka v bezpečnosti firmy** — průběžně ho vede k pořádku, k pravidelným kontrolám a ke
> **správě hesel** (největší reálný bordel ve firmách), aby se v tom neztratil. **Certifikace je
> milník, ne konec** — modul slouží dál, den za dnem. Celý ISMS elektronicky, bez papíru a e‑mailů,
> auditor i lidé pracují přímo v portálu. Nabízíme přes pana Antoše jako společnou spolupráci.
>
> **Hlavní hák:** *„Jaký je u vás největší bordel? Hesla."* → ukázat 🔐 Trezor (konec lepíků pod
> klávesnicí; každý má svůj šifrovaný trezor, firma vidí pořádek, ne obsah).
> **Ověřeno funkční 21.6. 00:35** (cockpit, dokumenty, SoA, TISAX, evidence, auditorský portál, feedback).

---

## Co ukázat — v tomto pořadí (5 obrazovek, ~5 minut)

1. **`/iso-admin` — produktový pohled certifikační firmy.**
   „Každý váš zákazník = samostatné elektronické ISMS." Vidíte EUROSOFT a STRATEGIE s běžícím ISMS
   (progres v %), a tlačítko **„Inicializovat ISMS"** u nového zákazníka — jedním klikem se mu
   z univerzální šablony založí celý systém (kroky, 19 dokumentů, 93 kontrol SoA, TISAX).

2. **„Otevřít cockpit" u EUROSOFTu → `/iso?tenant=2` — řízení ISMS.**
   - **Kroky k certifikaci** se stavem (registr rizik → SoA → podpisy → školení → interní audit →
     review → náprava + technické kroky vč. **plánu obnovy pro Michala**).
   - **19 dokumentů ISMS** elektronicky, u politik **✍️ Podepsat** = elektronický podpis (SES)
     klikem, se záznamem kdo/kdy/zařízení. **Žádný tisk.**
   - **📑 SoA — 93 kontrol** Annex A se stavem (92 aplikovatelných / 1 ne).
   - **🚗 TISAX — VDA ISA 6.0.3**: Information Security mapovaný z ISO (pokrytí ~74 %) → „jedna
     investice, dva výsledky"; Prototype Protection + Data Protection zvlášť. Cíl AL2.
   - **📎 Nahrané dokumenty (evidence)** — **104 reálných TISAX dokumentů EUROSOFTu** (politiky,
     Disaster Recovery Plan, ISA katalog 6.0.3, DQS report, NDA…) přímo v modulu.

3. **`/dokument` — dokumentace v appce s tiskem.**
   Tutoriál/plány se renderují v appce, **🖨 Tisk**, a **💬 widget pro všechny** (dotaz / nerozumím /
   špatně / nesouhlasím / doplnit) → rovnou do databáze.

4. **Auditorský portál `/iso-audit/<token>` — read‑only pro auditora.**
   V cockpitu „Vytvořit přístup" → vznikne odkaz pro auditora. Auditor přes něj **bez loginu** vidí
   dokumenty, SoA, evidenci — a hlavně **píše přímo nám** (žádný e‑mail), my to **hned vidíme** v
   cockpitu a **odpovíme přímo v portálu**. Vše auditované.

5. **`/iso` cockpit dole — „💬 Dotazy a připomínky"** — sem padají dotazy lidí i auditorů
   (auditorské zvýrazněné), jedním klikem odpovíme. **E‑mail jako pojistka s proklikem** do portálu.

---

## Klíčové prodejní body (řekni nahlas)
- **Totální digitalizace ISMS** — papír i e‑maily nahrazené portálem; auditor i lidé v jednom místě.
- **ISO 27001 i TISAX v jednom** — sdílené kontroly, jedna evidence, dva výsledky.
- **Multi‑tenant produkt** — certifikační firma spravuje všechny své zákazníky z jednoho admin pohledu.
- **Elektronický podpis (SES) + úplná auditní stopa** (kdo/kdy/zařízení) u každého úkonu.
- **Postaveno za víkend nad existující platformou** — důkaz rychlosti a síly STRATEGIE.

---

## Na co si dát pozor (poctivost vůči auditorovi)
- Dokumenty STRATEGIE jsou zatím **návrhy** (v0.1) — to je v pořádku, jsme ve fázi dorážení.
- Mluvit přesně: **„šifrováno při přenosu + tajemství v trezoru"**, **„append‑only audit"** (ne
  nadsazovat). Detail v `iso_tisax_harmonizace_2026.md` §4 a `iso27001_dorazeni_2026.md` §9.
- Skenované PDF mají slabší vytěžený text (OCR doplníme) — soubory se otevírají normálně.

---

## Go‑to‑market
**Přes pana Antoše** jako **společná nabídka EUROSOFT/STRATEGIE × certifikační společnost** —
neobcházíme ho. Oslovení dělá Marti; podklady (positioning) připraví Claude na vyžádání.

---

*Vše live na `strategie-ai.com`. Stav modulu a navazující dokumenty: `ISO_27001.md` (rozcestník).*


