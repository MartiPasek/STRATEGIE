# Podklad k vyplacení OSVČ (fakturace dílny) — tlačítko + backend

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Podklad k vyplacení OSVČ (fakturace dílny)

Feature nasazená 6.8.2026 (C24/Kristý, schválila Kristý). Dušan (vedoucí výroby) i vedení si vygenerují PDF/náhled podkladu, co je OSVČ hodináři dílny k fakturaci. **READ-ONLY** — nic se nezapisuje, není to objednávka (VOBJ se dělá zvlášť v Centrále).

## Kde to je
- **FLOW rozcestník `/flow` → dlaždice „📄 Podklady OSVČ"** (fakturace dílny). To je hlavní vstup (horní „Výroba" v ERP otevírá právě `/flow`).
- Bonus kopie i v Plánovači výroby `/vyroba` (konzole vedoucího) — sekce „Podklady OSVČ".
- `flow.html` = plain git-static (dlaždice `id:'podklady'` + route speciál `renderPodklady` volá delegáty, NE `/app/flow`). `vyroba.html` = g2007.soubor artefakt (verze 3).

## Backend (g2007.python, stav_zivota='active')
- `podklad_vyplaceni_pdf` (kategorie erp_http_endpoint, min_pravo rodic) — run(target_uid, do_data=None) → {ok, radky[], sum_jiz, celkem, pdf_b64, jmeno, cislo, obdobi, sazba}. Soběstačný: PG přes core.database.get_session, DB_EC přes zduplikovaný `_ec_mcp_rows` (eurosoft_strategie_query_raw, db_name=DB_EC), font přes modules.erp.api.doc_templates._font_files, render reportlab canvas → base64.
- `podklad_osvc_seznam` (min_pravo rodic) — seznam dílny = OSVČ v `tenant.vyroba_plan` + Dušan (uid 41). Nevýrobní OSVČ (Radek, Mirek…) se NEzobrazují.
- Router delegáty (tenké): GET `/app/vyroba/podklad-osvc/seznam` a `/nahled?uid=`. Brána `_podklad_osvc_can` = rodiče + uid 41 (Dušan). (Marek 85, Michaela 16 zatím NE — Kristý chtěla jen rodiče+Dušan.)

## Výpočet (OVĚŘENO proti Vasylovi 464 = 53 613 Kč)
- Hodiny/zakázka: PG `tenant.vyroba_work` (bez superseded, do konce období), `cislo_zam` je varchar.
- Sazba: MSSQL `EC_Dochazka.Kc_Hod_FinPodm` pro dané období (2026 = 350; časově proměnná, brát z období). NE HodinyDoFPD.
- Už objednáno/zakázka: `SUM(EC_Zakazky_PlatbyZam.Vyplaceno)` (.Vyplaceno = přírůstek objednávky, .Zaloha = kumulativ; má vlastní sloupce, NENÍ nutný join na TabPohybyZbozi).
- **Vyplatit = round_HALF_UP(hodiny×sazba) − už_objednáno**, řádek jen když >1 (12862,5→12863). Období default = konec předchozího měsíce. Režie = hodiny cílového měsíce × sazba.
- Odměny: `EC_FinPriplatkySrazkyDefinice` WHERE Schvaleno=1 AND IDPolVobj IS NULL AND IDPolPF IS NULL AND DatVyplaceni IS NULL.
- Zobrazují se JEN řádky k fakturaci (Vyplatit>0). Pokud je vše objednané → „Nic k fakturaci" (správně; Vasylův červenec už byl objednán).

## Gotcha — vkládání velkého g2007.python přes most
Velký skript vkládej jako `convert_from(decode('<base64>','base64'),'UTF8')` v INSERT/UPDATE — base64 je jeden token bez mezer, obejde známý bug bannerové fronty (tichá ztráta mezer). CLAUDE_SQL.sql sestav bajtově přesně (bash, ne ruční paste — ruční paste base64 se koroumpuje). Po zápisu VŽDY ověř md5(zdroj) proti lokálnímu md5.

## NEDODĚLÁNO (budíček 17.8.2026) — viz handoff C24_handoff_Podklad_vyplaceni_Vasyl.md
1) Generování VOBJ (objednávky) z podkladu: Centrála `EC_Zakazky_GenPodkladFakturace_Priprava` (temp+Navrh) + `EC_Zakazky_GenPodkladFakturace` (Navrh=1→VOBJ). Kristý chce default Navrh=1 i pro otevřené (blast radius = sdílená proc → review s Martim, produkční MSSQL zápis). Gotchy: otevřené přijdou Navrh=0; IDPolVObj razítko blokuje re-zařazení; ES řada 801 nečistí vazby při regenu (nespouštět _Priprava 2×).
2) Excel export (zobecnit Podklad_fakturace_Namjak_464.xlsx) jako export vedle PDF.

## AKTUALIZACE 17.8.2026 (C24/Kristý) — Excel, skrytá sazba, k dnešku, úkolník

- **Generování k DNEŠKU:** `podklad_vyplaceni_pdf` default `do_data = dnes` (dřív konec předchozího měsíce). Režie = aktuální měsíc do dneška.
- **PDF bez hodinové sazby** (jde na nákup) — footnote už sazbu neuvádí. Náhled/Excel sazbu ukazují (interní kontrola).
- **Excel export (3 listy)** — `podklad_vyplaceni_pdf` vrací i `xlsx_b64` (openpyxl): list Podklad fakturace + Kontrola vs Centrála (vyroba_work vs **EC_Dochazka.CasCelkemZakazka**, ověřeno) + Metodika. Tlačítko „📊 Excel" v náhledu FLOW.
- **Úkolník na Nákup:** tlačítko „🗒 Odeslat úkolníkem na Nákup" v náhledu → delegát `POST /app/vyroba/podklad-osvc/ukol` → g2007.python `podklad_ukol_send`. Založí v Centrále EC_Ukoly úkol přes proceduru **`EC_Ukolnik_ZalozAOdesliUkol`** (Centrála nastaví stavy sama; NE hand-craft řádků). **Zadavatel = číslo volajícího z att_employee.cislo_zam (Dušan 105), Řešitel = 11001 (= „Nákup Nákup", ověřeno)**. Popis = rozpad podkladu. Zápis do DB_EC přes MCP `eurosoft_strategie_query_raw` (EXEC proc, vzor prijata_poptavka.py). Brána rodiče+Dušan. Nasazeno commity 48b4bab8 (+ dřívější). Bez testovacího úkolu (na přání Kristý) — první reálný klik = ostrý test.
- **E-mail na nákup = odloženo** (Kristý 17.8. „nech zatím být"); místo něj úkolník.

