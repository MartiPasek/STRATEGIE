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
  modré podtržení 2px `#34506f`.
- **Filtrovací řádek je POD názvy sloupců** (ne nad nimi) — jako to má Marti (17.7.2026).
  Pořadí v `<thead>`: nejdřív řádek s názvy (`<tr>` s `<th>`), pod ním `<tr class="frow">` s filtry.
  Oba řádky jsou přilepené (sticky): názvy `top:0`, filtry `top:<PŘESNÁ výška řádku s názvy>`.
  POZOR: ten offset se **liší per tabulka** a musí sedět přesně, jinak při rolování vznikne nad
  filtrem mezera (offset moc velký) nebo překryv (moc malý). Faktury mají hlavičku **31px**
  (kvůli zaškrtávátku „vybrat vše" ve sloupci výběru), pokladny jen **25px**. Nekopírovat naslepo –
  změř výšku `thead th` dané tabulky.
- **Filtrovací kolonky černé, ohraničené** (tmavé pozadí `#0b0d10`, neutrální šedý rámeček
  `#363b43`, světlý text; řádek filtrů `#08090c`) — jako Marti, ať jsou vidět jako samostatná
  okénka a nesplývají. (Dřív byly světle šedomodré `#9fb2c8` — 20.7.2026 změněno na černé.)
- **Buňky:** jemné oddělovače sloupců, přetečení se ořízne třemi tečkami (…), řádek se při najetí
  myší zvýrazní.
- **Zaškrtávací (ano/ne) sloupce:** hlavička jen 1 písmeno (R/Ú/S/Z…) + tooltip s celým názvem, úzké.
- **Číselné sloupce** (Částka, Saldo, …) zarovnané doprava a dost široké i na miliony.
- **Sloupce roztahovací** tažením za pravý okraj; **dvojklik na okraj = zpět na výchozí šířku**.
  Na okraji je jen **jednoduchá dvojšipka `cursor:ew-resize`** (↔), **žádný modrý proužek** na hover
  (NE `col-resize` – ta má čárku uprostřed) – jako u Martiho (21.7.2026). Platí i pro kurzor těla
  během tažení (`document.body.style.cursor='ew-resize'`).
- **ŠÍŘKY SLOUPCŮ — jak se nastavují (Peťa 22.7.2026, ověřený finální postup):**
  - ⚠️ **PŘIPOMEŇ PEŤE: nastavení šířek dělá v CHROMU** (v běžném okně ERP, ne v
    samostatné appce). Natáhne sloupce tažením za pravý okraj hlavičky.
  - **Osobní tažení se UKLÁDÁ do databáze** (`tenant.att_ui_pref`, kod `dochazka_col_widths_u<uid>`),
    takže každému zůstane jeho nastavení (jako dřív framework grid). Načítání: osobní má
    přednost, jinak sdílené výchozí, jinak default v kódu.
  - **„Výchozí pro všechny" nastavuje CLAUDE, ne uživatel.** Postup: Peťa si natáhne sloupce
    v Chromu → řekne „nastaveno" → Claude si přečte její osobní záznam v DB (kod
    `dochazka_col_widths_u18`) a **povýší ho na sdílené výchozí** (kod `dochazka_col_widths`)
    přes SQL most (INSERT … ON CONFLICT). Projeví se všem po refreshi, **bez deploye**.
    **Žádné tlačítko „uložit šířky" na stránce** — Peťa ho výslovně nechce.
  - U starších přehledů (faktury/pokladny) jsou výchozí šířky v kódu (`_faktColDef`/`DCOLW_DEF`).
- **Krajní úzký sloupec značek (18px) úplně vlevo, PŘED prvním sloupcem** (21.7.2026): v řádku filtru
  je v něm **✕**, které zruší jen filtry sloupců (na data/šířku sloupce nemá vliv). V datových řádcích
  značky výběru — **tečka •** u vybraných řádků, **šipka ▶** u řádku, na kterém uživatel naposledy
  stál. (U faktur tuhle roli plní sloupec se zaškrtávátky; šipka ▶ je u aktuálního řádku.)
  Pozor: úzký sloupec potřebuje `padding:0`/`2px 0` na buňkách, jinak se ✕/šipka ořízne.
- **Výběr řádků myší:** klik na řádek ho označí/odznačí (zvýrazní modře), **Shift+klik** označí celý
  úsek. U faktur je výběr napojený na stejnou množinu jako zaškrtávátka (pro „Změna návrhu k platbě");
  u pokladen zatím jen vizuální. Klik do filtru/vstupu řádek NEvybírá (guard `closest('input,select,…')`).
- **Filtr čísel bere čárku i tečku:** hodnotu i hledaný text normalizuj (číslo přes `toFixed(2)`,
  pak `replace(/,/g,'.')`), ať „280,02" i „280.02" najde totéž (i „1 597,20"). Pokladny to 21.7.
  ztratily → vráceno; faktury (`_faktMatch`) to mají odjakživa.
- **📅 DATUMOVÝ FILTR — VŠUDE, kde je v přehledu/tabulce sloupec s datem (Peťa 23.7.2026, závazné):**
  každý datumový sloupec má mít ve filtrovacím řádku **klikací filtr** (ne psací), který otevře
  popup **„Výběr období"** s poli **Jeden den** (nastaví OD i DO stejně) / **Datum OD** / **Datum DO**
  a tlačítky **vymazat / zrušit / OK** — přesně jako v **Přijatých fakturách** (platby.html,
  `openSplatFilter`, sloupec Splatnost). Vzor přenesený i do docházky (`openDateFilter`,
  `dochazka-po-zakazkach.html`) a pokladen (`openDateFilterP`, `pokladny.html`).
  - Filtrování: datum řádku i meze převeď na číslo (`_dnum` z `DD.MM.YYYY`, `_inum` z `YYYY-MM-DD`)
    a porovnej rozsah — bere i datum s časem („23.07.2026 08:44"). Filtry se ukládají jako
    `FIL[sloupec+'_od']` / `FIL[sloupec+'_do']`, ✕ (zrušit filtry) je maže spolu s ostatními.
  - **Pravidlo:** kdykoli stavíš nebo upravuješ přehled a je v něm sloupec s datem, tenhle filtr tam dej.

## POJISTKA 2 — po deploji ověř, že server SERVÍRUJE novou verzi (21.7.2026)
Deploy může napsat **„DEPLOY: OK · cloud: OK"**, a přesto cloud NEPŘEVEZME novou verzi. Stalo se
21.7.: commit `platby.html`+`pokladny.html` prošel a byl na disku i v gitu, ale server pořád posílal
**starou** verzi — Peta viděla „pořád stejné" i po vypnutí/zapnutí aplikace.
- Proto po KAŽDÉM deploji **ověř skutečně servírovaný obsah**, ne jen hlášku „OK":
  `fetch('/platby?__t='+Math.random(),{cache:'no-store'})` (nebo `/pokladny`) a zkontroluj, že tam
  je tvoje konkrétní změna (nějaký unikátní kousek kódu/textu).
- Když tam změna NENÍ → **vynuť redeploy**: drobná změna (např. komentář `<!-- redeploy … -->`),
  ať vznikne nový commit, a nasaď znovu. Napodruhé to obvykle projde.
- Teprve pak řekni Petře „hotovo" a ať dá Ctrl+F5.
