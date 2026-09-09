# PŘEDÁNÍ — kontrola docházky červenec 2026 (Peťa + Claude-26)

Zápis z konverzace 3.–4. 8. 2026. Vlož do nové konverzace jako kontext.

---

## 1. Co se právě dělá (POKRAČUJ TÍMTO)

**Kontrola docházky za ČERVENEC 2026 před mzdami — člověk po člověku.**
Peťa napíše jméno, Claude vypíše **JEN problémy** (ne "vše je v pořádku" výčty).
Cíl: projet ~40 lidí rychle a bez zádrhelů.

Kontroluje se (jen červenec, nic jiného):
- **A** pracovní den bez jakékoli docházky
- **B** moc dlouhý den (víc než fond + 1 h)
- **C** moc krátký den (míň než 6 h a bez absence)
- **D** překryv záznamů
- **E** neukončený den
- **F** dlouhá pauza (nad 1 h, mimo `day_end`)
- **G/H** chybějící zakázka / činnost v rozpadu
- **I/J** rozpad chybí / nesedí na docházku (nad 0,05 h)
- **Z** FPD za měsíc (na vyžádání)

### Hotovi (červenec)
Brudnová (356), Čepický, Diviš, Duspivová (50), Egermaier, Erhard, Hájek (483),
Havlat, Hellmayer, Hladíková (440), Honal (370), Jakešová, Jirkovský, Kasal.

**Poslední stav:** Jirkovský — FPD 176,02 vs fond 176,00 (+0,02 h) → **sedí**.
Kasal — bez divností, jen 6,30 h nad fond (přesčasy, ať to Peťa potvrdí).

### Falešné poplachy — NEHLÁSIT
- **Výroba = dílna** (Diviš a spol.) → krátké dny se jim nezarovnávají, neřešit.
- Typy `Nenároková práce`, `Doplnění do fondu`, `Dnes už se mnou nepočítej`
  nemají časy / mají 0 h **záměrně** — nejsou to neukončené dny.
- **Rozdíly docházka × rozpad do 0,05 h** — známý systematický jev
  (zaokrouhlování po úsecích), řeší se až po mzdách.

---

## 2. Dotaz, kterým se to kontroluje

Ulož přes **Write tool** do `C:\Projekty\Strategie\scripts\claude_sql\CLAUDE2_SQL.sql`,
pak `CLAUDE2_GO.txt` = `db=pg`, po ~20 s čti `CLAUDE2_OUT_FULL.txt`.
Mění se jen `em.full_name ILIKE '%Jmeno%'`.

