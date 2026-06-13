# HR modul Benefity — požadavky + návrh (9. 6. 2026)

Zdroj: 2 e‑maily od Šárky Novotné (EUROSOFT) + Excel `Věrnostní poukázky_2025_SN_260608.xlsx`.
Deadline importu věrnostních poukázek: **konec června 2026** (proplácí se ve mzdě za červen).

## Seznam benefitů (Šárka, 9.6.)
Dovolená 5 týdnů/rok · 2 sick days/rok · stravenkový paušál · **věrnostní poukázka** ·
bonus za doporučení nového zaměstnance · jazykové kurzy · firemní/teambuildingové akce ·
home office · daňová úspora za údržbu firemního oblečení · daňová úspora za HO ·
občerstvení na pracovišti · příspěvek na mobilní tarif (po roce spolupráce) ·
1 den dovolené navíc při 10. výročí.

## Věrnostní poukázka — business pravidla
- Roční benefit za odpracovaný **končící rok**, předává se před Vánoci jako benefit.
- **Proplácí se ve mzdě za červen** následujícího kalendářního roku.
- Každý rok **koeficient** (dle hospodaření; navrhuje management — Michaela, schvaluje Marti).
  **2025 = koeficient 1.** Výsledek = základ × koeficient.
- Dostávají **všichni**.
- **Při odchodu se VŽDY proplatí** (ať z jejich nebo naší strany) — **VÝJIMKA:** když
  zaměstnanec dostane **vyšší než zákonné odstupné**, poukázka se neproplácí (a musí být
  na to při odchodu **upozorněn**). Hlídá Šárka v offboardingu (doplnit do procesu).
- Spravuje **Šárka**.

## Excel (import 2025)
List1, ~70 řádků: `Číslo zaměstnance · Věrnostní poukázka 2025 (částka) · Poznámky (příjmení) · Koeficient`.
Částky 3 000–7 000 Kč. Koeficient prázdný = 1.

## Návrh univerzálního modulu (v duchu finance/org v2)
- **`tenant.benefit_type`** — číselník benefitů (název, kategorie: finanční/volno/nepeněžní,
  způsob výplaty, popis, aktivní).
- **`tenant.benefit_award`** — přiznání benefitu člověku: user_id, benefit_type, rok, základ,
  koeficient, výsledná částka, měsíc výplaty, stav (plán → schváleno → vyplaceno), poznámka.
- Věrnostní poukázka = první ostrý typ. Napojení na **finance v2** (`wage_component` — červnová výplata).
- Viditelnost: **payroll_officer / parent** (ACL jako finance v2). Lidé svůj benefit zatím ne (Marti 9.6.: „pro teď stačí").

## Stav: čeká na konzultaci Marti-AI (úkol, doktrína #8) — viz níže.
Otázky Q1–Q6 poslány Marti-AI jako úkol 9.6.2026. Po jejích závazných závěrech → Fáze A
(schéma + import 70 lidí + přehled pro Šárku + podklad pro mzdy).
