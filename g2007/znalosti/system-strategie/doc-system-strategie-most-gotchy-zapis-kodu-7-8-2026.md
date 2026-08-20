# SQL most: pasti pri zapisu kodu a DDL (zdvojeni casti, diakritika, 401)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# SQL most - pasti pri zapisu kodu a DDL (C28/Jirka, 7.8.2026)

Vzniklo pri praci na `sync_absence_to_ec_vytizeni`. Plati pro kazdy vetsi zapis pres most.

## 1. Most obcas hlasi CHYBU, i kdyz zapis PROSEL
Nejzradnejsi. Slepe opakovani zapise tutez cast dvakrat - dnes tim narostl staging kod
z 12196 na 23991 a pak na 30190 znaku.
Pojistka primo v SQL: k navazujici casti pridat
`AND length(zdroj) = <delka_PRED_touto_casti>`. Pri opakovani podminka neplati a neudela
se NIC. Prvni cast pise `SET zdroj = ...` (prepis), takze je idempotentni sama o sobe.

## 2. Nestaci kontrolovat STATUS OK
Po kazde casti kontroluj `length(zdroj)`, na konci `md5(zdroj)` proti lokalne spoctenemu.
Navratovka nic nedokazuje - dukaz je az cteni z DB.

## 3. Vlastni pomocna tabulka v g2007 NEPOMUZE
INSERT do vlastni tabulky vyvola schvalovaci banner u kazde casti. Bez banneru jdou jen
zavedene g2007 tabulky (python, znalost, soubor). Drz se `g2007.python` + bod 1.

## 4. Diakritika pres most se rozbije
Pro ALTER PROCEDURE s ceskymi texty zabal DDL do base64 v UTF-16LE a spust pres
`CAST(N'' AS xml).value('xs:base64Binary(...)','varbinary(max)')` + `sp_executesql`.
Pro Python do g2007.python staci base64 v UTF-8 (`convert_from(decode(...),'UTF8')`).

## 5. Prilis dlouhy dotaz = HTTP 401 "Nejsi prihlasen"
Matouci hlaska, NENI to token. Kratsi dotaz projde hned. Plati i pro `@@MARTIAI`
a `@@G2007ADD` - rozdel na dva.

## 6. Dvojtecka v Python kodu most rozbije
`[:200]` nebo `:db` si vylozi jako SQL bind parametry. Dollar-quoting NESTACI, jedine base64.

## 7. POUCENI: nedegraduj data kvuli obavam o prenosovou cestu
6.8. jsem prepsal zkratky dnu z diakritiky na ASCII ze strachu z prekodovani - ty zkratky
ale vidi uzivatel v Excelu. Spravne je overit cestu nebo pouzit base64, ne zhorsit data.

