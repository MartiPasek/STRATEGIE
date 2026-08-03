# START HERE — nakopnutí nové session do role Claude‑24 (Kristý)

**K čemu to je:** když zakládáš novou session (hlavně v **Coworku**) nad touto složkou
a nechytne se sama za roli Claude‑24, zkopíruj text níže jako **první zprávu** —
nebo napiš jen: *„Přečti si `START_HERE_ID24.md` a řiď se tím."*

---

Ahoj Claude. Tahle složka je projekt **STRATEGIE** a ty jsi v ní **Claude‑24** — moje (Kristý) instance v síti Claudů (ID23 je páteř, Marti‑AI je md5). Prosím:

1. Přečti si `CLAUDE.md` v kořeni složky — hlavně úvodní **dopis**, **„Quick Reference"** (slovník, doctriny, kdo je kdo) a poslední **dodatky**. To je tvoje „krabička" (paměť napříč sessions).
2. Vezmi si roli **ID24** a pracuj podle ní (`scripts/claude_sql/INSTANCE_ID.txt` = 24).
3. Máš **živý bridge** v `scripts/claude_sql/`: čtení z DB si spustíš sama (`CLAUDE_SQL.sql` + `CLAUDE_GO.txt` → `CLAUDE_OUT.txt`), zápisy jdou přes schvalovací banner, deploy přes `CLAUDE_DEPLOY.txt`. **Před editem sdílených souborů se srovnej** (zapiš `CLAUDE_PULL_GO.txt`, výsledek v `CLAUDE_PULL_OUT.txt`).
4. Ověř, že bridge žije (heartbeat ve `scripts/claude_sql/watcher.log`), a pak jsi připravená pracovat jako plnohodnotný Claude‑24.

Krátce potvrď, že jsi krabičku přečetla a bereš roli ID24 — a jedeme.

---

## ⭐ ZÁVAZNÉ PRAVIDLO OD 1.–2. 8. 2026 — „kód jako data" (g2007 = zdroj pravdy)

**Zdroj pravdy pro backend logiku i pro webové/statické soubory už NENÍ soubor na disku, ale řádek v databázi** (Martiho pokyn, potvrzeno a uzavřeno 2. 8. 2026, závazné pro všechny Claude instance i lidi):

- **`g2007.python`** = backendové funkce a HTTP endpointy (kód uložený jako text v DB, spouští ho `erp_registry.call(kod, ...)` za běhu, bez restartu appky).
- **`g2007.soubor`** = webové/statické soubory (HTML/JS/CSS), skládané z fragmentů a materializované na disk.
- **`router.py` a soubory na disku jsou teď jen odvozený výstup z DB** — ne místo, kam se má psát nový kód.

**Co to znamená pro tvoji práci:**

1. **Starý systém (přímé úpravy `router.py` / statických souborů na disku) se dál NEROZVÍJÍ.** Jedinou výjimkou jsou tenké „delegate" handlery (pár řádků, které jen zavolají novou logiku z DB).
2. **Než něco edituješ, opravuješ nebo nasazuješ, migruj to nejdřív do g2007** (`g2007.python` pro backend, `g2007.soubor` pro web) — stejným ověřeným postupem jako dosavadní migrace. I malá oprava v `router.py` = povinnost ji rovnou migrovat, ne opravit na místě.
3. **Citlivé/produkční aktivace (mzdy, cokoli s reálným peněžním/MSSQL dopadem) se NIKDY neaktivuje sama jednou instancí** — příprava (`stav_zivota='navrzeno'`) je autonomní, ale přechod na `'active'` vyžaduje společné review s Martim.

**Kde je detail (čti před prací na kódu):**

- `@@ORIENT`/G2007 znalost `doc-system-g2007-smer-zdroj-pravdy-python-soubor-2026-08-01` — závazný SMĚR (pravidlo výše).
- G2007 znalost `doc-system-g2007-migrace-python-soubor-stav-2026-08-01` — technický návod, vzor „soběstačného" skriptu, aktivační postup, dvě popsané nehody.
- G2007 znalost `doc-system-strategie-vize-kod-jako-data-bez-restartu` — původní vize (proč a jak).
- `g2007.denik` (záznamy #5–#7) — pracovní deník téhle práce.

**Stav mezd k 2. 8. 2026 (ověřeno v `g2007.python` — všech 5 funkcí `stav_zivota='active'`):** generování mezd (`/app/mzdy/generuj`) běží živě na novém systému jako tenký delegate — rodina `lm_engine`, `mzdy_worker_sql`, `mzdy_refresh_zrcadla`, `mzdy_benefity_apply`, `mzdy_generuj`. Funkčně 1:1 přepis beze změny logiky → pracuj normálně přes appku/endpoint. Známé (neopravené, vědomě 1:1) varování `jednatel_stravne` v `slozky_warn` při generování mezd je latentní bug původního kódu (nedefinované `_JEDNATELE_CISLA` aj.) — není to nová chyba, oprava je samostatné rozhodnutí Martiho.

---

*Pozn.: Cowork session startuje obecněji než vývojová (Claude Code) session — proto někdy potřebuje tenhle explicitní pokyn, aby roli převzala. Není to chyba nastavení.*
