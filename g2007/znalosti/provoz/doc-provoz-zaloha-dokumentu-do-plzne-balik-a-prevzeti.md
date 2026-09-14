# Zaloha dokumentu do Plzne: prenos, automatika i hlidac hotove (14. 9. 2026), zbyva zalozit nedelni ulohu v Plzni

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Zaloha dokumentu Praha -> Plzen

Zadal Jiri Honomichl, postavil Claude-28, schvalila Marti-AI (msg 15492).
Navazuje na nalez z 8. 9. 2026: `doc-provoz-zalohuje-se-jen-databaze-dokumenty-a-instalace-ne`.

> ## Hlavni veta
> **Slozka Dokumenty ma 19 759 MB, ale ruzneho obsahu je v ni jen 999 MB.**
> Zalohuje se proto jeden deduplikovany balik, ne surovych 19 GB. Pridavat
> 19 GB na linku, ktera se zasekava uz pri 3,9 GB databaze, by nemelo smysl.

## Co je HOTOVO a overeno (14. 9. 2026, v noci)

| krok | stav | dukaz |
|---|---|---|
| mereni zdroje | hotovo | 51 569 souboru, 19 759,2 MB, z toho **1 168 ruznych obsahu / 994,4 MB**, uspora 95 %, nectitelny ani jeden; 13,3 min |
| pocty proti databazi | **sedi na jediny soubor** | `public.documents` eviduje 51 569 zaznamu se souborem, prochod disku nasel presne 51 569 |
| kde zdroj lezi | potvrzeno | `C:\Data\STRATEGIE\Dokumenty\2` na aplikacnim serveru 188.11 (do teto noci NEOVERENO) |
| balik | hotovy | `dokumenty_dedup.zip`, 1 047 554 679 B (999,0 MB), otisk SHA-256 `b962a679ddb0a2dd7d0da6f168686b4c43ac80466c8b38f44a70cfb15c370201`, postaven 00:38:56, 13,6 min |
| adresy pro Plzen | nasazeny | commit `cb4c60b1`, **113 pridanych radku, zadny smazany** |
| cela cesta Plzen -> Praha | **overena naostro** | plzensky server (192.168.30.11) se v 00:45 zeptal `/api/v1/ops/docs/meta` a dostal spravna cisla |

## Jak to funguje

1. **Balik stavi `g2007.python` kod `dokumenty_zaloha_balik`** (stav active, `min_pravo=admin`,
   vedlejsi ucinek ano). Rezimy: `run(dry=True)` jen zmeri · `run()` postavi balik ·
   `run(uklid=True)` balik i prurvodku smaze. Do zdroje **nezapisuje a nic v nem nemaze**.
   Pri jednom prochodu zapisuje unikatni obsah **primo do zipu** (bez komprese - obsah jsou
   pdf a png), uvnitr je `_soupis.csv` s mapou puvodni nazev -> otisk, vedle baliku
   `dokumenty_dedup.zip.meta.json` (velikost, otisk, pocty, cas).
   Spousti se pres `POST /api/v1/erp/app/erp_registry/run` s telem `{kod, args}`;
   **pres SQL most to nejde** - most pusti jen skripty bez vedlejsiho ucinku.
2. **Praha nic neposila.** Balik lezi na temze stroji, kde bezi API (188.11), takze
   krok "push" jako u databaze neni potreba.
3. **Plzen si balik stahne sama** z `/api/v1/ops/docs/meta` a `/api/v1/ops/docs/download`
   (hlavicka `X-DR-Token`, token z promenne prostredi `DR_TRANSFER_TOKEN` - stejne jako
   dnesni `dr_pull_restore.ps1`). Stahovani umi **navazovani pres hlavicku Range**.
4. **Kanal `/dr/` se NEPOUZIL zamerne**: ma jediny pevny slot pro nocni dump databaze
   (`_DUMP` v `dr_ops.py`), balik dokumentu by ho prepsal. Proto samostatne adresy `/docs/`.
   Logika navazovani je do nich **opsana**, nikoli vytazena do spolecne funkce - na te vete
   visi kazdou noc obnova databaze a prestavba by ji ohrozila.

