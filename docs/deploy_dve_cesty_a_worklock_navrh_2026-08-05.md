# Návrhy řešení: dvě cesty deploye + WORK_LOCK zámek

**Autor:** Claude-24 (Kristý) · **Datum:** 5. 8. 2026 · **Stav:** návrh k rozhodnutí (Marti / Kristý / Marti-AI)

Vzniklo z incidentu 5. 8. 2026 kolem `@@G2007PUBLISH mobile.html` (self-test deadlock opraven zvlášť, commit `26bb5810`). Během řešení narazily obě strukturální díry, které Kristý pojmenovala. Oba body jsou **ověřené z kódu**, ne domyšlené.

---

## Bod 1 — Dvě cesty nasazení si šlapou po nohou

### Co se děje (ověřeno v kódu)

`@@G2007SESTAV` i `@@G2007PUBLISH` (v `modules/erp/api/router.py`, blok `diag_sql`) skládají artefakt z fragmentů v `g2007.soubor` a **zapisují ho přímo na disk cloudu** přes `open(_abs, "w")` (řádky ~37597 a ~37763). Cílové soubory (např. `apps/api/static/mobile.html`) jsou přitom **trackované v gitu** — v `.gitignore` nejsou (ověřeno).

Výsledek: přímý zápis udělá z trackovaného souboru „dirty working tree". Git deploy (`CLAUDE_DEPLOY`) dělá `git rebase --autostash`; dirty projekce se autostashne, a když origin mezitím tentýž soubor změnil, **autostash pop skončí konfliktem → blokuje deploy všem session na stroji**. Přesně tohle dnes ráno drželo nasazení ~08:35–09:21.

Jádro problému: `mobile.html` na disku je podle doktríny „kód jako data" (1.–2. 8. 2026) **jen projekce** z `g2007.soubor` (= zdroj pravdy). Přesto je zároveň verzovaný v gitu → má **dva zapisovatele** (publish píše projekci z DB, git verzuje). To je ta kolize.

### Potvrzeno naostro (Jirka / C28, 5. 8. 2026) — TICHÁ ztráta práce v OBOU směrech

Není to jen „dirty tree blokuje deploy". Reálný případ ukázal horší selhání: soubor `dochazka-opravy.html` je současně v gitu i v `g2007.soubor`.
- **Deploy přepsal publikaci:** C28 v 10:46 publikoval úpravu z DB přes `@@G2007PUBLISH` a ověřil na produkci. Během hodiny běžely git deploye (commity `4ed90eb9`, `2419404a`, `931554fd`), které **překopírovaly verzi z gitu na disk → publikace z DB se tiše ztratila**. Deploy udělal přesně to, co má — chyba je, že soubor žije na dvou místech.
- **A obráceně:** dopolední publikace ze staršího `g2007.soubor` by málem přepsala Peťinu práci ze 4. 8. večer, protože kopie v DB byla o den pozadu.

Tedy nejde jen o dva zapisovatele, ale o **dvě editační cesty** (někdo edituje fragment v `g2007.soubor` a publikuje, někdo edituje `.html` přímo a commitne). Kdokoli přijde druhý, tomu prvnímu tiše přemaže práci — bez konfliktu, bez varování.

### Možnosti

**Recommended — A) Jeden zdroj pravdy: přestat verzovat materializované artefakty v gitu + jedna editační cesta.**
Přidat skládané artefakty (`apps/api/static/mobile.html`, `dochazka-opravy.html` a spol.) do `.gitignore` a doplnit **materializaci při startu / po deployi** (vytáhnout aktuální `obsah` z `g2007.soubor` na disk, než appka začne obsluhovat). Tím git projekci nikdy nevidí → dirty tree i tichý přepis (viz Jirkův případ) zmizí u kořene. Nutná součást A: **všechny editace jdou přes `g2007.soubor` + publish; přímá editace `.html` a commit do gitu končí** — což je jen vynucení už přijaté doktríny „kód jako data" (1.–2. 8.). 
*Cena:* boot-time/deploy-time krok „materializuj artefakty z g2007.soubor" (jinak po čistém checkoutu `/mobile` 404 do první publikace); platí i pro blue-green secondary. Jednorázově naimportovat aktuální disk-verze do `g2007.soubor`, ať se nic neztratí při přechodu.

**B) Publish si projekci rovnou commitne.** Po zápisu na disk + DB udělá publish `git add <artefakt> && commit` (přes watcher, author = instance). Tree pak není nikdy dirty. 
*Cena:* spousta drobných auto-commitů; publish nově potřebuje git přístup (dnes jen píše na disk) → víc provázání. Neřeší dvojího zapisovatele, jen ho zakrývá.

**C) Sladit obě cesty zámkem + tolerovat projekci.** Publish i deploy berou stejný advisory lock (už existuje `778899` pro deploy); deploy před rebase udělá `git checkout -- apps/api/static/*.html` (zahodí regenerovatelnou projekci). 
*Cena:* workaround, dvojí zapisovatel zůstává; křehčí na údržbu.

**Doporučení:** A jako cílové řešení (sedí na už přijatou doktrínu). Když bude potřeba rychlá záplata dřív, C jako přechod.

---

## Bod 2 — WORK_LOCK.txt se dostává do konfliktu a blokuje commity

### Co se děje

`WORK_LOCK.txt` je **jeden sdílený git-trackovaný soubor**, do kterého připisují všechny session (i napříč stroji). Souběžné editace z různých lane/strojů → git merge konflikt (stav `UU`) → **blokuje commit všem na stroji** (`Committing is not possible because you have unmerged files`). Stalo se to C26 3. 8. a dnes 5. 8. dvakrát. Je to klasický „konfliktový magnet": mutable sdílený soubor + souběžný zápis + commit.

### Možnosti

**Recommended (cíl) — A) Přesunout work-lock/presence z gitu do DB.**
Už existuje `fw.claude_instance` (presence board, heartbeat — ověřeno v `router.py`). Rozšířit ho, nebo přidat `fw.work_lock` (append-only: instance, lane, téma, dotčené soubory, čas). Každá session dělá `INSERT` řádku → žádný sdílený soubor, žádný merge konflikt. Čtení přes most. Odstraní celou třídu konfliktu a sedí na „stav jako data".

**Recommended (hned, levné) — B) Per-instance soubory místo jednoho.**
Nahradit `WORK_LOCK.txt` adresářem `WORK_LOCK/<instance>.txt` (každá session píše **jen svůj** soubor). Dvě session = dvě různé cesty → git nemá co mergovat → žádný konflikt. Bez schématu, hotové za chvíli.

**C) Gitignorovat WORK_LOCK.txt** — zamítnuto: pak ho nevidí ostatní stroje, což je celý smysl.

**Doporučení:** B jako okamžitá mitigace (dnes to pálí), A jako cílová architektura — v duchu „additivně, ne perfektně" (doktrína #11).

---

## Otevřené k rozhodnutí

1. Bod 1: jdeme na **A** (gitignore + materializace při startu), nebo zatím **C** jako záplata?
2. Bod 2: nasadit hned **B** (per-instance soubory) a **A** (DB) naplánovat, nebo rovnou **A**?
3. Schéma `g2007`/`fw` vlastní Marti-AI → DDL (varianta A u obou) dělá dle doktríny **ona**; Claude připraví návrh + sync volajících míst.
