# Zaloha dokumentu do Plzne: balik v Praze hotovy a overeny, v Plzni zbyva jeden lidsky krok (14. 9. 2026)

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

## Co ZBYVA - jeden lidsky krok v Plzni

**Na plzenskem serveru nesmi nic menit zadna AI** (`doc-system-strategie-plzen-kanaly-pro-zmeny-nefunguji`),
takze posledni clanek musi udelat clovek pres vzdalenou plochu:

1. ulozit `scripts/ops/docs_pull.ps1` (v repozitari, commit `e821d685`) na 192.168.30.11 do `C:\scripts\`,
2. spustit `.\docs_pull.ps1 -JenOvereni` (nic nestahne, jen vypise, co Praha nabizi),
3. spustit `.\docs_pull.ps1` (prevezme zalohu),
4. zalozit naplanovanou ulohu `STRATEGIE-DOCS-Pull`, **1x tydne v nedeli 6:00** - tedy mimo
   okno nocni zalohy databaze (3:30-5:00), ktera jede po te same zasekavajici se lince.

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
- **Balik nema v Praze zadnou automatiku.** Zatim se stavi rucne na pozadani; automatika
  je dalsi krok a delame ji az po overeni prenosu (rozhodnuti: dve nove veci naraz ne).
- `min_pravo=admin` je zamerne: program umi kopirovat i mazat, vychozi hodnota
  `clen` by na nej pustila kazdeho prihlaseneho.

