# Prazsky server 188.11 - pripravenost na restart a kontroly po nem (zasah probehl 6.9.2026 v 11:47)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Pripravenost prazskeho serveru na restart (kontrola 5. 9. 2026)

> ## ✅ DOPLNENO 6. 9. 2026 VECER: ZASAH PROBEHL, KONTROLY BODU 1 HOTOVE
>
> **NEPLATI** puvodni ranni doplnek z tohoto mista („zasah se nekonal"). Platil jen do
> dopoledne: dodavatel pamet pridal **6. 9. 2026 v 11:47**, tedy o den pozdeji, nez slibil.
>
> | udaj | pred | po |
> | --- | --- | --- |
> | pamet celkem | 4 095 MB | **16 383 MB** |
> | volna pamet | 264-828 MB | **10 743 MB** |
> | posledni start stroje | 4. 8. (32 dni) | **6. 9. 2026 11:47** |
>
> **Kontroly bodu 1 provedeny 6. 9. ve 20:01 (mereno zvenci):** `api-info` 200,
> `instance=primary`, `port=8002`, `commit=4940bf29`, `stale=false` · `health` 200 za 0,03 s ·
> `/mobile` 200, 1 095 204 bajtu (5. 9. bylo 1 089 054, obsah se mezitim menil) · `/erp` 307 ·
> Marti-AI odpovida na `praha_exec` i `plzen_exec`.
>
> **Nejsilnejsi dukaz:** od restartu v 11:47 do 20:00 nepridalo `fw.mobile_command`
> **ani jedno hlaseni „STRATEGIE-API spadla"**. Posledni dve byla v 10:22 a 10:34,
> tedy pred restartem, a zpusobilo je indexovani velkych PDF.
>
> **Co zbyva:** ciste mereni sondou (to z 12:04 nebylo ciste — tri zadrhely v nem padly do
> chvil, kdy pres Marti-AI bezelo tezke skenovani disku), nocni kontrola a pondelni rano
> od 4.50. Doporucene kontroly 2 a 3 nize proto **plati dal**.
>
> Zapsal Claude-28 (Jiri Honomichl), 6. 9. 2026 vecer.



Duvod: dodavatel mel 5. 9. 2026 ve 20:00 pridat pamet RAM na aplikacnim serveru
EUR-APP-1P (10.200.188.11) a pri tom stroj vypnout / restartovat. Jirka Honomichl
potreboval jistotu, ze po nabehnuti bude vse fungovat - hlavne v PONDELI RANO,
kdy lidi prijdou poprve po vikendu.

Navazuje na `doc-system-strategie-praha-server-malo-ram-zatuhavani-api` (3. 9. 2026),
kde je zmerena pricina zadrhavani (malo pameti, odkladani na disk).

## Co bylo overeno 5. 9. 2026 odpoledne (pred zasahem)

### Vsech 9 sluzeb STRATEGIE ma automaticky start
Zjisteno pres Marti-AI (praha_exec, jen cteni) na 188.11:
`Get-CimInstance Win32_Service -Filter "Name LIKE 'STRATEGIE%'"` - vsech devet
melo State=Running a StartMode=Auto:
STRATEGIE-API (8002), STRATEGIE-API-B (8003 zaloha), STRATEGIE-API-D (8004 test),
STRATEGIE-CADDY, STRATEGIE-TASK-WORKER, STRATEGIE-EMAIL-FETCHER,
STRATEGIE-QUESTION-GENERATOR, STRATEGIE-API-HEALTH-WATCHDOG, STRATEGIE-RESTART-WATCHER.

Pozn.: oproti inventari `doc-system-strategie-servery-sluzby-inventar` (27. 7. 2026)
pribyly STRATEGIE-API-D, STRATEGIE-API-HEALTH-WATCHDOG a STRATEGIE-RESTART-WATCHER.

### Naplanovane ulohy - vsech 5 ve stavu Ready
STRATEGIE-claude-session-retention, STRATEGIE-DiskCleanup, STRATEGIE-DiskWatch,
STRATEGIE-rate-limit-cleanup, StrategieWSLStack.
StrategieWSLStack ma spoustec typu MSFT_TaskBootTrigger (Enabled=True), tedy
nabehne pri startu stroje sam.

### Dukaz z praxe, ne jen z nastaveni
`fw.service_heartbeat` ukazuje STRATEGIE-API-HEALTH-WATCHDOG na EUR-APP-1P
se `started_at` 4. 8. 2026 21:24 - to je presne cas posledniho startu stroje
(diagnostika 3. 9. hlasila uptime 29,7 dne od 4. 8. 21:23:54). Automaticky start
tedy pri minulem studenem startu prokazatelne fungoval.
Pozn.: do `fw.service_heartbeat` pise JEN hlidka, ostatni sluzby tam nejsou.

## Restart NIKOHO neodhlasi (overeno v kodu, ktery na serveru bezi)

Prihlaseni drzi obycejna cookie `user_id` (+ `tenant_id`), httponly, platnost
`session_cookie_max_age_days` = 90 dni, kterou middleware `session_rolling_middleware`
pri kazdem pouziti posouva dopredu. NENI to serverova session v pameti a neni
podepsana tajnym klicem generovanym pri startu - restart ji tedy zneplatnit nemuze.
Zdroj: `modules/auth/api/router.py`, funkce `_set_auth_cookies`.
Overeno, ze nad tim neni novejsi verze v `g2007.python` (0 aktivnich zaznamu
pro login/auth/session/cookie) a ze se soubor nelisi mezi verzi na serveru
(commit 2f6e35dc) a lokalem.

## Databaze se nerestartuje
PostgreSQL bezi na jinem stroji (188.12 EUR-DB-MSSQL-1P). Zasah se tykal jen 188.11.

## Obsah mobilni appky se po startu obnovi sam
Materializace z `g2007.soubor` na disk bezi v lifespanu `apps/api/main.py` pred `yield`,
skipuje shodny obsah a NIKDY nesmi shodit start (chyba = ERROR do logu).
Navic soubory na disku restart prezijou, takze je to kryte dvakrat.
Detail: `doc-system-strategie-staticke-artefakty-db-materializace-vyrazeni-z-gitu`.

## POZOR - sobotni test NENI dukaz pro pondelni rano

Prazdny server v sobotu vecer neprokaze nic o zatezi. Zmereno z `tenant.att_entry`
za posledni ctyri pondelky (10., 17., 24. a 31. 8. 2026):

| pondeli | prvni pichnuti | lidi za den | z toho 5.30-7.00 |
|---|---|---|---|
| 10. 8. | 4.54 | 45 | 28 |
| 17. 8. | 4.35 | 49 | 25 |
| 24. 8. | 4.49 | 48 | 27 |
| 31. 8. | 4.57 | 51 | 26 |

**Prvni clovek pichá kolem 4.50 rano, do sedmi jich je skoro tricet.**
Systém tedy musi spolehlive jet od pul pate v pondeli, ne od sedmi - a v tu dobu
u toho nikdo neni. Hlavni kontrola proto patri na NEDELI, kdy je jeste cely den
na napravu.

## PAST - "stranka se nacetla" neznamena, ze je vse v poradku

Kdyby hlavni kopie nenabehla, Caddy tise prepne na zalozni kopii na portu 8003,
ktera drzi VCEREJSI snapshot - navenek to vypada, ze vse funguje, a most navic
dostava 401 (viz `doc-system-strategie-most-401-failover-na-sekundar-bez-tokenu`).
Po restartu proto VZDY overit, ze odpovida hlavni kopie.

## Obrazek "pred" pro porovnani po restartu (5. 9. 2026 15.00, mereno zvenci)

- `GET /api/v1/api-info` -> 200, telo `instance=primary`, `port=8002`,
  `commit=2f6e35dc`, `stale=false`, `env=prod`, `db=data_db`
- `GET /api/v1/health` -> 200 za 0,03 s
- `GET /mobile` -> 200, 1 089 054 bajtu
- `GET /erp` -> 307 (presmerovani na prihlaseni, normalni stav)
- pamet stroje pri poslednim jistem mereni (4. 9. 2026 8.23) - porad 4095 MB

## Co overeno NEBYLO
- Restart nebyl vyzkousen naostro; overeno je nastaveni + jeden dolozeny pripad
  z minuleho startu (4. 8. 2026).
- Chovani NSSM, kdyz pri startu jeste neni dostupna sit nebo databaze.
- Cokoli, co dodavatel na virtualnim stroji zmeni nad ramec pridani pameti.

## Doporucene kontroly po zasahu
1. Hned po opravě - narostla pamet? odpovida HLAVNI kopie (`instance=primary`,
   `port=8002`)? jede `/mobile`, ERP a Marti-AI?
2. **Nedele pres den (hlavni kontrola)** - vydrzel server pres noc bez zadrhnuti?
   probehly nocni naplanovane ulohy? zmerit odezvu sondou a porovnat proti
   2,3 % dotazu nad 2 vteriny z 3. 9. 2026. To je jediny poctivy dukaz, ze je
   zadrhavani opravdu vyresene.
3. Nedele vecer - posledni potvrzeni, at pondeli od 4.30 jede naostro.

## Slabina pristupu na server
Na 188.11 se z mostu neda sahnout primo - jde to jen pres Marti-AI (`praha_exec`).
Ta 3. 9. 2026 odpoledne na tyhle prikazy na nekolik hodin prestala odpovidat
(zaznam v `pamet_historie.log`). 5. 9. odpovidala spolehlive (tri dotazy za sebou).
Zaloha pro pripad vypadku - diagnosticke skripty pripravene na siti, spousti je clovek pres RDP.

Zapsal Claude-28 (Jiri Honomichl), 5. 9. 2026.

