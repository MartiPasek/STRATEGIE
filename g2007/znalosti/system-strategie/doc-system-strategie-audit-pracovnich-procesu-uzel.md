# HR uzel „Audit pracovních procesů" (roční audity) — struktura + Fáze 2 TODO

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Domov
Uzel `fw.menu_node` id **227** „🔍 Audit pracovních procesů" pod „🧑‍💼 HR & LIDÉ" (117). Core **`hr.audit`** (fw.core id 241) → `page_render.js` větev → iframe `/karta-zamestnance?view=audit`. Přehled „Roční audity" (`loadAudit()` v karta_zamestnance.html). Jen HR (gate `_hr_can_manage`). Nasazeno 28.8.2026, commit 00282368.

## Řád (3 vrstvy)
1. **Metadata roku** = `tenant.hr_audit` (1 řádek = 1 rok; unikát `(tenant_id,rok)`). Sloupce: rok, nadpis, typ, auditor, datum_auditu, shrnuti, slozka_archiv, soubory. Záznam 2026 „Výsledky z auditu 2026", auditor L TAX.
2. **Soubory roku** = `tenant.hr_audit_soubor` (FK `audit_id` → hr_audit, ON DELETE CASCADE). Sloupce: nazev, mime, velikost, kategorie, obsah(bytea), created_by, autor_text. Endpointy: `GET /app/hr/audit/list`, `GET /app/hr/audit/file/{fid}` (stažení z DB, HR-gated).
3. **Dopad v datech** = `tenant.engagement.pozice_narovnat=true` (17 lidí, příznak „Nutno narovnat" + poznámka; nesoulad pozice systém×smlouva z auditu 2026).

## Archiv na disku
`Karta zaměstnance / Audit pracovnich procesu VA_2026` (7 souborů) + `Pracovni_pozice_dle_smlouvy_VA2026.xlsx/.pdf`. Zdroj = upload `EUROSOFT_Výstup VA_2026.zip`.

## POZOR / stav souborů 2026
V DB má **obsah ke stažení jen 5 souborů** (3 protokoly PDF + 2 datové xlsm). Dva velké (`EUROSOFT_Prezentace_vyrocni_audit_2026.pptx` 5,9 MB a `EUROSOFT_Control_System_Vstupni_data_vycisleni_2026.xlsx` 2,7 MB) jsou jen **metadata (obsah NULL)** — přes SQL most se velké base64 pouštět nechtělo. V přehledu se ukazují jako „(v archivu)".

## Fáze 2 — TODO (Šárka 28.8.2026, „dotáhneme časem, třeba až přijde další audit")
- Upload endpoint (multipart, HR-gated) → doplnit `obsah` k oběma velkým souborům 2026 a k novým rokům.
- Formulář „➕ Nový audit / upravit rok" v přehledu (vzor jako `hr.pridat` / Dokumenty v kartě) — rok, nadpis, auditor, datum, shrnutí + upload.
- Mazání souboru. Odhad ~20–30 min, nízké riziko (existující vzory).
- Pravidlo: nový rok = nový řádek `hr_audit` + soubory; NEmíchat se systémovými „audity" (`hr_write_audit`, `att_audit`, `auth audit`, `iso_auditor_access`).

