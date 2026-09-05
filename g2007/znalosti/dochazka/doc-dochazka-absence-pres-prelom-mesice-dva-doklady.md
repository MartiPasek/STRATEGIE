# Absence přes přelom měsíce vzniká jako samostatný zápis za každý měsíc — Správa i appka (4. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Rozhodla Peťa 4. 9. 2026:** *„je potřeba udělat, i když se zadá nemoc od 27.8. do 4.9., musí to udělat dva řádky — na srpen a na září, tak jako to bylo v Centrále."* Na dotaz, jestli dělit i mateřskou, odpověděla: *„dělit i mateřskou a to, co se dělilo v Centrále."* Na dotaz, jestli dělit i dovolenou zadanou z mobilu: *„jo."* → **jednotné pravidlo bez výjimek, na obou cestách.**

## Proč

Každý měsíc se schvaluje a účtuje sám za sebe. Když nemoc běží přes přelom, musí jít srpnová část schválit a poslat do mezd ve chvíli, kdy zářijová ještě nemá známý konec. Peťa 4. 9. 2026: *„vždy i když je to přes přelom měsíce, by měl být ten zápis za daný měsíc schválený."* Navazuje na postup zadávání nemoci — začátek podle neschopenky hned, provizorní konec, bez fajfky; po doručení ukončení se doplní skutečný konec a schválí (viz `doc-mzdy-obdobi-nemoci-do-mezd-z-neschopenky-ne-z-pracovnich-dnu`).

## Dvě vrstvy, ve kterých absence žije

1. **Zápis o období** — `tenant.att_absence_request`, jeden řádek s od–do, druhem, hodinami za den a stavem schválení. U nemoci odpovídá neschopence. Tohle se od 4. 9. 2026 dělí po měsících.
2. **Denní záznamy** — `tenant.att_entry` na jednotlivé pracovní dny, vznikají z toho období. Ty se počítají do hodin a do mezd.

⚠️ **Neříkej tomu „doklad".** Peťa 4. 9. 2026 se ptala *„co znamená u nás dovolená doklad má? jaký doklad?"* — to slovo v jejím jazyce znamená papír od lékaře nebo úřadu, ne řádek v databázi. Piš „zápis o období" nebo „období od–do".

⚠️ **A obě vrstvy jsou uživatelův JEDEN řádek.** Peťa 27. 8. 2026: *„pořád říkáš dny a žádost, ale já to tam nemám dvakrát."* Dělení po měsících je vnitřní mechanika — člověk u obrazovky má vidět prostě dva řádky, srpnový a zářijový. Detail v `doc-dochazka-sprava-dochazky-zadost-vs-den-a-fajfka`.

## Jak to měla Centrála (ověřeno v datech 4. 9. 2026)

⚠️ **Past, do které jsem spadl:** `EC_Dochazka_Udalosti` **míchá absence s obchodními událostmi**. Sloupec `Typ` je `EC_EventTyp.ID`, kde 3–9 obsahuje Projekt, Zakázku, Nabídku, Poptávku (typ 5 = Zakázka má 8 613 řádků a nemá s nepřítomností nic společného). Číselník `EC_Vytizeni_TypyUdalosti` **je jiný a na tuhle tabulku nesedí** — kdo ho použije, dostane úplně jiné názvy. Vždy joinovat na `EC_EventTyp`.

Centrála měla druhy nepřítomnosti rozdělené na dvě skupiny:

**Měly období od–do** (a to se dělilo po měsících):

| Druh | Období | Dnů v plánu |
|---|---|---|
| Nemocenská | 328 | 1 365 |
| OČR | 122 | 808 |
| Nařízené volno | 74 | 104 |
| Mateřská dovolená | 35 | 2 056 |
| Neplacené volno | 25 | 50 |
| Nepřítomnost OSVČ | 20 | 629 |
| Překážka v práci | 16 | 0 |
| Otcovská | 9 | 32 |
| Volno 60 / 70 / 80 / 90 % | 38 / 37 / 2 / 5 | — |

**Období NIKDY neměly** — jen jednotlivé dny v `EC_Dochazka_PlanNepritomnost`:

| Druh | Období | Dnů |
|---|---|---|
| **Dovolená** | **0** | 5 298 |
| **Dovolená navíc** | **0** | 2 091 |
| Home office | 0 | 5 762 |
| Sick day | 0 | 960 |
| Lékař | 0 | 907 |
| Služební cesta / montáž | 0 | 521 |

Druh „Dovolená" v číselníku Centrály existoval (`EC_EventTyp.ID=3`, `DruhCinnosti=20`), ale **nebyl použitý ani jednou**.

