# Migrace router.py/web do g2007.python a g2007.soubor — stav a jak pokracovat (1.8.2026)

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## !! NEPLATI k 28. 8. 2026 v jednom bodu: fragmenty mobilu maji KAZDY vlastni IIFE
> 
> Veta nize "fragmenty 20+ NEJSOU nezavisle IIFE, jsou to hole function deklarace uvnitr JEDNE
> obalove funkce ... pres closure, ne pres window" **uz neplati**. Dnes je kazdy dilek mobilu
> **vlastni `<script>` blok s vlastni IIFE**, ktera si zavislosti bere z `window.__M2W`
> a na konci registruje sve funkce pres `__setImpl` / prime prirazeni do `window.__M2W`.
> Funkce z jednoho dilku **neni videt z jineho**, dokud se nezaregistruje.
> Zjisteno naostro 27. 8. 2026 (pad `_mojeHlavicka is not defined` pri presunu fotky a Novinek
> mezi dilky 48 a 60). Detail: [[doc-system-strategie-mobil-dilky-nejsou-jedna-closure]].
> **Zbytek dokumentu plati beze zmeny** - puvodni veta je nize schvalne ponechana.

# Migrace router.py/web do g2007.python a g2007.soubor — stav a jak pokracovat (1.8.2026)

Napsal Claude-23 na zaklad zadosti Martiho, aby byl system srozumitelny pro ostatni
Claude instance (Peta/Claude-26, Jirka/Claude-28, dalsi) i pro lidi. Shrnuje DVA
paralelni "kod jako data bez restartu" mechanismy, jejich prikazy, bezpecnostni
pravidla a znamé nehody s pouzenim.

## 1) g2007.python — PYTHON FUNKCE (backend logika)

Zdroj pravdy = radek v `g2007.python` (sloupce: kod, zdroj, popis, kategorie,
stav_zivota, verze, puvodni_umisteni, vedlejsi_ucinek), NE soubor na disku.
Nacitac: `modules/erp/api/erp_registry.py` — `erp_registry.call(kod, *args, **kwargs)`
nacte `SELECT zdroj, verze FROM g2007.python WHERE kod=:k AND stav_zivota='active'`,
zkompiluje pres `compile()+exec()` do izolovaneho namespace (cache podle (kod,verze)),
zavola `run(...)`. Zadny restart procesu. Trigger `g2007.fn_python_archiv_pred_update`
pri kazde zmene `zdroj`/`stav_zivota` inkrementuje `verze` a ulozi PREDCHOZI stav do
`g2007.python_historie` (kompletni auditni historie vcetne md5 obsahu pres kazdou verzi).

Router.py endpoint se migruje takto: puvodni telo funkce se prevede na "sobestacny"
skript (zadne zavislosti na globals routeru — pomocne funkce se bud verbatim
duplikuji primo do skriptu, nebo se JIZ MIGROVANE zavislosti volaji cross-script
pres `erp_registry.call("jiny_kod", ...)`), vlozi se do g2007.python, a handler
v router.py se prepise na tenky "DB-driven delegate":

```python
@api_router.post("/app/attendance/checkout")
async def att_checkout(req: Request) -> JSONResponse:
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    body = await req.json()
    from modules.erp.api import erp_registry as _ereg
    result = _ereg.call("att_checkout", uid, (body or {}).get("reason"), (body or {}).get("presence"))
    status = result.pop("_status_code", 200) if isinstance(result, dict) else 200
    return JSONResponse(result, status_code=status)
```

**Aktivace = 2 kroky, oddelene:** (1) INSERT s `stav_zivota='navrzeno'` — nic zive.
(2) UPDATE `stav_zivota='active'` — az kdyz je obsah overeny. Router.py handler se
teprve pak (samostatny deploy) prepne na `erp_registry.call(...)`. Aktivovat PRED
deployem delegate patche, ne obracene.

