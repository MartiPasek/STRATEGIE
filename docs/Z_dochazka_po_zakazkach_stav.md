# Docházka po zakázkách — stav k 22.7.2026 (handoff pro pokračování)

> Claude‑26 + Peťa, konec dlouhé session. Shrnutí pro navázání v nové konverzaci.
> Detaily: `doc-dochazka-po-zakazkach-prehled`, `doc-system-strategie-prehledy-tabulky-standard`,
> `doc-system-strategie-prehledy-sirky-sloupcu`. Vše NASAZENO a funkční.

## Co je hotové
- **Strom:** složka `🕒 Docházka` (uzel 188) → `🛠 Opravy docházky` (183) + `🏭 Docházka po
  zakázkách` (189, jádro `dochazka.centrala`) + `⏭ Naplánovaná budoucnost` (190,
  `dochazka.zakazky_budoucnost`). Viditelnost 11 lidí.
- **Přehled = VLASTNÍ stránka** `/dochazka-po-zakazkach` (iframe hook na ZAČÁTKU
  `dispatchPageRender` v page_render.js — jádro má data_source, jinak by se vykreslil
  framework grid). Endpoint `modules/erp/api/dochazka_zak_tab.py` bere SQL z data_setů
  `dochazka.zakazky_vse_list` / `_budoucnost_list` a spouští (převádí Decimal/date → JSON).
- **Data:** `tenant.vyroba_work` (práce na zakázce + skutečná činnost, C+app) UNION absence
  z `att_entry` (category='absence', bez přestávek), absence mají zakázku `Rezie` + centrálské
  číslo. Sloupce jako Delphi 109, bez CasBlbost/CasRezie, DruhCinnosti = ec_cislo, CasKonec
  s datem. CasCelkem ověřeno = setinná soustava (sedí na Centrálu).
- **Číselník činností zarovnán na Centrálu (1046/1047):** `vyroba_cinnost` má `strategie_cislo`
  (záloha) + `ec_cislo` (centrálské). Data přemapována (`cinnost_id_orig` záloha). Import opraven
  (mapuje přes ec_cislo). Přidána „Odměny fin.zakázek" (id 50, ec 27). Rezie sjednocena bez háčků.
- **Vzhled = standard** (rámeček, sticky hlavička bez velkých písmen, filtr pod názvy + ✕,
  úzký sloupec značek • / ▶, filtr čísel čárka/tečka, roztahování přes colgroup + vodicí čára,
  filtr 1px pod hlavičku = konec prosvítání). Totéž 1px fix nasazeno i pokladny/faktury; velká
  písmena v hlavičce zrušena i tam.
- **Šířky sloupců:** osobní tažení se ukládá do DB (`tenant.att_ui_pref` kod
  `dochazka_col_widths_u<uid>`), sdílené výchozí = kod `dochazka_col_widths`. **Peťa nastaví
  v Chromu, řekne „nastaveno", Claude povýší osobní na sdílené** přes most (bez tlačítka, bez
  deploye). Petiny výchozí už nastavené (22.7. 21:26). ⚠️ Peťě příště PŘIPOMENOUT: nastavení
  dělá v Chromu.

## Otevřené / k rozmyšlení
- Absence: mapa centrálských čísel je zatím přímo v data_setu (CASE dle `att_entry_type.code`),
  ne v `vyroba_cinnost` — pro nové typy doplnit.
- Číselník: „ostatní – kanceláře" (id 45, mrtvá, 0 použití) bez ec_cislo; Režie (14) a
  Bez rozlišení (43) záměrně bez ec_cislo (nejsou činnost).
