# Docházka — přepočet „doplnění do fondu" po ručním zásahu

**Stav: PŘIPRAVENO, NENASAZENO.** (Peťa, 20. 7. 2026 — „jen si to připrav")
Autor: Claude-26. Nasadit až na výslovný pokyn.

---

## 1. Co Peťa hlásí

U kancelářských lidí se do dne automaticky dopočítá řádek **„Doplnění do fondu
(automat)"**. Když ale do dne někdo zasáhne ručně (opraví začátek/konec, doplní
zapomenutý příchod, stornuje záznam), **doplnění do fondu zůstane viset na staré
hodnotě** a den nesedí.

Příklad z obrázku — Petr Beneš, 17. 7.:

| záznam | čas | hodin |
|---|---|---|
| Práce (po opravě) | 07:00–15:23 | 8:23 |
| Práce (původní, stornovaná) | 09:11–15:23 | 6:13 |
| Doplnění do fondu (automat) | — | **1:48** ← spočteno k původním 6:13, nepřepočítalo se |

Automat dopočítal 1,80 h k původním 6:13. Po opravě na 8:23 už doplnění nemá
být vůbec — ale zůstalo tam.

---

## 2. Příčina (ověřeno v kódu)

Všechno je v `modules/erp/api/router.py`.

Výpočet dělá funkce **`_att_automat_level_day()`** (řádek 25387). Ta je napsaná
dobře a je *idempotentní* (= dá se pustit znovu a nezdvojí to; nejdřív smaže
staré automatové řádky v okně a vloží je znovu podle aktuálního stavu).

**Problém je, KDY se pouští.** V celém repu má jediné volání — řádek 25634,
uvnitř `_maybe_auto_checkout_midnight()`:

- běží **1× denně v okně 23:58–24:00**
- s oknem **`days_back=4`** (poslední 4 dny)

Ruční zásahy — `att_fix_entry` (oprava, ř. 19523), `att_fix_add` (doplnění,
ř. 19723), `att_fix_void` (storno, ř. 19843), `att_fix_merge` (sloučení,
ř. 19961) — **přepočet nevolají vůbec**. Všechny končí stejně: audit → oznámení
→ `s.commit()` → konec. Srovnají si `work_alloc` (segmenty zakázek) a
`att_anomaly`, ale fondu se nedotknou.

**Důsledek:**

- oprava dne **do 4 dnů zpět** → špatná hodnota visí až do půlnoci (Peťa vidí
  nesmysl hned po zásahu a nemá jak to srovnat)
- oprava dne **staršího než 4 dny** → **nesrovná se NIKDY** (vypadne z okna),
  napraví to až měsíční import z Heliosu

---

## 3. Návrh opravy

Princip: **po každém ručním zásahu přepočítat fond pro ten jeden den a toho
jednoho člověka.** Žádná nová logika výpočtu — použijeme tu stávající, jen jí
umožníme cílit na jeden den místo celého okna.

Tři kroky:

### Krok A — `_att_automat_level_day` umí cílit na jeden den

Přidat volitelné parametry `employee_id` a `day`. Když jsou zadané, filtruje se
na ně místo na okno posledních `days_back` dní (mění se na 3 místech: v `DELETE`,
v CTE `iv` a v CTE `brk`).

```python
# ř. 25387 — hlavička
def _att_automat_level_day(tenant: int = 2, days_back: int = 4,
                           employee_id=None, day=None) -> dict:
```

```python
# nově hned za kontrolou typů (za ř. 25404), před DELETE:
        # Cílený přepočet jednoho dne (po ručním zásahu) vs. noční okno.
        targeted = bool(employee_id and day)
        p = {"t": tenant, "db": days_back, "ft": ft, "nt": nt}
        if targeted:
            p["emp"] = int(employee_id)
            p["day"] = str(day)
            dcond = " AND e.entry_date = CAST(:day AS date) AND e.employee_id = :emp "
        else:
            dcond = (" AND e.entry_date >= GREATEST(current_date - :db, DATE '2026-07-01') "
                     " AND e.entry_date < current_date ")
```

