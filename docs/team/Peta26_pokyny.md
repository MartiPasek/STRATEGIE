# Trvalé pokyny od Petry pro Claude‑26
(Číst při startu. Aktualizováno 13. 7. 2026.)

## Přístup k práci
- Cílím na **maximální výsledek** a snažím se věc **dotáhnout sám**, vlastními nástroji —
  most (čtení DB, dotazy), `git pull`, úpravy souborů, nasazení přes blue‑green (vždy vratné).
- Nejdřív hledám, jak to zvládnu **sám / spolu s tebou**, ne jak to hodit na ostatní.
- Budu **proaktivní**: navrhnu řešení a rovnou ho posunu k cíli, ne jen popíšu problém.

## Git
- **Před KAŽDÝM započetím práce udělej nejdřív `git pull`** (přes most), ať se koukám do
  **aktuálně nastavených věcí** (aktuální kód a stav), a **napiš Petře, že ho dělám.**
- Když Petra napíše **„udělej git pull"**: proveď ho **přes most**, NE přes PowerShell
  a NE žádej Petru, ať to ťuká.
  Postup: vlož `scripts/claude_sql/CLAUDE_PULL_GO.txt`, počkej ~10–15 s, přečti
  `scripts/claude_sql/CLAUDE_PULL_OUT.txt` (most spustí `git pull --rebase --autostash`).
- **Před KAŽDÝM nasazením (deploy) udělej nejdřív `git pull`** (přes most) — a **napiš Petře,
  že ho děláš** — ať se vždy staví na aktuálním kódu.

## Most (bridge) — KDE je a jak spolu nasazujeme ⚠️ (ať nekoukám jinam)
- **Most = služba Windows `STRATEGIE-CLAUDE-SQL`** (běží `scripts/claude_sql_runner.py`).
  Moje instance = **Claude‑26 (Peta)**, počítač **Peta‑NTB**. `INSTANCE_ID.txt` = 26.
- **VŠECHNY povelové soubory jsou ve složce `scripts/claude_sql/` — NIKDY ne v kořeni projektu.**
  (Kořenové `CLAUDE_*.txt` most nečte, jsou to slepé soubory. Tohle mě 13.7. zdrželo — psala jsem
  povely o patro výš a nic se nedělo.)
- **Ověření, že most žije (tepe):** `scripts/claude_sql/watcher.log` — poslední řádek „heartbeat OK"
  má být čerstvý (přibývá ~každých 30 s). Když poslední tep není aktuální → služba stojí.
- **Git pull:** vlož `scripts/claude_sql/CLAUDE_PULL_GO.txt` → výsledek `scripts/claude_sql/CLAUDE_PULL_OUT.txt`.
- **Nasazení (deploy) — Petra NIC nepotvrzuje, prostě nasadím:**
  1. `scripts/claude_sql/CLAUDE_DEPLOY.txt` = 1. řádek jednořádková commit zpráva; další řádky = cesty souborů (nebo `ALL`).
  2. `scripts/claude_sql/CLAUDE_DEPLOY_GO.txt` = zapsat JAKO POSLEDNÍ (to je spouštěč).
  3. Výsledek `scripts/claude_sql/CLAUDE_DEPLOY_OUT.txt` (~5–30 s). Deploy sám udělá pull (rebase) +
     commit + push + nahrání na cloud + restart aplikace. Blue‑green = vždy vratné.
- **⚠️ NIKDY nesahej na git přes připojenou složku** (device bash / mount) — vznikne `.git/index.lock`,
  který **zasekne most** (přesně to se stalo 13.7.2026). Číst soubory přes složku ano, ale žádné
  `git` příkazy (status/log/blame/…) přes ni.
- **Když se most zasekne:** Petra ho restartuje — **Windows → Služby (Services) → `STRATEGIE-CLAUDE-SQL`
  → pravý klik → Restartovat** (nebo v PowerShellu jako správce `Restart-Service STRATEGIE-CLAUDE-SQL`).
  Ověřeno 13.7. — po restartu naskočí do logu „forwarder started · Claude‑26 (Peta)".

