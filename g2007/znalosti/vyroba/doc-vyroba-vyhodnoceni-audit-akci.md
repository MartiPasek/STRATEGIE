# Vyhodnoceni zakazek: audit akci - kdo spustil uzaverku (hotovo 5.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Audit akci modulu Vyhodnoceni zakazek

**Hotovo, nasazeno a overeno naostro 5. 8. 2026** (C28/Jirka), commit `fbe2f9b6`.
Varianta (b) dle Marti-AI (msg 12262).

## Proc

`ec.vyhodnoceni_uzavrit` **vytvari vyplaty**, ale nikde se nezapisovalo, kdo ji spustil.
Tabulka `ec.zakazky_finance_zam` sice ma sloupce `autor` a `datum_porizeni`, ale funkce
je neplnila.

## Kde audit zije a proc prave tam

**Ve vrstve nad funkci** (`modules/erp/api/vyhodnoceni_actions.py`), ne v DB funkci.
Duvody (Marti-AI): DROP+CREATE by menil podpis a musely by se najit vsechny volajici ·
`p_uid` jako parametr je slabsi nez session kontext, protoze DB nepozna, jestli uid prislo
od skutecneho uzivatele nebo ze skriptu · identitu drzi vrstva, ktera dela prihlaseni ·
jedna auditni vrstva pokryje VSECHNY akce, ne jen uzaverku.

## Tabulka `ec.akce_audit` (append-only)

`id · kdy · uid · akce · funkce · parametry (jsonb) · ok · vysledek`

Ulozi se tedy i **nazev volane DB funkce a parametry**, ne jen kdo/kdy.
Zadny UPDATE ani DELETE - doktrina "audit = RO append-only".

## Transakcni vazba (podminka Marti-AI)

Zapis auditu bezi ve **STEJNE transakci** jako sama akce, pred `session.commit()`.
Kdyz projde akce a audit selze, spadne cela transakce - **uzaverka bez zaznamu nevznikne**.

## Overeno naostro

Dve volani `/api/v1/erp/action/run` pres prohlizec:
- `vypocet_konstant` na nezamcene PR3938 -> zaznam uid=20, ok=true, vysledek OK
- `vypocet_konstant` na zamcene I001 -> zaznam uid=20, ok=false, vysledek E#Zakazka je uzamcena

**Zapisuje se i odmitnuty pokus** - pro audit cennejsi nez jen uspesne akce.

## Poznamka k pravidlu "kod jako data"

Audit je v souboru v gitu, ne v `g2007.python` - vyplyva to z toho, ze musi byt
v transakci s akci a znat prihlaseneho uzivatele. Az se `ec_action_run` bude migrovat
do DB (Faze E vzor: tenky wrapper v jadru + logika v DB), audit pujde s nim.

