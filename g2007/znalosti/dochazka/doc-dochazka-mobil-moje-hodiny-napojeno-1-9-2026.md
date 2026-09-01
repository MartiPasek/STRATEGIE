# Moje hodiny v mobilu - napojeno na skutecny vypocet (1. 9. 2026), pocita se stejne jako prehled Nesplneny FPD

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Moje hodiny v mobilu - napojeno na skutecny vypocet

**Zadal Jirka Honomichl 1. 9. 2026, schvalila Marti-AI (msg 14134 a 14140).
Pripominkovaly Peta Safrankova (dochazka) a Kristyna Maresova (procesy) - obe pripominky
jsou zapracovane. Nahrazuje stav popsany v [[doc-dochazka-mobil-moje-hodiny-nuly-dokud-neni-zdroj]].**

## Co to je

Karta **"Moje hodiny"** na obrazovce **Muj prehled** v mobilni aplikaci. Clovek na ni vidi
za mesic, kolik odpracoval, kolik ma mit, a jestli je nad fondem nebo pod nim.
Prepinac mesicu (sipky), vychozi je aktualni mesic, dopredu se nejde.

Od 17. 8. 2026 tam byly **zamerne nuly**, protoze tri prehledy davaly tri ruzna cisla.
31. 8. 2026 se dva z nich sjednotily na vypocet Peti a duvod k nulam tim padl.

## Odkud se cisla berou

Zdroj je `g2007.python` **`app_dochazka_moje_hodiny`** (verze 4, active), adresa
`app/dochazka/moje-mesic` v jadre je uz jen tenka spojka (delegat).
Vypocet je **prevzaty z ERP prehledu Dochazka - Kontrolni prehledy - Nesplneny FPD**
(`g2007.python dochazka_kontrola_data`, `_KONTROLA_FPD_SQL`) - do toho prehledu se NESAHALO.

Rozdily proti prehledu, obe zamerne:
- **obdobi je parametr** (rok, mesic), prehled ma napevno posun na minuly mesic do 12. dne,
- **filtruje se na jednoho cloveka**, ne na tym.

## Co karta ukazuje a proc

| prvek | proc |
|---|---|
| velke cislo = **skutecne odpracovane hodiny** | `hodiny_mzdove` MINUS to, co do fondu dopsal automat (`att_entry`, source automat, typ `fond_doplneni`). **Podminka Peti** - ty hodiny nikdo neodpracoval. Za srpen 2026 to delalo u Martiho Paska 118,37 h ze 238,13 h a u Jirky Honomichla 37,56 h z 284,96 h. |
| **dovolena a nemoc zvlast** | Podminka Kristyny - v ERP prehledu je absence schovana ve sloupci "Odpracovano" a lidem to nesedi. V srpnu 2026 melo absenci **50 z 60 lidi** se zaznamy, 25 z nich 40 h a vic. |
| **radek s cislem z ERP prehledu** (`fpd`, `fpd_chybi`) | Podminka Peti - obe cisla musi byt ze stejneho mista, aby se karta s Petinym prehledem nemohla rozejit. V karte je u nej veta "Tohle cislo o tobe vidi i HR a vedeni." |
| **veta o volne vs. pevne pracovni dobe** | Podminka Kristyny - kancelari se odecitaji hodiny nad denni fond, dilne ne, a dva lide vedle sebe se stejnou dochazkou by jinak nechapali, proc maji jine cislo. Ukazuje se **jen u kategorie s `dopichavat_fond`** (podminka Marti-AI, jinak by to matlo dilnu). |
| **vyrazne "k dnesnimu dni"** | Podminka Kristyny - v prubehu mesice je skoro kazdy v minusu. |
| **"Neni to o penezich"** | Podminka Kristyny - minus neni srazka, plus neni narok na proplaceni. |
| **"Cisla se jeste meni"** | Podminka Kristyny - dovolena, nemocenska a opravy se doplnuji zpetne. |
| **tlacitko "Nesedi ti hodiny, napis nam"** | Podminka Kristyny - at dotazy nespadnou na mistry. |
| **planovana nepritomnost OSVC zvlast** (`nepritomnost_osvc`) | Podminka Peti - ta se do fondu nepocita, takze bez teto vety vypada clovek jen jako dluznik. |

