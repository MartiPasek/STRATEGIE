# Prilohy z posty: filtr pri prijmu + 50 593 priloh, jejichz soubor uz na disku neni (6.9.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Prilohy z posty: filtr pri prijmu a chybejici soubory

**Zapsal:** Claude-28 (Jiri Honomichl), 6. 9. 2026 · **Nasazeno:** `224d9719`
Zadal Jirka Honomichl, schvalila Marti-AI (msg 14548 a 14551).

## 1. Polovina evidovanych priloh na disku NEEXISTUJE

**Marti Pasek kolem 21. 8. 2026 sam smazal starsi prilohy kvuli nedostatku mista.**
Rez je podle poradi zaznamu: **vsechno pod id 122892 je pryc**, zaznamy v databazi zustaly.

Hranice overena NA KUS: v databazi je od id 122892 presne **51 084** zaznamu a ve slozce
`C:\Data\STRATEGIE\Dokumenty` presne **51 084** souboru. Namatkove zkontrolovano sest
dokumentu u zakazky (Prefakturace ES, Cenik 2026-03, Licencni smlouva) — vsechny chybi.

**Dopad:** 49 920 priloh nejde otevrit, z toho **805 je prirazenych k zakazce**.
Clovek je v seznamu vidi, ale soubor nedostane.

**Reseni (6. 9. 2026):** do `public.documents` pridan logicky sloupec **`file_missing`**;
u 50 593 zaznamu nastaven na pravdu a zaroven `file_size_bytes` na nulu.
**Evidence velikosti tim spadla ze 79 GB na skutecnych 19 GB** (na disku je 18,74 GB).
Zaznamy se NEMAZALY — Jirka rozhodl oznacit, ne mazat.

⚠️ **Kdo scita velikost priloh, musi pocitat s `file_missing`.** U oznacenych je velikost nula,
takze bezny soucet uz vraci skutecnost; puvodni velikosti jednotlivych smazanych souboru
se timto krokem ztratily (soucet byl 60 GB).

## 2. Filtr priloh pri prijmu

Misto: `modules/erp/api/mail_mirror.py`, funkce `_save_attachments` + nova `_priloha_ukladat`.

**Uklada se:** pdf, doc, docx, xls, xlsx, xlsm, xlsb, ppt, pptx, csv, txt, rtf, odt, ods, odp,
msg, eml **a obrazky nad 1 MB** (skeny, fotodokumentace, vykresy).
**Zahazuje se:** obrazky pod 1 MB (gif, png, jpg, jpeg, bmp, ico, svg, emz, wmz, heic, tif).
**Nezname pripony se ukladaji** — filtr je prisny jen tam, kde je to dolozene.

### Proc prave 1 MB — klicovy dukaz

`image004.jpg` ma 2 533 kusu, ale jen **4 ruzne velikosti**; `image003.jpg` 2 212 kusu
a 2 velikosti. **Nejsou to fotky, je to tyz obrazek z paticky ulozeny tisickrat.**
Hranice 1 MB chrani skutecne fotky z telefonu (2-5 MB).
Gifu bylo 5 072 kusu, ale jen **19 ruznych nazvu** (image001.gif az image013.gif, footer.gif).

### Overeni v provozu (6. 9. 2026, nasazeno v 10:07)

| obdobi | priloh | z toho malych obrazku | z toho gifu |
|---|---|---|---|
| do 10:07 | 402 | 290 | 44 |
| od 10:07 | 12 | 0 | 0 |

**Uspora ~2 400 souboru a ~290 MB denne** (pred filtrem prirustek ~1,4 GB a 3 000-5 700 souboru/den).

⚠️ **Vyjimku "prilohy u zakazky ukladat vzdy" NELZE udelat** — v okamziku ukladani prilohy
z posty jeste zadna zakazka prirazena neni, prirazuje se pozdeji.

## 3. K cemu ten sber je a kdo ho pouziva (merena cisla)

Ucel podle Marti-AI: znalostni baze nad firemni postou (smlouvy, faktury, podklady k zakazkam)
plus archiv pro dohledani.

Skutecnost od 1. 7. 2026: **166 406 ulozenych priloh** proti **93 vyhledavanim**.
Pouzivani klesa: cerven 41x, cervenec 43x, srpen 7x, zari 2x.
Hledali: Marti Pasek 35x, Kristyna Maresova 29x, Michaela Hladikova 10x, Sarka Novotna 7x,
Zuzana Duspivova 4x, Vladimir Mares 3x, Simona Urbanova 2x, po jednom Jiri Honomichl,
Pavel Zeman a Petra Safrankova.

**Ze 45 skutecnych dotazu nehledal obrazek, fotku, logo ani vykres ani jeden.** Hledaly se
smernice, kalkulace rozvadecu, ceniky, dochazka, BOZP, ISO 27001, TISAX, specifikace pro CRM.

> ⚠️ Poctiva vyhrada: vyhledavani je semanticke nad textem, takze obrazek se pres nej stejne
> najit neda. Absence dotazu proto nemusi znamenat absenci potreby. Marti-AI s vyhradou
> souhlasila — je to vstup pro rozhodnuti, ne jediny dukaz.

## 4. Doporuceni Marti-AI, ktere zbyva rozhodnout

*"Mazani nebyl problem, byl to symptom. System potrebuje politiku, ne jednorazove cisteni."*
Navrhuje zavest pravidlo, jak dlouho se prilohy drzi, misto nouzovych mazani.

