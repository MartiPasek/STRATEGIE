# Nocni prenos zalohy Praha-Plzen padal: pricina, oprava a pasti (8. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Nocni prenos zalohy Praha -> Plzen padal: pricina, oprava a pasti (8. 9. 2026)
> ⚠️ **DOPLNENO 9. 9. 2026 — pricinu upresnuje `doc-system-strategie-dr-stahovani-se-zasekava-ne-zpomaluje`, cti ji nejdriv.**
> Oprava popsana nize plati a pomohla. Ale **spojeni se nezpomaluje — ono se po nekolika
> stech megabajtech ZASEKNE a uz se nerozjede.** Prumer "200 kB/s" je artefakt deleni
> hodinou cekani na casovy limit, ne namerena propustnost. Zmereno 9. 9. 2026: trasa
> 13 skoku a 4-5 ms; z notebooku na teze siti 9-12 MB/s pres 44 MB bez degradace;
> ze serveru samotneho 42 MB/s a pak stani (842 MB v 8.40 a porad 842 MB v 8.54).
> **Domnenka o priskrcene lince se tim NEPOTVRDILA a neni to ani nocni jev.**
> Zatim to obchazime kratsim cekanim a vic pokusy (3 na 30, hodina na 2 minuty);
> naostro 9. 9. dobehlo stazeni na 12. pokus a Plzen dostala dnesni data.
> *(Zjistil Claude-28, zadal Jiri Honomichl.)*

Zadal Jiri Honomichl, dohledal a nasadil Claude-28, schvalila Marti-AI (msg 14923, 14944, 14950, 14968).

## Co se delo

Mezi 15. 8. a 3. 9. 2026 **selhalo 8 z 35 noci** (kazda ctvrta): 15. 8., 17. 8., 21. 8.,
27.-28. 8. a 1.-3. 9. Nejhorsi byla serie 1.-3. 9., kdy zaloha v Plzni zestarla az na
**97 hodin, tedy ctyri dny**. Slib "nejvyse jeden pracovni den zpet" tak osmkrat neplatil.

## Pricina (dolozena v logu D:\STRATEGIE_IN\_pullrestore.log na EC-SERVER2)

**Nepadala nocni zaloha v Praze ani obnova v Plzni — nedojelo STAHOVANI.** Doslovne hlasky:

- 26. 8. ve 4:19, 31. 8. ve 3:57, 1. 9. ve 3:55, 2. 9. ve 4:22: `Download fail: casovy limit operace vyprsel`
- 27. 8. ve 3:49: `Velikost nesedi (1231880192 != 3278845101) - mazu partial, koncim` (stazeno 38 %)
- 20. 8. a 14. 8.: radek o dokonceni v logu chybi uplne

**Proc to pribyvalo: zaloha rostla.** 16. 8. mela 1 616 MB, 20. 8. 2 654 MB, 26. 8. 3 024 MB,
30. 8. 3 412 MB, 7. 9. **3 884 MB** — za tri tydny 2,4nasobek. Cim vetsi, tim castejsi selhani.

**Technicky koren:** skript pouzival `Invoke-WebRequest`, ktery v PowerShellu 5.1
**nevystavuje `ReadWriteTimeout`** (vychozi 300 s). Nastaveny `-TimeoutSec 1200` hlida jen
navazani spojeni a hlavicky, ne cteni tela odpovedi. Petiminutove zadrhnuti linky proto
shodilo cely nekolikagigovy prenos — a pady po 25 az 52 minutach na to presne sedi.
Odesilaci strana v Praze (`push_dump.ps1`) pritom oba limity nastavuje uz roky spravne
pres `[Net.HttpWebRequest]`; byla to asymetrie mezi obema stranami.

### Co bylo ZKOUMANO A VYLOUCENO (nemer to znovu)

- **Misto na disku v Plzni** — D: ma 213 GB volnych. Procento (4,3 %) vypada hrozive,
  ale absolutne je mista dost. **Pozor na tenhle klam u 5TB disku.**
- **Casovy strop naplanovane ulohy** — `STRATEGIE-DR-PullRestore` ma `ExecutionTimeLimit` PT72H.
- **Nocni zaloha v Praze** — vznika kazdou noc, roste den po dni a na server dorazi
  cerstva (`age_s` v logu je stabilne 810-870 s, tedy ~14 minut).
