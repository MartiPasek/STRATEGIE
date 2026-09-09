# Nocni prenos DR: spojeni Plzen-Praha se ZASEKAVA, nezpomaluje - mereni 9. 9. 2026

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Nocni prenos DR: spojeni se ZASEKAVA, ne zpomaluje

Zmereno 9. 9. 2026 (Jiri Honomichl / Claude-28). Nahrazuje starsi vyklad, ze za nedojizdejicim nocnim prenosem stoji **priskrcena linka Plzen - Praha** (domnenka z 27. 7. 2026, vedena jako otevreny bod "na Michala").

> ## Hlavni veta
> **Spojeni se nezpomaluje - ono se po nekolika stech megabajtech ZASEKNE a uz se nerozjede.**
> Prumer "200 kB/s" byl artefakt: nekolik set MB preteklo plnou rychlosti a pak se hodinu
> cekalo na casovy limit. Kdo deli stazene bajty celkovym casem, dostane nesmysl a zacne
> hledat sirku pasma, kterou hledat nema.

## Merene dukazy (vse 9. 9. 2026 dopoledne)

| co | vysledek |
|---|---|
| trasa z kancelare na 185.219.169.86 (`tracert`) | 13 skoku, **4-5 ms**, bez ztrat |
| Jirkuv notebook (192.168.30.200, taz sit jako server), 40x stazeni verejne stranky = 44 MB | **9-12 MB/s stabilne**, bez degradace |
| EC-SERVER2 sam, 10x tataz stranka | **3,8-9,0 MB/s** |
| EC-SERVER2, stahovani dumpu 3 921 MB | prvnich 842 MB za ~70 s = **42 MB/s**, pak **stani** |
| totez o 14 minut pozdeji | **porad presne 842 MB**, nula bajtu |

**Zasekne se na promenlivem miste** - v noci kolem 748 a 664 MB, dopoledne na 842 MB, pri dalsim behu uz na 85 MB. **Neni to tedy pevny strop na objem.** Neni to ani nocni jev: chova se stejne v 9 rano.

## Co bylo VYLOUCENO (nemer to znovu)

- **Sirka pasma a trasa** - 42 MB/s namereno, trasa cista, odezva 4-5 ms.
- **Nocni hodina** - stejne chovani dopoledne.
- **Dve soubezne kopie skriptu** - overeno vypisem procesu, bezi jen jedna.
- **Vymena souboru na strane Prahy** - `@@DRDIAG` ukazal dump nedotceny
  (4 111 262 489 B, ulozeny v 01:16 UTC). Hlaska skriptu "zaloha se mezitim vymenila"
  byla mylny zaver z chybne odpovedi serveru, ne skutecna vymena.
- **Rozdelovani mezi dve instance aplikace** - `/api/v1/api-info` volane 10x vratilo
  vzdy `instance=primary, port 8002`.

## Co s tim delame (obchazka, ne oprava)

V `C:\scripts\dr_pull_restore.ps1` se **zkratilo cekani a zvysil pocet pokusu**, aby se
mrtve spojeni poznalo rychle a navazalo se:

| | pred 9. 9. | po |
|---|---|---|
| pokusu | 3 | 30 |
| cekani na mrtvem spojeni (`Timeout` i `ReadWriteTimeout`) | 3 600 000 ms (1 h) | 120 000 ms (2 min) |
| pauza mezi pokusy | 300 s | 20 s |

**Vysledek naostro 9. 9. 2026:** stazeno cele (3 920,8 MB) v 10:08:23 na **12. pokus ze dvanacti**,
obnova 10:08:28 az 10:18:19, aplikace nahore, uloha Ready. Kazdy pokus vzal 500-800 MB.
Dva pokusy se ztratily na chybe 404 kolem 9:47. Prave proto se pocet pokusu zvedl na 30 -
dvanact proslo o vlasek.

⚠️ **Je to obchazka.** Pricina - co useka dlouhe spojeni - **zustava neznama a otevrena**.
Merene podklady vyse jsou pripravene pro spravce site: nehleda se propustnost, hleda se,
co zabije spojeni po nekolika stech megabajtech.

## Jak poznat, ze uz je to opravene doopravdy

V logu `D:\STRATEGIE_IN\_pullrestore.log` se prestanou objevovat radky
`Download fail ... casovy limit operace vyprsel` a stazeni projde **na prvni pokus**.
Dokud tam ty radky jsou, jede se dal na obchazku.

_Souvisi:_ `doc-system-strategie-dr-prenos-praha-plzen-pricina-a-oprava-2026-09-08`,
`doc-system-g2007-dr-obnova-30-11`, `doc-provoz-topologie-serveru-praha-plzen`