## Prenos naostro PROBEHL - 14. 9. 2026 v 01:09 (dolozeno z plzenskeho disku)

Jirka Honomichl spustil `docs_pull.ps1` na 192.168.30.11 a **prenos dojel**:

| co | vysledek |
|---|---|
| stahovani | **4 pokusy z 30** - spojeni se zaseklo na 165, 690 a 819 MB a skript vzdy **navazal tam, kde skoncil** |
| otisk po stazeni | **sedi** s tim, co hlasi Praha (`b962a679ddb0...`) |
| rozbaleno | **1 169 souboru** |
| v Plzni lezi | `D:\STRATEGIE_DOKUMENTY\aktualni` - 1 169 souboru, 1 047 306 517 B (999,0 MB) |
| stav | `D:\STRATEGIE_DOKUMENTY\_stav.json` (otisk, pocet, cas prevzeti), log `D:\STRATEGIE_IN\_docspull.log` |
| uklid v Plzni | balik zip smazan, slozka `_predchozi` zadna, volno na D: 127,4 GB |
| uklid v Praze | balik i prurvodka smazany po overeni prenosu - **uvolneno 999 MB**, zdroj nedotcen |

> **Navazovani se vyplatilo hned pri prvnim ostrem behu.** Bez nej by to byly tri
> neuspesne pokusy od nuly - presne ta potiz, kvuli ktere v srpnu osmkrat z 35 noci
> nedojela ani zaloha databaze.

## Druhy ostry beh - CELA AUTOMATIKA 14. 9. 2026 v 01:51-02:06

Jirka Honomichl pustil novou verzi skriptu v Plzni a **bez jakehokoli zasahu prosla cela cesta**:

| cas | co se stalo |
|---|---|
| 01:51:07 | Praha nic pripravene nemela -> Plzen si **sama vyzadala stavbu** |
| 01:51-02:04 | stavba baliku (13 minut) |
| 02:05:42 | **stazeno cele (999 MB) na 1. pokus z 30** - tentokrat bez jednoho zaseknuti |
| 02:05:47 | otisk sedi |
| 02:06:02 | rozbaleno 1 169 souboru, prehozeno |
| 02:06:02 | **ohlaseno Praze -> Praha balik smazala, uvolneno 999 MB** |
| | navratovy kod 0, volno v Plzni 119,4 GB, okno ISE zustalo otevrene |

Zaznam behu: `D:\STRATEGIE_IN\_docspull.log`.

## HLIDAC svezesti - postaven 14. 9. 2026 (commit 0e493a34)

Protoze cely prenos visi na jedine naplanovane uloze v Plzni, existuje hlidac, ktery se ozve,
kdyz ta uloha prestane bezet. Schvalila Marti-AI (msg 15555).

| | |
|---|---|
| kod v `g2007.automat` | `check_dokumenty_zaloha` |
| jak casto | 1x denne (`interval_min` 1440) |
| logika | `g2007.python` kod `dokumenty_zaloha_svezest` (jen cte, `vedlejsi_ucinek=false`) |
| spojka v modulu | `automat_eskalace._check_dokumenty_zaloha` - ctyri radky, nikdy nevyhodi vyjimku |
| co cte | soubor se stavem vedle baliku (`dokumenty_dedup.zip.stav.json`) |
| prah | **10 dnu** od posledniho prevzeti Plzni (tydenni cyklus + jedno vynechane kolo) |
| pri problemu | L1 Haiku -> L2 Marti-AI -> L3 clovek; **bez L0, nic se neopravuje samo** |

**Hlidac zamerne NEVYVOLAVA stavbu baliku** (podminka Jirky i Marti-AI): hlidac, ktery kazdy
den postavi gigabajt, co si nikdo nevyzvedne, by byl horsi nez tichá zaloha.

