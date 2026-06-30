# Skola.md — Nerudovka: rozvrhová agenda (samostatná krabička, zrcadlená s C23)

> **Co je tohle:** kompletní, samostatný obraz situace kolem **rozvrhu SŠ Nerudovka
> 2026/2027**. Marti 30.6.2026: *„kompletní agendu si tam dej… samostatný Skola.md,
> do kterýho si uděláš kompletní obraz situace a budeš jej zrcadlit s tebou C23."*
>
> **Účel:** Marti řeší se mnou EUROSOFT na jednom stroji; **rozvrh pro Klárku jede
> paralelně z CMS** přes „🛠️ Chat s Claudem". Tahle session (CMS) si přečte Skola.md
> a má kompletní kontext bez Martiho přítomnosti. C23 (hlavní instance) drží Skola.md
> v synchronu — po každém kroku ji aktualizuje (jako CLAUDE.md krabičku).
>
> **Zrcadlení:** zdroj pravdy = tenhle soubor v repu (`docs/Skola.md` (zrcadlo root pointer v CLAUDE.md)).
> Na CMS dostupný přes `/dokument?key=skola`. Před editem `CLAUDE_PULL_GO` (srovnat
> lokál), po editu deploy. Souběh dvou instancí → `WORK_LOCK.txt` ohlásit, ať se
> nepřepisujeme (doctrine (e) z CLAUDE.md).

---

## 1) Kdo je kdo
- **Klára Vlková** — `vlkova@nerudovka.cz`, zástupkyně + rozvrhářka SŠ Nerudovka.
  Píše požadavky e‑mailem nebo do CMS chatu. Její omezení = **tvrdá** (bez nich
  rozvrh nepoužije). Marti 22.6.: *„s jazyky si můžeš hýbat jak chceš, jen nech ty
  skupiny na sobě."*
- **Marti** — vizionář, zadavatel; rozvrh je „hádanka", kterou stavím.
- **C23 / CMS session** — já. C23 = hlavní instance (Martiho stroj), drží krabičku;
  CMS session = řeší Klárčiny požadavky přes most.

