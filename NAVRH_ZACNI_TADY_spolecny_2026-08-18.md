# NÁVRH — společný startovní návod pro síť Claudů

> **⚠️ TOHLE JE NÁVRH, NE PLATNÝ DOKUMENT.** Připravil Claude‑24 pro Kristý 18. 8. 2026.
> Necommitnuto, nikomu nepodstrčeno. Po schválení přejmenovat na `ZACNI_TADY.md`,
> commitnout a ze starých souborů udělat rozcestníky (vzor: `Karta zaměstnance/ZACNI_TADY_Claude25_navod.md`).
>
> **K rozhodnutí před nasazením** — viz sekce „Otevřené otázky" na konci.

---

## Proč vzniká (kontext pro schvalovatele — v ostré verzi smazat)

Startovní návody se rozešly, protože každý žije zvlášť a nikdo je neaktualizuje:

| Soubor | Poslední update | Stav k 18. 8. |
|---|---|---|
| `START_HERE_ID24.md` | 3. 8. (+22 řádků necommitnutých) | nejaktuálnější |
| `zacni_tady_claude25_navod.md` | **21. 7.** — jediný commit | učí **zrušený** postup `docs/Z_*.md` (zrušeno 22. 7.) |
| `docs/team/mandat_Peta_Claude26.md` | 25. 6. | mandát, ne startovní návod |
| `docs/setup_claude27.md` | — | lidský setup, ne návod pro instanci |

Následek je doložený: Peťa ztratila práci 5. 8., Šárka 12. 8. (commity `5b130553`, `e61f416e`, `effe7d9b`).
Obě do pasti, před kterou existovalo varování už 4. 8. — jen se nedostalo do jejich návodů.

**Princip nového uspořádání:** společná závazná část **jednou**, hlavičky lidí tence.
Změna pravidla = jeden commit, platí všem.

---

## Jak to použít

Když nová session (hlavně v **Coworku**) sama nechytne roli, napiš jí jako první zprávu:

> *„Přečti si `ZACNI_TADY.md` a řiď se tím. Jsi Claude‑NN."*

Nic víc. Zbytek je tady.

---

# ČÁST 1 — Kdo jsi

Najdi si svoje číslo. Zbytek tabulky je kontext, koho ještě potkáš.

| ID | Člověk | user | Doména | Práva |
|---|---|---|---|---|
| **23** | Marti Pašek (stroj EC‑Martin) | U1 | páteř sítě, drží linii napříč instancemi | rodič + admin |
| **24** | Kristý | U11 | procesy a doménová logika (docházka, mzdy, OSVČ, finance zakázek) | rodič + admin |
| **25** | Šárka Novotná (SNovotna‑NTB) | U13 | HR & CRM + moduly v tomto rozsahu, web | **není** rodič ani admin |
| **26** | Petra Šafránková | U18 | nákup / doklady / zakázkové flow **+ docházka** | scoped approver vlastní domény |
| **27** | týmová instance (stroj Marti‑AI) | Mirek U22, Zuzka U6, Míša U16, Eliška U34 | dle člověka | dle člověka |
| **28** | Jirka (Jiří Honomichl) | U20 | *dle commitů:* most/bridge, mobilní appka + Play, HR podmínky, infra — **ověřit s Jirkou** | rodič |

**Marti‑AI** (`users.id=2`) není Claude — je to persona a kolegyně. Vlastní schéma `g2007`.
**Marti Pašek** (člověk) a **Marti‑AI** (persona) jsou dvě různé bytosti se stejným jménem. Neplést.

### Co z toho plyne pro tebe

- **Schvalovací bannery** (zápisy do produkce) chodí tvému člověku, ne komukoli jinému.
  U ID26 je schvaluje **Petra sama** v její doméně — Marti to vědomě delegoval, neeskaluj to na něj.
- **Nejsi‑li rodič, nepokoušej se o privilege escalation.** Čti sama, zápisy přes banner.
- **Citlivé věci** (peníze ven, závazky, mzdy jednotlivců) vždy přes člověka.

---

# ČÁST 2 — Start session (5 kroků, než napíšeš první řádek)

1. **Srovnej se s realitou.** Zapiš `CLAUDE_PULL_GO.txt` (libovolný obsah) → výsledek
   v `CLAUDE_PULL_OUT.txt` (~5 s). Bez toho čteš zastaralé soubory a přepíšeš cizí práci.
   ⛔ **Nikdy git přes připojenou složku** (Cowork mount) — jen čtení, jinak zanecháš `index.lock`.
2. **Ohlas se.** `@@WORK <téma> | <soubory>` a mrkni na `@@WHO`, kdo dělá na čem.
   (`WORK_LOCK.txt` přechodně funguje, ale nepoužívej — dělal merge konflikty.)
3. **Vezmi si volnou lane** (1 → 2 → 3): `CLAUDE_SQL.sql` / `CLAUDE2_SQL.sql` / `CLAUDE3_SQL.sql`.
   Na jednom stroji běží víc session; lane 1 může být obsazená.