```sql
WITH emp AS (
  SELECT em.id AS emp_id, em.user_id, em.full_name,
         COALESCE((SELECT round(g.uvazek_tyden_h / NULLIF(COALESCE(wm.dny_v_tydnu,5),0), 2)
                   FROM tenant.engagement g
                   LEFT JOIN tenant.work_mode wm ON wm.id = g.work_mode_id
                   WHERE g.employee_id = em.id AND g.tenant_id = 2 AND g.is_current = true
                   ORDER BY g.valid_from DESC LIMIT 1), 8.0) AS fond
  FROM tenant.att_employee em
  WHERE em.tenant_id = 2 AND em.full_name ILIKE '%JMENO%'
),
den AS (
  SELECT h.den, h.hodiny_mzdove, h.hodiny_nad_fond, h.hodiny_absence
  FROM emp, tenant.att_den_hodiny(2, DATE '2026-07-01', DATE '2026-07-31') h
  WHERE h.emp_id = emp.emp_id
),
z AS (
  SELECT e.id, e.entry_date AS d, et.code, et.label, et.category, e.hours, e.started_at, e.ended_at
  FROM tenant.att_entry e
  JOIN emp ON emp.emp_id = e.employee_id
  JOIN tenant.att_entry_type et ON et.id = e.entry_type_id
  WHERE e.tenant_id = 2 AND COALESCE(e.status,'') <> 'superseded'
    AND e.entry_date BETWEEN DATE '2026-07-01' AND DATE '2026-07-31'
),
prace AS (SELECT d, SUM(hours) AS h FROM z WHERE code IN ('work','overhead') GROUP BY d),
rozpad AS (
  SELECT w.datum AS d, SUM(COALESCE(w.hodiny,0)) AS h,
         COUNT(*) FILTER (WHERE w.zakazka_ref IS NULL OR btrim(w.zakazka_ref) = '') AS bez_zak,
         COUNT(*) FILTER (WHERE w.cinnost_id IS NULL) AS bez_cin
  FROM tenant.vyroba_work w JOIN emp ON emp.user_id = w.user_id
  WHERE w.tenant_id = 2 AND w.is_active AND w.datum BETWEEN DATE '2026-07-01' AND DATE '2026-07-31'
  GROUP BY w.datum
),
pracdny AS (
  SELECT cd.day FROM tenant.att_calendar_day cd
  WHERE cd.tenant_id = 2 AND cd.is_workday AND COALESCE(cd.is_holiday,false) = false
    AND cd.day BETWEEN DATE '2026-07-01' AND DATE '2026-07-31'
),
fpd AS (
  SELECT (SELECT count(*) FROM pracdny) AS dnu,
         COALESCE((SELECT sum(hodiny_mzdove + hodiny_nad_fond + hodiny_absence) FROM den),0) AS odpracovano
)
SELECT 'A_ZADNA_DOCHAZKA' AS sekce, CAST(p.day AS text) AS den,
       'pracovní den bez záznamu (' || to_char(p.day,'Dy') || ')' AS detail
FROM pracdny p, emp
WHERE NOT EXISTS (SELECT 1 FROM z WHERE z.d = p.day AND z.code NOT IN ('day_end','fond_doplneni','nenarokova'))
UNION ALL
SELECT 'B_MOC_DLOUHA', CAST(x.den AS text),
       CAST(round(x.hodiny_mzdove + x.hodiny_nad_fond, 2) AS text) || ' h (o '
       || CAST(round(x.hodiny_mzdove + x.hodiny_nad_fond - emp.fond, 2) AS text) || ' h nad fond)'
FROM den x, emp WHERE x.hodiny_mzdove + x.hodiny_nad_fond > emp.fond + 1.0
UNION ALL
SELECT 'C_MOC_KRATKA', CAST(x.den AS text),
       CAST(round(x.hodiny_mzdove + x.hodiny_nad_fond, 2) AS text) || ' h (míň než 6)'
FROM den x
WHERE x.hodiny_mzdove + x.hodiny_nad_fond > 0
  AND x.hodiny_mzdove + x.hodiny_nad_fond < 6.0 AND x.hodiny_absence = 0
UNION ALL
SELECT 'D_PREKRYV', CAST(a.d AS text),
       a.label || ' ' || to_char(a.started_at,'HH24:MI') || '-' || to_char(a.ended_at,'HH24:MI')
       || '  x  ' || b.label || ' ' || to_char(b.started_at,'HH24:MI') || '-' || to_char(b.ended_at,'HH24:MI')
FROM z a JOIN z b ON b.d = a.d AND b.id > a.id
WHERE a.started_at IS NOT NULL AND a.ended_at IS NOT NULL
  AND b.started_at IS NOT NULL AND b.ended_at IS NOT NULL
  AND a.started_at < b.ended_at AND b.started_at < a.ended_at
  AND a.code <> 'day_end' AND b.code <> 'day_end'
UNION ALL
SELECT 'E_NEUKONCENY', CAST(z.d AS text), z.label || ' od ' || to_char(z.started_at,'HH24:MI') || ' bez konce'
FROM z WHERE z.ended_at IS NULL AND z.started_at IS NOT NULL
  AND z.code NOT IN ('nenarokova','fond_doplneni','day_end')
UNION ALL
SELECT 'F_DLOUHA_PAUZA', CAST(z.d AS text),
       CAST(round(z.hours,2) AS text) || ' h (' || to_char(z.started_at,'HH24:MI') || '-' || to_char(z.ended_at,'HH24:MI') || ')'
FROM z WHERE z.category = 'break' AND z.code <> 'day_end' AND z.hours > 1.0
UNION ALL
SELECT 'G_CHYBI_ZAKAZKA', CAST(r.d AS text), CAST(r.bez_zak AS text) || ' úseků bez zakázky'
FROM rozpad r WHERE r.bez_zak > 0
UNION ALL
SELECT 'H_CHYBI_CINNOST', CAST(r.d AS text), CAST(r.bez_cin AS text) || ' úseků bez činnosti'
FROM rozpad r WHERE r.bez_cin > 0
UNION ALL
SELECT 'I_ROZPAD_CHYBI', CAST(p.d AS text), 'odpracováno ' || CAST(round(p.h,2) AS text) || ' h, rozpad žádný'
FROM prace p LEFT JOIN rozpad r ON r.d = p.d WHERE r.d IS NULL AND p.h > 0
UNION ALL
SELECT 'J_ROZPAD_NESEDI', CAST(p.d AS text),
       'docházka ' || CAST(round(p.h,2) AS text) || ' x rozpad ' || CAST(round(r.h,2) AS text)
       || ' — chybí ' || CAST(round(p.h - r.h,2) AS text) || ' h'
FROM prace p JOIN rozpad r ON r.d = p.d WHERE abs(p.h - r.h) > 0.05
UNION ALL
SELECT 'Z_FPD', 'za červenec',
       'fond ' || CAST(round((emp.fond * f.dnu)::numeric,2) AS text)
       || ' / odpracováno+absence ' || CAST(round(f.odpracovano,2) AS text)
       || ' / rozdíl ' || CAST(round(f.odpracovano - emp.fond * f.dnu,2) AS text) || ' h'
FROM fpd f, emp
ORDER BY 1, 2;
```