Ze skupiny s obdobím se u událostí od roku 2024 (329 kusů) 77 končí posledním dnem měsíce, 64 začíná prvním a jen 7 přechází přes přelom. U nemocenské **ani jedna ze 119**. Jediná výjimka byla **mateřská** — ta šla vcelku přes přelom roku (1. 1. – 31. 12.). Peťa si pamatovala opak; rozhodnutím ze 4. 9. 2026 **dělíme i ji**.

**Závěr pro dovolenou:** v Centrále u ní slepený zápis přes přelom vzniknout nemohl, protože žádné období neměla. U nás období má → dělí se jako všechno ostatní, na obou cestách.

## Kde to žije

**1. Správa docházky** — `modules/erp/api/dochazka_absence_sprava.py` (soubor na disku, deploy, commit `4ba3687b`):

- **`_po_mesicich(d_od, d_do)`** — rozdělí období na kusy po kalendářních měsících. Období uvnitř jednoho měsíce vrací jediný prvek, tam se nemění nic.
- **`dochazka_abs_new`** (POST `/app/dochazka-abs/new`) — po všech validacích (nárok, zámek, hodiny, práva se kontrolují **jednou na celé období**) se v cyklu založí období + denní záznamy za každý měsíc. Audit je jeden souhrnný a vypisuje čísla všech vzniklých řádků. Odpověď nese `ids` a `casti`.
- **`dochazka_abs_save`, větev A (nepromítnutá žádost)** — když se úpravou období roztáhne do dalšího měsíce, původní řádek zůstane na prvním měsíci a na zbylé vzniknou nové. Typický případ: nemoc s provizorním koncem 31. 8. se po neschopence prodlouží do 4. 9.

**2. Mobilní appka** — `att_absence_request` v `g2007.python`, **verze 20** (hot-swap, bez deploye). Stejná smyčka po měsících kolem INSERTu; `abs_promitni_zadost` se volá pro každý měsíční zápis zvlášť a `_dnu_prom` je jejich součet (na něm visí přepočet doplnění do fondu). Odpověď nese `ids` a `casti`. Záloha předchozí verze: `att_absence_request__zaloha_20260904` (`stav_zivota='inactive'`, md5 `254ef163f29fe8a75f1422bc8014b434`). Zapsáno přes base64 podle `doc-system-strategie-most-pyrun-a-base64-zapis`, md5 ověřeno na bajt.

Z appky přitom jako období přichází jen **dovolená, sick day a home office** — nemoc, OČR, lékař a mateřská mají mobilní cestu zavřenou od 26. 8. 2026 (Peťa: *„žádosti k nemocem, OČR, lékaři a mateřské z appky přece nejdou"*; ověřeno na datech — ze 14 letošních zápisů těchto druhů vzniklo 12 ve Správě a dva z appky jsou z doby před 26. 8.).

## Co se tím NEMĚNÍ

- **Přehled Správy docházky (`fw.data_set` 178) dělil po měsících už od 12. 8. 2026** — `date_trunc('month', d)` je v partition ostrovů i v `GROUP BY`. Změna ze 4. 9. je o **období**, ne o zobrazení. Přínos je, že srpen jde schválit a zaúčtovat samostatně.
- **Období nese kalendářní dny, ne pracovní.** Kus, který padne celý na víkend (nemoc 30. 8. – 4. 9. → srpnový kus 30.–31. 8.), vznikne **bez denních záznamů**. Je to záměr — mzdy potřebují i víkendové kraje neschopenky, ale do Docházky new patří jen pracovní dny.
- **Denní záznamy se zakládají hned, i do budoucna** (k 4. 9. 2026 je jich 176 dovolené a 79 mateřské až do 31. 12.). **Docházka new je ale nezobrazuje** — `fw.data_set` 177 (`dochazka.zakazky_vse_list`) má `WHERE d <= CURRENT_DATE`. Budoucnost je vidět výhradně ve Správě docházky, a tam ji Peťa mít chce: *„ve Správě docházky je to dobře, protože je to vlastně i budoucnost, ale v Docházce new je jen současnost do dnes."*

## Kontrola rozporů (4. 9. 2026)

Prohledáno celé G2007 na znalosti o přelomu měsíce, slepování řádků a budoucích dnech. **Nic k zneplatnění** — dvě nejbližší znalosti pravidlo potvrzují a zůstávají v platnosti:

- `doc-dochazka-sprava-vs-new-co-se-preklapi` (Peťa 30. 7. 2026) — *„Překlopení řeší samo datum: přehled filtruje `d <= CURRENT_DATE`."*
- `doc-dochazka-sprava-dochazky-zadost-vs-den-a-fajfka` (Peťa 27. 8. 2026) — dvě vrstvy pod jedním řádkem, fajfka = schválení.

## Ověření

Zadat absenci přes přelom (ve Správě i z mobilu) a zkontrolovat, že v `tenant.att_absence_request` vznikly dva řádky se stejným druhem a navazujícími obdobími.

