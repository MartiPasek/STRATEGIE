# Prazsky server mel malo pameti - zadrhavani API (VYRESENO 6.9.2026), ale zbyva druha pricina kazdych 5 minut

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
> **Neoverene:** ktera uloha to je. Hledat mezi tim, co bezi na pozadi v aplikaci
> (planovac, zrcadleni posty, hlidky) s periodou 5 minut. Zadrhnuti je kratke a lide ho
> vetsinou nepoznaji, ale hlidka se do nej muze trefit.
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