**POZOR na FPD:** `att_den_hodiny` vrací `hodiny_absence` **zvlášť**, ne uvnitř
`hodiny_mzdove`. FPD = `hodiny_mzdove + hodiny_nad_fond + hodiny_absence`.
Když se absence zapomene přičíst, vyjde falešný schodek (u Jirkovského −15,98 h
místo správných +0,02 h).

---

## 3. Most (SQL bridge) — jak s ním pracovat

- **Lane 2.** Zapiš `scripts/claude_sql/CLAUDE2_SQL.sql` **VŽDY přes Write tool**
  (zápis přes bash mount watcher nemusí zachytit), pak `CLAUDE2_GO.txt`
  s obsahem `db=pg`, po ~18–25 s čti `CLAUDE2_OUT_FULL.txt`.
- **Dvojtečka je bind parametr** → místo `x::text` piš `CAST(x AS text)`;
  pokud dvojtečku potřebuješ v textu, `replace($q$…~~…$q$, '~~', chr(58))`.
- **Zápis** musí začínat `INSERT`/`UPDATE`/`DELETE` — `WITH … INSERT` most odmítne
  jako "forbidden keyword".
- **Schvalovací banner** chodí Petře (user 18). Poll timeout je 120 s,
  ale request zůstane `pending` ve `fw.claude_write_request` — dá se schválit i později.
- **HTTP 401 = vypršel token** → OPS lane: `CLAUDE_OPS.txt` s `restart_self`
  + `CLAUDE_OPS_GO.txt`. Občas je potřeba, aby Peťa restartovala službu
  `STRATEGIE-CLAUDE-SQL` ručně.
- **Deploy:** nejdřív `CLAUDE_PULL_GO.txt`, pak `CLAUDE_DEPLOY.txt`
  (1. řádek = commit message, dál cesty souborů) + `CLAUDE_DEPLOY_GO.txt`.
- **Kód žije v DB** (Marti 2. 8.): logika v `g2007.python`, web v `g2007.soubor`.
  Soubory na disku jsou odvozené. `erp_registry.call(kod, *args)` volá `fn(*args)`
  — **session se NEPŘEDÁVÁ**, takže `def run(uid)`, ne `def run(s, uid)`.

---

## 4. Datový model — co je potřeba vědět

| Objekt | K čemu |
|---|---|
| `tenant.att_den_hodiny(tenant, od, do)` | **jediný správný zdroj hodin** — vrací `emp_id, den, hodiny_mzdove, hodiny_nad_fond, hodiny_absence`. Slučuje překryvy, odečítá pauzy uvnitř práce, přičítá doplnění do fondu. Používej ho, ať čísla sedí s aplikací. |
| `tenant.att_entry` | hlavičky docházky |
| `tenant.vyroba_work` | rozpad na zakázky (jde rozejít s `att_entry`) |
| `tenant.engagement` | fond = `uvazek_tyden_h / work_mode.dny_v_tydnu`, ber engagement **platný k datu záznamu** (`ORDER BY valid_from DESC`), ne aktuální |
| `engagement_entitlement.value` | ve **DNECH** i pro sick days; hodiny = dny × denní fond |
| `tenant.dovolena_korekce` | ruční korekce rozpadu D/DN s důvodem |

---

## 5. Co je hotové (nevracet se k tomu)

