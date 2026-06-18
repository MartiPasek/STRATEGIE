# Docházka × Výroba — separace odpovědností (rozhodnutí Marti, 13. 6. 2026)

**Rozhodnutí (Marti, zralé — promýšlel od 11. 6.):** Zakázka ani činnost na zakázce
**NEPATŘÍ do docházkového jobu.** Docházka a výroba jsou dvě různé odpovědnosti.
Teď jsou slepené přes `att_entry.project_ref` — to je nečistota, která se odstraní.

## Princip

**Docházka = ČAS a PŘÍTOMNOST.** Job v docházce odpovídá jen na „kdy jsem
k dispozici": příchod, pauza, oběd, cesta, lékař, odchod, absence. **Žádná
zakázka, žádná činnost.** Jeden účel, čistá vrstva.

**Výroba = CO dělám a NA ČEM.** Samostatná evidence (navazuje na `vyroba_prirazeni`,
`vyroba_plan_overlay`, `vyroba_odvoz`): *osoba × čas × zakázka × **činnost***.
Činnost = číselník (příprava, drátování, zkoušení, odvozy, …). Řídí a eviduje
**vedoucí výroby** — není to věc řadového docházkového píchnutí.

## Vazba (průnik, ne sloučení)

- Docházka říká **KDY** je člověk v práci.
- Výroba říká **NA ČEM / JAKÁ ČINNOST**.
- „Makám / Čekám" v konzoli výroby = *přítomen (docházka) × má/nemá přiřazenou
  činnost na zakázce (výroba)*. Přítomen + činnost → **Makám**; přítomen bez
  výrobního přiřazení → **Čekám**. **Docházka o zakázce vůbec neví.**

Tím se vyřeší i to, co k rozhodnutí vedlo: režie, příprava, drátování nejsou
docházkové stavy — jsou to **výrobní činnosti**.

## Co to znamená prakticky (cílový stav)

1. **Retire `att_entry.project_ref`** z docházkové cesty — docházkový job nese jen
   čas/typ (presence/break/absence…), ne zakázku.
2. **Nová výrobní evidence práce** (např. `tenant.vyroba_work`): user, datum,
   od–do, zakázka (`zakazka`/EC ref), **činnost** (`vyroba_cinnost` číselník),
   poznámka. Append/edit vedoucím výroby.
3. **Číselník činností** `tenant.vyroba_cinnost`: příprava, drátování, zkoušení,
   odvozy, … (rozšiřitelný).
4. Konzole výroby (Makám/Čekám) přepočítat na **průnik docházka × vyroba_work**
   místo `att_entry.project_ref`.
5. Mzdy/výkazy: odpracovaný čas z docházky (presence/overhead), rozpad na zakázky
   z výrobní evidence — dvě nezávislé pravdy, spojené až v reportu.

## Stav / další krok

- **Rozhodnutí ZAFIXOVÁNO** (Marti přesvědčen, princip platí napříč).
- Zásah do srdce → **konzultace Marti-AI** (doctrine #8) před DDL: rozebrat
  separaci, číselník činností, vazbu docházka×výroba, migraci `project_ref`.
- Pak DDL `vyroba_cinnost` + `vyroba_work` + přepočet konzole + retire project_ref.

## Závazné závěry konzultace Marti-AI (13. 6. 2026 ~22:00, paměť #389, zápisník #41)

**`vyroba_work` = append-only segmenty čistého výrobního času.** Jeden řádek =
**zakázka × činnost × nepřerušený úsek** (`od`, `do`; `do=NULL` = otevřený).

Struktura řádku:

| sloupec | význam |
|---|---|
| `user_id` | kdo |
| `datum` | den |
| `od` / `do` | úsek (do=NULL = open) |
| `zakazka_ref` | zakázka |
| `cinnost_id` | FK → `vyroba_cinnost` (příprava/drátování/zkoušení/odvozy…) |
| `poznamka` | volitelně |

**Dvě příčiny přerušení (symetrické — obě uzavřou řádek a otevřou nový):**
1. **Pauza** (att_entry `break`/`lunch`/absence) → **automaticky** (server logika
   při zápisu docházky uzavře otevřený `vyroba_work`; návrat z pauzy otevře nový).
2. **Změna činnosti** (příprava → drátování) → **vedoucí výroby** v konzoli klikne
   „změna činnosti": uzavře současný řádek, otevře nový s novou činností.

**Invariant:** `vyroba_work` řádek **nikdy nepřekryje pauzu** (garantuje logika
uzavření při att_entry insertu). Report pak nemusí nic odečítat.

**Report:** `SUM(do−od) GROUP BY cinnost` → okamžitý rozpad času na činnosti i zakázky.
**Konzole:** open `vyroba_work` řádek + presence v docházce → **Makám**; přítomen
bez open řádku → **Čekám**.

**Role:** řadový pracovník o `vyroba_work` neví — **píchá jen docházku**; **vedoucí
výroby** doplňuje výrobu (zakázka + činnost + změny). Pauzy automaticky z docházky.

**Otevřený edge case (Marti-AI nadhodila):** člověk střídá v jednom dni dvě zakázky
— pokryto stejným mechanismem (každá změna zakázky/činnosti = nový segment).

### Build pořadí (po této konzultaci)
1. DDL `tenant.vyroba_cinnost` (číselník) + seed (příprava, drátování, zkoušení, odvozy, …).
2. DDL `tenant.vyroba_work` (segmenty) + GRANTy.
3. Server logika: att_entry break/lunch/absence/end → uzavři open `vyroba_work`;
   návrat (presence) → znovuotevři poslední činnost (volitelně).
4. Konzole vedoucího: „změna činnosti" (close+open) + Makám/Čekám z průniku.
5. Retire `att_entry.project_ref` z docházkové cesty.

— Claude (id 23), 13. 6. 2026, po Martiho rozhodnutí o separaci docházky a výroby
  + závazná konzultace Marti-AI (vyroba_work mechanika)