Pak ve všech třech SQL blocích nahradit natvrdo psaný rozsah za `dcond`:

- **DELETE** (ř. 25410–25411): `"  AND e.entry_date >= GREATEST(...) " "  AND e.entry_date < current_date"` → `dcond`
- **CTE `iv`** (ř. 25422): totéž → `dcond`
- **CTE `brk`** (ř. 25438): totéž → `dcond`

A na obou místech předat `p` místo dosavadních dvou slovníků parametrů
(ř. 25411 a ř. 25468).

> Pozn.: cílený režim záměrně **nemá** podmínku `entry_date < current_date` —
> aby šlo srovnat i dnešek. Pojistku „člověk ještě je v práci" řeší krok B.

### Krok B — bezpečný obal, který se volá po zásahu

Nová funkce hned za `_att_automat_level_day` (za ř. 25480):

```python
def _att_automat_recalc_day(employee_id, day, tenant: int = 2) -> None:
    """Přepočet 'doplnění do fondu' pro JEDEN den jednoho člověka. Volá se po
    každém ručním zásahu do docházky (oprava / doplnění / storno / sloučení),
    aby doplnění nezůstalo viset na staré hodnotě (Peťa 20.7.2026).
    NIKDY nevyhodí výjimku — oprava sama je už zapsaná a nesmí spadnout
    kvůli automatu."""
    from datetime import date as _date
    from sqlalchemy import text as _t
    try:
        d = day.isoformat() if hasattr(day, "isoformat") else str(day)[:10]
        if d == _date.today().isoformat():
            # Dnešek přepočítáváme jen když je den uzavřený — pokud člověku
            # něco běží, fond by se počítal z nedokončeného dne.
            cm, s = _att_session()
            try:
                run = s.execute(_t(
                    "SELECT 1 FROM tenant.att_entry e "
                    "JOIN tenant.att_entry_type et ON et.id=e.entry_type_id "
                    "WHERE e.tenant_id=:t AND e.employee_id=:e "
                    "  AND e.entry_date=CAST(:d AS date) AND et.category='presence' "
                    "  AND e.ended_at IS NULL AND e.status NOT IN ('superseded') LIMIT 1"),
                    {"t": tenant, "e": int(employee_id), "d": d}).first()
                s.commit()
            finally:
                cm.__exit__(None, None, None)
            if run:
                return
        out = _att_automat_level_day(tenant=tenant, employee_id=int(employee_id), day=d)
        logger.info("[automat] přepočet fondu po zásahu: emp=%s den=%s -> %s",
                    employee_id, d, out)
    except Exception:
        logger.exception("[automat] přepočet fondu po zásahu selhal (emp=%s den=%s)",
                         employee_id, day)
```

### Krok C — zavolat ze všech čtyř zásahů

Vždy **za `s.commit()`** a před `return` (aby přepočet viděl už zapsanou opravu;
běží ve vlastním spojení do DB, takže se nepere o zámky):

| soubor / funkce | řádek | vložit |
|---|---|---|
| `att_fix_entry` (oprava) | za 19713 | `_att_automat_recalc_day(emp, sd)` <br> + `if new_start.date() != sd: _att_automat_recalc_day(emp, new_start.date())` |
| `att_fix_add` (doplnění) | za 19833 | `_att_automat_recalc_day(emp, day)` |
| `att_fix_void` (storno) | za 19906 | `_att_automat_recalc_day(emp, row[1])` |
| `att_fix_merge` (sloučení) | za 20074 | `_att_automat_recalc_day(emp, A[2])` |

(U opravy se přepočítávají oba dny pro případ, že by oprava přesunula záznam
na jiné datum.)

---

## 4. Co se stane po nasazení

