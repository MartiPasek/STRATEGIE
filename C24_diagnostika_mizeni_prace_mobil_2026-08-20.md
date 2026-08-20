# Proč nám mizí práce v mobilní appce — diagnostika

**Zpracoval:** Claude‑24 (Kristý) · **Datum:** 20. 8. 2026
**Podnět:** zmizelo tlačítko „📊 Stáhnout rozpad (Excel)" v dlaždici Přefakturace (nasazeno 20. 7., pryč 21. 7.).
**Metoda:** všechno níže je **ověřené z gitu a z kódu**, ne domyšlené. U každého tvrzení je commit / řádek.

---

## 1. Závěr napřed (a je nepříjemný pro nás, ne pro Jirku)

**Konkrétní ztrátu z 21. 7. nezpůsobil Jirka.** Způsobil ji náš vlastní commit z 20. 7.

- 20. 7. 16:10 commit `c863e0627` (*Claude‑24 / Kristý*) zapsal tlačítko **jen do `apps/api/static/mobile.html`** — do **vygenerovaného** souboru.
- Zdrojový dílek `apps/api/static/mobile_parts/73_pref_poptavka.js` v tu chvíli **už existoval** (ověřeno: `git cat-file -e c863e0627:…73_pref_poptavka.js` = ANO) a **naše změna v něm nebyla** (ověřeno: `grep -c prefStahniExcel` v dílku k 21. 7. = **0**).
- 21. 7. 08:59 commit `82a2886de` (*Claude‑28 / Jirka*, zámky docházky) upravil **dílek** `60_dochazka.js` a nechal `mobile.html` **znovu sestavit z dílků**. Sestavení přepsalo `mobile.html` verzí, ve které naše změna nikdy nebyla → tiše zmizela.
- Otisk v diffu to potvrzuje: hunky `@@ -5282` a `@@ -6823` = Jirkova práce (přidání), hunky `@@ -8882/-8891/-8931` = **odebrání** našeho bloku přefakturace. Klasický obraz regenerace, ne ruční mazání.
- `c863e0627` byl v té chvíli **už v hlavní větvi** (`git merge-base --is-ancestor c863e0627 82a2886de` = ANO), takže to nebyl konflikt větví ani chybějící `pull`.

**Root cause: měnili jsme vygenerovaný výstup místo zdroje.** Build pak udělal přesně to, co má.

---

## 2. Proč je to „opakovaný problém" — je to celá třída chyb, ne jeden člověk

Stejná třída ztráty (změna zapsaná mimo skutečný zdroj pravdy) udeřila opakovaně a **pokaždé někomu jinému**:

| Kdy | Koho | Co zmizelo | Doklad |
|---|---|---|---|
| 21. 7. 2026 | Kristý / C24 | tlačítko Excel v Přefakturaci | `82a2886de` (regenerace z dílků) |
| 5. 8. 2026 | Peťa | rozsah absence dle úvazku (lidem se zkráceným úvazkem se strhávalo víc dovolené) | `f4f7e6e7`, popsáno v `scripts/build_mobile.py` |
| 12. 8. 2026 | Šárka | číselník pojišťoven, profilová fotka, karta Novinky, potvrzení účasti | `6a000461`, `865f538b`, `7b233f87`, `7ca280dc` |
| 5. 8. 2026 | C28 | publikace z DB přepsána git deployem během hodiny | `docs/deploy_dve_cesty_a_worklock_navrh_2026-08-05.md` |
| 18. 8. 2026 | Jirka | část commitu tiše nezaindexována, deploy přesto hlásil OK | `33cb649d` → oprava `28e1397b` |

Z 92 řádků, které Peťa a Šárka napsaly, **jich 89 v appce nikdy nebylo** — a nikde to nehlásilo chybu. Do DB se to doneslo až 17. 8.

Společný jmenovatel: **jeden soubor žil na dvou místech** (git i DB, zdroj i výstup) a nic nehlídalo, že píšeš do toho špatného.

---

## 3. Co už je opravené (a kdo to opravil)

Většina díry je **zavřená**, a velký kus zavřel právě Jirka:

1. **Dílky ven z gitu** — `5b130553` (Jirka, 17. 8., schválila Marti‑AI): `apps/api/static/mobile_parts/` do `.gitignore` (ověřeno: `.gitignore` řádek 167), `build_mobile.py` přepsán na **varování**, které tuhle nehodu jmenovitě popisuje včetně obětí a správného postupu.
2. **Artefakty ven z gitu** — sestavené stránky jsou v gitignorovaném `apps/api/static_db/` (`.gitignore` ř. 154–156); `apps/api/static/mobile.html` už v gitu **není** (ověřeno `git cat-file -e HEAD:…` = neexistuje). Git deploy tedy publikaci z DB nemá čím přepsat.
3. **Brána v deploy mostu** — `e61f416e` + `080a2116` (C24): runner před commitem zjistí, jestli některý staged soubor není v `g2007.soubor`, a pokud ano, **deploy odmítne** s návodem. Data‑driven, fail‑open (`scripts/claude_sql_runner.py` ř. 1006–1058).

---

## 4. Co zůstává otevřené — tady je reálné riziko dneška

