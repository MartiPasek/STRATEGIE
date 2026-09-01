# Schvalovani absenci: zeleny pruh nahrazen dlazdici s VLASTNI viditelnosti (1. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Rozhodnuti

**Zadal Jiri Honomichl 1. 9. 2026, schvalila Marti-AI (msg 14167).** Zeleny pruh
„Ke schvaleni: N" (`id=dochApprBar`) na obrazovce Dochazka je **zrusen** a nahrazen
**dlazdici „Ke schvaleni"** v sekci SPRAVA DOCHAZKY, hned vpravo vedle „Opravy dochazky".

Jirka rozhodl ctyri veci: dlazdici vidi **kazdy, kdo ma neco ke schvaleni** (ne jen lide s pravy
oprav) · je videt **vzdy** (ne jen pri praci, jako byval pruh) · **stary pruh se rusi uplne** ·
klik dela totez co pruh (`go("absence")`).

## ⭐ Jadro veci: dlazdice MUSI mit vlastni viditelnost, jinak odstrihne 9 lidi

Sekce **SPRAVA DOCHAZKY** (`id=dochFixSec`) se zobrazuje jen pri **`can_fix`** (clenstvi ve skupine
`DOCHAZKA - OPRAVY`, nebo rodic) **nebo `can_lock`** (uzivatele 18, 13, 20, nebo rodic).

**Schvalovatelu absenci je ale 16** (`tenant.att_approver` + osobni vyjimky `tenant.att_odpovednost`
agenda `volno`) a **do te sekce jich patri jen 7**. Pouhy presun pruhu do sekce by tedy
**devet lidi pripravil o schvalovani** - overeno dotazem 1. 9. 2026, jmenovite:

> Jan Svoboda (12) · Marek Honal (85) · Martin Pasek (35) · Michaela Hladikova (16) ·
> Ondrej Pillar (21) · Petr Benes (31) · Vladimir Mares (22) · Zdenek Cepicky (39) ·
> Zuzana Duspivova (6)

Bylo by to presne to, cemu mel pruh z 5. 8. 2026 zabranit („schvalovani cizi absence NESMI zmizet
jen proto, ze vedouci sam zrovna maka").

**Reseni:** `_apprCell` ma vlastni prepinani (`showAppr(n)`) podle **poctu zadosti k rozhodnuti**
z `GET /api/v1/erp/app/attendance/absence/inbox`, nezavisle na `can_fix`/`can_lock`. Dotaz se
vola **vzdy** (drive jen kdyz clovek makal, s omezenim 30 s). Sekce se otevre, kdyz je videt
aspon jedna z dlazdic (`_secShow()`); komu chybi prava k opravam, uvidi sekci jen s tou svou.

## Pozor pri cteni dat: kdo ma zadost vs. koho se tyka

Sprava se vidi ruzne podle prav (`att_absence_inbox`): **rodic, spravce (`users.is_admin`) nebo
drzitel prava `neschopenky`/write vidi VSECHNY cekajici zadosti**; ostatni jen ty, kde jsou
`manager_user_id`. Jirka je spravce, proto na jeho uctu ukazuje dlazdice **celkovy** pocet.
Pri overovani dopadu se tedy neptej „kolik ceka na neho", ale **kdo je uveden jako schvalovatel**.

## Vzhled odznaku

Odznak byl puvodne zeleny (#34d399, bily text = kontrast **1,92 : 1**) - **to byla chyba pri
zavedeni**, vybrana kvuli souladu se zrusenym zelenym pruhem. Tyz den sjednoceno: vsechny odznaky
v appce maji **#c62828 s bilym textem (5,62 : 1)**, viz [[doc-system-strategie-mobil-odznaky-jednotna-cervena]].

## Overeni

Na **zive `/mobile` pod uctem Jiriho Honomichla** (pod ukazkovym uctem se odznaky vubec
nevykresli, protoze demo nema co schvalovat): sekce ukazuje dve dlazdice vedle sebe,
„Opravy dochazky" s odznakem 3 a „Ke schvaleni" s odznakem 2; klik otevre obrazovku Absence
se seznamem (1. 9. 2026 Petr Benes - dovolena 1. 9., Michaela Hladikova - home office 4. 9.).

_Souvisi:_ [[doc-dochazka-dlazdice-vzdy-viditelne-pravni-duvod]],
[[doc-dochazka-vedouci-jediny-zpusob-a-fronta-oprav-rodice]],
[[doc-dochazka-schvalovani-absenci-kde-a-jak]]