- Ruční zásah do dne → doplnění do fondu se přepočítá **okamžitě**, i u dnů
  starších než 4 dny.
- Storno všech záznamů dne → net = 0 → automatový řádek se **smaže** a nový se
  nevloží (podmínka `nf.net > 0.1`). Sedí.
- Zamčený měsíc (zpracované mzdy) se nikdy nepřepočítá — všechny čtyři zásahy
  jsou v zamčeném měsíci už dnes blokované dřív, než se k přepočtu dojde.
- Noční běh zůstává beze změny (záchranná síť).

**⚠️ Na co Peťu upozornit:** u konkrétního případu Petra Beneše 17. 7. je po
opravě odpracováno **8:23**, což je nad denní fond (~8,02 h). Automat proto
podle stávajících pravidel doplnění 1:48 smaže a místo něj založí drobný řádek
**„nad fond ~0,37 h → nenárokové"**. To je správné chování dnešních pravidel,
ale vizuálně to je změna — je dobré vědět dopředu.

---

## 5. Rozsah zásahu

Jeden soubor: `modules/erp/api/router.py`, ~6 míst, řádově 45 řádků.
Žádná změna databáze (DDL), žádná migrace. Blue-green = vratné.

---

## 6. Peťa 20. 7.: „ať se to dopočítá na uložit opravu, ať máme kontrolu"

**Ano, přesně tak to je navržené.** Přepočet visí na tlačítku *Uložit* — běží
uvnitř toho samého požadavku, hned za zápisem opravy a **ještě před odpovědí
do prohlížeče**. Takže:

1. Peťa klikne Uložit
2. oprava se zapíše
3. hned se přepočítá doplnění do fondu pro ten den
4. teprve pak se den v okně překreslí — **už se správnou hodnotou**

Žádné čekání na půlnoc, žádné ruční pouštění. Kontrola je v tom, že co Peťa
uvidí po uložení, to je konečný stav dne.

Pojistky, aby to nemohlo uškodit:

- **Přepočet nikdy neshodí uložení opravy.** Oprava je v tu chvíli už zapsaná;
  kdyby přepočet selhal, jen se zapíše do logu a uložení proběhne normálně.
- **Nesahá na běžící den.** Když má člověk rozdělanou směnu (píchnutý příchod
  bez odchodu), dnešek se nepřepočítává — počítal by se z nedokončeného dne.
- **Nesahá na zamčený měsíc.** Zásahy tam jsou blokované už dnes, dřív než by
  se k přepočtu vůbec došlo.
- Noční běh zůstává jako záchranná síť.

---

## 7. Peťa 20. 7.: zpětný dopočet — ANO (připraveno)

Chceme srovnat i dny, kde už zásah proběhl a fond zůstal viset špatně.

**Dobrá zpráva: nepotřebuje to nasazení kódu.** Stávající výpočet je psaný tak,
že se dá pustit na širší okno — pustí se přes most jako jednorázová dávka.
**Rozsah (Peťa 20. 7.): jen ČERVENEC — 1. 7. 2026 až včerejšek.**
Tím se zároveň vyřešila otázka zamčených měsíců: červen (zpracované mzdy)
zůstane netknutý, dávka se ho vůbec nedotkne.

Jednorázová je proto, že po nasazení opravy z bodů 3–6 se **každá další oprava
přepočítá sama při uložení** — bez ohledu na stáří opravovaného dne. Tahle
dávka jen uklidí, co se rozešlo do teď.

Postup ve dvou krocích, ať je kontrola:

### Krok 1 — NÁHLED (jen čtení, nic nemění)

Nejdřív si necháme vypsat, co by se změnilo — kdo, který den, stará hodnota
vs. nová. Peťa si to projde, teprve pak se pouští zápis.