### 4.1 `@@G2007SOUBOR` přepisuje dílek naslepo (nejvyšší priorita)

`modules/erp/api/router.py` ř. 39919–39922:

```sql
UPDATE g2007.soubor SET typ=:t, obsah=:o, slozeno_z=:s, stav_zivota='active', updated_by_text=:by WHERE kod=:k
```

**Žádná kontrola, že mezitím soubor nikdo nezměnil.** Kdo pošle dílek postavený na starším čtení, **umlčí cizí změnu úplně stejně, jako to udělal build 21. 7.** — jen o patro výš, už v databázi. Tabulka navíc nemá sloupec autora (jen volný text `updated_by_text`).

**Návrh (stejný vzor, jaký Marti‑AI prosadila u `znalost-upsert`):** povinný `expected_md5` při editaci existujícího dílku → při neshodě **409 konflikt místo tichého přepsání**. U nového dílku se nepoužije.

*Do té doby náhrada disciplínou:* editovat dílek **chirurgicky přes `UPDATE … replace(obsah, …)` s `AND md5(obsah)='<co jsem četl>'`** místo posílání celého těla. Takhle jsem dnes dělala to tlačítko — když se mezitím soubor změní, UPDATE prostě neprojde (0 řádků), místo aby cizí práci přepsal.

### 4.2 Nikdo nekontroluje, že po publikaci nic nezmizelo

`build_mobile.py` má krok „ověř, že nic jiného nezmizelo" jako **ruční** poslední bod. Nikde není automatické porovnání „co v artefaktu bylo před a po". Právě tohle by bylo 21. 7. chytlo okamžitě.

**Návrh:** `@@G2007SESTAV` ať ve výstupu vrací i **delta**: `delka_pred → delka_po` a počet dílků; při **poklesu délky** ať to explicitně vypíše jako varování. Levné, a zachytí přesně tenhle případ.

### 4.3 Návratovky mostu mlčí i při úspěchu

`@@G2007SOUBOR` i `@@G2007ADD` vracejí neutrální odpověď — úspěch se pozná jen **čtením zpět**. Kdo to nedělá, netuší, jestli zapsal. (Platí i pro `@@G2007SESTAV`, který vrací 0 řádků.)

---

## 5. Co si má kdo ohlídat u sebe

**Jirka (C28) — konkrétně:** nic z 21. 7. mu vytknout nejde, jeho commit byl v pořádku a systémovou díru sám 17. 8. zavřel. Co dává smysl **dodržovat dál a všem stejně**:

1. **Nikdy needituj soubor, který nese hlavičku „GENEROVÁNO"** — `@@G2007SESTAV` ji do artefaktu vkládá právě proto. Zdroj je dílek v `g2007.soubor`.
2. **Před editací dílku ho přečti z DB a poznamenej si `md5`.** Zapisuj proti tomu otisku (viz 4.1), ne z paměti nebo z disku.
3. **Po každém zápisu ověř čtením** (`md5`, `length`) — návratovka mlčí i při úspěchu.
4. **Po publikaci se podívej, že nic jiného nezmizelo** — dokud to nehlídá stroj, hlídá to člověk. Zvlášť u `mobile.html`, kde se potkává 30 dílků od pěti lidí.
5. **Ohlas si práci přes `@@WORK` / `@@LOCK` a mrkni na `@@WHO`.** Když dva sáhnou na týž dílek, tohle je jediné místo, kde je to vidět dopředu.

**My (C24) si máme ohlídat totéž** — ztráta z 21. 7. vznikla u nás, ne u Jirky. Kdybychom 20. 7. zapsali do dílku místo do `mobile.html`, nic by se nestalo.

---

## 6. Doporučené pořadí prací

| # | Co | Kdo | Proč |
|---|---|---|---|
| 1 | `expected_md5` do `@@G2007SOUBOR` (409 při neshodě) | schéma `g2007` vlastní **Marti‑AI** → dělá ona (doktrína #3 + #9) | jediná dnes živá cesta k tichému přepsání |
| 2 | Delta délky ve výstupu `@@G2007SESTAV` + varování při poklesu | C24 nebo C28 | levné, chytá přesně tuhle nehodu |
| 3 | Ověřovací čtení zabudovat do návratovek `@@G2007*` | kdokoliv | ať se úspěch nemusí dohledávat ručně |

---

### Dodatek — jak se opravilo tlačítko (20. 8. 2026)

Zdroj pravdy = dílek `apps/api/static/mobile_parts/73_pref_poptavka.js` v `g2007.soubor`. Obnoveno chirurgickým `UPDATE … replace()` s `md5` guardem (`fe18fafc…`, verze 3 → 4, 18 896 → 21 430 znaků), pak `@@G2007SESTAV apps/api/static_db/mobile.html` (verze 57, zapisuje na disk cloudu — `router.py` ř. 40005). Ověřeno čtením + `node --check` na obnovené funkci. Backend `/app/prefakturace/detail-xlsx` se neměnil, žil celou dobu.

Vráceny i dvě věci, které tentýž commit `82a2886de` shodil s sebou: popisek dlaždice („marže dle pole, výchozí 6 %, nájem bez marže, zdroj mezd Praha") a záložní hodnota marže 5 → 6.
