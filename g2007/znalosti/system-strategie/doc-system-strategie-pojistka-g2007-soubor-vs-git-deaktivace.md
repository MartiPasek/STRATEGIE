# Pojistka g2007-soubor-vs-git deaktivovana 17.8.2026 (hlidala pravidlo zrusene 5.8.)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se stalo
Pojistka `tenant.pojistka` id=23, kod **g2007-soubor-vs-git** (zavedla Peta + Claude-26 dne 5.8.2026) svitila **trvale cervene**, aniz by slo o skutecnou chybu. Dne 17.8.2026 byla po schvaleni Marti-AI **deaktivovana** (`aktivni=false`) a duvod byl dopsan primo do jejiho popisu.

## Jake pravidlo hlidala
Po publikaci artefaktu pres `@@G2007PUBLISH` se obsah zapsal na cloud disk a do `g2007.soubor`, ale ne do gitu. Necommitnuta zmena na cloudu znamenala dirty working tree, `/deploy/now` vracelo `reason=dirty_working_tree` a **blokovalo deploye celemu tymu** (incident 5.8.2026, `dochazka-opravy.html` v14/v15 - Kristy to musela na 10.200.188.11 odlozit stashem a restartovat API).

## Proc uz neplati (dva nezavisle duvody)
1. **Pravidlo bylo 5.8.2026 zruseno.** Slozka `apps/api/static_db/` je v `.gitignore`, artefakty se do gitu **zamerne necommituji** (viz `doc-system-strategie-staticke-artefakty-db-materializace-vyrazeni-z-gitu`). Overeno 17.8.2026 - `git ls-files apps/api/static_db` vraci **0 souboru**. Dirty working tree z artefaktu tedy nevznika.
2. **Sama kontrola nikdy neoverovala nasazeni.** SQL znelo
   `SELECT NOT EXISTS (SELECT 1 FROM g2007.soubor s WHERE s.typ='artefakt' AND s.updated_at < now() - interval '24 hours' AND s.updated_at > now() - interval '30 days')`
   - tedy pouze **stari artefaktu**, zadna vazba na git ani na deploy. Takovy artefakt existuje prakticky vzdy, takze vysledek byl trvale `false`. K 17.8.2026 na ni viselo **10 artefaktu** z 5.-12.8. (dochazka-opravy.html, dochazka-po-zakazkach.html, vyroba.html, registr-absenci.html, dochazka-zakazky.html, foto.html, martinky.html, overit.html, marti.html, index.html) - vsechny `apps/api/static_db/*.html`.

## Rozhodnuti Marti-AI (17.8.2026)
Varianta A - vypnout a zduvodnit, **neprepisovat na novou kontrolu**. Jeji slova - *trvale cervena pojistka je horsi nez zadna, protoze ji prestanes vnimat a prehlednes skutecny problem; ticha cervena je slepa zona.* Nahradni kontrola by potrebovala jasne zadani, co presne ma hlidat, kdyz `static_db` v `.gitignore` zustava zamerne. Souhlas Marti-AI staci, Petu jako autorku neni nutne oslovovat - **neni to kritika jeji prace, jen zmena kontextu** (pravidlo, na kterem pojistka stala, prestalo platit).

## Otisk zapisu (overeno ctenim, ne navratovkou)
- pred - `aktivni=true`, popis 670 znaku, md5 `90e84aeac7bc0693a779da99e94fe98c`
- po - `aktivni=false`, popis 1606 znaku, md5 `c898b56fd3398c0a5ce13b9a49705a2d`
- `SELECT count(*) FROM tenant.pojistky_check()` = **0 cervenych** (pred zapisem 1)
- celkovy stav pojistek - **45 aktivnich, 1 vypnuta** (jen tato) - zadna jina se nedotkla

## Poucení pro pristi
- **Kdyz se zrusi pravidlo, projdi pojistky, ktere ho hlidaly.** Zruseni tabulky nebo pravidla umi pojistku bud utisit, nebo naopak rozsvitit natrvalo - viz take `doc-system-strategie-narok-dovolene-pravidla` (pojistka opirajici se o smazanou tabulku hlasila CHYBA KONTROLY, tedy nehlidala vubec).
- **Kontrola musi merit to, co pravidlo rika.** Tato merila stari artefaktu, ale pravidlo bylo o nasazeni do gitu - byla by falesne cervena i v dobe, kdy pravidlo platilo.
- Pojistka se **nemaze**, jen vypina - historie i duvod zustavaji v `popis`, zapnout jde kdykoli.

Zapsal Claude-28 za Jirku, 17.8.2026, schvalila Marti-AI.

