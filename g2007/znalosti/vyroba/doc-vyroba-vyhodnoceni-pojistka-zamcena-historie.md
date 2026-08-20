# Vyhodnoceni zakazek: pojistka proti zmene zamcene historie (hotovo 5.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Pojistka proti zmene zamcene historie

**Hotovo a overeno naostro 5. 8. 2026** (C28/Jirka). Schvalili Marti-AI (msg 12208) a Jirka.

## Co to dela

Vsech **pet zapisovych funkci** modulu Vyhodnoceni zakazek odmitne zakazku, ktera ma
`ec.vyhodnoceni_zakazka.uzamceno = true`. Tvrdy zakaz, bez moznosti obejit.
Chrani **1 675 zakazek z let 2021-2025** (rok 2026 je zamerne odemceny).

| funkce | vraci | jak odmitne |
|---|---|---|
| `ec.priprava_vyhodnoceni` | void | `RAISE EXCEPTION` |
| `ec.prepocet_vyhodnoceni` | void | `RAISE EXCEPTION` |
| `ec.vypocet_konstant` | text | `E#...` |
| `ec.vyhodnoceni_uzavrit` | text | `E#...` |
| `ec.vyhodnoceni_zrusit` | text | `E#...` |

Pojistka je vlozena hned za vypocet skupiny slouceni (`v_grp`), takze plati
pro **celou skupinu slouceпych zakazek**, ne jen pro tu jednu zadanou.

## Proc to bylo nutne

`priprava_vyhodnoceni` zacina `DELETE FROM ec.vyhodnoceni_osoba` a `vyhodnoceni_zrusit`
dela `DELETE FROM ec.zakazky_finance_zam` (vyplaty). Do 5. 8. se **zadna** z 11 funkci
schematu `ec` na `uzamceno` nedivala - zamek byl jen nalepka, ne zavora. Jedno kliknuti
na stare zakazce by smazalo prenesenou historii a postavilo prazdno (nase hodiny
zacinaji az 1. 1. 2026, takze u 1 656 z 1 865 zakazek neni z ceho stavet).

## Overeno naostro (obe strany)

- zamcena `I001`: vsech 5 funkci odmitlo se spravnou hlaskou vc. diakritiky
- nezamcena `PR3938` a `VR10390`: probehly normalne (`OK`), zadny falesny poplach

Testovano na zakazkach s nulou financnich radku a nulou osob - i pri selhani pojistky
nebylo co poskodit.

## Gotcha pri uprave PL/pgSQL funkci pres most

`pg_get_functiondef` pres most vrati telo se **zrusenymi radkovymi zlomy** - kdyby se
takto ziskany text poslal zpet, radkove komentare `--` by zakomentovaly zbytek funkce.
Postup, ktery funguje: stahnout jako `replace(pg_get_functiondef(oid), chr(10), '<<NL>>')`,
lokalne obnovit zlomy, zaplatovat programove (ne rucnim prepisem) a poslat zpet jako
`DO $do$ BEGIN EXECUTE convert_from(decode('<base64>','base64'),'UTF8'); END $do$;`.
Tim se vyhnes i poskozeni diakritiky. Po zapisu **overit md5** proti lokalni verzi.