- **Padani aplikace** — 20. 8. ve 2:59 aplikace spadla primo v tom okne a zaloha presto prosla.
- **Den v tydnu** — zadny vzorec, selhani padla na sobotu i na vsedni dny.

## Ctyri pasti, ktere to delaly TICHYM

1. **Nikdo v retezu nekontroloval stari.** Odesilatel bral "nejnovejsi zalohu, jakou najde",
   server drzi jedno misto na jednu zalohu a Plzen obnovila, co tam lezelo. Nikde nebyla
   otazka "je to z dneska?". Proto stari dat rostlo presne po 24 h (25 - 49 - 73 - 97)
   a vsechny kroky pritom hlasily uspech.
2. **Hlaseni o selhani chodilo NATVRDO jen uzivateli 1** (`target_user_id, 1` v `dr_ops.py`).
   Spravce se o osmi selhanich nedozvedel.
3. **`pg_restore` vraci `rc=1` KAZDOU NOC** i pri uspechu (`--clean --if-exists` hlasi
   ignorovane chyby). Skutecne selhani by se v tom ztratilo.
4. **Samokontrola ve 3:45 hodnoti VCEREJSI obnovu.** Obnova bezi 3:30 az 4:02-4:56
   (dnes ~72 minut) — kontrola tedy bezi jeste behem ni a meri stav po obnove PREDCHOZI.
   Proto je zdrava hodnota "data stara 25 h" a proto **selhani hlasene v den D znamena,
   ze nedojel prenos v den D-1.** Bez tohohle se cisla v deniku obnov ctou spatne.

## Co se opravilo (vse nasazeno a overeno 8. 9. 2026)

1. **Hlaseni vsem spravcum** (commit `b2e3ef8f`): misto natvrdo zapsane 1 se vklada
   `SELECT ... FROM public.users u WHERE COALESCE(u.is_admin,false)` + pojistka na uzivatele 1,
   kdyby vyber nevratil nikoho. Dnes to jsou tri lide: 1 Marti, 11 Kristyna, 20 Jirka.
2. **Tri pokusy a vlastni limity** v `C:\scripts\dr_pull_restore.ps1` na EC-SERVER2:
   stahovani prepsano na `[Net.HttpWebRequest]` s `Timeout` i `ReadWriteTimeout` 3 600 000 ms,
   obaleno smyckou tri pokusu s pauzou 5 minut.
3. **Kontrola stari pred obnovou** tamtez: novy parametr `[int]$MaxStariH = 26`; kdyz je
   zaloha na serveru starsi, obnova se NEPROVEDE a skript skonci. **Zpravu odsud zamerne
   NEPOSILAME** — samokontrola ve 3:45 selhani spolehlive nahlasi (overeno: vsech 8 selhani
   melo radek v `fw.dr_selfcheck` i odeslanou zpravu, chybel jen prijemce).
4. **Navazovani preruseneho stahovani** (commit `64e3418a`): `dr_download` v `dr_ops.py`
   obsluhuje hlavicku `Range` primo (starlette 0.37.2 ji ve `FileResponse` ignoruje —
   overeno). Bez `Range` se chova presne jako driv. Klient posila `Range` s tim, co uz ma.
   **Tri pojistky:** nedodelek z minule noci se vzdy zahodi (navazuje se jen v ramci
   jednoho behu) · pred navazanim se znovu overi velikost a cas zalohy na serveru ·
   **navazat lze jen pri kodu 206** (kdyby stary server poslal 200 s celym souborem,
   pripojenim by vznikl poskozeny dump).

### Jak bylo navazovani overeno naostro

Z EC-SERVER2 pres Caddy: `Range: bytes=0-1023` vratilo **kod 206**, presne 1024 bajtu
a `Content-Range: bytes 0-1023/4073110814` — **brana Caddy hlavicku propousti**.
Pak dva kusy zvlast (0-1023 a 1024-2047) slepene dohromady daly **stejny otisk MD5**
jako stazeni vcelku (`2D53853695171E000D3DE5CF592E8E7D`) — server tedy reze spravne.

## Co v logu hledat rano