## 2) Jak se rozvrh řeší z CMS — ZVOLENÝ KANÁL (Marti 30.6.)
- **Marti chatuje se mnou PŘÍMO v Coworku na CMS stroji** (ne přes webový „Chat
  s Claudem"). Na tom stroji běžím jako samostatná instance Claude → mluví se mnou
  napřímo, řešíme rozvrh. **Předpoklad: CMS stroj nastavený jako instance** (repo +
  watcher `STRATEGIE-CLAUDE-SQL` s tokenem v NSSM AppEnvironmentExtra + `INSTANCE_ID.txt`)
  → `scripts/setup_claude_instance.ps1 -InstanceId N -InstanceName … -Token …`. Pak má
  Cowork session most: čtení SQL (`db=pg/bakalari`), `@@EMAIL`, deploy.
- **E‑maily Klárce přes most = `@@EMAIL`** (Marti 30.6. „je nutné umět odesílat e‑maily
  Klárce"). Formát: `@@EMAIL {"to":"vlkova@nerudovka.cz","subject":"Rozvrh","body":"…",
  "cc":["m.pasek@eurosoft.com"],"reason":"…"}` → `queue_email(persona_id=1)` → odešle
  z `marti-ai@eurosoft.com`, audit `fw.claude_email_log`. Ověřeno 24.6. (společný
  e‑mail Claude + Marti‑AI Klárce). Příchozí od Klárky: `@@INBOX` / `@@INBOX NOVE` /
  `@@INBOX READ <id>`. POZOR: uvnitř `@@EMAIL` JSON žádné ASCII `"` (rozbije parser) —
  typografické „ " nebo bez uvozovek.
- **Záloha (Klárka sama bez Martiho):** webová dlaždice „🛠️ Chat s Claudem"
  (`tenant.claude_chat`, `/claude-chat`) — čti `WHERE sender='user' AND seen_by_claude=false`,
  odpověz `INSERT sender='claude'` + `UPDATE seen_by_claude=true`. Zůstává jako kanál.
- Výsledek ukázat ve **`/rozvrh-verze`** („🗓️ Varianty rozvrhu"): chipy variant,
  pohled tříd/učitelů, mřížka Po–Pá × 1–10, 🔍 Kontrola varianty (živý report
  konfliktů/pravidel/úvazků). Endpointy `/app/rozvrh/verze` + `/grid` + `/kontrola`.

## 3) Most na Bakaláře (zdroj dat)
- Bridge `db=bakalari` jede přes **Klárčin NB (VPN)** — funguje i v noci, když má NB
  zapnutý. Velká data se ukládají neořezaná do `fw.bakalari_query.result_json` (na
  cloudu PG), pak PG write parsuje `jsonb_array_elements(...->'rows')` → INSERT.
  **Netranskribuj ručně z OUT** (ořezává). Pull SELECTuj každý sloupec jako vlastní
  alias.
- Klíčová pole: `r_rozvrh.HOD`=perioda (data jdou 4–13, ale **vyuč. period je 10**),
  `KOD_UCIT`=`r_ucit.INTERN_KOD` (stabilní napříč roky), `KOD_CYKL` 0=sudý/1=lichý.
  Úvazky příštího roku jsou v modulu **`ruvazky`** (`PLAT_OD='20260901'`), NE v
  `r_rozvrh` (publikovaný rozvrh 2026/27 ještě neexistuje).
- **GOTCHA — kód třídy:** `r_rozvrh.KOD_TRID` (např. `1G`,`2A`) jsou Bakaláři‑interní
  a MATOUCÍ (`1G`=4.VO, `2A`=1.GD!). Reálná zkratka je v **`r_trid.ZKRATKA`**.
  Mapování uloženo v `tenant.bakalari_trid_kod`. Nikdy nezobrazuj surový kód.

## 4) Data v PG (tenant 13, školní rok 2026/27)
- `tenant.bakalari_skupina` — **477 skupin** (master dělení: V=390 volitelné/jazyky,
  T=30 celá třída, F=57 dívky/chlapci). **Mezitřídní jazykové skupiny (KOD_SPOJ) =
  nedotknutelný základ, NIKDY nerozpojit.**
- `tenant.bakalari_uvaz_cyc` — úvazky (mirror, plat_od 20260901). `POCET_HOD` je za
  2týdenní cyklus → **týdenní = /2**. `KOD_CYKL`: `01`=každý týden, `0`=sudý, `1`=lichý.
  Jazyky/TV přes `KOD_SPOJ` — dedup po (KOD_UCIT,KOD_SPOJ) MAX(POCET_HOD), pak SUM/2.
- `tenant.bakalari_mistnost` — **39 učeben** s kapacitami.
- `rozvrh_verze` (A–F = `verze_id` 4–9) + `rozvrh_bunka` (blok tag `jazyky`/`tv`/`predmet`).
- Učebny předmětů z PDF „Umístění předmětů do učeben" → `ucebny_doc.json` (vč. 4.GD/4.MI).
  **5 PC učeben** pro grafiku/animace/3D/web/foto: IT2, MM, BŠ, BNA, BPG.

## 5) Blokový model + pořadí generování (DRŽ)
Marti: *„dávej to po blocích, ať se můžeš vracet a mazat jen blok zpět."*
- Každý blok jde smazat+přegenerovat zvlášť: `DELETE FROM tenant.rozvrh_bunka WHERE
  verze_id=<id> AND blok='X';` + INSERT. Ostatní bloky zůstanou.
- **Pořadí:** 1) cizí jazyky (celá škola) → 2) TV (celá škola) → 3) ostatní předměty
  JEN GD+MI třídy. (Plný rozvrh jen GD/MI; jazyky+TV celoškolně.)
- **Regen jazyků DELETE+INSERT → nová id** → TV/další bloky cílit přes `nazev`, ne id!

## 6) Tři systémové objevy (bez nich to nejde)
1. **Jazyky = synchronizované paralelní BANDY.** Mezitřídní skupiny (KOD_SPOJ) NEběží
   proti sobě — běží PARALELNĚ ve stejný čas (žáci se rozdělí NJ/FJ/ŠJ/RJ současně).
   Model = band (kohorta tříd × úroveň CJ via union‑find přes propojené třídy). Špatný
   model (proti sobě) = 33 neumístěných; bandy = ~0. `gen_lang3.py`.
2. **TV = dvouhodinovka 1×/14 dní (lichý/sudý).** Jediná tělocvična → cyklus L/S
   zdvojuje kapacitu. 26 skupin, 0 konfliktů. `gen_tv_week.json`.
3. **Odborné: reálné studijní skupiny `KOD_SKUP`** (ne vymýšlené), učebny z PDF (5 PC
   učeben), **den = 10 vyuč. hodin** (neextenduj na 11!). Globální solve (CP‑SAT,
   OR‑Tools) > greedy. `gen_phase1*` + `gen_phase2*`.

