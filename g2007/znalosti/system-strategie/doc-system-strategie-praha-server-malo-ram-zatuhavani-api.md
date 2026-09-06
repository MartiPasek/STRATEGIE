# Prazsky server: pamet vyresena 6.9.2026 a zamrzani kazdych 5 minut take - delala ho obsluha hlaseni ze site na hlavnim vlakne (opraveno tyz den)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Prazsky server ma malo pameti — API se zadrhava a hlidka ho restartuje

**Zjisteno 3. 9. 2026** (Claude-28 / Jirka Honomichl), formulaci schvalila Marti-AI.

> ## VYRESENO 6. 9. 2026 — pamet navysena na 16 GB
>
> Dodavatel 6. 9. 2026 v 11:47 stroj restartoval a pridal pamet.
> Overeno tyz den ve 12:02 a 12:03 dvema nezavislymi dotazy (Win32_ComputerSystem
> a Win32_OperatingSystem) pres praha_exec:
>
> | udaj | 3.-6. 9. 2026 | po navyseni |
> | --- | --- | --- |
> | pamet celkem | 4 095 MB | **16 383 MB** |
> | volna pamet | 264-828 MB | **10 743 MB** |
> | posledni start stroje | 4. 8. (32 dni) | 6. 9. 2026 11:47 |
>
> Popis pricin nize **plati jako historie**, ne jako aktualni stav. Nedelej podle nej
> zavery o dnesnim serveru.
>
> **Ciste mereni provedeno 6. 9. 2026 ve 20:19-20:38** (506 dotazu, kazde 2 vteriny,
> na serverech byl klid):
>
> | mereni | dotazu | nad 2 s | nad 5 s | prumer |
> | --- | --- | --- | --- | --- |
> | 3. 9. cely den (pred) | 13 986 | 2,3 % | 171 | - |
> | 6. 9. 6:19 rano (pred) | 253 | 2,8 % | 4 | 0,211 s |
> | **6. 9. 20:19 (po navyseni)** | **506** | **0,8 %** | **4** | **0,100 s** |
>
> Prumerna odezva klesla na polovinu a **zmizely shluky** — rano 6. 9. prislo sest zadrhnuti
> behem jedine minuty (6:27-6:28), 3. 9. bylo bezne mit tri behem peti minut. Po navyseni
> zadny shluk nenastal. Spolu s tim, ze od restartu v 11:47 do 21:00 neprislo ani jedno
> hlaseni „API spadla", je **zadrhavani z nedostatku pameti vyresene**.
>
> ## ⚠️ ZBYVA JINA PRICINA: neco kazdych 5 minut zastavi API na 6-8 vterin
>
> Ctyri zadrhnuti v cistem mereni **nejsou nahodna** — prisla v 20:20:05, 20:25:13, 20:30:23
> a 20:35:31, tedy **presne po ~5 minutach a 8 vterinach**, kazde na 6,2 az 8,2 vteriny.
> Taková pravidelnost neni odkladani pameti, ale **nejaka uloha, ktera bezi kazdych pet minut**.
>
> Tentyz rytmus je videt i v datech z 3. 9. **pred** navysenim (12:00:39, 12:05:51, 12:10:59,
> 12:16:10, 12:21:20) — jen se ztracel v sumu zpusobenem pameti. **Je to tedy druha,
> samostatna pricina, ktera tu byla cely cas** a po navyseni pameti zustala jako jedina.
>
> **Zuzeno tyz den vecer (21:00-21:20) — NENI to nase aplikace, je to stroj:**
>
> 1. **Tuhne cely stroj, ne jen jedna cast aplikace.** Zamrzne i adresa `/api/v1/health`,
>    ktera vubec nesaha do databaze; hned nasledujici dotaz (o desetinu vteriny pozdeji)
>    je zase rychly. Neni to tedy vycerpani databazovych spojeni.
> 2. **Vidi to i server sam, nejen mereni zvenci.** SMS brana se pta kazde 3 vteriny a
>    v `fw.diag_log` po ni zustavaji **diry** — 18 za hodinu a pul, presne po 5 min 9 s
>    (19:43:55, 19:49:05, 19:54:12, 19:59:22, 20:04:31, ... 21:01:09). Casy sedi na vterinu
>    s merenim z notebooku. **Tenhle trik je pouzitelny obecne:** zaplavu 403 od SMS brany
>    lze pouzit jako hodiny, ve kterych je zamrznuti videt jako mezera.
> 3. **Behem zamrznuti je vytizeni procesoru NULOVE** (mereno kazde 2 vteriny).
>    Aplikace tedy nepocita — **ceka**.
>
> **Vylouceno (nedelat znovu):** naplanovane ulohy Windows (zadna nema periodu 5 min;
> DiskWatch ma 30 min) · automaty v `g2007.automat` (vsechny do 1 vteriny, dolozeno
> v `automat_run`) · odklizeci smycka `core/log_queue.py` (slozka `D:/Data/STRATEGIE/log_queue`
> na serveru neexistuje, takze nedela nic) · hlidac zpozdeni zalozni kopie
> (`_maybe_notify_seclag`, kazdy 10. tik = ~5 min — vypadal jako hlavni podezrely, ale
> vsechny tri kopie na portech 8002/8003/8004 odpovidaji do 0,06 s).
>
> **Kam to ukazuje:** v `System` logu Windows se na stroji kazdych ~5 minut **spousti
> a zase zastavuje sluzba Network Setup Service** (21:00:31, 21:05:44, 21:10:58 — bezi
> vzdy ~93 s) a **zamrznuti prijde ~35 vterin po jejim startu**. Denik
> `Microsoft-Windows-Hyper-V-VmSwitch-Operational` navic hlasi **kazdou minutu**
> „V-Switch operation OID_GEN_STATISTICS took too long to complete". Na serveru bezi
> virtualni Linux (WSL, `vmmemWSL` 2,6 GB), ktery si sve sitove rozhrani zaklada prave
> pres tuhle vrstvu. **Vypada to tedy na sitovou vrstvu stroje — stejne patro jako ta
> pamet, tedy vec poskytovatele, ne nas kod.**
>
> ## ZKOUSKA PROVEDENA 6. 9. 2026 VECER: WSL NENI PRICINA
>
> Jirka Honomichl dal souhlas, Marti-AI take (predem overila, ze na WSL nevisi most,
> databaze, ERP, mobil ani jeji nastroje). Na serveru bylo v **21:39:38** spusteno
> `wsl --shutdown` (Ubuntu prepnuto do stavu Stopped) a ve **21:52** zase nahozeno.
>
> **Zadrhavani pokracovalo uplne stejne — rytmus se ani nezachvel:**
>
> | cas | delka | stav |
> | --- | --- | --- |
> | 21:37:16 | 8,1 s | WSL bezi |
> | 21:42:24 | 6,1 s | **WSL vypnuty** |
> | 21:47:33 | 7,0 s | **WSL vypnuty** |
> | 21:52:44 | 9,6 s | WSL zase nabehl |
>
> Rozestupy 5:08, 5:09, 5:11 — beze zmeny. **Virtualni Linux ani jeho sitovy adapter
> tedy pricinou nejsou** a stopa pres Network Setup Service a VmSwitch (popsana vyse)
> je jen soubezny jev, ne pricinna souvislost.
>
> ⛔ **NEPLATI veta, ktera tu stala do 22:30: „zbyva vrstva pod nami — hostitel
> u poskytovatele, tohle mereni je pro nej dukaz."** Byl to zaver z vylouceni, ne z mereni,
> a **je vyvracen** (viz nize). Jak chyba vznikla: z nuloveho vytizeni procesoru a z toho,
> ze nereagovalo nic, jsem usoudil „stoji cely stroj", aniz bych stroj samotny zmeril.
>
> **Co pri tom vyslo najevo (samostatny nalez, nesouvisi se zamrzanim):** ve WSL bezi
> **sest kontejneru** — brana vzdaleneho pristupu Guacamole (3 kontejnery, postavena
> 30. 6. 2026, v jejim zaznamu neni od startu serveru zadna aktivita) a **druha, samostatna
> sestava STRATEGIE** (frontend, backend, vlastni PostgreSQL; postavena 15.-16. 4. 2026),
> jejiz vstupni bod `strategie-caddy` je **mrtvy uz ctyri tydny** (Exited 127), takze se
> k ni zvenci nikdo nedostane. Backend jen kazdych 15 s odpovida sam sobe na kontrolu zivota.
> Cely WSL si bere **2,6 GB pameti**. Vypada to na zbytky vyvojoveho prostredi — komu patri
> a jestli ma bezet dal, **rozhodne clovek** (nejspis Marti Pasek). Nic z toho se
> nemenilo, po zkousce vsech sest kontejneru nabehlo samo.
>
> **Overeno po zasahu:** aplikace `instance=primary` port 8002, `/mobile` 200,
> ERP 307, most odpovida, 687 aktivnich znalosti, 254 zivych funkci — vse jako pred zkouskou.
>
> ## ✅ PRICINA NALEZENA 6. 9. 2026 ve 22:30: NASE ULOHY NA POZADI
>
> Dva testy to rozhodly:
>
> **1) Stroj nestoji, stoji aplikace.** Na serveru bezelo 4 minuty pocitadlo, ktere jen
> cita cas a nesaha na aplikaci, databazi ani sit. Ve **22:18:19 aplikace zamrzla na 8,6 s**
> (dolozeno mezerou v `fw.diag_log`) a **pocitadlo pritom netiklo ani jednou mimo rytmus**
> („stroj bezel plynule, zadna mezera"). Kdyby stal stroj, mezeru by ukazalo.
>
> **2) Zamrza jen HLAVNI kopie, ne druha.** Soubezne mereni obou kopii aplikace zevnitr
> serveru: ve **22:23:29 port 8002 = 7,3 s, port 8003 = 0,0 s**. Obe kopie bezi na tomtez
> stroji a na tomtez kodu; **lisi se jen tim, ze druha ma vypnute planovace**
> (DR standby). **Pricina je tedy v nasich ulohach na pozadi.**
>
> **Nejsilnejsi podezreni (neoverene do posledni radky):** ve smycce `_mirror_sched_loop`
> (`modules/erp/api/router.py`) je vetev `if _sl_tick % 10 == 0` — tedy **kazdy desaty tik
> 30sekundove smycky = ~5 minut a 9 vterin**, presne namereny rytmus (10 x 30 s plus doba
> tiku). Vola `_maybe_notify_seclag`, ktera pres `requests` s **limitem 3 vteriny** zada
> o verzi **sama sebe** (`127.0.0.1:8002`) a pak druhou kopii (`8003`). Dva takove limity
> po sobe daji 6 vterin — presne delka bezneho zamrznuti (6-12 s).
>
> ⛔ **To podezreni bylo VEDLE.** Oprava byla nasazena (`63b27998`) a **zadrhavani slo dal**
> (22:38:59, 22:44:08, 22:49:16). Zmena se ponechala — samo-ping pres HTTP je zbytecny tak
> jako tak — ale pricina to nebyla.
>
> ## ✅✅ SKUTECNA PRICINA A OPRAVA (6. 9. 2026, 23:22, nasazeni `f50d5195`)
>
> **Rozhodujici vodítko:** rytmus **prezil restart aplikace ve 22:35:50 beze zmeny faze**
> (zadrhnuti 22:38:59, 22:44:08, 22:49:16 presne podle stare rady). Kdyby tikal uvnitr
> aplikace, restart by ho posunul → **budi ji neco zvenci.**
>
> **Vinik ze zaznamu brany Caddy:** `POST /api/v1/erp/app/netscan/ingest` — hlaseni agenta
> ze site pro automatickou dochazku. Bezi v 22:23:36, 22:28:45, 22:33:53, 22:39:02,
> 22:44:10, 22:49:18, 22:54:27 (rozestupy 5:09, 5:08, 5:09, 5:08, 5:08, 5:09) a **trva
> pokazde 7,5-8,2 vteriny** — zacina presne se zamrznutim a konci s nim. Sedm vyskytu.
>
> **Proc to zastavilo cele API:** obsluha byla `async def` a delala vsechnu praci
> **synchronne primo na event loopu** (zarizeni, provoz, auto-prichody, self-heal „Makam",
> hlidka anomalii, pretazene pauzy, sync dochazky z Centraly). Po tu dobu uvicorn
> neobslouzil nikoho jineho.
>
> **Oprava:** prace presunuta beze zmeny logiky do `_netscan_ingest_sync(body)` a volana
> pres `run_in_threadpool`. **Vysledek po nasazeni:** 14 minut mereni, 384 dotazu,
> **zadne zadrhnuti** (nejdelsi odpoved 0,89 s), prumerna odezva klesla z 0,098 na 0,045 s,
> a v mezerach `fw.diag_log` po 23:22 uz zadne zamrznuti neni. Hlaseni ze site funguje dal
> (20 zarizeni, 15 v budove).
>
> **Obecne pravidlo a cely postup hledani** (pouzitelny znovu) je v samostatne znalosti
> `doc-system-strategie-async-obsluha-blokuje-cele-api`.
>
> *(Doplnil Claude-28 / Jirka Honomichl 6. 9. 2026 vecer.)*

