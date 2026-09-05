# Potvrzovani odvozu z docházkoveho tabletu stoji od 22.7.2026 - 44 nepotvrzenych odvozu

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## !! POZNAMKA - nazvy tlacitek se 5. 9. 2026 zmenily
> Text nize popisuje udalosti z roku 2026, kdy se tlacitko pro zahajeni prace jmenovalo
> "Makat". **Zamerne se neprepisuje** - o minulosti je pravdivy. Dnes se to tlacitko
> jmenuje **START** (rozhodl Jiri Honomichl 5. 9. 2026).
> Aktualni stav: [[doc-dochazka-mobil-dochazka-prejmenovani-a-pravdivost-navodu-5-9-2026]]

## Nalez (overeno 25.8.2026 v DB_EC i v nasi DB)

**Potvrzovani odvozu zakaznikum z docházkoveho tabletu (prehled „Doprava zakaznikovi", definice 27) prestalo fungovat 22.7.2026 a od te doby nikdo nepotvrdil ani jeden odvoz.**

| obdobi | naplanovano | potvrzeno | nepotvrzeno |
|---|---|---|---|
| leden-kveten 2026 | 121 | 119 | 2 |
| cerven 2026 | 23 | 21 | 2 |
| **cervenec 2026** | 30 | 21 | **9** |
| **srpen 2026 (k 25.8.)** | **35** | **0** | **35** |

Posledni potvrzeny odvoz **21.7.2026 ve 14 hodin 02 minut**. Celkem **44 nepotvrzenych odvozu**; Dusan a ZDivis o nich nedostali notifikaci.

## Pricina - retez je uzavreny

1. Odvozy potvrzovali od ledna 2025 **jen ctyri lide, prakticky dva**: Svenda Jaroslav (os.c. 488, 407 potvrzeni) a Nosek Martin (os.c. 425, 80 potvrzeni). Dalsi dva maji dohromady 11 potvrzeni, posledni v zari 2025.
2. **Oba hlavni prisli o opravneni na terminal tentyz den - 22.7.2026** (audit `fw.ec_dml_log`, via='vypni_dochazka'). Spustilo to jejich prvni „Makat" v mobilni appce -> funkce `ec_vypni_dochazku` zapsala `TabCisZam_EXT._AuthDochazka = ''`.
3. Prihlasovaci procedura tabletu **`EC_DochazkaLogin`** pousti dovnitr jen cloveka, ktery ma v `_AuthDochazka` hodnotu **`D`, `A` nebo `U`**. S prazdnou hodnotou vyber nic nevrati, `@LoginOK = 0` a clovek se na tablet **vubec neprihlasi** - proto padla i pracovni tlacitka.
4. **V mobilni appce potvrzeni odvozu NENI.** Existuje prehled (`app_vyroba_odvozy`) a poznamky (`app_vyroba_odvoz_pozn_list` / `_create`), ale **zadna ziva funkce nezapisuje `DatumOdvezeni`**. Stara cesta je zavrena, nova nedodelana.

Log prihlaseni (`EC_Dochazka_AppLogPrihlaseni`) ukazuje odpovidajici zlom - do 21.7. se oba hlasili 7-17x denne, po 22.7. uz jen jednotlive ojedinele pokusy (Svenda naposledy 13.8.). Pozor, log nerozlisuje uspech a neuspech, takze je to indicie; dukaz je v kodu prihlaseni.

## Platne hodnoty `_AuthDochazka`

Procedura uznava **`D`, `A`, `U`** a nic jineho. Rozlozeni u aktivnich zamestnancu k 25.8.2026: **`U` = 27 lidi** (jedina hodnota, kterou aktivni lide realne maji), **prazdny retezec = 69** (aktivne vymazano nasi funkci), **NULL = 17** (nikdy nenastaveno), `A` a `D` po jednom u lidi, kteri uz nejsou aktivni.

⚠️ **Prazdny retezec a NULL nejsou totez.** Prazdny retezec = nekdo to vymazal. Pri analyzach je rozlisuj.

## Dve vrstvy, ktere se pletou

| vrstva | co ridi | kde |
|---|---|---|
| opravneni **cloveka** | jestli se na tablet vubec prihlasi | `TabCisZam_EXT._AuthDochazka` |
| vypinace na **zarizeni** | ktera tlacitka jsou na tom kterem tabletu videt | `EC_Dochazka_NastavZar.TlOdvozy`, `.TlBeistellung` |

Pro jednoho cloveka opravdu nejde zapnout jen Odvozy bez dochazky (opravneni je vse, nebo nic) - ale **vypnout tlacitko na konkretnim tabletu jde**, plosne pro vsechny, kdo k nemu prijdou. Stav k 25.8.2026: `TlOdvozy` zapnuto na Tablet_Vedlejsi_Vchod, Tablet_Prizemi_Perforex, Ondra_Pc a jednom nepojmenovanem zaznamu; vypnuto na Tablet_3NP a Tablet_Perforex.

## PAST - `_BlokovatDochazku` nepouzivat jako „nech terminal, zakaz dochazku"

Nabizi se vratit opravneni `U` a dochazku zakazat pres `_BlokovatDochazku` (13 aktivnich lidi tak dnes je). **Je to cizi mechanismus:** `EC_Dochazka_ZahajBlokaci` k nemu posila notifikaci „Mate nesplneny ukol, prihlaseni do dochazky je blokovano" a trigger `EC_Dochazka_I` pri zapisu dochazky **zaklada a odesila ukol** o nesplnenych povinnostech pri sprave ukolniku. Clovek by dostaval vyzvy o neexistujicim provineni.

## Jak funguje samotne potvrzeni (procedura `EC_DopravaZakaznikovi_PotvrzeniOdvozu`)

- **Je to prepinac, ne jednosmerne potvrzeni** - `DatumOdvezeni = IIF(DatumOdvezeni is null, GETDATE(), NULL)` a stejne `OdvozPotvrdil`. Druhy stisk potvrzeni zrusi a smaze i to, kdo ho udelal; puvodni hodnota zustane jen v archivu `EC_DopravaZakaznikovi_Archiv`.
- **Notifikace odejde i pri tom zruseni**, porad s textem „byla prave oznacena jako odvezena". Prijemce to muze svest na scesti.
- **Prijemci jsou natvrdo v kodu** - `LoginId` = `ZDivis` a `Dusan`. Pri personalni zmene se musi sahnout primo do procedury.

## Beistellung

Tlacitko Beistellung na tabletu vola `EC_Zakazky_NastavBeistellung`, ktera nastavuje `tabZakazka_ext._StavBeistellung` na hodnoty typu ANO / NE / CEKA. **Neni to dochazkova vec, je to stav zakazky.** Parametr „kdo zmenu provedl" procedura prijima, ale **nepouziva** - zmeny Beistellungu se nikam neloguji, takze vypadek u nich nejde zmerit. V mobilni appce Beistellung **neni vubec**.

## Souvislost s rozhodnutim z 30.7.2026

Znalost [[doc-dochazka-vypnuti-centrala-tablet-tlacitka]] nese rozhodnuti Kristy + Jirky z 30.7.2026, ze se terminal **neobnovuje** a pracovni akce se udelaji jako tlacitka v appce. K 25.8.2026 je hotovy jen **prehled** odvozu, potvrzovani ne - proto ten vypadek. **Rozhodnuti, jak dal, je na Jirkovi** (dodelat potvrzovani do appky vs. vratit opravneni na tablet) a otevrena zustava i otazka, co s temi 44 nepotvrzenymi odvozy.

## Doporuceni, ktere plati dal

Nez se `_AuthDochazka` nuluje, **ulozit puvodni hodnotu** (dnes se loguje jen nova, takze zpetne se neda rekonstruovat), a u lidi, kteri terminal pouzivaji i na **praci**, nulovat vyberove, ne plosne.