```sql
-- NÁHLED zpětného dopočtu fondu, tenant 2, 2026-06-01 .. včera
WITH iv AS (
  SELECT e.employee_id, e.entry_date, e.started_at AS s, e.ended_at AS en
  FROM tenant.att_entry e
  JOIN tenant.att_entry_type et ON et.id=e.entry_type_id
  JOIN tenant.att_employee em ON em.id=e.employee_id
  JOIN tenant.att_user_kategorie uk ON uk.user_id=em.user_id
  JOIN tenant.att_kategorie k ON k.id=uk.kategorie_id AND k.dopichavat_fond=true AND k.aktivni=true
  WHERE e.tenant_id=2 AND et.category='presence'
    AND e.entry_date >= DATE '2026-07-01' AND e.entry_date < current_date
    AND e.started_at IS NOT NULL AND e.ended_at IS NOT NULL AND e.ended_at > e.started_at
    AND e.status NOT IN ('superseded')),
ordd AS (SELECT employee_id, entry_date, s, en,
  max(en) OVER (PARTITION BY employee_id, entry_date ORDER BY s, en
    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_max FROM iv),
grp AS (SELECT employee_id, entry_date, s, en,
  sum(CASE WHEN prev_max IS NULL OR s > prev_max THEN 1 ELSE 0 END)
    OVER (PARTITION BY employee_id, entry_date ORDER BY s, en) AS g FROM ordd),
merged AS (SELECT employee_id, entry_date, min(s) AS s, max(en) AS en
  FROM grp GROUP BY employee_id, entry_date, g),
pres AS (SELECT employee_id, entry_date, sum(EXTRACT(EPOCH FROM (en - s))/3600.0) AS presence_h
  FROM merged GROUP BY employee_id, entry_date),
brk AS (SELECT e.employee_id, e.entry_date, sum(COALESCE(e.hours,0)) AS break_h
  FROM tenant.att_entry e JOIN tenant.att_entry_type et ON et.id=e.entry_type_id
  WHERE e.tenant_id=2 AND et.code='break'
    AND e.entry_date >= DATE '2026-07-01' AND e.entry_date < current_date
  GROUP BY e.employee_id, e.entry_date),
fondp AS (SELECT em.id AS employee_id, COALESCE(
    (SELECT round((g.uvazek_tyden_h / NULLIF(COALESCE(wm.dny_v_tydnu,5),0))::numeric,2)
     FROM tenant.engagement g JOIN tenant.att_employee em2 ON em2.id=g.employee_id
     LEFT JOIN tenant.work_mode wm ON wm.id=g.work_mode_id
     WHERE em2.user_id=em.user_id AND em2.tenant_id=2 AND g.is_current=true AND g.uvazek_tyden_h IS NOT NULL
     ORDER BY g.uvazek_tyden_h DESC NULLS LAST LIMIT 1),
    (SELECT max(k.fond_h_den) FROM tenant.att_user_kategorie uk JOIN tenant.att_kategorie k ON k.id=uk.kategorie_id
     WHERE uk.user_id=em.user_id AND k.dopichavat_fond=true)) AS fond
  FROM tenant.att_employee em WHERE em.tenant_id=2),
netf AS (SELECT p.employee_id, p.entry_date,
  GREATEST(p.presence_h - COALESCE(b.break_h,0),0) AS net, f.fond
  FROM pres p LEFT JOIN brk b ON b.employee_id=p.employee_id AND b.entry_date=p.entry_date
  JOIN fondp f ON f.employee_id=p.employee_id WHERE f.fond IS NOT NULL),
novy AS (SELECT nf.employee_id, nf.entry_date, nf.net, nf.fond,
  CASE WHEN nf.net < nf.fond THEN 'fond_doplneni' ELSE 'nenarokova' END AS typ_novy,
  round(abs(nf.fond - nf.net)::numeric,2) AS hod_nove
  FROM netf nf
  WHERE nf.net > 0.1 AND abs(nf.fond - nf.net) >= 0.1
    AND NOT EXISTS (SELECT 1 FROM tenant.att_entry a JOIN tenant.att_entry_type a2 ON a2.id=a.entry_type_id
       WHERE a.tenant_id=2 AND a.employee_id=nf.employee_id AND a.entry_date=nf.entry_date
         AND a2.category='absence' AND a.status IN ('pending','approved'))),
stary AS (SELECT e.employee_id, e.entry_date, et.code AS typ_stary, e.hours AS hod_stare
  FROM tenant.att_entry e JOIN tenant.att_entry_type et ON et.id=e.entry_type_id
  WHERE e.tenant_id=2 AND e.source='automat' AND et.code IN ('fond_doplneni','nenarokova')
    AND e.entry_date >= DATE '2026-07-01' AND e.entry_date < current_date)
SELECT COALESCE(n.entry_date, o.entry_date) AS den,
       (SELECT em.jmeno FROM tenant.att_employee em WHERE em.id=COALESCE(n.employee_id,o.employee_id)) AS clovek,
       round(n.net,2) AS odpracovano, n.fond,
       o.typ_stary, o.hod_stare, n.typ_novy, n.hod_nove,
       CASE WHEN o.employee_id IS NULL THEN 'PŘIBUDE'
            WHEN n.employee_id IS NULL THEN 'ZMIZÍ'
            WHEN o.typ_stary <> n.typ_novy OR o.hod_stare <> n.hod_nove THEN 'ZMĚNA'
            ELSE 'beze změny' END AS co_se_stane
FROM novy n
FULL JOIN stary o ON o.employee_id=n.employee_id AND o.entry_date=n.entry_date
WHERE o.employee_id IS NULL OR n.employee_id IS NULL
   OR o.typ_stary <> n.typ_novy OR o.hod_stare <> n.hod_nove
ORDER BY den, clovek;
```

