# DPP placené za návštěvu (úklid): dopočet z docházky místo pevné ruční složky — 26. 8. 2026

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# DPP placené za návštěvu — dopočet z docházky

**Zadala Peťa, nasadil Claude‑26, 26. 8. 2026.** Ověřeno čtením po zápisu.

## Pravidlo

**1 000 Kč za každou návštěvu (den se záznamem v docházce), maximálně 4 000 Kč za měsíc.**
**Nezáleží na dni v týdnu** — Herejtová chodí ve čtvrtek, ale v lednu, dubnu i červenci 2026 přišla jednou ve středu.

Skript: `g2007.python` kód **`mzdy_dpp_navstevy_rows`**, seznam lidí v konstantě `_DPP_NAVSTEVY` (dnes jediný: **EC 525 Světlana Herejtová**, úklid, Helios složka 700). Volá se z `mzdy_generuj` hned za ručními složkami.

## Jak se pravidlo našlo

První dva pokusy **nesedly** — je to zapsané schválně, ať to nikdo nezkouší znovu:

- *„4 000 ÷ počet čtvrtků × kolikrát byla"* → leden vyšel 3 200, ale vyplatilo se 4 000.
- *„počítat týdny místo čtvrtků"* → březen a červen vyšly 3 200 (kalendářní týden přetéká přes konec měsíce).

Sedí až **1 000 za návštěvu se stropem 4 000**: souhlasí se všemi výplatnicemi 1–7/2026 (všude 4 000, i v měsících, kdy přišla 5×) i se staršími poznámkami z Centrály — *„3 000 – 3 týdny ze 4"* (8/2025), *„3 000"* (12/2025). Potvrdila Peťa.

## Co to nahradilo a proč

Ruční složka `tenant.mzdy_rucni_slozka` (EC / 525 / MS 700) dávala **4 000 napevno** bez ohledu na to, jestli člověk přišel. **26. 8. 2026 byla VYPNUTA** (`aktivni=false`, požadavek mostu #2497 schválila Peťa).

⚠️ **Vypnout ruční složku bylo nutné hned**, ne později: dokud běží obě cesty, částka by se od nahrání docházky **zdvojila** (4 000 + 4 000). Je to táž chyba, kterou Marti řešil 10. 7. 2026 — *„Herejtová 8000 místo 4000, jednatelé/Šenft 2×"_.

## ⚠️ Past, kvůli které vznikl hlídač

**Docházka z tabletu chodí v DÁVKÁCH SE ZPOŽDĚNÍM.** Červencové záznamy se nahrály 30. 7., červnové 31. 7. K 26. 8. neměla za srpen **ani jeden** záznam.

Když se měsíc nenahraje před generováním, dopočet vrátí **nulu** a člověk dostane 0 Kč místo 4 000 — **tiše**.

Proto pojistka **`dpp-za-navstevu-ma-dochazku`** (`tenant.pojistka`, aktivní od 26. 8. 2026): kontroluje, že každý člověk placený za návštěvu má za **minulý měsíc** aspoň jeden záznam docházky. Když svítí červeně → **ověř nahrání tabletu PŘED generováním mezd**.

## Když se přidává další člověk

**Seznam je na DVOU místech** a musí se doplnit na obou:

1. `_DPP_NAVSTEVY` ve skriptu `mzdy_dpp_navstevy_rows`
2. seznam čísel v kontrole pojistky `dpp-za-navstevu-ma-dochazku`

## Pojistka ve skriptu samotném

Skript **nikdy nevyhodí výjimku** — při chybě vrátí prázdný seznam. Je totiž připojený ke stejnému volání jako ruční složky, takže by výjimkou shodil i odměny jednatelů.

## Kdo zůstává na ruční složce

Šenft (EC 374, DPP 700, 9 000) — docházku nemá vůbec, částka je fixní, dopočet by u něj neměl z čeho počítat. Jednatelé (EC 2, ES 41, EC 47, složka 693) — jejich odměna v Podmínkách už je a míří správně na 693, ale ruční složka má přednost; přepnutí je připravené, jen se neudělalo.

Souvisí: [[doc-mzdy-zdroj-pravdy-podminky-misto-centraly]] · [[doc-mzdy-prevodnik-odmena-jednatele-693-vs-432]]