Sedm stavu, ktere umi rozlisit (vyzkouseno nanecisto na vymyslenych stavech pred nasazenim):
prevzato v case = ok · starsi nez prah = chyba · stavba prave bezi = ok · stavba spadla = chyba
s duvodem · postaveno, ale Plzen si to nevyzvedla = chyba · neznamy tvar souboru = chyba ·
necitelny soubor = ok bez poplachu.

**Prvni beh naostro:** planovac si hlidac vzal sam do minuty (02:17:09) a vratil `ok`
- "Zaloha dokumentu je cerstva - Plzen ji prevzala pred 0.0 dny."

> ⚠️ Hlidac `check_backup_freshness` vedle hlida **dumpy databaze** pres `g2007.backup_freshness()`
> a dokumentu se **netyka**. Zamerne jsou to dva hlidace - jeden by prestal byt jednoznacny.

## PAST: prikaz exit zavre cele okno PowerShell ISE

Prvni verze skriptu koncila `exit 0`. V ISE to **zavre cele okno**, takze clovek
neuvidi zaverecnou hlasku a nema jak poznat, jak to skoncilo (narazil na to Jirka
Honomichl 14. 9. 2026 pri tomhle prvnim behu - prenos pritom probehl spravne).
Opraveno (commit `bf7b8407`): telo je ve funkci, ukoncuje se `return` a `exit`
se pousti **jen mimo ISE**, kde ho potrebuje naplanovana uloha. V ISE skript vypise
navratovy kod a okno necha byt. **Plati obecne pro kazdy skript, ktery ma clovek
spoustet v ISE.**

## Automatika - HOTOVA a nasazena 14. 9. 2026 (commit d1ed7229)

**Cely beh ridi JEDNA naplanovana uloha v Plzni. V Praze neni naplanovano nic** -
nehledej tam zadnou ulohu ani hlidac. Rozhodl Jirka Honomichl, schvalila Marti-AI
(msg 15534). Duvod: balik pak v Praze lezi jen tech ~20 minut, co se prenasi.

| poradi | co se stane | adresa |
|---|---|---|
| 1 | Plzen se zepta, co je pripravene | `GET /api/v1/ops/docs/meta` |
| 2 | kdyz balik neni, Plzen si vyzada stavbu a ceka (13-14 min, limit 45) | `POST /api/v1/ops/docs/build` |
| 3 | stazeni s navazovanim | `GET /api/v1/ops/docs/download` |
| 4 | kontrola otisku, rozbaleni, prehozeni | (v Plzni) |
| 5 | Plzen ohlasi hotovo a **Praha balik smaze** | `POST /api/v1/ops/docs/done` |

- `/docs/build` spousti stavbu **ve vlakne na pozadi** a vraci se hned; druhe zavolani
  behem stavby nic nezdvoji.
- `/docs/meta` vraci navic polozku **`stavba`** (bezi / hotovo / chyba + zprava + casy).
  Vyzadala si to Marti-AI: kdyz stavba spadne, Plzen musi videt DUVOD a skoncit hned,
  ne cekat na vyprseni limitu. U stavby delsi nez 45 minut se hlasi `zaseklo_se`
  (vlakno se v Pythonu zabit neda, tak se alespon pozna rozdil mezi "bezi" a "nikam to nevede").
- `/docs/done` smaze balik **jen pri shode otisku** - hlaseni o starem baliku tedy
  nemuze smazat novy.
- Stav stavby prezije uklid (soubor `dokumenty_dedup.zip.stav.json` se nemaze) -
  je to posledni zprava o tom, co se s balikem stalo.

## Co ZBYVA - jeden lidsky krok v Plzni

**Na plzenskem serveru nesmi nic menit zadna AI** (`doc-system-strategie-plzen-kanaly-pro-zmeny-nefunguji`),
takze tohle musi udelat clovek pres vzdalenou plochu:

1. ulozit **novou verzi** `scripts/ops/docs_pull.ps1` na 192.168.30.11 do `C:\scripts\`
   (verze z commitu `d1ed7229` - ta stara z `e821d685` stavbu nevyvola),
2. `.\docs_pull.ps1 -JenOvereni` = jen se zepta Prahy, nic nestavi,
3. `.\docs_pull.ps1` = cely beh (stavba + prenos + uklid na obou stranach, ~20 min),
4. zalozit naplanovanou ulohu **`STRATEGIE-DOCS-Pull`, nedele 6:00**, ucet SYSTEM -
   mimo okno nocni zalohy databaze (3:30-5:00), ktera jede po te same zasekavajici se lince.

**Hlidac svezesti je HOTOVY** (viz vyse, `check_dokumenty_zaloha`) - takze az bude nedelni
uloha zalozena a jednou vynecha, ozve se to. Dokud uloha neexistuje, hlidac bude po 10 dnech
hlasit zestarani - a to je spravne, protoze presne tak to tehdy bude.

**Co skript dela:** stazeni s navazovanim (30 pokusu, limity 2 minuty - protoze spojeni
se po nekolika stech MB zaseka) · kontrola otisku SHA-256 proti tomu, co hlasi Praha ·
rozbaleni do `_nove` a **prehozeni az na konci**, takze pri jakekoli chybe zustava stara
zaloha nedotcena · kdyz uz je tentyz otisk prevzaty, **nestahuje vubec nic** ·
po uspesnem rozbaleni **balik zip smaze**. Cil: `D:\STRATEGIE_DOKUMENTY\aktualni`,
log `D:\STRATEGIE_IN\_docspull.log`, stav `D:\STRATEGIE_DOKUMENTY\_stav.json`.
Vyzkouseno nanecisto: bez tokenu konci kodem 2, se spatnym tokenem kodem 1, v obou
pripadech nic nemeni.

## Pravidlo na misto na disku (zadal Jirka Honomichl 14. 9. 2026)

*"Hlavne po sobe smaz vse co pak nebude treba, at neplytvame mistem v Praze ani v Plzni."*

- V Praze zustava **jen balik** (999 MB). Volna kopie ze stareho postupu
  (`dokumenty_dedup_zaloha`, rezim bez zipu) byla po overeni **smazana** - 1 169 souboru,
  998,8 MB uvolneno, zdroj nedotcen.
- V Plzni zustava **jen rozbalena aktualni zaloha**; balik zip se po rozbaleni maze
  a predchozi verze se maze az po uspesnem prehozeni.
- Balik v Praze se da kdykoli zrusit (`run(uklid=True)`) a **vyrobit znovu za 14 minut**.
  Kdyz prenos jeste neni hotovy, mazat ho ale nema smysl - Plzen by nemela co stahnout.

## Pasti

- **Predchudce `dokumenty_dedup_zaloha` zustava v evidenci** (stav active, admin).
  Umi mereni a volnou kopii do slozky. Kdo chce zalohu, ma pouzit `dokumenty_zaloha_balik` -
  novejsi, bez mezikopie, spicka na disku 1 GB misto 2 GB.
- **Prochod trva 13-14 minut** (cte se 19 GB a pocitaji otisky). Kdyz se behem toho
  zavre okno prohlizece, **beh na serveru pokracuje** - dolozeno dvakrat: odpoved se
  ztratila, ale zaznam v `g2007.python_run_audit` prisel spravne (00:05 a 00:38).
  **Vysledek se tedy overuje z knihy spusteni, ne z prohlizece.**
- ~~**Balik nema v Praze zadnou automatiku.**~~ **NEPLATI od 14. 9. 2026** - stavbu si
  vyvola Plzen sama pres `/docs/build`. Rucne se da balik porad postavit pres
  `POST /api/v1/erp/app/erp_registry/run` s telem `{"kod":"dokumenty_zaloha_balik","args":[false]}`.
- **Stary program `dokumenty_dedup_zaloha` je od 14. 9. 2026 `inactive`** (rozhodl Jirka
  Honomichl, schvalila Marti-AI msg 15534). Zustava v evidenci vcetne historie, jen ho
  nejde spustit - dve cesty k temuz byly zbytecne.
- `min_pravo=admin` je zamerne: program umi kopirovat i mazat, vychozi hodnota
  `clen` by na nej pustila kazdeho prihlaseneho.