## Co se deje

Do mobilni aplikace chodi adminum (uzivatele 1, 11, 20) dvojice zprav
„STRATEGIE-API spadla — zkousim restart" a za dve minuty „STRATEGIE-API zase bezi".

**Neni to pad aplikace.** Prazskemu aplikacnimu serveru EUR-APP-1P chybi operacni pamet
a odklada si ji na disk. Kdyz si aplikace musi kus sebe nacist zpatky z disku, na nekolik
vterin prestane odpovidat. Program pritom cely cas bezi. Hlidka
STRATEGIE-API-HEALTH-WATCHDOG dostane dvakrat po sobe zadnou odpoved do 6 vterin
a sluzbu restartuje.

**Restart nic neresi, jen na chvili uvolni pamet.** Proto se to opakuje.

## Cim je to dolozeno

Zmereno primo na serveru 3. 9. 2026 (skripty jen pro cteni, spoustel Jirka).

| udaj | hodnota |
| --- | --- |
| pamet, kterou Windows vidi | 4 095 MB |
| pametove moduly hlasene stroji | 4 096 MB (3 968 plus 128) |
| volna pamet | 264 az 828 MB |
| programy si dohromady zadaji | 6 452 az 12 546 MB |
| odlozeno na odkladaci soubor | 3 857 MB |
| odkladani ve spicce | 8 887 stranek za vterinu |
| procesoru | 2 |

