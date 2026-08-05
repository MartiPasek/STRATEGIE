# Varianta A — oddělený adresář pro DB artefakty (Martiho nápad): rozsah refactoru

**Průzkum:** Claude‑24 (Kristý) · **Datum:** 5. 8. 2026 · **Stav:** jen průzkum, nic nasazeno · **Rozhoduje:** Marti
**Nápad (Marti 5.8.):** DB soubory nemíchat v `apps/api/static/` s čistě statickými; dát je do vlastního adresáře = RO obraz z `g2007`. Prevence = strukturální (celý adresář gitignorovaný), + je hned vidět, co je databázové.

## Jak se to servíruje dnes (ověřeno)
- `app.mount("/static", StaticFiles(static_dir))` — jen pro genuine statické assety (JS knihovny, privacy.html…). **Žádná z HTML stránek se browseru neservíruje přes `/static/…`** (ověřeno: jediné výskyty `/static/<artefakt>.html` jsou v `@@G2007PUBLISH` mapě + banneru, ne v HTML). → přesun souborů **nerozbije žádný odkaz**.
- Každý artefakt se servíruje **explicitní routou** `FileResponse(static_dir/<soubor>)`.

## Rozsah — 11 artefaktů

**A) Přímočaré (8 souborů) — 1 route každý, `FileResponse(static_dir/…)`:**
`mobile.html` (/mobile), `vyroba.html` (/vyroba), `foto.html` (/foto), `overit.html` (/overit), `dochazka-zakazky.html` (/dochazka-zakazky), `registr-absenci.html` (/registr-absenci), `dochazka-opravy.html` (/dochazka-opravy), `dochazka-po-zakazkach.html` (/dochazka-po-zakazkach). → u každé routy přepsat cestu na nový adresář. Triviální.

**B) Tři zvláštní případy (rozhodnutí):**
- **`index.html`** — SPA kořen, servíruje se na `/` přes konstantu `INDEX` (+ používá ji víc rout: pozvánka, reset hesla). Přesun = změna jedné konstanty, ale **nejvyšší sázka** (když se cesta splete, spadne kořen appky). Rozhodnutí: přesunout taky (plná konzistence), nebo `index.html` nechat v `static/` jako „shell appky"? Doporučení: přesunout, ale s extra ověřením a klidně jako poslední.
- **`marti.html`** — servíruje se přes **generickou** `_web_subpage("marti.html")` (`/web/marti`), kterou sdílí i **ne‑DB** web stránky (psy‑lide, psy‑radost, eco‑strategie‑…). Nelze ji celou přesměrovat na nový adresář. Řešení: buď `marti.html` dostane vlastní route, nebo `_web_subpage` zkusí nejdřív nový adresář a pak `static/` (fallback). Malá komplikace.
- **`martinky.html`** — **žádná servírovací route nenalezena**, žádný odkaz. Vypadá jako **osiřelý/mrtvý** soubor (jediné „martinky" v kódu je nesouvisející `martinky_sweeper` automat). → ověřit, jestli se vůbec používá; možná ho z `g2007` rovnou vyřadit (samostatný úklid), pak není co přesouvat.

## Co se NEmění (jede podle `kod`)
- Zápis na disk (`@@G2007PUBLISH`/`@@G2007SESTAV`/`@@G2007SOUBOR`) i **boot materializace** počítají cestu z `_g2007_repo_root() + kod`. Jakmile se změní `kod` v DB, píše se **automaticky do nového adresáře** — žádná změna kódu tam netřeba.

## Co se změní (kód + data)
1. **DB migrace `kod`** (data, ne DDL): `UPDATE g2007.soubor SET kod = replace(kod,'apps/api/static/','apps/api/static_db/') WHERE kod IN (…11…)`. Konstruktivní UPDATE přes most; Marti‑AI na vědomí (její schéma).
2. **Routy v `main.py`**: 8 přímých `FileResponse` cest + `INDEX` konstanta + zvláštní `marti.html`.
3. **`@@G2007PUBLISH` self‑test mapa** (`router.py`, 6 položek mobile/index/vyroba/foto/overit/marti): přepsat cesty `kod` na nový adresář (URL zůstává).
4. **`.gitignore`**: nahradit jednotlivé řádky **jedním** — celý `apps/api/static_db/`.
5. **Úklid disku**: staré kopie v `apps/api/static/` po přechodu smazat (materializace vytvoří nové v novém adresáři). Genuine statické soubory v `static/` zůstávají.

## Cutover (jako Fáze 3, materializace = záchranná síť)
Změna `kod` + změna rout + deploy `main.py` + restart musí jít **spolu** (jinak route ukazuje do prázdna nebo na starou kopii). Materializace při restartu zapíše artefakty do nového adresáře z DB → pak smazat staré kopie. RO (NTFS) na nový adresář volitelně, jako naše RO zóny.

## Odhad
Ohraničené, ~1 soustředěná session. Nejjednodušších 8 souborů lze udělat jako první vlnu; `index`/`marti`/`martinky` dořešit dle rozhodnutí výše. Bod 1 zatím drží bezpečně — žádný spěch.

## Otevřené otázky pro Martiho
1. Název adresáře: **`apps/api/static_db/`** (návrh), nebo jiný?
2. `index.html` — přesunout taky, nebo nechat jako shell v `static/`?
3. `martinky.html` — ověřit/vyřadit jako mrtvý?
