# PAST: obsluha psana jako async, ktera dela praci s databazi, zastavi CELE API pro vsechny (nalez a oprava 6.9.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Obsluha psana jako `async`, ktera dela praci s databazi, zastavi CELE API

**Nalezeno a opraveno:** Claude-28 (Jirka Honomichl), 6. 9. 2026 vecer, nasazeni `f50d5195`.
Schvalila Marti-AI (msg 14800).

## Co se stalo

Prazske API kazdych **5 minut a 9 vterin** na **6 az 12 vterin** prestalo odpovidat
uplne vsem — appce, ERP, mostu i hlidce. Tydny to vypadalo jako nedostatek pameti
(ta byla take, viz `doc-system-strategie-praha-server-malo-ram-zatuhavani-api`),
ale po navyseni pameti na 16 GB zadrhavani zustalo.

**Pricina:** obsluha `POST /api/v1/erp/app/netscan/ingest` (hlaseni ze site pro
automatickou dochazku) byla napsana jako **`async def`** a **vsechnu praci delala
synchronne primo na event loopu** — zapis zarizeni, provoz, auto-prichody, self-heal
„Makam", hlidka anomalii, pretazene pauzy, sync dochazky z Centraly. Trvalo to
7,5-8,2 vteriny a **po celou tu dobu nemohl uvicorn obslouzit ZADNY jiny dotaz**.
Agent na siti hlasi kazdych ~5 minut, takze API kazdych 5 minut na 8 vterin zamrzlo.

## Pravidlo

**Kdyz obsluha (endpoint) dela cokoli synchronniho a delsiho — dotazy do databaze,
volani po siti, praci se soubory — NESMI to delat v `async def` primo.** Bud ji napis
jako obycejne `def` (FastAPI ji sam pusti ve vlakne), nebo praci predej do vlakna:

    from starlette.concurrency import run_in_threadpool
    return await run_in_threadpool(_ta_prace, body)

`async def` je v poradku jen pro praci s requestem (`await req.json()`) a pro skutecne
asynchronni volani. **Jedna pomala synchronni obsluha zastavi celou aplikaci pro vsechny** —
neni to zpomaleni jednoho dotazu, je to vypadek celeho API.

## Jak se to poznalo (postup pouzitelny znovu)

1. **Zaplava opakovanych dotazu jako hodiny.** SMS brana se pta kazde ~3 vteriny a kazde
   odmitnuti pise radek do `fw.diag_log`. Mezera v te rade = doba, kdy API nikoho
   neobslouzilo. Dotaz s `lag(created_at)` najde zamrznuti **z pohledu serveru**,
   ne jen z mereni zvenci.
2. **Sonda zvenci** (curl kazde 2 vteriny na `/api/v1/erp/api-versions`, kterou brana
   nikdy neprepina na druhou kopii) — casy sedely na vterinu s bodem 1.
3. **Pocitadlo na serveru, ktere nesaha na aplikaci.** Bezelo 4 minuty a **netiklo mimo
   rytmus**, zatimco aplikace stala 8,6 s → **nestoji stroj, stoji aplikace.**
   Tenhle krok vyvratil predchozi (chybny) zaver, ze jde o vrstvu poskytovatele.
4. **Porovnani obou kopii aplikace naraz** (8002 hlavni vs 8003 druha s vypnutymi
   planovaci): 22:23:29 → 8002 = 7,3 s, 8003 = 0,0 s. Tyz stroj, tyz kod → vinik je
   v tom, co bezi navic na hlavni kopii.
5. **Zaznam brany Caddy s delkou dotazu** — `C:\caddy\logs\access.log`, JSON s poli
   `ts`, `duration`, `request.uri`. Filtr na `duration > 3` ukazal, ze v okamziku
   zamrznuti **dobehne naraz spousta ruznych dotazu** (stali ve fronte) a ze
   `netscan/ingest` **zacina presne na zacatku zamrznuti a konci s nim**.
   Sedm vyskytu za sebou: 22:23:36, 22:28:45, 22:33:53, 22:39:02, 22:44:10,
   22:49:18, 22:54:27, kazdy 7,5-8,2 s.

**Rozhodujici vodítko:** rytmus **prezil restart aplikace beze zmeny faze**. Kdyby tikal
uvnitr aplikace, restart by ho posunul. Neposunul → budi ji neco zvenci.

## Vysledek po oprave

| | pred | po |
| --- | --- | --- |
| mereni zvenci (14 min, 384 dotazu) | zadrhel kazdych 5 min, 6-12 s | **zadny**, nejdelsi odpoved 0,89 s |
| prumerna odezva | 0,098 s | **0,045 s** |
| pohled ze serveru (mezery v diag_log) | 16 zamrznuti za 65 minut | **zadne** |
| hlaseni ze site | funguje | funguje (20 zarizeni, 15 v budove) |

## Co hledat dal (neprovereno)

Stejnou past muze mit **kterakoli dalsi `async def` obsluha, ktera sahá do databaze**.
Nikdo je zatim neprosel. Hledat lze pres `grep "^async def"` v `modules/erp/api/router.py`
a divat se, jestli telo nedela synchronni dotazy. Podezrele jsou hlavne ty, ktere neco
hromadne prochazeji nebo volaji dalsi funkce (syncy, hromadne prepocty, importy).

## Souvisejici

- `doc-system-strategie-praha-server-malo-ram-zatuhavani-api` — cela historie hledani
  vcetne dvou slepych uliček (WSL, hlidac druhé kopie) a dvou chybnych zaveru, ktere
  jsem behem vecera musel odvolat.