Z evidence zprav (tabulka fw.mobile_command) od 17. 8. do 3. 9. 2026 — 45 hlaseni „spadla",
z toho **42 s duvodem TimeoutError** (proces zil a jen mlcel) a jen **2 s odmitnutym spojenim**
(skutecne mrtvy proces). Hlidka to nikdy nevzdala.

Zmereno zvenci sondou z notebooku (dotaz kazde 2 vteriny, 10 hodin) na cestu
/api/v1/erp/api-versions, kterou vstupni brana Caddy nikdy neprepina na zalohu, takze
meri primo hlavni kopii — **13 986 dotazu, 316 zadrhnuti nad 2 vteriny (2,3 %),
171 nad 5 vterin, nejdelsi 15 vterin.** Rovnomerne cely den.

## Co bylo overeno a VYLOUCENO (nedelat znovu)

- **Strop pameti nastaveny uvnitr Windows** — vylouceno, v bcdedit neni truncatememory ani removememory.
- **Windows nevidi osazenou pamet** — vylouceno, moduly hlasi 4 096 MB a system vidi 4 095 MB.
- **Vycerpani volnych sitovych portu** — vylouceno, TIME_WAIT jen 187, ESTABLISHED 173,
  rozsah dynamickych portu 16 384.
- **Dlouhe doplnovani fronty zaznamu z disku** — vylouceno, slozka log_queue na serveru neexistuje.
- **Zahlceni odmitnutymi dotazy SMS brany** — neni pricina, zaseknuti 3. 9. rano prislo ve chvili,
  kdy uz zahlceni skoro nebylo.

