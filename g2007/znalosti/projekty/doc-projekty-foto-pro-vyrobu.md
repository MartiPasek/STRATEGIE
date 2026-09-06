# Fotky pro výrobu — fotodokumentační modul (Etapa 1)

> oblast: `projekty` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> **ZMENA 6. 9. 2026 - dlazdice se dnes jmenuje jinak a druha cesta byla zrusena.**
> Dlazdice v Aplikacich se nove jmenuje **📷 Foťáky výroba** (driv byla bez hacku) a druha dlazdice „Fotky“ na pracovni
> plose Vyroby **byla odstranena** - na stranku fotek ted vede jedina cesta.
> Stranka sama ma nove v appce nadpis „📷 Foťáky výroba“ misto obecneho „Prehled“.
> Text nize popisuje stav k 29. 7. 2026 a v tomhle bodu uz neplati.
> Rozhodl Jiri Honomichl 6. 9. 2026.

> **POSTUP UVNITŘ SROVNÁN 6. 9. 2026.** Do té doby tenhle dokument předepisoval sestavování
> mobilní stránky přes `scripts/build_mobile.py` a commit `mobile.html` do gitu — **tak se to
> už nedělá** a kdo se tím řídil, jeho práce se do appky nedostala a nikde to nenahlásilo chybu
> (přesně takhle se 5.–12. 8. 2026 tiše zahodila práce Peti a Šárky). Věta uvnitř je opravená
> na skutečný stav; závazný postup pro celou síť drží
> `doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje`.
> (Varování doplnil Claude-28 18. 8. 2026, text srovnán 6. 9. 2026 — obojí na zadání
> Jiřího Honomichla, schválila Marti-AI.)

# Fotky pro výrobu — fotodokumentace (Etapa 1, nasazeno 29.7.2026, C23 + Marti)

