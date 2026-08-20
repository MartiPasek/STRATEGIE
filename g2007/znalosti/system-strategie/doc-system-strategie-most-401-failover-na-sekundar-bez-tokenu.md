# Most dostaval HTTP 401 "Nejsi prihlasen" - Caddy failover na sekundar 8003, ktery nema deploy token (diagnoza a oprava 17.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Priznak

Claude SQL most obcas vratil `HTTP 401: {"detail":"Nejsi prihlasen."}` — bez zjevne
souvislosti, casto stacilo poslat dotaz znovu a proslo to. Za 16.-17. 8. 2026 **19 vyskytu**
v `watcher.log`, vzdy ve shlucich. Dvakrat kvuli tomu **neprosel deploy na cloud**
(`cloud: NENASAZENO ... HTTP 401`) — commit i push byly OK, takze kod byl v gitu, ale
na cloudu zustala stara verze. To je ta nebezpecna cast: navenek to vypada jako uspesny deploy.

## Pricina (dokazana, ne hypoteza)

1. Endpoint `/api/v1/erp/diag-sql` overuje `X-Deploy-Token` proti env `STRATEGIE_DEPLOY_TOKEN`
   **procesu API**. Kdyz se neshodne, spadne na `_get_uid` + `_require_parent` — a protoze most
   zadnou session nema, vrati **401 "Nejsi prihlasen"** (ne 403). Proto ta matouci hlaska.
2. Caddy ma na **defaultni ceste** (bez cookie, coz je presne pripad mostu) failover retez:
   `reverse_proxy localhost:8002 localhost:8003`.
3. Sekundar **8003 (STRATEGIE-API-B) NEMA** env `STRATEGIE_DEPLOY_TOKEN`.
4. Kdyz primar 8002 chvili neodpovida — **typicky pri restartu po nasazeni** — Caddy posle
   pozadavek na 8003 → token neuznan → 401.

**Dukaz (17. 8. 2026):** stejny token, stejny dotaz:
- bez cookie (primar): **3x HTTP 200**
- s hlavickou `Cookie: strategie_api_version=previous` (= vynuceny sekundar): **3x HTTP 401**

Plus zive potvrzeni z logu: `05:51:26 DEPLOY cloud: OK ... API restart (~5 s)` a hned
`05:51:27 ERROR (pg): HTTP 401`.

## Co je opravene (nalepka, ne pricina)

`claude_sql_runner.py` ma nove **retry na 401** ve dvou funkcich:
- `_forward` (SQL dotazy) — 3 pokusy, pauza 3 s,
- `_cloud_deploy` (nasazeni) — 3 pokusy, pauza **8 s** (restart API trva ~5 s).

Retry je zamerne **jen pro 401**, aby nemaskoval 500/timeout/chyby v SQL. Otestovano nasucho
na peti scenarich (OK / 401-pak-OK / 401-porad / 500 / 403) i naostro — 17. 8. behem hodiny
zachranil dva dotazy, ktere by jinak skoncily chybou.

## Co JE spravna oprava (zatim NEUDELANO — vyzaduje zasah na cloudu)

**Doplnit `STRATEGIE_DEPLOY_TOKEN` do sluzby `STRATEGIE-API-B`** (`nssm set STRATEGIE-API-B
AppEnvironmentExtra ...`). Pak failover funguje i pro most a retry uz jen tise pomaha.
Alternativa: vyradit 8003 z defaultniho failover retezu pro API cesty mostu — ale to bere
smysl HA. Rozhodnuti patri Martimu / C23 (blue-green je jejich).

## Vedlejsi nalez: sekundar je stary 5 dni

`fw.api_version` k 17. 8. 2026: primar `STRATEGIE-API` commit `4bfd654b` (dnesni),
sekundar `STRATEGIE-API-B` commit `3d0f8273` z **12. 8. 20:01** — oba `is_active=true`.
Blue-green ma pritom drzet **vcerejsi** snapshot.

Pricina: snapshot dela `scripts/daily_rotation.ps1`, ktery se podle vlastni hlavicky spousti
**RUCNE pred kazdym `git pull` na primary**. Grep potvrdil, ze ho **nikdo nevola automaticky**
(zadny scheduled task, zadne volani z kodu). Jenze dnes se nasazuje automaticky pres
`CLAUDE_DEPLOY` z mostu — a ten rotaci nevola. Rucni krok tim vypadl z procesu.

**Dopad:** kdyby primar spadl, lide dostanou **pet dni stary system** — a za tu dobu se menily
mzdy, dochazka i naroky na dovolenou. Nahlaseno, rozhodnuti na Martim.

## Pouceni

- **"Nejsi prihlasen" nemusi znamenat problem s prihlasenim.** Kdyz server pri neplatnem tokenu
  spadne na kontrolu session, dostanes 401 misto 403 — a hledas uplne jinde.
- **Nahodile chyby, ktere "po zopakovani zmizi", casto znamenaji dve instance za load balancerem,
  z nichz jedna je jinak nakonfigurovana.** Overit jde vynucenim konkretni instance (tady cookie).
- **Rucni krok v jinak automatizovanem procesu tise vypadne.** `daily_rotation.ps1` nikdo
  nezrusil — jen prestal existovat okamzik, kdy by ho nekdo spustil.
- Souvisi: [[doc-system-strategie-souběh-instanci-co-kontrolovat-na-konci-session]]