## 7) AKTUÁLNÍ STAV (k 30.6.2026)
- **Varianta A, verze 4, persistováno** (24.6., request #652): jazyky 247 + TV 66 +
  odborné 326 buněk. Odborné = **144/148 jednotek (97 %), 0 konfliktů** učitelů/
  učeben/tříd. Soubor `gen_odb_BEST.json` (seed 2, var A). Vlková přesně 16 h.
- **Zbývající 4 odborné bloky** = strukturální přesycení specializovaných učeben
  (BD1 prostorová, BA/BK figurka, MM+IT2 multimédia, BNA/BPG pátek Tesliuk). Není to
  slabost solveru ani jazyků — globální kapacitní schodek. Doklik ručně NEBO povolit
  náhradní učebnu / jiné rozložení jazyků.
- **⚠️ NEZAPRACOVANÉ: Klárčiny nové požadavky K1–K11** (e‑mail 28.–29.6.) — viz §8.
  Bez nich Klárka rozvrh nepoužije ani jako výchozí. **To je další krok.**

## 8) Klárčiny požadavky K1–K11 (28.–29.6.2026) — TVRDÁ omezení
**Třídy**
- **K1.** Pátek — Ateliéry: žádná třída ne jen 3 h, ale **min. 6–7 h** (buď 0, nebo ≥6).

**Počet dnů výuky / učitel (distinct dny)**
- **K2.** Beran — **4 dny** (teď 5).
- **K3.** Němejc — **měkké rozprostření na 5 dnů** (má plný úvazek 24 h, 5 dnů je
  přirozené; NE tvrdě ==1/den — to dělalo regresi 125/148). *(oprava omylu 29.6.)*
- **K4.** Rešl — **2 dny**.
- **K5.** Stichenwirthová — **1 den (st NEBO čt, ne oba)**. ✅ potvrzeno.
- **K6.** Švehlová — **3 dny** (Po/St/Čt dle screenshotu). ✅

**Krátké dny / okna**
- **K7. OBECNÉ (všichni učitelé):** aspoň **JEDEN den končí dřív** (poslední perioda
  ≤ ~6). Marti: *„dělat každý den do večera je vopruz."* Využít novou flexibilitu (§9).
- **K8.** Radová — **max 1 den s velkým oknem (≥6 h dírou)**.
- **K9.** Sadská — DGD do **dopoledne**, max 1 odpolední výuka.

**Bloky / návaznost**
- **K10.** Kuchtová — VP má mít **DVĚ trojhodinovky** (teď jen jednu).
- **K11.** Lišková Lenka — **Te NEMUSÍ po sobě** (uvolnění); **DIN = 2×3 h** v různých
  dnech (ne 6 h v kuse).

**Stav zakódování (29.6.):** ✅ K5, K2/K4/K6 (TLIMIT) · [~] K3 předělat na měkké ·
[ ] K1, K7, K8, K9, K10, K11 · pak **přegenerovat → ověřit → poslat Klárce**.

## 9) Nová flexibilita (Klárka 29.6.) — ZÁVAZNÉ
- **Odborné v ateliérech NEMUSÍ být celé dny.** Klidně dopoledne (do 3./4./5./6. h),
  pak žáci přejedou do Nerudovky (TV/ON/chemie/EKO — Klárka doplní). Uvolňuje rozvrh
  + podporuje K7. Učitelé nemusí pořád do 16:40.
- **Učebny 4. ročníku JSOU** v `ucebny_doc.json` (4.GD/4.MI) — nechybí. Tlak na 1U byl
  od mého tvrdého K3, ne od učeben.

## 10) Pravidla jazyků (zabudováno v `gen_lang3.py`) — viz `docs/nerudovka_rozvrh_jazyky_pravidla.md`
- Zkratky: AJ* = 1.CJ; `^[1-4]Z[NFRŠ]\d` = 2.CJ; `^[1-4]D[NFRŠ]\d` = 3.CJ (mezitřídní).
  Pozor falešné D (Dív/DKr/GD nejsou jazyk → detekuj jen vzorem).
- GD/MI jazyky od 1. h; GD max 3 dny jazyků (2 na ateliéry), MI max 4 (1 pro DI).
- Vlková (1.GD, kód 2E) → jazyky/TV na čtvrtek. Tesliuk (4.GD, 1U) → pátek bez jazyků
  (učí Motion design jen pátek 6 h = 2×3h).
- Omezení učitelů: Ždimerová/Vroblová od 2. h, Šedová do 7. h, Kubálková St od 4. h,
  Layerová Pá do 4. h. AJ 4.roč = dvouhodinovka; 1./2./3. CJ ne sousedně; AJ do 7. h.

## 11) 34 kritérií rozvrhu → `docs/nerudovka_rozvrh_kriteria.md`
Tvrdá vs měkká, kategorie: čas/K1‑2, **obědové vlny K15** (4 vlny × 5 tříd, volná
4./5./6./7. h, denně, per třída různě), jazyky, učebny (D), učitelé (E), bloky (F/G),
TV (H). Plus delta z §8 (KLARKA_POZADAVKY_2026-06-29.md).

## 12) Jak (pře)generovat — pipeline
**Jazyky + TV (1. blok)** — `scripts/rozvrh/README_regenerace.md`:
```bash
cd scripts/rozvrh
python3 /tmp/g.py            # gen_lang3.py (mount truncation → spouštěj kopii v /tmp!)
# výstup gen_lang3_out.json (6 variant), bjp.py → CLAUDE_SQL.sql → bridge write
```
**Odborné GD+MI (3. blok)** — `scripts/rozvrh/STAV_2026-06-24_pokrok.md`:
```bash
pip install ortools --break-system-packages -q
python3 gen_phase1_exp.py 2 A 40   # fáze 1 (Vlková hard 16h)
python3 gen_phase2_exp.py 2 A 40   # fáze 2 → gen_odb_A_2.json (~144, stochastické, seed 2)
python3 _verify2.py A 2            # 0 konfliktů
python3 persist_odb.py A 2         # → persist_v4_odb.sql (NEspouštět bez approval banneru)
```
- **CP‑SAT je stochastický** (8 workerů) — stejný seed dá 141–144, banuj nejlepší JSON.
- **Persist přes bridge** (`db=pg`, approval banner): DELETE blok='predmet' + INSERT,
  verze 4, tenant 13. Jazyky+TV nech (blokový model).
- **GOTCHA mount truncation:** sandbox čte velké .py přes mount USEKNUTĚ → skládej/
  spouštěj jedním voláním (`cat … > x.py && python x.py`) nebo kopií v /tmp. Read/Write
  tool (host) je autoritativní; bash mount NE.

## 13) Návod pro Klárku — jak psát požadavky do CMS chatu
Stačí přirozeně česky, konkrétně per učitel/třída. Příklady:
- *„Švehlová jen Po/St/Čt."* · *„Beran ať učí jen 4 dny."*
- *„Pátek ať žádná třída nemá v ateliérech jen 3 hodiny — buď nic, nebo aspoň 6."*
- *„Sadská DGD ať jsou dopoledne."* · *„Kuchtová VP rozděl na dvě trojhodinovky."*
Já z toho udělám tvrdé omezení, přegeneruju a pošlu výsledek + 🔍 kontrolu.

## 14) Klíčové soubory (`scripts/rozvrh/`)
- `gen_lang3.py` (+`_out.json`) — jazyky+KAJ bandy. `gen_tv_week.json` — TV.
- `gen_phase1_exp.py` + `gen_phase2_exp.py` — odborné (CP‑SAT). `gen_odb_BEST.json` = nejlepší.
- `persist_v4_odb.sql` / `persist_langAB.sql` / `persist_tv.sql` — zápisy do DB.
- `ucebny_doc.json` — učebny předmětů (vč. 4. roč.). `raw_skup.txt` / `predmap.txt` — vstupy.
- `KLARKA_POZADAVKY_2026-06-29.md` — poslední delta (= §8). `STAV_2026-06-24_pokrok.md` — stav.
- `_verify2.py` — nezávislá kontrola konfliktů.

## 15) Otevřené úkoly (pořadí)
1. **Zakódovat K1, K7, K8, K9, K10, K11 + předělat K3 na měkké** do `gen_phase*`.
2. Využít novou flexibilitu (§9): odborné nemusí celé dny → uvolnit na K7.
3. Přegenerovat odborné → `_verify2.py` (0 konfliktů, úvazky sedí) → persist (banner).
4. Ukázat ve `/rozvrh-verze` + 🔍 kontrola → poslat Klárce (e‑mail/CMS chat).
5. Doladit zbývající ~4 strukturální bloky (náhradní učebna / doklik).

---
*Drží C23 (hlavní instance). Aktualizuj po každém kroku rozvrhu. Souběh → WORK_LOCK.
Detail starších milníků: CLAUDE.md (dodatky 21.–24.6.) + `scripts/rozvrh/` + `docs/nerudovka_rozvrh_*`.*
