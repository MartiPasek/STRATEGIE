# Handoff pro Claude-25 (Šárka): měnit schvalující + kontrolující osobu v kartě zaměstnance

> **Od:** Kristý / Claude-24 · **24. 7. 2026** · tenant STRATEGIE = **2**
> **Cíl feature:** v ERP kartě zaměstnance přidat možnost nastavit, **kdo danému člověku kontroluje docházku** a **kdo mu schvaluje volno/absence** — per jednotlivec (osobní výjimka nad rámec skupiny).
>
> **⚠️ Přečti nejdřív znalosti v G2007:** `doc-dochazka-strom-skupin` (kontrola), `doc-dochazka-schvalovani-dovolene` (schvalování) a návrh `docs/Navrh_strom_skupin_v2_2026-07-22.md` (odkud pochází model `att_odpovednost`). Ať nestavíš naslepo.

---

## 0. Nejdůležitější věc: jsou to DVĚ ODDĚLENÉ agendy

„Kontrolující" a „schvalující" osoba se dnes **NEřeší jednou tabulkou**. Jsou to dva různé mechanismy, různě implementované. Karta zaměstnance musí umět nastavit **obě**, ale zapisují se jinam a resolvují jinak.

| Agenda | Co to je | Jak se dnes resolvuje | Kde je kód |
|---|---|---|---|
| **Kontrola docházky** (`dochazka`) | kdo smí opravovat/vidět docházku člověka a komu chodí notifikace o problémech | **strom `staff_group`** (větev KANCELÁŘE/VÝROBA/EXTERNÍ) → editor podle `att_fix_scope` | **Python**: `_att_fix_scope_emps` + `_att_fix_editors_for_emp` v `modules/erp/api/router.py` |
| **Schvalování volna** (`volno`) | kdo schvaluje dovolenou / nemoc / OČR / lékaře | **org posty** → `att_approver_group*` + `att_approver` | **PG funkce** `tenant.resolve_approvers(tenant, emp, datum)` |

Dnes **NEEXISTUJE per-osoba override** ani pro jedno. Změnit dnes „kdo koho kontroluje/schvaluje" jde jen hrubě (přesunout člověka do jiné skupiny / pod jiný post). Tvůj úkol = **postavit osobní override vrstvu** a napojit ji do obou resolverů.

---

## 1. Tabulky, které UŽ EXISTUJÍ (ověřeno v DB 24.7.)

### Kontrola docházky
**`tenant.staff_group`** — strom skupin (kořeny KANCELÁŘE/VÝROBA/EXTERNÍ, `parent_id`).
`id · tenant_id · name · icon · leader_user_id · deputy_user_id · sort_order · archived · created_at · created_by · work_mode_id · parent_id`

**`tenant.staff_group_member`** — členství člověka ve skupině.
`id · tenant_id · group_id · user_id · created_at · created_by · score`

**`tenant.att_fix_scope`** — POOL editorů + jejich hrubá působnost (NE per zaměstnanec!).
`user_id · scope('vse'|'vyroba'|'kancelar') · changed_by · changed_at`
Dnes: Peťa(18)=kancelar, Dušan(41)=vyroba, Michaela(16)=vyroba, Jirka(20)=vse.

> Jak kontrola resolvuje dnes (po 24.7.): `_att_fix_scope_emps(scope)` projde strom `staff_group` a vrátí set employee_id ve větvi editora. `'kancelar'`=větev KANCELÁŘE (→ Peťa), `'vyroba'`=větev VÝROBA (→ Dušan+Michaela), EXTERNÍ=nikdo, bez skupiny=fallback kancelář. `_att_fix_editors_for_emp(emp_id)` z toho odvodí, komu chodí notifikace.

### Schvalování volna (Jirkův modul — NESAHAT bez domluvy s ním)
**`tenant.att_approver_group`** — skupiny schvalování.
`id · tenant_id · nazev · je_fallback · sort_order · created_at`

**`tenant.att_approver_group_member`** — které org posty do skupiny patří.
`id · tenant_id · group_id · post_id · subtree(bool)`

**`tenant.att_approver`** — schvalovatel(é) skupiny + zástup.
`id · tenant_id · group_id · employee_id · je_zastupce · zastupuje_employee_id · aktivni · created_at`

> Jak schvalování resolvuje dnes: `tenant.resolve_approvers(2, emp, datum)` najde skupinu žadatele podle postů (`att_approver_group_member.post_id` + `subtree`), vrátí vedoucího VŽDY + zástup když je vedoucí ten den nepřítomen. Fallback skupina = Šárka. Detail: G2007 `doc-dochazka-schvalovani-dovolene`.