## Schvalování (bannery)
- Moje (Claude‑26) write požadavky se schvalují **Petře (user 18), NE Martimu.** Ověřeno na
  živých datech (`fw.mobile_command` → `target_user_id = 18` u požadavku #863), přesně jak psala
  Kristý (Claude‑24).
- **Neeskaluj** write requesty na rodiče s odůvodněním „Petra nemá práva" — bannery chodí Petře
  a ona si je schvaluje sama v appce (sekce „ke schválení" / oranžový banner v ERP).
- Pozn.: aplikační capability (`tenant.user_capability`, kde má Petra u „mzdy" jen čtení) je
  **jiná vrstva** než schvalování bannerů — neplést dohromady.

## Styl komunikace (Petra)
- **Tykáme si.** Petra a Claude si tykají — v KAŽDÉ nové konverzaci rovnou tykej, nikdy nezačínej vykáním.
- **Piš STRUČNĚ.** Krátké, k věci.
- **Piš lidsky, ne programátorsky** — Petra není programátorka. Cizí/odborné slovo dej
  do závorky s vysvětlením.

## Jak Petře připravit e-mail (14.7.2026)
- **Odesílatel (From):** do hlavičky `.eml` dávej `p.safrankova@eurosoft.com` (ne petra@eurosoft.com).
Když Peta řekne „připrav mail" (do Outlooku, ať ho jen odešle):
- Udělej soubor **`.eml`** s hlavičkou **`X-Unsent: 1`** (Outlook ho pak otevře jako **rozepsaný**
  mail v režimu psaní, ne jako přijatý), s předmětem, tělem a případnou **přílohou**.
- Pošli ho přes `SendUserFile`. Peta klikne „Download and open" → otevře se hotový mail v Outlooku
  → doplní „Komu" → Odeslat. (Martiho adresu můžu doplnit do `To`, když ji řekne.)
- **Dlouhý obsah dávej do přílohy** (soubor), NE do těla — `mailto`/tělo dlouhý text (hlavně česky
  s háčky) ořezává nebo neotevře.
- Pozn.: dřív jsme to dělali i přes „extra tlačítko"; `.eml` je spolehlivá varianta.

## POJISTKA před nasazením (14.7.2026 — poučení z chyby)
Než nasadím upravený soubor, VŽDY ověř, že moje kopie NENÍ oříznutá starou cache:
- Po `device_stage_files` porovnej **autoritativní `bytes` z výsledku** s reálnou velikostí
  staženého souboru (`wc -c`). Když nesedí → kontejner drží STAROU cache; použij čerstvou kopii
  (u malých souborů čti přes `device_bash`, u velkých obnov přes `git show <commit>:cesta` jen ke čtení).
- Stalo se: nasadil jsem `router.py` ze staré cache a vrátil tím cizí i vlastní změny (−4 KB).
  Chytit se to dá i podle divného počtu řádků v `CLAUDE_DEPLOY_OUT.txt` (moc insertions/deletions).

## Jak mají vypadat PŘEHLEDY (tabulky) — jednotný vzhled (17.7.2026)
Všechny velké přehledy (Faktury přijaté, Pokladní doklady a další) mají vypadat **stejně**.
Referenční vzor: `apps/api/static/pokladny.html` (`table.dokl`) a `platby.html` (`table.fakt`).
- **Rámeček** kolem tabulky (1px `#2a3546`, radius 8px) + silnější stylované posuvníky (scrollbary).
- **Hlavička přilepená (sticky):** VELKÁ PÍSMENA, bílá, tučná (700), tmavé pozadí `#1c2636`,
  modré podtržení 2px `#34506f`. Nad hlavičkou přilepený **filtrovací řádek**.
- **Filtrovací kolonky tlumené** (světle šedomodré `#9fb2c8`, tmavý text) — NE zářivé.
- **Buňky:** jemné oddělovače sloupců, přetečení se ořízne třemi tečkami (…), řádek se při najetí
  myší zvýrazní.
- **Zaškrtávací (ano/ne) sloupce:** hlavička jen 1 písmeno (R/Ú/S/Z…) + tooltip s celým názvem, úzké.
- **Číselné sloupce** (Částka, Saldo, …) zarovnané doprava a dost široké i na miliony.
- **Sloupce roztahovací** tažením za pravý okraj; **dvojklik na okraj = zpět na výchozí šířku**.
- **DŮLEŽITÉ chování šířek:** je **pevné VÝCHOZÍ nastavení pro všechny**. Tažení je jen **DOČASNÉ** —
  po obnovení stránky se vše vrátí na výchozí. **NEUKLÁDAT** šířky do prohlížeče (localStorage).
  (Výchozí šířky měň v kódu v `_faktColDef` / `DCOLW_DEF`.)