**Schvalovaci banner (doktrina 31.7.2026, viz `doc-system-strategie-cil-migrace-router-py-g2007-python-schvaleno`):**
INSERT/UPDATE ktere pisi VYHRADNE do `g2007.python` (zadna primichana jina tabulka)
bezi autonomne, BEZ Martiho schvaleni v banneru. DELETE/TRUNCATE/ALTER na g2007.python
zustavaji gated (schvaluje Marti). POZOR: pokud `zdroj` skriptu sam OBSAHUJE syrove
SQL retezce (INSERT/UPDATE jako stringy uvnitr Python kodu — coz u techto skriptu je
bezne, jsou to DB handlery), regex guard v `/diag-sql` je muze OBCAS vyhodnotit jako
vicezapisovy prikaz a poslat do bannerove fronty (`fw.claude_write_request`) i kdyz
cilova tabulka je porad jen g2007.python.

**ZNÁMÁ NEHODA (1.8.2026):** presne tahle bannerova fronta ma bug — u velkych SQL
payloadu obcas TICHE ZTRATI jednotlivé mezery uprostred dlouhych odsazovacich behu
(pravdepodobne pri prenosu/zpracovani textu pred zapisem). Zasáhlo to `att_checkout`
a `att_absence` behem Faze F migrace. Bylo to odhaleno bisekci md5 hashe proti
lokalni referenci, opraveno cilenym patchem, ale NASLEDNE starsi/spatny pokus o
opravu (request #1651) byl omylem schvalen a poskozeni na chvíli vratil zpet — pak
opet opraveno. **Pouceni: po jakekoli aktivaci/opravu skriptu VZDY over posledni
stav primo v `g2007.python_historie` (md5(zdroj) po verzich), NE jen podle toho, co
rika banner nebo co si pamatuje predchozi session — automatizovany/schvalovaci kanal
muze obsah nechtene zmenit.** Query vzor:

```sql
SELECT verze, stav_zivota, platne_od, nahrazeno_at, length(zdroj), md5(zdroj)
FROM g2007.python_historie WHERE kod = '<kod>' ORDER BY verze;
-- + aktualni radek primo z g2007.python pro live md5
```

**Overovani pred aktivaci:** `erp_registry.selftest_compare_any_stav(kod, legacy_fn, args)`
porovna DB-verzi (jakykoli stav_zivota) s puvodni legacy funkci na stejnych vstupech.
Necha se spustit rucne pred prepnutim na 'active'.

**Stav k 1.8.2026 (pocty aktivnich `stav_zivota='active'` radku v g2007.python):**
dochazka=60, dochazka_mzdy=3, erp_funkce=48, erp_http_endpoint=16, mzdy=4 (+1 inactive).
Faze B (30-31.7, dochazka aktivace) az Faze F (1.8, posledni davka: att_fix_resync,
att_checkin, att_checkout, att_absence, mzdy_c_smlouva_save) — vsech 5 z Faze F je
nyni `active`, hash-overene, a realne otestovane Martim (2x, uspesne). `python_run_audit`
loguje kazde realne volani `erp_registry.call()` (kod, uid, ok, chyba, trvani_ms) —
uzitecne pro potvrzeni, ze aktivovana cesta uz opravdu bezi na produkcnim provozu.

`mzdy_generuj` byl vedome VYNECHAN z Faze F (zavisi na externim MSSQL Helios spojeni
+ tehdy nemigrovane `_mzdy_benefity_apply`, jde o primy vypocet vyplat).

**AKTUALIZACE 2.8.2026 (Claude-23):** cela rodina uz je PRIPRAVENA — `lm_engine`,
`mzdy_worker_sql`, `mzdy_refresh_zrcadla`, `mzdy_benefity_apply`, `mzdy_generuj`
(5 kusu), vsechny `stav_zivota='navrzeno'` (md5/py_compile/funkcne overeno, NIC
aktivni). Detaily a nalezena latentni chyba puvodniho kodu (blok jednatelske stravne,
nedefinovana jmena `_JEDNATELE_CISLA` aj., tise zachytavano try/except) viz
`g2007.denik` #5 a #6 a docstring skriptu `mzdy_generuj`. Aktivace = pouze po
spolecnem review s Martim (zadna solo aktivace u realnych mezd) — plati porad,
beze zmeny.

## 2) g2007.soubor — WEB / STATICKE SOUBORY (HTML/JS/CSS)

Analogicky system pro frontend. Sloupce: kod (relativni cesta v repu, napr.
`apps/api/static/mobile.html`), typ (`zdroj` = fragment, `artefakt` = sestaveny
vysledny soubor), obsah, slozeno_z (pole kodu zdrojovych fragmentu — jen u artefaktu),
stav_zivota, verze (stejny archiv-trigger vzor jako g2007.python).

NA ROZDIL od g2007.python (in-process exec cache), zde se aktualni obsah artefaktu
**materializuje na disk** — routy jako `/mobile` ctou soubor znovu z disku pri kazdem
requestu (`Cache-Control: no-store` v main.py), takze zapis na disk = okamzite zive,
bez restartu API.

**Prikazy (v `/diag-sql` dispatch, `modules/erp/api/router.py`):**
- `@@G2007SOUBOR <kod> | <typ:zdroj|artefakt> [| slozeno_z=a,b,c]` + obsah na
  dalsich radcich — upsert radku; u typ=artefakt rovnou zapise i na disk.
- `@@G2007SESTAV <kod_artefaktu>` — sestavi artefakt z jeho zdroj fragmentu (podle
  poradi v slozeno_z), zapise DB+disk. Nizkourovnovy nastroj pro rucni zasah.
- `@@G2007EXPORT <kod>` — znovu vyexportuje aktualni DB obsah na disk beze zmeny
  (kdyz se obsah opravil primo v DB, jen dohnat disk).
- `@@G2007PUBLISH <kod_artefaktu>` — **DOPORUCENA cesta pro beznou publikaci.**
  Sestavi kandidata (nebo vezme aktualni obsah, pokud neni skladany), provede
  sanity kontroly (delka, JS syntax pres `node --check` je-li dostupny), zalohuje
  aktualni zivy soubor, zapise kandidata na disk, SAM SE OVERI na zive URL, a
  pokud appka nenaběhne, automaticky vrati zalohu zpet (DB zustane nedotcena).

**ZNÁMÁ NEHODA (1.8.2026, vypadek /mobile):** naivni vlozeni `</script><script>`
separatoru mezi jednotlive `.js` fragmenty (aby byly izolovane) appku rozbilo —
fragmenty 20+ NEJSOU nezavisle IIFE, jsou to holé function deklarace uvnitr JEDNE
sdilene obalove funkce otevrene v `10_core.js` a zavrene az v
`74_claude27_render_init.js`, sdileji lokalni promenne (app, el, topbar, SCREENS, B)
pres closure, ne pres window. Reakce na tento vypadek = postaveni `@@G2007PUBLISH`
(self-verify + auto-rollback).

**Stav k 1.8.2026:** cely `/mobile` je uz rozlozeny na ~28 zdroj fragmentu
(`apps/api/static/mobile_parts/*`) + sestaveny artefakt `mobile.html` (verze 5,
slozeno_z = presne tech 28 fragmentu). Sandboxova zkusebni kopie `mobile2.html` +
`mobile_parts2/*` (pouzita k overeni izolacniho pristupu, ktery zpusobil vyse
zmineny vypadek) byla po overeni, ze uz je bajt-identicka s `mobile.html`/
`mobile_parts/*` (zadna unikatni logika navic), 1.8.2026 SMAZANA (viz `g2007.denik`
#3 a schvaleny banner request #1652) — nova logika uz je plne v `/mobile`, sandbox
byl nadbytecny. Dalsi samostatne artefakty uz v g2007.soubor (zatim bez
zdroj-rozkladu, jen artefakt primo): `index.html`, `marti.html`, `foto.html`,
`overit.html`, `vyroba.html` — kandidati na stejny rozklad na fragmenty jako
`mobile.html`, az bude prostor.

## 3) Spolecna pravidla pro OBA systemy

- Zdroj pravdy je VZDY DB radek, nikdy soubor na disku primo editovany rucne (u
  g2007.soubor se na disk jen EXPORTUJE/PUBLIKUJE odvozeny vysledek).
- Zapis do znalostni baze (`g2007.znalost`, vcetne tohoto dokumentu) jde VYHRADNE
  pres `@@G2007ADD <oblast> <slug> | <nadpis>` + obsah — NE raw INSERT (zbytecny
  banner), NE stary zpusob `docs/Z_*.md`/`@@G2007DOC` (ZAKAZANO).
- Pred aktivaci cehokoli citliveho (mzdy, dochazka, financni data): over hash
  posledni verze v prislusne `_historie` tabulce, ne jen "vypada to OK" z pameti.
- Prace na tomto se zaznamenava do `g2007.denik` — viz sekce 4 nize.
- Mazani (DELETE/TRUNCATE/ALTER) zustava VZDY gated pres banner — jen konstruktivni
  operace (INSERT/UPDATE) bezi autonomne. `device_bash`/primy pristup na disk
  soubory na disku NEUMI mazat (bridge to neumoznuje, ani vlastni docasne soubory
  jako napr. git zamky) — na fyzicke smazani/vycisteni disku se pouziva git
  (add/commit/push pres deploy most), nebo se pozada Marti o rucni zasah.

## 4) g2007.denik — pracovni denik / audit trail prace na migraci

Ucel: prave proto, aby se nemohla zopakovat situace z 1.8.2026, kdy jedna Cowork
session autonomne pracovala (s Martiho svolenim) na migraci dochazky/mzdy, ale
zamrzla driv, nez stihla vysledek radne predat a zapsat — a Marti pak nemel odkud
zjistit, co presne se stalo a v jakem stavu to je, krome kusu zkopirovaneho textu
z mrtve session. `g2007.denik` je presne pro tohle: trvaly, dohledatelny zaznam
"kdo, kdy, co delal, s jakym vysledkem", nezavisly na tom, jestli konkretni chat/
session prezije.

**Schema** (`g2007.denik`): `id`, `instance` (napr. "Claude-23"), `vlakno
(volitelne, pro vetveni v ramci jedne instance), `spustil` (kdo praci zadal, napr.
"uzivatel:Marti"), `zahajeno_at`, `dokonceno_at` (NULL dokud bezi), `stav`
("hotovo" / jina hodnota dle potreby), `co_resim` (text, co presne se resi/resilo),
`vysledek` (text, vysledek/shrnuti), `soubory` (pole cest k dotcenym souborum),
`g2007_kody` (pole kodu z g2007.python/g2007.soubor, kterych se prace tykala),
`git_commit_sha` (pokud prislusi konkretni commit).

**Kdy zapisovat:** na zacatku netrivialni ucelene prace (zahajeno_at, stav zatim
bez dokonceno_at) a/nebo na konci (dokonceno_at + vysledek) — minimalne VZDY pri
dokonceni prace, ktera by mela byt dohledatelna pro ostatni (aktivace, oprava,
vetsi vysetrovani). `INSERT`/`UPDATE` do `g2007.denik` je konstruktivni operace,
bezi autonomne stejne jako u g2007.python — bez schvalovaciho banneru.

**Aktualni obsah k 1.8.2026** (3 zaznamy): #1 oprava chybejici sekce "Potvrd si
dochazku" v mobilni appce; #2 oprava dirty_working_tree na cloud APP zpusobene
primym zasahem na produkci; #3 dnesni prace popsana timto dokumentem (pozehnani
Faze F, vysetreni incidentu #1651, sepsani teto dokumentace, smazani mobile2
sandboxu). Kdokoli dalsi (clovek nebo Claude instance) si muze `SELECT * FROM
g2007.denik ORDER BY id` a vidi presne, co se delo, aniz by musel prochazet chat.

## 5) Co zbyva / navrh dalsiho postupu

- g2007.python: zbytek router.py mimo dochazku/mzdy/vyrobu jeste neprozkoumany
  systematicky — dalsi vlna by mela projit modul po modulu (napr. ERP poptavky/
  nabidky/kalkulace, ktere uz vlastni samostatnou EC_GenPoptavku cestu a NEJSOU
  soucasti teto migrace).
- g2007.soubor/web: `index.html`/`marti.html`/`foto.html`/`overit.html`/
  `vyroba.html` jsou zatim jen holé artefakty bez zdroj-rozkladu — dalsi kandidati
  na stejny vzor jako `mobile.html` (rozklad na fragmenty + `@@G2007SESTAV`/
  `@@G2007PUBLISH`), az bude prostor.
- Doporuceni: kazda dalsi vlna migrace by mela KONCIT hash-overenim (viz bod 1
  vyse) drive, nez se cokoli oznaci Martimu jako "hotovo", a zapisem do
  `g2007.denik` (bod 4 vyse), aby to bylo dohledatelne i pro ostatni.