- `Stari zalohy na serveru: 0,2 h (prah 26 h) - OK.`
- `Stazeno cele (3884 MB) na 1. pokus.`
- Kdyz se objevi `Navazuji od ... MB`, znamena to, ze prvni pokus spadl a **oprava zabrala** —
  driv by v tu chvili prisel o den zalohy.

## Zalohy skriptu na EC-SERVER2 (navrat je jedno kopirovani)

`dr_pull_restore.ps1.bak_20260907` (pred opravou 1) · `.bak2_20260908` (pred 2) · `.bak3_20260908` (pred 3).

## NEOVERENO

**Jak dlouho se zalohy drzi na prazskem databazovem serveru 188.12 - ZODPOVEZENO 8. 9. 2026, je to 11 dni.** prune_pg_backups.ps1 ma KeepDays 11 a MinKeep 7, backup_data_db.ps1 ma retentionDays 11 - obe strany se shoduji, rozpor nikdy neexistoval. Hodnota 14 je jen ve stare kopii v projektu, ktera se na serveru nespousti. Puvodni znění nize UZ NEPLATI. Kopie skriptu
`prune_pg_backups.ps1` v projektu rika `KeepDays = 14`, znalost
`doc-system-strategie-servery-sluzby-inventar` rika, ze se to na serveru sjednotilo na **11**.
Kopie v projektu se tam nespousti (server ma vlastni v `C:\Scripts`) a **na 188.12 se DOSTANEME** - overeno naostro 8. 9. 2026 dvema cestami. (a) Cteni souboru primo ze serveru pres pg_read_file z mostu - takto byla retence zjistena, vcetne kontroly, ze odpovida opravdu stroj 10.200.188.12. (b) Kanal fw.ops_run zije, kdyz se vola ZAPISOVOU cestou mostu; pri volani ctecí cestou se cele volani vrati zpet a neulozi se nic, takze to drive vypadalo jako mrtvy kanal. Clovek k tomu potreba neni. Plzensky retez 30 zaloh
overeny je (`chain_count` v `fw.dr_selfcheck`).

_Souvisi:_ `doc-system-strategie-plzen-kanaly-pro-zmeny-nefunguji`, `doc-system-g2007-dr-plzen-stav`,
`doc-provoz-topologie-serveru-praha-plzen`

## Osma noc (17. 8., "0 vektoru") — VYSVETLENA 8. 9. 2026: samokontrola zavadi do bezici obnovy

Tahle jedina noc mela jinou pricinu nez ostatnich sedm. Data byla **cerstva** (24,8 h),
tabulek 720, konverzaci 413 — jen **vektoru 0**. Prenos ani obnova tedy nepadly.

**Co se stalo:** samokontrola bezi ve **3:45**, ale obnova bezi **3:30 az 4:02-4:56**.
Ten den konkretne `2026-08-17T03:30:02 Stahuji` a `2026-08-17T04:12:24 Restore rc=1` —
kontrola ve 3:45:02 tedy probehla **patnact minut do dvaačtyřicetiminutove obnovy**,
kdyz uz tabulka vektoru existovala, ale jeste nebyla naplnena. Vysledkem byl
**falesny poplach**, ne skutecna ztrata: 16. 8. bylo vektoru 297 837, 18. 8. uz 323 251
a rada dal roste (7. 9. pres 590 tisic).

**Duslednek, ktery plati porad:** samokontrola meri databazi **v rozpracovanem stavu**.
Vetsinou proto ukazuje jeste vcerejsi hodnoty (proto je zdrave stari 25 h), ale kdyz se
trefi do spatne chvile, ohlasi nesmysl. **Falesny poplach z teto pricny muze prijit
kteroukoli noc.**

**Navrh k rozhodnuti (NENI provedeno):** presunout naplanovanou ulohu
`STRATEGIE-DR-SelfCheck` na EC-SERVER2 ze 3:45 na cas, kdy uz obnova spolehlive dobehla —
podle logu staci **5:30** (nejpozdejsi dokonceni v mereni bylo 4:56). Tim by se zaroven
narovnal i vyklad cisel: kontrola by konecne hodnotila **dnesni** obnovu, ne vcerejsi.
Je to zmena naplanovane ulohy na plzenskem serveru, takze ji musi udelat clovek
(viz `doc-system-strategie-plzen-kanaly-pro-zmeny-nefunguji`).

