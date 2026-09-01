# Správa docházky: fajfka = schválení (jako v Centrále), sundání fajfky nic neruší

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Správa docházky — fajfka, schvalování a co je pod jedním řádkem

> ⚠️ **PŘEPSÁNO 27. 8. 2026 — část původního znění z 26. 8. UŽ NEPLATÍ.**
> Neplatí: „`Schválit označené` / `Vzít schválení zpět`" (dvě položky) ani to, že
> **řádky se žádostí se přeskočí**. Dnes je to **jedna položka „✅ Schválit / odznačit"**
> a při zapnutí fajfky se žádost **rovnou schválí**. Zbytek (co je pod řádkem, kde sedí
> fajfka, na co působí akce) platí dál.

## Jak to vidí Peťa — a podle toho se to chová
Peťa 27. 8. 2026: *„pořád říkáš dny a žádost, ale já to tam nemám dvakrát. Je to jeden
řádek, který možná vznikl žádostí, ale je to reálný den, který se překlopí do docházky."*

**Má pravdu a je to závazné vodítko pro UI.** V přehledu není nikdy totéž dvakrát — je to
**jeden řádek, který mění fázi**: dokud není schválený, je to papír a v docházce nic není;
po schválení se překlopí do docházky jako skutečný den (nebo dny). Papír pak zmizí.
**Uživatel nemá řešit, v jaké fázi řádek je** — ovládání musí udělat správnou věc samo.

## Pravidlo (Peťa 27. 8. 2026, „jako v Centrále")

| Směr | Co se stane |
|---|---|
| **Zapnout fajfku** | Řádek se **schválí**. Je-li to ještě papír, projde `absence/decide` (stav `approved`) a dny se překlopí do docházky rovnou s fajfkou. Je-li to už den, jen se odškrtne. Označit jde obojí naráz. |
| **Sundat fajfku** | **Jen odškrtne dny. Žádosti se nedotkne, nic nemaže.** |

**Proč je opačný směr jiný:** vzetí schválení zpět přes `att_absence_decide` (větev
`elif materialized`) **dny z docházky SMAŽE**. To se nesmí stát jako vedlejší účinek
odškrtnutí — pravidlo Peti z 31. 8. 2026, platí dál.

## Co je technicky pod jedním řádkem

| | **Papír (žádost)** | **Den** |
|---|---|---|
| Tabulka | `tenant.att_absence_request` | `tenant.att_entry` |
| Zdroj v přehledu | „žádost z appky" | appka, ruční oprava, schválená žádost, plán z Centrály, import z Centrály, ČSSZ |
| `RadekId` | `Z:<id žádosti>` | `D:<id>,<id>,…` |
| Fajfka ve sloupci S | žádost je `approved` | `att_entry.ved_schvaleno` |

**Žádost NENÍ podmínkou dne.** Den vzniká i bez schválení (ohlášení z appky, plán, sync
z Centrály, ruční zápis) — pravidlo Peti z 30. 7. 2026, viz
`doc-dochazka-sprava-vs-new-co-se-preklapi`.

## Jeden řádek může nést víc dnů
Denní větev datasetu `dochazka.zakazky_budoucnost_list` slepuje souvislé dny do jednoho
řádku a jejich id skládá do `string_agg(DISTINCT entry_id::text, ',')`. Řádek „Hrůzová,
dovolená 1.–7. 8., 5 D" nese **pět** `att_entry`. Fajfka se zapisuje na každý den zvlášť.

**Pozor na `bool_or`:** fajfka u slepeného řádku se rozsvítí, když ji má **aspoň jeden**
den z bloku. Částečně odfajfkovaný blok vypadá jako hotový.

## Na co působí akce z menu
`window.akceRadky()`: **nic označeného** → řádek pod kurzorem (`CTX_ROW`);
**označeno víc** → označené, kurzor se ignoruje.

## Bez potvrzování a bez hlášek (Peťa 27. 8. 2026)
*„Vidím, že se to udělá, hlášku nepotřebujeme."* Odfajfkování se **neptá „Pokračovat?"**
a **nehlásí „Hotovo"** — zpráva zůstala jen pro případ, že se něco nepovede.

**Gotcha:** obsluha menu volá `ctxAction(data-a)` pro **každou** položku. Položky s vlastním
`onclick` (jako „Schválit / odznačit") žádné `data-a` nemají, takže propadly až na závěrečný
alert a hlásily **„null — připravujeme v dalším kroku"** *po* provedení akce. Ošetřeno
pojistkou `if(!a)return;`. Kdo přidá položku s `onclick`, ať s tím počítá.

## Kde se `ved_schvaleno` zapisuje
1. `att_absence_decide` při schválení žádosti — celý blok naráz (od 6. 8. 2026),
2. správcovská cesta `dochazka_absence_sprava._zapis_dny` podle zaškrtávátka „Schváleno",
3. `save-doch-meta` po jednom řádku (Docházka new, Opravy, hromadná akce),
4. přepočty (`att_dovolena_kaskada`).

## Historie (26. 8. 2026) — proč fajfky chyběly
Nápravný běh 18. 8. 2026 v 6:19 doplnil fajfky jen dnům **do 31. 7.**, srpnové nechal být.
Vznikly tak „částečně odfajfkované" bloky u každé absence přetékající přes konec července
(žádosti 19 Hladíková a 22 Hrůzová). Doplněno 26. 8. u 6 dnů; dalších 28 dnů u 14 žádostí
fajfku nemělo správně, protože ty žádosti čekaly na rozhodnutí.