## Kdo kartu s porovnanim NEVIDI

Rozhodl Jirka podle Kristyny (puvodne rekl "vsichni", pak zmenil). Misto cisel dostanou vetu proc.
Vraci se `has=false` a pole `rezim` a `duvod`.

- **dohody (DPP)** - nemaji fond, proti kteremu porovnavat,
- **externi OSVC** - osobni cislo nad 9000,
- **"Bez dochazky"** - podminka v karte zamestnance,
- **materska**,
- **bez uvazku ve smlouve**.

⚠ **Filtry kontrolniho prehledu se na osobni kartu nekopiruji jako celek** - prehled odpovida
na otazku "koho mam hlidat", karta na otazku "kolik jsem odpracoval ja". Kdyby se vzaly 1 ku 1,
melo by prazdnou kartu 24 ze 78 aktivnich lidi.

## Dve pasti, na ktere se prislo az pri overovani

1. **Karta zamestnance v ERP cte TUTEZ adresu** (`apps/api/static/karta_zamestnance.html`,
   dlazdice s hodinami + souhrn v Dochazce) a **pta se BEZ urceni mesice**. Prvni den v mesici
   proto dostavala "Mesic prave zacal" a dlazdice zmizela uplne.
   Reseni - kdyz volajici mesic NEURCI a v aktualnim mesici jeste neubehl zadny cely den,
   vrati se **minuly mesic** s priznakem `nahradni_mesic`. Mobil se to nedotkne, ten mesic
   urcuje vzdy sam a dostane vysvetlujici vetu "Mesic prave zacal".
2. **"Dnesek" se bere z DATABAZE** (`SELECT current_date`), ne z hodin aplikacniho serveru.
   Upozornila Marti-AI - kdyby server bezel v UTC a clovek byl v Praze, po pulnoci by se hranice
   "neubehl zadny cely den" rozesla o den. Zaroven je to tentyz zdroj casu jako v ERP prehledu.

Pri te prilezitosti se v karte zamestnance doplnil **radek "Dovolena a nemoc" a "Dohromady
se pocita"** - bez nich cisla na obrazovce nedavala dohromady (u Maresove svitilo odpracovano
72,69 h proti fondu 168 h a k tomu "prescas 8,69 h").

## Jak to bylo overeno (1. 9. 2026)

- vypocet spusten pres `@@PYRUN` na osmi lidech vcetne hranicnich pripadu (materska, dohoda,
  "Bez dochazky", OSVC s planovanou nepritomnosti, uzavreny i rozdelany mesic),
- `fpd` porovnano s Petinym prehledem - sedi,
- adresa vyzkousena naostro v prohlizeci pro tri lidi a tri kombinace parametru,
- karta v mobilu proklikana na zive `/mobile` vcetne prepinani mesicu,
- karta zamestnance v ERP otevrena na Maresove, obe mista zkontrolovana, zadna chyba v prohlizeci,
- otisky (md5) zdroje porovnany proti lokalne spoctenym - sedi na znak.

## Co zustalo otevrene

- **Hodiny nad denni fond u kategorie "Volna kancelarska doba (bez prescasu)"** (25 lidi,
  za srpen 2026 celkem 361,8 h u 23 z nich) se do fondu nezapocitavaji. Podle Peti konto hodin
  (`tenant.att_konto_settlement`) **nikdy nezacalo bezet** - vsech 7 zaznamu vzniklo najednou
  12. 6. 2026 jako jednorazovy prevod zustatku ze stare Centraly. Kam ty hodiny jdou, je otazka
  na Sarku Novotnou, ne na dochazku. Marti-AI to vede jako otevreny bod.
- Peta navrhla zvazit, jestli ma kartu videt **interni OSVC** - u nich je slovo "manko"
  zavadejici, zadny fond dluzny nemaji. Zatim ji vidi.

