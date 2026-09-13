# Pripravit doplni lidi, Prepocet ne - bez prvniho kroku chybi ve vyhodnoceni 600 pripadu prace

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# "Pripravit" a "Prepocet" nedelaji totez

**Zmerila C24 (Kristy) 11. 9. 2026** na zivych datech. Neni to teorie - je to rozdil
12 738 hodin.

## Rozdil v jedne vete

| tlacitko | funkce | co umi |
|---|---|---|
| **1. Pripravit hodnoceni** | `ec.priprava_vyhodnoceni` | **smaze seznam osob a postavi ho znovu z nasi dochazky** (a pak si sam zavola prepocet) |
| **3. Prepocet hodnoceni** | `ec.prepocet_vyhodnoceni` | jen opravi hodiny a premie lidem, kteri v seznamu **UZ JSOU** |

**Prepocet neumi nikoho pridat.** Kdo na zakazce pracoval, ale v seznamu prevzatem
z Centraly neni, tomu se prace nezapocita.

## Rozsah problemu (stav 11. 9. 2026, otevrene odemcene zakazky)

- **600 pripadu** "clovek ma u nas na zakazce hodiny, ale ve vyhodnoceni neni"
- **12 738 hodin**, ktere by se do premii nepromitly
- tyka se **100 ze 112** otevrenych zakazek

Priklad VR10608: ve vyhodnoceni 387,86 h, v nasi dochazce 463,13 h. Rozdil 75,27 h
jsou ctyri lide (496, 126, 370, 49), kteri v seznamu z Centraly nejsou.
Neni to vyloucenymi cinnostmi - tech je na te zakazce nula hodin.

## Co z toho plyne pro praxi

**Vzdy zacinat krokem 1 (Pripravit).** Kdo skoci rovnou na Prepocet nebo na Uzavrit,
pracuje se seznamem osob z Centraly - a ten je u zakazek, na kterych se u nas pracovalo,
neuplny. Poradi tlacitek v liste uz je od 9. 9. srovnane podle skutecnych kroku,
takze staci jit zleva doprava.

## Co Pripravit stoji

Smaze cely seznam osob, takze prijdou hodnoty, ktere zadala Centrala a my je neumime
spocitat: `efektivita_osoba`, textove poznamky, hodnoceni kvality, priznak nepodepsaneho
zakazkoveho listu. K 11. 9. 2026 to u vsech 230 osob otevrenych zakazek delalo
**2 efektivity, 1 poznamku a 0 hodnoceni kvality** - prakticky nic. U jinych obdobi
to muze byt jinak, takze pred hromadnym zasahem to stoji za zmereni.

## Poznamka k hromadnemu spousteni

11. 9. 2026 probehl hromadny **Prepocet** na 25 otevrenych zakazkach (audit v
`ec.akce_audit`, kanal "hromadny prepocet C24 11.9.2026"). Srovnal hodiny stavajicim
lidem a oznacil je `zdroj='strategie'`, ale **chybejici lidi nedoplnil** - prave kvuli
rozdilu popsanemu vyse. Zbylych 13 zakazek s osobami zustalo nedotcenych (rozhodnuti
Kristy: dal hromadne nezasahovat, doplni to Dusan svym kliknutim).
Zaloha stavu pred behem: `docs/zaloha_osoby_pred_hromadnym_prepoctem_2026-09-11.md`.

## Pouceni pro instance

Nez doporucis hromadne spusteni nejake akce, **over si, co presne ta akce dela** -
ne co si o ni myslis podle nazvu. "Prepocet" znelo jako "srovnej vsechno", ve skutecnosti
je to "srovnej to, co uz tam je". Rozdil se ukazal az na datech.