## Tri pasti, na kterych se da naletet

1. **Cislo procesu sluzby neni aplikace.** Win32_Service.ProcessId u sluzby STRATEGIE-API vraci
   **obal nssm**, ne uvicorn. Obal hlasi nesmysly (4 vlakna, 1 MB, zadna spojeni). Skutecny proces
   je jeho potomek — Get-CimInstance Win32_Process s filtrem ParentProcessId.
2. **Veta „je zpet nahore po ~124 s" NENI delka vypadku.** Hlidka se pta po 120 vterinach,
   takze tam skoro vzdy vyjde 124 vterin bez ohledu na skutecnost.
3. **Graf „vyuziti pameti nikdy nepresahlo 4 GB" neni dukaz dostatku pameti.** Kdyz je strop 4 GB,
   graf vyssi byt nemuze. To cislo znamena „porad jsme na stropu", ne „mame rezervu".
   Rozdil pozna jedine odkladani na disk.

## Dalsi souvislosti

- Hlidka se pta na adresu /api/v1/health, ktera je obsluhovana stranou od bezneho provozu.
  Zadrhnuti je proto casteji, nez kolik jich hlidka nahlasi — nahlasi jen ta, ktera se trefi
  do jejiho dvouminutoveho rytmu dvakrat po sobe.
