# Excel „Plánování vytížení" (Dušan) — navaznosti absencí na DB_EC + zadání dořešení

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Excel „Plánování vytížení" (Dušan, vedoucí výroby) — absence ze STRATEGIE

Ověřeno end-to-end 5.8.2026 (C23, rozbor VBA sešitu v162 + živé dotazy DB_EC a PG).
Zadání Marti: promítnout plánované absence ze STRATEGIE do Dušanova přehledu.
**Předáno Jirkovi + Claude-28 k realizaci.**

## Jak sešit funguje
- XLSM s VBA, ADO/SQLOLEDB na EC server (192.168.99.15), katalog ze `Settings.ini` (= DB_EC).
- Čte view `dbo.ECv_Vytizeni_*`, píše přes procedury `dbo.EC_Vytizeni_*` (Aktualizace = `EC_Vytizeni_AktualizujData_NEW`).
- Absence: VBA `basNepritomnost.NactiNepritomnostALL` čte `dbo.ECv_Vytizeni_SeznamNepritomnost`
  (list „Nepřítomnost" + barevná časová osa), seznam lidí z `ECv_Vytizeni_SeznamLidiNepritomnost`
  (= EC skupina 31, aktivní dle `tabciszam_EXT._Neaktivni=0`).

## Funkční řetěz (OVĚŘENO, funguje)
`tenant.att_planned_absence` (PG, naše pravda)
→ job **`sync_vytizeni_absence`** (`fw.mirror_job`, enabled, á 180 min; kód v `g2007.python kod=sync_absence_to_ec_vytizeni`; ručně `@@VYTIZABS [dnu_zpet]`)
→ **`st.EC_Vytizeni_NepritomnostSTRATEGIE`** v DB_EC (DELETE+INSERT, mapování přes `tenant.att_employee.cislo_zam`, barvy dle druhu činnosti)
→ `dbo.ECv_Vytizeni_SeznamNepritomnost` (přesměrováno na st 28.6.2026, rollback: `docs/ec_view_vytizeni_nepritomnost_rollback.md`)
→ Excel. K 5.8.: 499 řádků, 7.7.–31.12.2026, 43 lidí, view vrací 54 řádků/11 lidí na 30 dní.

## DÍRY (proč Dušanovi absence chybí) — TOHLE DOŘEŠIT
1. **`EC_Vytizeni_GenerujInfoDatum`** — 4× čte mrtvou `dbo.EC_Dochazka_PlanNepritomnost`. Plní denní INFO buňku (seznam „kdo je volný" + hodiny volna skupin 13/32/33). Důsledek: lidi na dovolené vypadají volní, součty volna = 0. Volá se při každé Aktualizaci.
2. **`ECv_Vytizeni_Vypomoc`** — čte mrtvou tabulku; výpomocím (skupina 30) se v den absence nenulují hodiny ani nebarví buňky.
3. **Drift `_Neaktivni`**: view filtruje `tabciszam_EXT._Neaktivni=0`; Kuska (č. 460) je ve STRATEGII aktivní s 21 budoucími dny absence, v EC neaktivní → z view vypadává. EC personálka se neudržuje → drift poroste.
4. `EC_Vytizeni_GenerujPlanNepritomnost` — mrtvý generátor (plní mrtvou tabulku z mrtvých EC docházkových zdrojů; „Predikce dovolených" hardcoded léto 2025). Volá se zbytečně na startu každé Aktualizace.

## Schválený směr (Marti 5.8.: „takhle mi to stačí", Recommended varianta)
- ALTER `ECv_Vytizeni_Vypomoc` + `EC_Vytizeni_GenerujInfoDatum`: mrtvá tabulka → `st.EC_Vytizeni_NepritomnostSTRATEGIE`. POZOR: st tabulka NEMÁ sloupec ID — testy `N.ID is null` / `isnull(id,0)>0` přepsat na EXISTS / `pn.CisloZam IS NOT NULL`.
- V `AktualizujData_NEW` vypnout `EXEC EC_Vytizeni_GenerujPlanNepritomnost` (proc nechat v DB).
- Drift: rozšířit sync o Prijmeni/Jmeno/Aktivni ze STRATEGIE do st + view přepnout na COALESCE (primárně st, fallback TabCisZam). Jednorázově: Kuskovi odznačit `_Neaktivni` v EC.
- Před každým ALTER uložit původní definici do rollback docu (rozšířit `docs/ec_view_vytizeni_nepritomnost_rollback.md`).
- Otevřená otázka na Dušana: chce obnovit „Predikci dovolených" (rezervu 24 h/den) nad novými daty?

## Gotchy
- Sync hlásí „vlozeno 546", tabulka má 499 řádků (vše z jednoho běhu) — nejspíš duplicity v PG plánu tiše dedupnuté na EC straně. PROVĚŘIT při realizaci (duplicitní (CisloZam,Datum,Druh) by ve view zdvojily hodiny).
- st tabulka: sloupce CisloZam, DatumPripadu, DenVTydnu, DruhCinnosti, PocetHodin, Barva, synced_at (bez PK v definici sync skriptu — ověřit indexy).
- THP lidé (Šafránková aj.) nejsou ve skupině 31 → mimo Dušanův pohled (zřejmě záměr, sešit je pro dílnu/montéry).
- Zápisy do DB_EC = write přes most/MCP se schvalovacím bannerem.

