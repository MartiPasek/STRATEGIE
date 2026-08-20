# Orchestrace Martinek v1 - NASAZENO A OVERENO E2E (2.8.2026): g2007.ukol + dispatcher + Agent Inbox UI

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co je nasazeno (2.8.2026, C23 + Marti, plan v docs/martinky_org_struktura_navrh_2026-08-02.md)

Org. struktura AI agentu dle Martiho vize: ~20 Martinek (1 typ kalkulace / 1 zakaznik = domena) + maminka (dispatcher, casem Eliscina konverzacni vrstva) + Marti-AI/Marti oversight. Stavi na architekture Marti-AI #280 (Martinka = domena na konverzaci, NE nova identita) a na rozhodnutich Marti 2.8.: (1) fronta prace = NOVE tabulky v g2007 s ceskymi nazvy, (2) hybrid dispatch = event pri zadani + rucni trigger + prepinac, (3) schvalovani vysledku clovekem prepinatelne.

## Datovy model (DDL request #1660)
- g2007.ukol: domain_kod (FK tool_domain), predmet, popis (delegacni kontrakt CIL/VYSTUP/PODKLADY/HRANICE), stav (zadan|bezi|blokovan|ceka_na_cloveka|ke_schvaleni|hotovo|selhal|zrusen), priorita, termin, zadal_user_id, resitel_user_id (default 2 = Marti-AI), vysledek, vysledek_ref, conversation_id, pokusu, posledni_beh_at, schvalil_user_id, schvaleno_at.
- g2007.ukol_potreba: ukol_id, typ (chybi_vstup|potrebuje_schvaleni|chybi_data|chyba_nastroje|...), od_koho_user_id, co, stav (otevrena|splnena|zrusena), vyreseni. STRUKTUROVANE potreby = "maminka vi co deti potrebuji" pres SELECT, ne cteni konverzaci.
- g2007.nastaveni: martinky_event_dispatch (on/off), martinky_autoschvaleni (on/off).

## Skripty (g2007.python, kategorie='martinky', vse min_pravo=clen, aktivni v1/v2)
martinka_ukol_zaloz(uid, domain_kod, predmet, popis, priorita, termin) - zalozi + event dispatch v daemon threadu; martinka_dispatch(uid, ukol_id=None) - vezme 'zadan' ukoly, stav='bezi', postavi goal (kontrakt + POVINNY FORMAT ZAVERU s markery), vola martiai_agent_service.run_goal (guardy: kill switch, rozpocty, ruce dle cil_ruce_enabled), parsuje [STAV: HOTOVO] / [POTREBA typ=... co=...] -> ke_schvaleni|hotovo / ukol_potreba + ceka_na_cloveka|blokovan / selhal; martinka_prehled(uid) - data pro UI; martinka_potreba_vyres(uid, potreba_id, vyreseni) - splni potrebu, vyreseni APPENDUJE do popisu ukolu (Martinka to pri dalsim behu vidi), kdyz 0 otevrenych potreb -> zpet 'zadan' + event dispatch; martinka_ukol_schval(uid, ukol_id, schvalit|vratit|zrusit, poznamka) - vratit appenduje pripominku do popisu + re-dispatch.

## UI (g2007.soubor artefakt, zadny deploy)
https://strategie-ai.com/static/martinky.html - pocty per stav, AGENT INBOX (otevrene potreby vsech AI na jednom miste, tlacitko Vyresit/dodat), tabulka ukolu (Schvalit/Vratit/Spustit/Zrusit), Novy ukol s sablonou delegacniho kontraktu, rucni "Spustit dispatcher" pro debug. Vola POST /app/erp_registry/run (cookie auth).

## OVERENO E2E naostro (2.8. ~17:30, pres Claude-in-Chrome pod Martiho session)
Ukol #1 (HOTOVO vetev): zadan -> event -> Martinka bezela -> "Soucet 15+27=42..." -> ke_schvaleni -> clovek schvalil -> hotovo. Ukol #2 (POTREBA vetev): Martinka spravne NIC nedomyslela, ohlasila POTREBA chybi_vstup "Kusovnik (BOM)..." -> ceka_na_cloveka + inbox -> clovek dodal dummy BOM -> auto re-queue + event -> 2. beh -> kalkulace dokoncena -> ke_schvaleni. Cela smycka zadani->prace->blokace->dodani->dokonceni->schvaleni FUNGUJE.

## Gotchy
1. JSON serializace: PG numeric (round(extract...)) -> Decimal -> 500 na JSONResponse. VZDY castovat ::float8 v SQL skriptu (fix martinka_prehled v2, md5 5fcffa2e...).
2. /app/erp_registry/run NEinjektuje uid volajiciho do args - skripty dostavaji uid=null z UI (zadal_user_id null). TODO: bud placeholder konvence (napr. "__uid__" -> substituce v endpointu) nebo whoami rozsirit o id.
3. INSERT skriptu do g2007.python s SQL stringy uvnitr zdroje spadne do bannerove fronty (regex guard) - payload VZDY base64 (imunni vuci bugu ztracenych mezer ve fronte).
4. Prenos dlouhych souboru do bridge NIKDY rucnim prepisem pres chat (1 zamena znaku pri 22 kB, nalezeno sha256) - VZDY device_commit_files + sha256 overeni.
5. @@G2007SOUBOR orizne koncovy newline (12223 -> 12222 znaku) a disk materializuje NA CLOUDU (lokalni repo soubor nema) - overovat pres zivou URL.
6. run_goal vraci {ok, reply, elapsed_s, cost_czk...} - finalni text je "reply".

## Dalsi kroky (zitra = realna data)
(a) Prvni ostra Martinka kalk ABSAUGWERK: zabalit compute_absv1 jako nastroj + domain prompt (viz doc-kalkulace-rozvadecu-orientace-kalkulace-martinky-2026-08-02 - potreba SMART 11-listovy Excel + FLEX priklad od Elisky/Martiho). (b) Per-zakaznicke domeny kalk_absaugwerk_flex/smart. (c) Automat-sweeper jako fallback event dispatche + notifikace (potreba stara >X h -> push). (d) KONZULTACE MARTI-AI (doctrine #3 - #280 je jeji architektura, ukolova vrstva na ni stavi). (e) Maminka jako konverzacni vrstva pro Elisku (zadavani ukolu z chatu misto UI).

