# Správa docházky schovávala řádky — datum ze žádosti rozbilo odstraňovač duplicit (12. 8. – 4. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Správa docházky schovávala řádky

> oblast: `dochazka` · našla Peťa 3. 9. 2026, dohledal a opravil Claude-26 4. 9. 2026

## Příznak
Peťa 3. 9. 2026: *„máme tam tři dny a v sumaci je 1 D."* Řádek Elišky Kolářové
3.–5. 8. 2026 ukazoval **„1 D"**, přestože jsou to tři dny (24 h). A hůř —
**dva z těch tří dnů se v přehledu vůbec nezobrazovaly.**

Celkem se skrývalo **24 řádků u 9 aktivních lidí** (Kolářová, Honomichlová, Lišková,
Trunec, Hladíková, Šafránková Michelle, Zeman, Novotná, Diviš). Nejvíc Zeman (5)
a Lišková (3).

## Příčina — dvě věci, které se sešly

Datová sada **`fw.data_set` id 178 (`dochazka.zakazky_budoucnost_list`)**.

1. **Odstraňovač duplicit** (existoval už před 30. 7. 2026) zahazuje řádky se stejným
   `employee_id, typ_code, odd, dokon`. Měl smysl — táž absence chodí do přehledu
   dvakrát, jednou jako denní záznamy a jednou jako žádost.
2. **12. 8. 2026 (zadala Peťa)** se změnilo, odkud se berou datumy: nově **ze ŽÁDOSTI**,
   ne z vlastních dnů řádku. Důvod byl správný — nemoc 1.–10. 8. začíná v sobotu,
   ale denní záznamy jsou až od pondělí, a v přehledu musí být vidět 1. 8.

**Od té chvíle měly VŠECHNY řádky jedné žádosti stejné `odd`/`dokon`** — a odstraňovač
duplicit je začal považovat za jeden a týž řádek. Ze tří skupin nechal jednu, dvě zahodil.
Zároveň zůstal počet dnů té jedné skupiny → odtud „3.–5. 8. = 1 D".

Ověřeno v zálohách: verze z **30. 7. 2026** má `min(d) odd, max(d) dokon` (datum
z vlastních dnů) a odstraňovač duplicit tehdy kolidovat nemohl. Verze z **25. 8. 2026**
už má obojí. **Vada tedy žila 12. 8. – 4. 9. 2026**, ale projevovala se zpětně na celé
historii, protože přehled se počítá živě.

## Co to NEovlivnilo
**Nic než pohled.** Nárok a čerpání se počítá přímo z `tenant.att_entry`
(`att_narok_cerpani`), ne z tohoto přehledu — nikomu se nespočítalo míň dnů dovolené
a do mezd to nešlo. Data byla celou dobu v pořádku.

## Oprava (4. 9. 2026, Peťa + Claude-26)
1. **Datum ze žádosti se drží jen tehdy, když z ní vyšel JEDEN řádek.** Jakmile se
   rozpadne na víc, ukazuje každý řádek svoje dny. Nemoc od soboty tím zůstala zachovaná.
2. **`ec_druh` se nese až do odstraňovače duplicit** a je součástí jeho klíče — dva
   půldenní řádky téhož dne (4 h řádná + 4 h navíc) se tak nepovažují za duplicitu.
3. **Popisek zůstává „Dovolená"** i u dnů dopočtených jako navíc. Peťa 4. 9.:
   *„ve Správě to nemůže být jako dovolená navíc"* — ve Správě se žádá dovolená
   a rozdělení na 20/30 je až dopočet kaskády pro Docházku new.

Ověřeno před nasazením: 716 → **731 řádků**, slepených 227 → 234 (nic se nerozdrobilo),
označení „navíc" 0 → **0**. Kontrola „je každý absenční záznam v přehledu vidět" projde
u všech aktivních lidí; zbyly tři záznamy bývalých zaměstnanců v zamčených měsících
(Mudra, Kliková, Hrdinka) — dva identické půldny téhož dne a druhu, Peťa 4. 9.
rozhodla nechat být. Záloha původní verze: `zaloha_data_set_178_2026-09-04.sql`.

## Poučení
**Když se mění, odkud se bere hodnota, je potřeba projít i všechna místa, která tu
hodnotu používají jako KLÍČ.** Tady se změnil zdroj datumů kvůli zobrazení a tichem
tím přestal fungovat odstraňovač duplicit, který na těch datumech stál. Nic nespadlo,
nic nehlásilo chybu — jen se přestaly zobrazovat řádky. Našlo se to náhodou, po třech
týdnech, a jen proto, že si Peťa všimla „1 D" u tří dnů.

## Souvisí
[[doc-dochazka-dovolena-radna-vs-navic-rozpad]] · [[doc-dochazka-absence-bez-casu-krome-lekare]]

