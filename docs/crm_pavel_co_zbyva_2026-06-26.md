# CRM pro Pavla — stav realizace (souhrn 3 sessions, k 29. 6. 2026)

Řazeno podle Pavlova původního seznamu připomínek (A–H). U každého bodu: **co je hotové a jak** + co případně zbývá. Dole **navíc** = věci nad rámec seznamu.

Legenda: ✅ hotovo · 🟡 částečně / čeká na vstup · ❌ nezačato (rozhodnutí)

---

## A. Statistika práce obchodníka — ✅ hotovo
- Přehled **„Aktivity obchodníka"** (firma / typ akce / datum / splněno / poslední / průběh) + barevné odlišení + filtr.
- Souhrnný pruh **„Moje CRM čísla"** nad přehledem (počty za období, default přihlášený obchodník).
- **„Poslední" se počítá automaticky** (poslední akce firmy) — obchodník neřeší ručně.

## B. LinkedIn v číselníku akcí — ✅ hotovo
- Akce grid bere **živý číselník** akcí včetně **LinkedIn**.
- LinkedIn **má skóre** (hodnota akce = 3) → akce se počítá do statistik.

## C. Formuláře akcí podle typu — ✅ hotovo
- V gridu Akce: **„Nový" → výběr typu akce → otevře se jádro podle typu**, samo doplní firmu + typ.
- Per-typ jádra: Osobní jednání, Info o zákazníkovi, Telefonát na firmu / na OO, E-mail na info / OO, Získání firmy, Sem zavolej, Získání kontaktu.
- Kosmetika polí (co u kterého typu skrýt) **doladěná v UI** (Kristý).
- *Zbývá:* Zakázka + Poptávky — čekají na čistý zdroj v `st.`/PostgreSQL (nestavět na staré `dbo`).

## D. Atraktivita / Důležitost / Potenciál — 🟡 návrh hotov, čeká na Pavla
- **Atraktivita**: doplněn srozumitelný popis škály (1–5 s významem).
- **Důležitost + Potenciál**: pole už v databázi existují; **návrh škál připraven** (samostatný dokument `crm_pavel_skaly_atraktivita_dulezitost_potencial.md`) k odsouhlasení Pavlem.
- *Zbývá:* Pavel potvrdí škály → přidám Důležitost + Potenciál na kartu jako dropdowny (+ případně dopočítaný Potenciál).

## E. Stav obchodního vztahu — ✅ hotovo
- Pole **„Stav obchodního vztahu" na kartě** — 12 stavů včetně 3 Pavlových (Dělají si sami / Založí si a ozve se / Nezájem – obvolat za rok).
- Přehled Kontakty: sloupec **„Obchodní stav" + barevné odlišení** firem podle stavu.
- **Automatika příštího kontaktu**: po Odmítl / Neaktivní / Archiv / Dělají si sami → datum se **smaže**; po „obvolat za rok" → **+1 rok**.

## F. Ověřený kontakt + zdroj kontaktu — ✅ hotovo
- Karta: zaškrtávátko **„Ověřený kontakt"** + dropdown **„Zdroj kontaktu"** (web / telefon / LinkedIn / veletrh / e-mail / doporučení / jiné).
- Přehled Kontakty: **oba sloupce**.

## G. D&B / LinkedIn integrace — ❌ čeká na rozhodnutí (Marti)
- Strategické/nákladové: D&B přes oficiální placené API (licence); LinkedIn scraper **ne** (proti podmínkám) — místo toho AI-asistovaný research + legální placené zdroje + dobrá evidence veletrhů v CRM.

## H. Hromadné maily + tracking otevření — 🟡 demo hotové, ostré čeká na právní OK
- **„Oslovit vybrané"**: výběr firem → náhled (komu / info@ / nemá e-mail / odhlášený) → výběr šablony → odhlašovací odkaz. E-mail příjemce: **osobní mail kontaktní osoby, jinak firemní** (čte z nového `st.`).
- **Demo rozesílka**: tlačítko **„📨 Odeslat teď (DEMO)"** pošle e-mail ze šablony na **testovací adresu** (zatím k.ksirova@eurosoft.com) z Marti-AI schránky — reálné firmy nikdy nedostanou nic.
- **Tracking otevření**: tracking pixel → **„🔄 Zkontrolovat otevření"** ukáže u otevřených „Otevřeno ✓".
- *Zbývá:* ostrá rozesílka na reálné firmy (právní OK), automatický **follow-up za ~14 dní**, přepnutí odesílatele na **Pavlovu schránku** (až bude připojená).

---

## Navíc — nad rámec původního seznamu (taky hotové)
- **Karta zákazníka opravená** — OK i Storno fungují; dole dva sub-gridy: **Kontaktní údaje** (osoby) a **Akce** (historie) s přidáváním / opravou / mazáním.
- **Telefonování**: u čísla **historie „Předchozí hovory na toto číslo"** + možnost upravit poznámku a příští kontakt.
- **Plán hovorů pro Pavla**: přehled firem s **příštím kontaktem** (po termínu / tento týden), stav a **vytáčení**.
- **Layout karty** doladěn (výšky panelů, rozmístění nových polí).

---

## Co čeká na rozhodnutí / vstup
- **D** — Pavel potvrdí škály Atraktivita / Důležitost / Potenciál (návrh připraven).
- **H** — právní OK na ostrý cold-mailing + připojení Pavlovy schránky.
- **G** — Marti: D&B licence + směr LinkedIn / veletrhy.
