# 223 — GO VP: pošta projects@ znovu živá + dobírka příloh (co splnilo bod 8/9 z 222)

**Stav:** vyřešení vstupní podmínky trychtýře · 21. 7. 2026 · Claude (C23), přes bridge · ověřeno na produkci

Navazuje na dok **222** (trychtýř zakázek). Dok 222 končí zjištěním, že celý funnel stojí na jednom předpokladu (bod 8/9): **`projects@` je od 7. 7. slepá — mrtvá nálevka = prázdný funnel.** Úkol #44 = data-based freshness jako vstupní podmínka. Tento dok popisuje, jak se ta podmínka splnila — a co u toho vyplavalo (přílohy + systémové riziko RAG procesu).

---

## 1. Pošta znovu teče (freshness — HOTOVO dopředu)
Ověřeno na `tenant.mail_message` (schránka `projects@` = user 111) k 21. 7. odpoledne:

- Poslední e-mail dorazil **21. 7. 13:39**, synchronizován **13:40** — zpoždění mirroru ~1 minuta (prakticky real-time).
- Job **`sync_mail_projects`** (`fw.mirror_job`): `enabled=true`, poslední běh **21. 7. 13:41** (+20 zpráv), další naplánován. Stav „přerušeno (recyklace workeru) — naváže" NENÍ chyba, jen restart workeru.
- Průběh zámku → rozmrznutí (počet e-mailů/den): 7. 7. = 53 (poslední den před zámkem) → **8.–19. 7. ≈ 0** (zámek) → **20. 7. = 153** (rozmrznutí/dobírání) → **21. 7. = 107** (živě).

**Bod 8/9 z 222 (freshness, úkol #44) je pro projects@ splněný.** Řídící věž jela na zdravé řece (Centrála) celou dobu; teď teče i ta mailová.

## 2. Díra, kterou to odhalilo — chybějící přílohy
Tělo e-mailů se zrcadlí, ale **přílohy padaly jen dopředu, od 20. 7.** Rozsah:

- Přílohy se ukládají kompletně (soubor + vytěžený text) **od 20. 7.** — 70 e-mailů 20.–21. 7. mělo přílohy v pořádku.
- **Chybělo 466 příloh z doručených e-mailů 17. 6.–7. 7.** — zprávy měly `ma_prilohy=true`, ale `prilohy_doc_ids` prázdné (pipeline je tenkrát nestahovala). Vše ve složce „doručené"; odeslané měly přílohy kompletní.

## 3. Root cause — NENÍ to Exchange, je to RAG proces
Klíčové zjištění. Přílohy jdou přes `_save_attachments` → `upload_document` (modul RAG), který u každého souboru **synchronně** volá `process_document` = extrakce textu → OCR → embeddings.

- Ta indexace **zamrzla na jednom GIFu** (`image002.gif` — podpisový obrázek), který zůstal 13 minut `is_processed=false` a **zablokoval celý jednovláknový loop dobírky**.
- Proto se každý pokus po ~14 zprávách zasekl — ne kvůli stahování z Outlooku (EWS), ale kvůli synchronní indexaci jednoho problémového souboru.
- Naivní hromadný sync (`@@MAILSYNC ... since=`) navíc jde od nejnovějších a tahá u každé zprávy celé HTML tělo (~400 kB) — k historickým na konci se ani nedostane.

## 4. Oprava (nasazeno na produkci)
Dvě věci, obě přes bridge auto-deploy:

1. **Cílená dobírka** — nová funkce `backfill_att` v `modules/erp/api/mail_mirror.py` + příkaz **`@@MAILATTFIX <uid> [max]`** (commit `ceac6399b`). Vytáhne z EWS **jen zprávy, které mají přílohu bez stažených dokumentů**, po jedné podle `ews_item_id`. Resumovatelné (bere jen stále chybějící), odolné vůči EWS (FaultTolerance bounded + timeout + pauzy).
2. **`skip_processing`** — dobírka **ukládá jen soubor**, těžká indexace se přeskočí (commit `3210d1cf5`). Přidán volitelný `skip_processing` do `upload_document` + `process` do `_save_attachments`. Jeden špatný soubor už nezasekne loop.

Výsledek: dobírka jede plynule (k 21. 7. 14:18 doplněno 269 ze 466, zbývá ~197, dokončuje se). Přílohy jsou **uložené a otevíratelné v poště**.

## 5. Zbývá dořešit (poctivě)
1. **Doindexace do RAG** — doplněné historické přílohy jsou uložené, ale kvůli `skip_processing` **nejsou zaindexované do RAG** (AI v nich zatím neumí vyhledávat). Je to samostatný, dávkově dávkovaný krok — spustit až po dokončení dobírky a **až po ošetření bodu 2**.
2. **Systémové riziko: `process_document` se může zaseknout i v běžném syncu.** Kdyby přišel nový e-mail s problémovou přílohou (GIF, poškozené PDF), synchronní zpracování může zamrznout poštovní job stejně jako předtím dobírku. Doporučení: **timeout / async zpracování příloh** v `process_document`. Malá, ale důležitá pojistka (a pravděpodobně jedna z příčin dřívějších zámků pošty).
3. **Sesterské schránky** `eliška` a `p.zeman (CRM)` běžely naposledy 18. 7. (lag ~3 dny). Pro VP trychtýř nevadí (tam jede jen `projects@`), ale patří to do úklidu.

## 6. Ops poznámky (pro příště)
- Bridge příkazy: **`@@MAILSYNC <uid> [limit] [noatt] [since=]`** = plný sync schránky (newest-first, tahá těla — na historii nevhodný). **`@@MAILATTFIX <uid> [max]`** = cílená dobírka jen chybějících příloh (store-only, resumovatelné).
- Metrika hotovo: `tenant.mail_message WHERE user_id=111 AND ma_prilohy AND (prilohy_doc_ids IS NULL OR prilohy_doc_ids::text IN ('','[]','null'))` → počet = kolik ještě chybí.
- Nikdy nespoléhat na jeden background thread bez pojistky — `sync_user_bg`/`backfill_att_bg` jsou fire-and-forget daemony; když spadnou, nikdo to neohlásí. Monitorovat přes DB metriku, re-trigger je idempotentní.

---
*Zapsal Claude (C23) přes bridge, 21. 7. 2026. Aktualizuje předpoklad z dok 222 (bod 8/9) + úkol #44. Mechanismus a follow-upy jsou trvalé; číslo dobírky je snapshot dne.*
