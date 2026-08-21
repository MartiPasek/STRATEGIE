# Zakladani ukolu v Centrale (EC_Ukoly) z kodu — tri pasti, na ktere se da naletet

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Kontext
Nas kod (`g2007.python` / `podklad_ukol_send`) zaklada v Centrale ukol na Nakup
a dava vic lidi do kopie. Zjisteno pri ostrem testu 20. 8. 2026 (C24 / Kristy),
plati pro KAZDY zapis do ukolniku Centraly pres MCP `eurosoft_strategie_query_raw`.

## Past 1 — `EC_GetUserCisZam()` vraci NULL pro nas servisni ucet
Varianta `EC_Ukolnik_ZalozAOdesliUkol_Loc` umi seznam kopii (`@SeznamKopie`) a laka
tim k pouziti. Na konci ale zapisuje do `EC_UkolyHistorieReseni` cislo zamestnance
z `dbo.EC_GetUserCisZam()`, tedy podle PRIHLASENEHO SQL UZIVATELE. Nas servisni ucet
zadne cislo nema → NULL → INSERT spadne na
„Cannot insert the value NULL into column 'CisloZam', table 'EC_UkolyHistorieReseni'".
Navenek se to projevi JEN jako `internal_error`, bez jakekoli napovedy.

Puvodni `EC_Ukolnik_ZalozAOdesliUkol` tuhle pojistku MA (`IF isnull(@UserCis,0)=0
SET @UserCis = 10008`) → **pouzivej ji**, i kdyz umi jen jednu kopii (`@Kopie int`).
Prvni kopii dej parametrem, zbytek si doplnis sam (viz Past 2 a 3).

Obecne pravidlo: pred pouzitim procedury Centraly zkontroluj, jestli nekde nesaha na
`EC_GetUserCisZam()` bez fallbacku. Nas ucet neni clovek.

## Past 2 — `EC_UkolyResitelVazba.Stav` musi byt vyplneny
Radek kopie (`Typ = 2`) potrebuje `Stav = 2` („Odeslan"; pozdeji si ji adresat precte
a Centrala prepne na 12 „Zkontrolovan"). Radek bez stavu ma `StavText = 'Undefined'`.
Vkladej tedy rovnou: `(IDUkol, Resitel, Typ, Stav, Aktivni, DatPorizeni, Autor)`
= `(<id>, <cislo>, 2, 2, 0, GETDATE(), SUSER_SNAME())`.

## Past 3 (ta zakerna) — detail ukolu cte kopie z `EC_Ukoly_Komplet`, ne z vazebni tabulky
`EC_Ukoly_Komplet` je DENORMALIZOVANA tabulka pro rychle zobrazeni; ma sloupce
`SeznamKopie` (cisla) a `SeznamKopieText` (prezdivky). Formular „Detail ukolu v2"
zobrazuje pole Kopie odtud. Procedura ji naplni jen podle toho, co sama zna — tedy
jen prvni kopii z `@Kopie`.

Dusledek: rucne vlozene kopie v databazi JSOU (a v `EC_UkolyResitelVazba` sedi vsechny
sloupce), ale v ukolu je porad videt jen ta jedna. Kontrola pres SELECT nad vazebni
tabulkou tedy NIC NEDOKAZE — musis se podivat do `EC_Ukoly_Komplet`.

Reseni: po vlozeni kopii ZAVOLAT
`EXEC EC_Ukolnik_AktualizujKomplet @ID=<IDUkol>, @PregenerovatResitele=1;`
Ta si seznam posklada z `EC_UkolyResitelVazba` (FOR XML PATH nad `Typ=2`) a dopise
i jmena. Overeno: pred volanim `SeznamKopie='475'`/`'AndreaB'`, po volani
`'1, 21, 381, 420, 442, 475'` / `'AndreaB, IvaH, IvanaH, Kristyna, Michelle, Peta'`.
`EC_Ukolnik_AktualizujKomplet` `EC_GetUserCisZam()` nepouziva, takze je pro nas bezpecna.

## Obecne pouceni
Centrala ma u ukolniku dve vrstvy: normalizovanou (`EC_UkolyResitelVazba`) a zobrazovaci
(`EC_Ukoly_Komplet`). **Kdyz do normalizovane vrstvy sahnes rucne, zobrazovaci se sama
nedopocita.** Stejny vzor ocekavej i u jinych „Komplet" tabulek Centraly — pri overovani
zapisu se vzdy divej do te vrstvy, ze ktere cte UI, ne do te, do ktere jsi zapisoval.

