# Zrcadla oz_ jsou behem syncu prazdna nebo neuplna - kdo je v tu chvili cte, dostane tiche nesmysly

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Zrcadlo `oz_` je behem obnovy prazdne nebo neuplne

**Nasla C24 (Kristy) 9. 9. 2026 naostro**, root cause dohledany v kodu. Neni to teorie -
stalo se to a poskodilo to data.

## Co se stalo

9. 9. v 08.45 bezela uzaverka vyhodnoceni zakazky VR10686. Ve stejnou minutu startoval job
`oz_sync_all` (interval 30 min). Funkce `ec.vypocet_konstant` nenasla v `tenant.oz_zakazky`
ani jeden radek pro zakazku, `SUM` pres prazdnou mnozinu vratil **NULL** - a funkce ten NULL
**zapsala do hlavicky vyhodnoceni**, cimz prepsala kalkulovane hodiny prevzate z Centraly
(14 -> NULL, limit 16,1 -> 0). Nasledny prepocet spocital vsem **nulove premie** a uzaverka
vyrobila vyplaty bez premii. **Nic neohlasilo chybu.**

Ze slo o prazdnou mnozinu a ne o nulove hodnoty dokazuje prave to `NULL`: `SUM` pres radky
s nulami vraci `0`, pres zadne radky `NULL`. Data ve zrcadle byla v poradku pred behem i po nem.

## Pricina (kod)

`modules/erp/api/oz_mirror.py`, funkce `fill()`:

```
r. 129   TRUNCATE tenant.<tabulka>
r. 137   INSERT ... (davka 500 radku)
r. 138   s.commit()          <- commit PO KAZDE DAVCE
```

`TRUNCATE` se zverejni ostatnim transakcim hned s prvnim commitem. Nez dobehne posledni davka,
vidi kazdy ctenar tabulku **prazdnou nebo naplnenou jen zcasti**. U `oz_zakazky` je to
5 697 radku, tedy zhruba dvanact davek, a data se mezitim tahaji z MSSQL pres MCP.

## CASTECNE NAPLNENI JE ZAKERNEJSI NEZ PRAZDNE

U slucene skupiny zakazek muze jedna chybet a druha byt pritomna. Soucet pak tise vyjde
spatne a **nedostanes ani NULL, ktery by varoval**. Tenhle scenar projde i pres pojistku nize.

## Rozsah

**Netyka se jen vyhodnoceni zakazek.** Kdokoli cte kterekoli `oz_` zrcadlo behem jeho syncu,
muze dostat neuplna data. Riziko roste s velikosti tabulky a s frekvenci cteni.

## Co je nasazeno (jen naplast)

`ec.vypocet_konstant` (request #2836, 9. 9.) odmitne s `E#` a **nesahne na hlavicku**, kdyz
zrcadlo zakazku neobsahuje. Chrani penize v tomhle jednom modulu, **neresi castecne naplneni**
ani ostatni ctenare.

## Korenova oprava - navrh k projednani

Naplnit **odkladaci tabulku** a prohodit ji s ostrou v jedne transakci (rename), takze ctenar
vidi bud celou starou, nebo celou novou. Detail vcetne toho, co overit pred nasazenim
(GRANTy, zavisle pohledy, chovani pri chybe, UNLOGGED) je v `docs/zrcadleni_atomicky_navrh.md`.
Tyka se sdilene infrastruktury - **patri Petovi a Jirkovi, ne jedne instanci**.

## Pouceni

- `SUM` pres prazdnou mnozinu vraci NULL, ne nulu. **NULL v agregatu = nenaslo se nic** -
  je to uzitecny rozlisovaci znak pri hledani techhle chyb.
- Funkce, ktera pocita z externiho zdroje, **nema zapisovat vysledek, kdyz zdroj nic nevratil**.
  Radeji nic nespocitat nez spocitat ze vzduchu.