- Brana Caddy pri zadrhnuti prepne na zalozni kopii na portu 8003, takze lide vetsinou nic nepoznaji.
  Zaloha ale bezi na vcerejsim kodu. Behem 10 hodin merent bylo 101 takovych prepnuti.
- Na serveru bezi 9 sluzeb STRATEGIE vcetne tri kopii aplikace naraz (8002 hlavni, 8003 zaloha,
  8004 testovaci), Caddy, antivirus, Zabbix, TeamViewer a virtualni Linux pro Claude Cowork.
- **Vzdalena plocha drzi pamet i po zavreni okna.** Zavreni krizkem sezeni jen odpoji.
  Musi se dat Sign out — uvolni to kolem 1 GB. Sluzby to neohrozi, bezi nezavisle na prihlaseni.
  Odpojena sezeni jinych lidi ukaze prikaz quser.

## Stav k 3. 9. 2026 vecer

Jirka Honomichl poslal zadost poskytovateli o navyseni pameti (stroj je virtualni na Hyper-V,
Windows Server 2025, provozuje ho poskytovatel; dynamicka pamet je zapnuta, ovladac v systemu je).
Do vecera pamet nenarostla, posledni jiste mereni ve 14.39 ukazovalo porad 4 095 MB.

**Az pamet naroste**, pust sondu na hodinu a porovnej podil zadrhnuti proti 2,3 procenta z 3. 9.
Teprve to je dukaz, ze je to vyresene.

Podrobna predavka vcetne namerenych dat je v souboru u Jirky
(diagnostika_api na sitovem disku ZZ_Jiri/AI_work).