**STAV k 29.7.2026 večer:** Etapa 1 KOMPLETNÍ a živá v appce. Dlaždice **📷 Fotáky výroba** v Aplikace → 🏭 Výroba & obchod (+ „Fotky" uvnitř Výroby) → stránka `/foto`. Focení + offline pre-check rozmazanosti + upload (media) + AI hodnocení (známka/verdikt ok-prefotit) fungují. Marti to od večera 29.7. zkouší a ladí z domova (prahy modelu datové, bez deploye). Commity: schéma+data (line 2), `e5a89508f` backend+UI, `89f9e6c57` AI hodnocení, `cc79f7efb` rebuild mobile.html.

Univerzální fotodokumentace opřená o Ondrův (INTERSOFT) systém `ai-processing-v2`. Cíl: focení k předmětu (generické — zakázka i cokoliv), offline kontrola rozmazanosti + AI hodnocení kvality, napojené do naší PWA.

## Kde co žije (ověřeno živě přes most)
- **DB_EC (kancelář, `db=mssql`)**: jen `EC_FotoSestavy` (58 = katalog „co se fotí", skupiny+záběry, VzoroveFoto, Napoveda, VyberZakazky) + view `ECv_REST_FotoSestavy` + SP `ec_rest_foto_PrihlasUzivatele`. Pomocná tabulka pro Android appku.
- **Ostrý AI systém NENÍ v EUROSOFT DB_EC** — běží v `HeliosDB` na 192.168.99.15 (INTERSOFT). Ondra poslal DDL v `analyzaFotky.zip`: tabulky `EC_Foto_NahraneFotografie`, `EC_foto_VysledkyAnalyzyFotografii` (metriky+AI 1:1), `EC_foto_VysledkyHodnoceniFotografii`, `EC_foto_AiModely` (váhy/prahy/hranice Excellent8/Good6/Fair4/prompt), `EC_Foto_AnalyzaZakazky` (coverage), `EC_Foto_FotografieProTrenovani`; procedury `ec_rest_foto_ZapisVysledek*`, `...ZahajAnalyzuZakazky`, `...NeuspesnaAnalyzaFotografie` (exp. backoff 1→30 min), `...Resetuj*`.
- Ondrův balík (offline metriky BRISQUE/Laplacian/blur/edge/gradient/perceptual + Azure OpenAI vision + prompty electrical_panel/general_quality) = referenční architektura.

## Co jsme postavili u nás (PostgreSQL, schéma tenant)
- Tabulky `tenant.foto_*` (8): `foto_model`, `foto_sablona`, `foto_zaber`, `foto`, `foto_vysledek`, `foto_hodnoceni`, `foto_analyza`, `foto_trenink` — 1:1 překlad z Ondrova modelu, jen generické (`predmet_typ`+`predmet_ref` místo natvrdo zakázky), binárka přes modul `media` (`foto.media_id`), autor=`user_id`.
- Seed: model `vychozi` (Excellent8/Good6/Fair4) + šablona `zakazka_rozvadec` + 37 záběrů importovaných z `EC_FotoSestavy` (Rozvaděč 8, Pulty 8, Příbal/Zásilka 4…).
- Backend `modules/erp/api/foto.py` → router `/api/v1/erp/app/foto/*`: `sablony`, `sablona/{kod}`, `attach`, `sada`, `smazat`, `prehled`, `vyhodnotit`. Registrace v `apps/api/main.py`.
- Stránka `apps/api/static/foto.html` na route `/foto` (auth přes cookie, `credentials:include`) — testovací focení: výběr zakázky+šablony, strom záběrů, focení telefonem (`input capture`), **offline Laplacian pre-check rozmazanosti v prohlížeči**, upload přes `/api/v1/media/upload`, auto-hodnocení, coverage bar.
- Dlaždice **📷 Fotky** ve Výrobě (`mobile_parts/52_vyroba.js`, `vyroba_hub`) → `openInApp('/foto')`.
- AI hodnocení `/vyhodnotit`: offline Laplacian (PIL+numpy, Ondrova normalizace) + Anthropic **vision Haiku** (`claude-haiku-4-5-20251001`) s promptem z `foto_model.ai_prompt_text` → JSON metriky → `foto_vysledek`+`foto_hodnoceni`, verdikt ok/prefotit (tvrdý override na rozmazanost).

## Gotchy / rozhodnutí
- **cv2 (opencv) NENÍ v serverovém venv** (jen v pyproject Pillow+numpy) → offline metriky přes PIL/numpy (Laplacian). BRISQUE/edge doplnit až bude potřeba.
- **Cloud `/deploy/now` občas vrátí HTTP 401** („Nejsi přihlášen") — přechodné; **retry CLAUDE_DEPLOY** projde (commit už je, watcher udělá noop-commit + push + deploy). Stejný přechodný 401 viděn i u čtení mostu.
- **Line 2 mostu** (`CLAUDE2_*`) použít při souběhu s ostatními instancemi (hlavní kanál drží C24/C26/C28). DDL/DML přes `db=pg` → banner; diakritiku v payloadu řešit **base64** (`convert_from(decode(...),'UTF8')`) nebo commitnout SQL jako soubor přes device_commit_files (mount jinak UTF-8 mrví).
- Model kvality je **datový** (váhy/prahy/hranice/prompt v `foto_model`) — laditelné bez deploye, jako Ondrovo `EC_foto_AiModely`.
- **⚠️ Změna dílku se v appce NEPROJEVÍ sama — musí se publikovat.** Dílky i sestavená stránka
  žijí **v databázi** (`g2007.soubor`); po úpravě dílku vždy `@@G2007PUBLISH apps/api/static_db/mobile.html`,
  jinak lidé v telefonu vidí starou verzi. Po publikaci navíc appka drží starou verzi v cache
  → pull-to-refresh.
  *(Opraveno 6. 9. 2026 — do té doby tu stálo „spusť `python scripts/build_mobile.py` a NECOMMITNEŠ-li
  i `mobile.html`, nezobrazí se to"; ten skript od 17. 8. 2026 jen vypíše varování a ani dílky,
  ani sestavená stránka už v gitu nejsou. Původní zkušenost autora platí dál — dlaždice „Foťáky"
  nebyla vidět, dokud se balík nepřestavěl; dnes je tím krokem publikace. Zadal Jiří Honomichl.)*

## Další kroky (TODO)
- Doplnit offline metriky (BRISQUE/edge/gradient) a coverage worker (`foto_analyza`, obdoba `ec_rest_foto_ZahajAnalyzuZakazky`).
- Přehled pro vedoucího nad `/app/foto/prehled`. Případně zrcadlení historie z HeliosDB. Import vzorových fotek (VzoroveFoto) k záběrům.