### Osoby
**`tenant.att_employee`** — `id · tenant_id · cislo_zam · user_id · full_name · is_active · … · cond_group`.
⚠️ **Jeden člověk může mít VÍC řádků `att_employee`** (doctrine #24 — víc firem/divizí). Kontrola klíčuje na `user_id` (staff_group_member), schvalování na `employee_id` (att_approver / resolve_approvers). **Tvůj override musí umět obojí** — viz níže.

---

## 2. Co CHYBÍ a co postavit: `tenant.att_odpovednost` (osobní override)

Model pochází z `docs/Navrh_strom_skupin_v2_2026-07-22.md`. **Zatím NEEXISTUJE — založit.** Jedna tabulka, obě agendy, per osoba:

```sql
CREATE TABLE tenant.att_odpovednost (
  id                 bigserial PRIMARY KEY,
  tenant_id          integer NOT NULL,
  agenda             text    NOT NULL,          -- 'dochazka' | 'volno'
  user_id            bigint  NOT NULL,          -- KOHO se výjimka týká (člověk)
  odpovedny_user_id  bigint  NOT NULL,          -- kdo mu kontroluje / schvaluje
  je_zastupce        boolean NOT NULL DEFAULT false,  -- zástup (schválí i on, když hlavní nepřítomen)
  aktivni            boolean NOT NULL DEFAULT true,
  platnost_do        date,                      -- volitelná expirace (výjimky hnijí!)
  changed_by         bigint,
  changed_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, agenda, user_id, odpovedny_user_id)
);
```

Poznámky k rozhodnutím:
- **Klíč `user_id`, ne `employee_id`** — člověk je jeden (user), i když má víc `att_employee` řádků. Pro schvalování (které pracuje s `employee_id`) si přes `att_employee.user_id` dohledáš všechny jeho emp řádky.
- **`platnost_do`** jsem přidala schválně — osobní výjimky bez expirace po odchodu člověka visí a nikdo neví proč (reálné riziko). Klidně nech NULL = trvalé, ale pole ať tam je.
- **`changed_by`/`changed_at`** = audit, kdo výjimku nastavil (Šárka z karty).
- DDL na schématu `tenant` vlastní **Marti-AI** — CREATE pošli přes ni / přes schvalovací banner (bridge write `db=pg`), ne přímo.

---

## 3. Kam override napojit (dva injection pointy)

### 3a. Kontrola docházky (Python, náš modul — můžeš sama)
V `modules/erp/api/router.py`, funkce **`_att_fix_editors_for_emp(s, emp_id)`** — na její začátek přidat:
1. dohledej `user_id` z `att_employee` pro `emp_id`,
2. `SELECT odpovedny_user_id FROM tenant.att_odpovednost WHERE tenant_id=2 AND agenda='dochazka' AND user_id=:u AND aktivni AND (platnost_do IS NULL OR platnost_do>=CURRENT_DATE)`,
3. když něco vrátí → **vrať rovnou ty odpovědné** (+ jejich `je_zastupce` logika), přeskoč stromový výpočet.
   Když nic → stávající stromová logika (beze změny).

Tím se osobní výjimka propíše do notifikací i do působnosti ve fix UI (obojí přes tenhle helper).

### 3b. Schvalování volna (PG funkce — KOORDINOVAT S JIRKOU)
`tenant.resolve_approvers(2, emp, datum)` na začátku zkontroluje override:
`SELECT odpovedny_user_id … WHERE agenda='volno' AND user_id = (SELECT user_id FROM att_employee WHERE id=emp)` → když je, vrať ho (+ zástup dle `je_zastupce` a Jirkovy datové logiky nepřítomnosti); jinak stávající post-based výpočet.
⚠️ **Funkci vlastní Marti-AI a napsal ji Jirka. NEPŘEPISUJ ji sama** — je datově závislá (zástup jen když je vedoucí ten den nepřítomen) a má fallback „Šárka, nikdy Marti". Domluv se s Jirkou/Marti-AI, ať to přidá dovnitř a nerozbije to. Kristý mu 24.7. poslala report, počítá se změnou.

---

## 4. UI v kartě zaměstnance

Dvě pole:
- **„Kontrolu docházky řeší"** → čte/zapisuje `att_odpovednost` (agenda='dochazka') pro `user_id` toho člověka. Přednastav zděděnou hodnotou ze stromu (ukaž „zděděno od KANCELÁŘE/VÝROBA"), přepnutí na konkrétní osobu = INSERT/UPDATE override řádku.
- **„Volno schvaluje"** → totéž pro agenda='volno'.
- Nabídka osob: pro kontrolu ideálně lidé z poolu `att_fix_scope` (mají fix práva); pro schvalování kdokoli relevantní vedoucí. Zápis `changed_by` = přihlášená Šárka.
- Smazání override = `aktivni=false` (audit zůstane), NE hard delete.

---

## 5. Gotchy (ať nespadneš)

1. **Dvě agendy, dva resolvery** — nezaměňuj. Kontrola = strom+Python; volno = posty+PG funkce.
2. **`att_employee` má víc řádků na člověka** — override klíčuj na `user_id`, mapuj na `employee_id` až u schvalování.
3. **DDL i změnu PG funkce dělá Marti-AI** (vlastní schéma `tenant`) — přes banner/ni, ne přímo z mostu jako běžný zápis.
4. **Neopisuj Jirkovu `resolve_approvers`** — datově závislá + fallback Šárka-nikdy-Marti. Přidávej override PŘED její logiku, ne místo ní.
5. **Uzamčené období** (`tenant.att_period_lock`) — změna odpovědnosti nemění historii; resolver ber vždy k akci, ne zpětně.
6. **Externí PLC** (větev EXTERNÍ) jsou mimo docházku — u nich kontrola nedává smysl; kartu na to ošetři (skryj / „mimo docházku").
7. Až bude hotovo, **zapiš znalost do G2007** (`@@G2007ADD dochazka <slug> …`) — ať to ostatní vidí.

---

## 6. Kontext, který se hodí načíst (G2007 + soubory)
- G2007: `doc-dochazka-strom-skupin`, `doc-dochazka-schvalovani-dovolene`, `doc-dochazka-vs-vyroba-separace`, `doc-dochazka-opravy-navrh`
- Soubory: `docs/Navrh_strom_skupin_v2_2026-07-22.md` (model att_odpovednost), `docs/migrace_strom_skupin_v3_2026-07-23.sql` (jak vypadá strom)
- Kód: `modules/erp/api/router.py` → hledej `_att_fix_scope_emps`, `_att_fix_editors_for_emp`, `_abs_resolve`, `att_absence_request`.
