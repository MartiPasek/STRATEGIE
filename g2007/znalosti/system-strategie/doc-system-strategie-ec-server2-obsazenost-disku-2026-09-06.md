# Cim je zaplneny plzensky EC-SERVER2 (zmereno 6.9.2026) a kde by se dalo uvolnit misto

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Cim je zaplneny plzensky server EC-SERVER2 (stav 6. 9. 2026)

**Zmeril:** Claude-28 (Jirka Honomichl), 6. 9. 2026. **Nic se nemazalo** — je to podklad
pro rozhodnuti. Uklid plzenskeho serveru neni Jirkova agenda, patri Michalu Sikovi
(rekl Jirka 6. 9. 2026).

## Proc to vzniklo

6. 9. 2026 rano se prah hlidace disku zvedl na 20 % vsem serverum a prvni upozorneni
prislo prave na EC-SERVER2 (disk D, 5,3 % volneho). Jirka chtel vedet, **cim to je
a jak rychle to roste**. Prah se tyz den vecer zuzil zpet jen na prazske servery —
viz `doc-system-strategie-hlidac-volneho-mista-prah-80-procent`.

## Disk D (5 000,9 GB, volnych 263 GB = 5,3 %)

| slozka | velikost | poznamka |
| --- | --- | --- |
| `Data` (firemni sitova slozka) | **3 766 GB**, 1 813 156 souboru ve 140 slozkach | ziva |
| `SQL_Backup` | 291 GB | zalohy databaze, drzi se ~mesic a prepisuji se |
| `Archiv` | 291 GB | mesicni archivy databaze, **nejnovejsi 1. 12. 2025** |
| `install` | 216 GB, 99 219 souboru | instalacky, ovladace, stare verze Centraly |
| `STRATEGIE_ARCHIVE` | 80 GB | drzi se ~mesic |
| `STRATEGIE_IN` | 15 GB | drzi se ~mesic |
| Helios + Helios_Test + PostgreSQL + Smernice | 22 GB | |
| kos (`$RECYCLE.BIN`) | 41 GB | |
| stinove kopie | 6 GB | **nejsou pricinou** |

Nejvetsi polozky uvnitr `Data`:

| slozka | velikost | naposledy zmena |
| --- | --- | --- |
| `Fotos` | **1 188 GB** (433 536 souboru) | 4. 9. 2026 — **ziva, roste** |
| `FTP` | **612 GB** (311 550 souboru) | duben 2025 — **mrtva** |
| `ZZ_Sarka` | 237 GB | osobni slozka |
| `ZZ_HSvoboda` | 177 GB | osobni slozka |
| `Podklady vyroba` | 174 GB | |
| `Poptavky` | 168 GB | |
| `Dilna` | 161 GB | |
| `ERP_Centrala` | 108 GB | |

Z `FTP` je **606 GB v jedine podslozce `archive_quest`** (311 548 souboru) — slozky
pojmenovane po zakaznicich, tedy archiv zakaznickych dat. Od dubna 2025 se nezmenil.
**Neni to smeti, je to mrtve** — o smazani rozhoduje obchod, ne IT.

## Disk C (499 GB, volnych 82 GB = 16,4 %)

**217,5 GB je `Program Files\Microsoft SQL Server`** — databaze Heliosu a Centraly
v zakladni slozce programu. Ziva data, porostou dal. Zbytek je drobny
(Program Files x86 12,4 GB, ProgramData 5 GB, TEMP 1,7 GB, kos 0 GB).

## Jak rychle to roste

**Historie volneho mista se nikde neuklada** — `fw.disk_monitor` drzi jen posledni
zmereny stav a stary prepise. Presne tempo tedy nikdo nezna. Co se zmerit dalo:

- **zalohy nerostou, rotuji** — `SQL_Backup` srpen 244 GB / 124 souboru, zari 47 GB / 24;
  soucet za srpen a zari se rovna celkove velikosti, takze se drzi zhruba mesic.
  Totez `STRATEGIE_ARCHIVE` a `STRATEGIE_IN`.
- **stare firemni slozky prakticky nerostou** — ve ctyrech velkych (Dilna, ERP_Centrala,
  InterniProjekty, IT_Data) pribylo za cely rok 2026 jen **4,5 GB**.
- **roste hlavne `Fotos`**, ktera je zaroven nejvetsi.

Zaver: disk **neni zaplnovan dennim prirustkem**, je zaplneny dvacet let nahromadenou
historii. To ale znamena i to, ze uklid je jednorazovy — bez neho se stav sam nezlepsi.

## Kde by se dalo uvolnit misto (nesmazano, ceka na rozhodnuti)

| co | ziska | na co si dat pozor |
| --- | --- | --- |
| kos | 41 GB | nic |
| `Archiv` (mesicni archivy stojici od 12/2025) | 291 GB | overit, jestli je nekdo nepotrebuje kvuli auditu |
| `install` (instalacky, stare verze Centraly) | 216 GB | patri sprave IT |
| `FTP\archive_quest` (zakaznicka data, od 4/2025 nedotcena) | 606 GB | **rozhodnuti obchodu**, jsou to data zakazniku |

Prvni tri = 548 GB (disk z 5 % na 16 % volnych), se ctvrtym 1 154 GB (na 28 %).

## Jak se to merilo (aby to slo zopakovat)

- Velikosti slozek na serveru pres `plzen_exec` Marti-AI (jen cteni).
  **Sken cele slozky `Data` v jednom prikazu spadne** (`mcp_call_failed`, prekroci limit) —
  delej to po skupinach slozek, nebo si to zmer ze site.
- Rozpad `Data` po podslozkach zmeren **ze site z notebooku** (`\\192.168.30.11\Data`),
  trval ~44 minut na 1,8 milionu souboru.
- Stari dat se meri pres `Group-Object` nad rokem z `LastWriteTime`.
- ⚠️ Pri psani skriptu pozor: pri zapisu pres prikazovou radku se **dve zpetna lomitka
  v ceste ke sdilene slozce srazi na jedno**, sken pak tise nenajde nic a skonci za vterinu.
  Cestu piš pres editacni nastroj a **vzdy zkontroluj, ze vysledek neni prazdny**.