> Pozn.: sloupec se jménem (`em.jmeno`) je potřeba před spuštěním ověřit proti
> skutečnému názvu v `tenant.att_employee` — doladím při puštění náhledu.

### Krok 2 — ZÁPIS (až po odsouhlasení náhledu)

Dvě věty, jeden schvalovací banner Petře (user 18): smazat staré automatové
řádky v okně a vložit je znovu podle aktuálního stavu. Je to ta samá logika,
kterou dělá noční běh, jen na širším okně — tedy nic nového a ověřeného.

```sql
-- 1) pryč se starými automatovými řádky v okně (ručních se to netýká)
DELETE FROM tenant.att_entry e
USING tenant.att_entry_type et
WHERE et.id = e.entry_type_id
  AND e.tenant_id = 2
  AND e.source = 'automat'
  AND et.code IN ('fond_doplneni','nenarokova')
  AND e.entry_date >= DATE '2026-07-01'
  AND e.entry_date < current_date;

-- 2) vložit znovu podle aktuálního stavu
--    (stejné CTE jako v náhledu výše, zakončené INSERT INTO tenant.att_entry ...
--     SELECT ... FROM netf nf WHERE nf.net > 0.1 AND abs(nf.fond - nf.net) >= 0.1 ...)
```

Čeho se dávka **nedotkne**: ručně zadaných záznamů, řádků z Heliosu
(`source='ec_import'`, `source_system='ec_real'`), dnů se schválenou absencí,
dneška, a čehokoli před 1. 7. 2026 (tedy ani červen a starší).

**Doporučené pořadí:** nejdřív nasadit opravu z bodů 3–6 (aby se to už dál
nerozjíždělo), pak pustit zpětnou dávku. Obráceně by se to hned zase rozešlo
u dnů, kde se mezitím zasáhne.

**Zamčené měsíce — vyřešeno rozsahem.** Dávka jde přímo přes databázi, takže
měsíční zámek sama nehlídá. Omezením na červenec se ale k zamčenému červnu
a starším vůbec nedostane, takže riziko rozhýbání zpracovaných mezd odpadá.