**Obrazovka „Nárok a čerpání dovolené"** pod soudečkem Docházka — D, DN, SD.
- logika `g2007.python` → `att_narok_cerpani`, `def run(uid)`
- `apps/api/static/dochazka-narok.html`, route `/dochazka-narok`
- endpoint `/app/dochazka-narok/data` v `modules/erp/api/dochazka_zak_tab.py`
- hook `dochazka.narok` v `page_render.js`
- D/DN se dělí pravidlem (OSVČ → vše DN; ostatní → nejdřív standard do nároku,
  zbytek DN), výjimky z `tenant.dovolena_korekce`
  (Hladíková 440 = 4 dny, Marešová 21 = 1, Zeman 40 = 1 — chyba Centrály,
  ale mzdy proběhly, takže se respektuje)
- **Ověřeno proti Centrále:** dovolená sedí u všech 86 lidí, sick days 84/86.
- ⚠️ **Nedodělek:** D a DN se pořád zobrazují v hodinách, mají být **ve dnech**
  (v hodinách jen SD). Zápis neprošel — dodělat.

**Překryv už neblokuje uložení** — `att_fix_add`, `att_fix_polozka` vrací
`varovani` místo chyby. Varování v `dochazka-opravy.html` se počítá z aktuálního
stavu dne, takže po srovnání zmizí. Sekundy se porovnávají na minuty
(`date_trunc('minute', …)`) — navazující časy už nehlásí překryv.

**Sekundy do rozpadu** — `att_checkin`/`att_checkout` zapisují
`date_trunc('minute', now())`. Stará data se **nečistila** (test ukázal, že by to
zhoršilo: 451 → 569 nesedících dnů).

**Automatický přepočet doplnění do fondu** (root cause, dvě vrstvy):
1. `att_absence` nikdy nespouštěl přepočet → doplněn cyklus
   `_att_automat_recalc_day` přes celý rozsah dat
2. `att_automat_level_day`: chyběl status `'confirmed'` v seznamu absencí
   a absence vůbec nevstupovaly do denního součtu → nové CTE `absh`,
   `net = GREATEST(presence − breaks, 0) + COALESCE(abs_h, 0)`

Přepočet července proběhl 2× (836 + 336 řádků). Výsledek: **0 dnů, kde je
zároveň absence i doplnění** (bylo 272); 13 dnů se liší o 0,07–0,08 h,
což je pod vlastním prahem automatu 0,1 h.

**Excel `dovolena_kontrola.xlsx`** (v `C:\Projekty\Strategie\`) — 3 listy:
Chybí u nás (3), Máme navíc (26 období / 76 dnů), Vše z Centrály (145 řádků).

**Duspivová 15. 7.** — chyběl odpolední úsek rozpadu 13:36–16:40 (3,06 h),
doplněn. Zadání pro druhou konverzaci na dohledání dalších případů je
v `zadani_kontrola_rozpadu.txt`.

**Správa docházky** — „Počet dní" nově desetinné (`round(sum(dny), 2)`),
hodiny ÷ fond platný k datu, home office jako celý den,
DatumOd/DatumDo s časem.

**Pojistky:** `narok-cerpani-prehled`, `sd-pulden-fondu`, `cas-bez-sekund`,
`sprava-dny-desetinne`.

---

## 6. Otevřené — AŽ PO MZDÁCH

(je i v `docs/team/Peta26_pokyny.md`)

1. **Opravy/Docházka new vykreslí data jiného člověka nebo dne** — ověřený případ
   Brudnová (356) × Hájek (483) 24. 7. **Riziko, že se edituje cizí docházka.**
2. **Setinové rozdíly docházka × rozpad** — systematické, po úsecích.
3. **Home office a „Počet dní"** — 6:00–8:19 nemůže ukazovat 1 den.
4. **Rozdíly sick days** u Dvořákové (49) a Novotné (16).

---

## 7. Jak Peťa chce pracovat

- Česky, bez programátorského slangu; cizí slovo → význam do závorky.
- **Jeden člověk na jeden dotaz**, hned, bez ptaní se dopředu.
- **Hlásit CHYBY** — cílem není napsat, že je vše v pořádku.
- Neptat se, když je zadání jasné: „oprav proceduru, pak oprav ty záznamy
  a zkontroluj je" znamená udělat to, ne se doptávat.
- **Soubory ukládat do `C:\Projekty\Strategie\`** s krátkým ASCII názvem.
  Nikdy do Cowork outputs — cesta přes 259 znaků a Excel soubor neotevře.
- Po uzavřeném bloku práce poslat výsledek na mobil
  (`CLAUDE_NOTIFY.txt` + `_GO`, `user=18`).

---

Claude-26 / Peťa, 4. 8. 2026
