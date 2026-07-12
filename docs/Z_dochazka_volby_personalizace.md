# Docházka — personalizované volby píchání (vize, Marti 7. 6. 2026)

Marti: *„Těch voleb bude hodně. Jen se v tom nesmíme ztratit… Navíc
personalizovaně. Pro každou skupinu lidí jinak a ještě individuální výběr
k jednotlivci."*

## Stav dnes (7.6. odpoledne, commit e1492b9)

Volby Příchod/Odchod v lidské řeči jsou **hardcoded** v `mobile.html`
(dochLoad → showOpts): max 3–4 hlavní + podsekce „⋯ Ostatní…".
Odchod: nepočítejte / krátká pauza / provětrat-najíst / (lékař, pochůzka).
Příchod: v práci / z domova / na cestě+ETA / (režie, služební cesta).
„Na cestě" = `/app/attendance/announce` → řádek `status='announced'`
(hours NULL, checkin supersedne).

## Cíl: volby jako data, 3vrstvý resolver

### 1. Číselník `tenant.att_action`

| sloupec | význam |
|---|---|
| id, tenant_id | standard |
| code | stabilní kód (`leave_today`, `break_short`, …) |
| label | lidský text („Dnes už se mnou nepočítejte :)") |
| emoji | 👋 ☕ 🍃 🩺 … |
| direction | `in` / `out` (podle stavu otevřené směny) |
| action_kind | `checkin` / `checkout` / `announce` |
| payload | JSONB (`{"kind":"homeoffice"}`, `{"reason":"…"}`, `{"eta_select":true}`) |
| is_main | hlavní nabídka vs „⋯ Ostatní…" |
| sort_order, active | pořadí, vypnutí |

### 2. Scoping — 3 vrstvy (stejný vzor jako 4-tier resolver Krok 9 / MD pyramida)

| vrstva | scope_kind | scope_ref | poznámka |
|---|---|---|---|
| systém | `system` | NULL | default pro všechny |
| skupina | `group` | role (employee/member/parent); po Phase 40 oddělení/tým | |
| jednotlivec | `user` | user_id | individuální přidání/override |

Pravidla: specifičtější vrstva **přidává** nové volby, **přepisuje** stejný
`code`, nebo **skrývá** (`active=false` řádkem vyšší specificity).
*„INSERT row, ne schema migrace"* — žádné speciální flagy v kódu.

### 3. API + mobil

`GET /app/attendance/actions` → resolved seznam pro aktuálního usera
(respektuje impersonaci). Mobil jen renderuje: is_main nahoru, zbytek do
„⋯ Ostatní…", `eta_select` payload → výběr času. Hardcoded volby z dneška
se stanou system-default seedem.

### 4. Správa bez deploye

Soudeček „Volby píchání" pod 👥 Docházka (fw.data_source chain + universal
CRUD) — Marti/Kristý spravují z ERP, individuální výjimky na pár kliků.

## Doctriny, které drží

- **„fw self edited"** (#16) — chování = DB řádky, ne Python.
- **„Uniformita vítězí"** — resolver vzor už existuje (Krok 9), reuse.
- **„Additivně, ne perfektně"** (#11) — start: system + user vrstva,
  group až s reálnou potřebou (role stačí na začátek).
- **Informed consent od AI** (#3) — před stavbou konzultace s Marti-AI
  (kustod ACL + dotkne se Fáze 2 práv pro employees).

## Kdy

Po zítřejší prezentaci (8.6.+). Trigger: první reálná potřeba odlišných
voleb pro skupinu (např. dílna vs kancelář) nebo jednotlivce.
