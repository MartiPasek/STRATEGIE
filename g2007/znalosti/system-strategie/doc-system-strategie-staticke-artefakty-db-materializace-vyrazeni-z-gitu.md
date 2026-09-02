# Staticke artefakty: DB je zdroj pravdy, vyradit z gitu + materializace pri startu (varianta A)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Problem — tri zdroje pravdy
Servirovane staticke soubory (`apps/api/static/*.html`) mohou zit ve TREH mistech: **git** (historie), **g2007.soubor** (DB, zdroj pravdy dle doktriny "kod jako data" 1.-2.8.2026), **disk cloudu** (co appka realne servíruje). Kdyz je soubor trackovany v gitu **I** ulozeny v g2007.soubor, ty dva "vlastnici" se rozjedou a nastava:
- **`dirty_working_tree`** — publikace z DB zapise na disk → disk se lisi od git HEAD → `git pull` na cloudu odmitne → **blokuje deploy VSEM instancim na stroji**.
- **Tiche mazani prace v OBOU smerech** — git deploy prekopiruje git verzi na disk a smaze tim publikaci z DB; a naopak publikace ze STARSI DB verze prepise novejsi git/zivou praci. Bez konfliktu, bez varovani. Realne incidenty 4.-5.8.2026 (smazana denni prace).

## Cilovy stav (varianta A, Marti schvalil 5.8.2026 "A+A")
Soubor vlastni **jen databaze**. Je v `.gitignore` + odebrany z trackingu (`git rm --cached`). Pri startu API se materializuje z `g2007.soubor` na disk.
- Materializace: `apps/api/main.py`, v lifespanu **pred `yield`**. `SELECT kod, obsah FROM g2007.soubor WHERE typ='artefakt' AND stav_zivota='active' AND obsah IS NOT NULL`; zapis na disk s `newline=""` (presne bajty, zadny CRLF preklad), skip kdyz disk uz ma stejny obsah, path-guard (cesta musi zustat pod repo rootem), a **NIKDY nesmi shodit start** (chyba = ERROR do logu + 404 az za behu). Bezi na primaru i sekundaru (kazdy svou slozku). BEZ `fcntl` locku — produkce je Windows.
- Stav k 5.8.2026: takto vyreseno **11 artefaktu**: 6 z 1.8. (foto, index, marti, mobile, overit, vyroba) + 4+1 z 5.8. (dochazka-zakazky, registr-absenci, dochazka-opravy, dochazka-po-zakazkach, martinky). Commit vyrazeni + materializace: `f6308e08`.

## BEZPECNY POSTUP prechodu (aby se NEZTRATILA prace — pouceni z 4.-5.8.)
1. **NEJDRIV srovnat DB na zivy obsah.** "Zive" = co je na disku cloudu (co lidi vidi). Over md5 disk vs `md5(obsah)` v DB. Kde je disk (zive) novejsi nez DB, **importuj zive → DB** bytove presne: `UPDATE g2007.soubor SET obsah=convert_from(decode('<base64_zive_verze>','base64'),'UTF8'), stav_zivota='active', updated_by_text='...' WHERE kod='...'` (base64 = `base64 -w0 <soubor>`; trigger archivuje starou verzi, verze++). Rozhodni "ktera je novejsi" podle `git log -1 <soubor>` (datum commitu) vs `updated_at` v DB. **NIKDY neudelej `git checkout` na soubor, jehoz ziva verze neni v DB** — vratil by starou git verzi na disk = smazal zivou praci (presne takhle se ztratila prace).
2. Az DB=zive u vsech: **jeden commit** = `.gitignore` (pridat soubory) + `git rm --cached --ignore-unmatch <soubory>` + materializace v `main.py`.
3. **Cloud prechod:** materializace pri restartu je **zachranna sit** — at git s diskem udela pri pullu cokoli (nechá starou / smaze), restart zapise spravnou zivou verzi z DB. Proto MUSI byt krok 1 hotovy driv.

## Jak PRIDAT NOVY servirovany staticky soubor spravne (aby past nevznikla)
Dej ho do `g2007.soubor` (`typ='artefakt'`, `@@G2007SOUBOR`) **A** do `.gitignore`; **nikdy ho necommituj do gitu**. Edituj pres DB (`@@G2007SOUBOR`/`@@G2007PUBLISH`), ne primo na disku.

## Gotchy
- `length(obsah)` v PG = pocet ZNAKU, ne bajtu (cestina = multibyte). Pro porovnani pouzij `md5(obsah)` vs md5 souboru, ne delku.
- `@@G2007PUBLISH` self-test viz `doc-system-g2007-g2007publish-selftest-event-loop-starvation`.
- Push commitu s `git rm --cached` mustaci pres MOST (deploy runner, PAT) — osobni ucty clenu nemaji push pravo do MartiPasek/STRATEGIE. Runner udela `git commit — SKIP` kdyz uz je commitnuto lokalne a stejne pushne.

## Prevence do budoucna (navrzeno 5.8., ceka na Martiho)
Hlidac v deploy toku: porovnat `git ls-files apps/api/static` × seznam artefaktu v `g2007.soubor`; prekryv (soubor v OBOU) = varovani/stop s navodem ".gitignore + git rm --cached". Chyti past DRIV nez zablokuje deploy. Alternativy: siroky `.gitignore apps/api/static/*.html`, nebo jen konvence (tento zaznam).

## ⚠️ Hranice: co v `g2007.soubor` JE a co tam NENÍ (ověřeno 2. 9. 2026)

**Doplněno 2. 9. 2026** (Claude-28 / Jirka Honomichl, na pokyn Marti-AI). Tenhle dokument
mluví o **servírovaných artefaktech** (`apps/api/static/*.html`). Neplatí ale na celou
složku `apps/api/static/` — a kdo si to tak vyloží, **bude zbytečně hledat v databázi
něco, co tam vůbec není**.

Změřeno dotazem nad `g2007.soubor` podle prefixu cesty:

| cesta | záznamů v `g2007.soubor` | kde je zdroj pravdy |
|---|---|---|
| `apps/api/static/mobile_parts/**` | **31** | **databáze** — na disku needitovat |
| `apps/api/static_db/**` | **13** | **databáze** — na disku needitovat |
| `apps/api/static/erp/**` (obrazovky ERP) | **0** | **git** — edituje se v repu a mění se nasazením |
| zbytek `apps/api/static/**` | **0** | **git** |

Prakticky: komponenty ERP (např. `apps/api/static/erp/components/page_render.js`)
se **mění v gitu a nasazují**, ne přes `@@G2007SOUBOR`. Doloženo mimo jiné commity
`a2da6fef` (1. 9. 2026) a `07949aee` (2. 9. 2026) a shodně to popisují i znalosti
[[doc-osoba-hr-dashboard-uzel]] a [[doc-vyroba-vyhodnoceni-zakazek]].