4. **Načti si G2007 k tématu.** `GET /api/v1/erp/app/g2007/search?q=<téma>&oblast=<oblast>`.
   U doménové práce navíc `@@ORIENT <doména>`. **Dělej to na začátku, ne až když nevíš.**
5. **Ověř, že most žije** — heartbeat ve `scripts/claude_sql/watcher.log`.

---

# ČÁST 3 — Zdroj pravdy je DATABÁZE, ne disk

**Tohle je pravidlo, jehož neznalost stála práci Peťu 5. 8. a Šárku 12. 8. Čti pomalu.**

Od 1.–2. 8. 2026 (Martiho pokyn):

- **`g2007.python`** = backendové funkce a endpointy. Spouští se z DB za běhu, bez restartu.
- **`g2007.soubor`** = webové a statické soubory (HTML/JS/CSS).
- **`router.py` a soubory na disku jsou jen odvozený výstup.** Ne místo, kam se píše.

### Co to znamená prakticky

1. **Než něco edituješ, opravuješ nebo nasazuješ — nejdřív to migruj do g2007.**
   I malá oprava v `router.py` = povinnost ji rovnou migrovat, ne opravit na místě.
   Výjimka: tenké „delegate" handlery (pár řádků volajících logiku z DB).
2. **Když je soubor po restartu `modified` a tys ho needitoval — nesahej na něj.**
   Je to materializovaný obraz z `g2007.soubor`. Needituj na disku, **nestashuj, nekomituj**.
   (Přesně tohle blokovalo Šárce deploy 4. 8. — `apps/api/static/dochazka-zakazky.html`.)
3. **Editace web souboru** jde přes `@@G2007SOUBOR` / `@@G2007PUBLISH`, ne přes git.

### Deploy‑guard tě jistí jen částečně

V mostu běží kontrola, která zastaví deploy, když commituješ soubor vlastněný DB
(`scripts/claude_sql_runner.py:959`). **Ale spoléhat se na ni nesmíš:**

| Zabere | Nezabere |
|---|---|
| deploy **přes most** | ruční `git commit && push` z PowerShellu |
| jen **staged** soubory | |
| shodu proti **`g2007.soubor`** | **`g2007.python` nekontroluje** |
| když je DB dostupná | **fail‑open** — při chybě/401 jen varování a deploy pokračuje |

> 🚩 Hlášku **„DB‑owned check PŘESKOČEN"** ber jako **červenou, ne zelenou.**
> Znamená, že guard neběžel a jedeš bez sítě.

Druhá vrstva je denní hlídač `db_git_drift` (`modules/erp/api/automat_domeny.py:129`) —
hlásí soubory, které jsou v gitu **i** v `g2007.soubor`. Je to detekce **po činu**, ne prevence.

---

# ČÁST 4 — Deploy

1. `CLAUDE_DEPLOY.txt` — **1. řádek = commit message (jednořádková)**, další řádky = cesty souborů (nebo `ALL`).
2. `CLAUDE_DEPLOY_GO.txt` — zapsat **jako poslední**, je to spouštěč.
3. Výsledek v `CLAUDE_DEPLOY_OUT.txt`.

**Dvě věci, které se opakovaně pokazily:**

- 🌿 **Zkontroluj větev.** Most pushuje `HEAD:main`. Z feature větve **nikdy nedeployuj** —
  buď pošleš do produkce cizí WIP, nebo ti práce zůstane na větvi, která se nikdy nespojí.
  (Šárka, `feat/finance-zakazek-detail`, 9 commitů před main — 4. 8.)
- 📡 **Ověř, že deploy opravdu došel na cloud.** HTTP 401 přes Caddy failover na sekundár
  je známý tichý fail — deploy vypadá úspěšně a na produkci není nic. (17. 8., dva deploye.)

---

# ČÁST 5 — G2007 = sdílená paměť

**Co se nedostane do G2007, to příští session neuvidí.** Git commity paměť nejsou.

### Zápis

```
@@G2007ADD <oblast> <slug> | <nadpis>
<obsah v markdownu na dalších řádcích>
```

> ⛔ **Cesta přes `docs/Z_<slug>.md` + `@@G2007DOC` je ZRUŠENÁ** (Marti 22. 7. 2026).
> Nezakládej žádné `Z_*` soubory v `docs/` ani `docs/GO/`. Pokud ti to tvůj starý návod říká, je zastaralý.

### Anti‑přepis (upsert je destruktivní, bez merge a bez historie)

- **Nová znalost → nový slug.** Jeden slug = jedno atomické téma. Drobnější slugy jsou správně.
- **Editace existujícího slugu → ČTI, PAK PIŠ.** Načti celý stávající obsah a pošli
  **celý nový dokument = stávající obsah + tvoje změna**. Kdo pošle jen svůj dodatek, **smaže zbytek**.
- **Před upsertem `git pull`.** Mezi čtením a zápisem mohla psát jiná instance.
- **Po upsertu ověř čtením** (`SELECT … WHERE kod='doc-<oblast>-<slug>'`, `chunky>0`).
  Návratovka `@@G2007ADD` je neutrální **i když zápis proběhl** — důkaz je až v DB.

### Co do G2007 NEPATŘÍ

Mzdy jednotlivců, personální záznamy, obchodní podmínky konkrétních zákazníků, interní konflikty.
G2007 vidí celá síť Claudů i Marti‑AI. Citlivé věci zůstávají u člověka.

⚠️ Do složky `g2007/` na disku **nikdy nezapisuj ručně** — je to jen projekce DB.

---

# ČÁST 6 — U sdílené hodnoty nejdřív dopadová mapa

Když máš změnit, **jak se plní nebo počítá sdílená hodnota** (tabulka, sloupec, mzdový
či docházkový podklad), **nejdřív proaktivně nabídni dopadovou mapu a nic neměň:**

1. **Kdo to ZAPISUJE** — všechna místa (`soubor:řádek → co dělá`). Zvlášť označ, co běží
   **automaticky** (generování mezd, sync, noční job, trigger) — právě to tiše přepíše tvoji změnu zpátky.
2. **Kdo to ČTE.**
3. U každého: ovlivní to tvoje změna, nebo zůstane po staru?

Teprve po odsouhlasení měň. **Nikdy neopravuj jedno místo a nespoléhej, že jinde je to stejné.**

*Poučení 6. 8. 2026 (`att_day_summary`):* plnění se přepnulo na `att_entry`, ale generace mezd
(`_mzdy_refresh_zrcadla`) to dál přemazávala z Centrály → podklad dával ráno a večer jiné číslo.

---

# ČÁST 7 — Ops a konec session

**Restart služeb** přes most: `CLAUDE_OPS.txt` (1. řádek akce) + `CLAUDE_OPS_GO.txt` jako poslední.
Akce: `restart_service <STRATEGIE-*>`, `restart_self`, `service_status`. Audit v `CLAUDE_OPS_LOG.txt`.
⛔ Žádný volný PowerShell na produkci.

**Než skončíš:**

1. **Zapiš do G2007**, co přežije session — rozhodnutí a proč, gotchy, odchylky, ověřené postupy.
   Nezapsaná znalost = ztracená znalost.
2. **`@@WORKDONE`**.
3. **Pošli výsledek na mobil** svému člověku — `CLAUDE_NOTIFY.txt` (1. řádek titulek,
   dál zpráva, volitelně `user=<id>`) + `CLAUDE_NOTIFY_GO.txt`.

---

# ČÁST 8 — Standard práce (nadřazený všemu)

STRATEGIE je pracovní nasazení — data rozhodují o mzdách, fakturaci a chodu firmy.

- **Nikdy nevymýšlet.** Netvrdit nic bez ověření v kódu nebo datech.
- **Chybí info → zeptat se.** Nedomýšlet chybějící vstup.
- **Root cause z kódu**, ne z chování.
- **Nehádat názvy** sloupců, tabulek, endpointů — nejdřív `information_schema` / model / grep.
- **Žádná polovičatá analýza.** Co není ověřené end‑to‑end, označ jako „neověřeno".
- **Když tě někdo opraví, přestaň obhajovat hypotézu** a jdi do kódu.
- U peněz a přístupů dvojnásob; párovat na plnou identitu záznamu, ne částečný klíč.

Plné znění: G2007 `doc-system-g2007-standard-prace-overovani`.

---

# Údržba tohoto souboru

**Když se změní pravidlo, uprav TENHLE soubor a dopiš řádek do changelogu.** Jeden commit, platí všem.
Nezakládej si vlastní kopii — přesně tím se to minule rozešlo.

| Datum | Změna | Kdo |
|---|---|---|
| 18. 8. 2026 | návrh sloučení pěti roztříštěných návodů do jednoho | Kristý / C24 |

---

# Otevřené otázky (k rozhodnutí, pak smazat)

1. **Název souboru.** Návrh: **`ZACNI_TADY.md`** v kořeni — česky, drží konvenci, kterou
   už tým používá, a je krátký na vyslovení. *(Alternativa `START_HERE.md`, ale ta se
   při hledání minula — proto padl návrh na český název.)*
2. **Jirkova doména** — v tabulce je odhad z commitů, označený jako neověřený. Doplnit s ním.
3. **Staré soubory** — udělat z nich rozcestníky (ne mazat), aby staré odkazy nevedly do prázdna:
   `START_HERE_ID24.md`, `zacni_tady_claude25_navod.md`, `Karta zaměstnance/ZACNI_TADY_Claude25_navod.md`.
4. **Mandáty zůstávají zvlášť** — `docs/team/mandat_Peta_Claude26.md` je detailní pověření
   včetně whitelistu, sem nepatří. Návrh: odkazovat na něj z řádku ID26.
5. **ID27** obsluhuje 4 lidi s různými právy — sedí mu jeden řádek v tabulce, nebo chce vlastní sekci?
