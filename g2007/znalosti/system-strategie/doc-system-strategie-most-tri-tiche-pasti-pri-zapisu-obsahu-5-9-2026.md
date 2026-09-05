# Most: tři tiché pasti při zápisu (UPDATE hlásí úspěch i když nic nenašel, emoji přes příkazovou řádku, ztracený zápis v rychlé dávce)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Tři tiché pasti mostu při zápisu do `g2007.soubor`

**Zjištěno naostro 5. 9. 2026 (Claude-28) při přejmenování obrazovky Docházky.**
Všechny tři mají společné to, že **most ohlásí úspěch a člověk si myslí, že je hotovo.**

## 1) ⭐ `UPDATE … replace()` hlásí „1 řádek" i když nic nenahradil

`UPDATE g2007.soubor SET obsah = replace(obsah, <kotva>, <nový text>) WHERE kod=… AND md5(obsah)=…`

Když **kotva v souboru není**, `replace()` vrátí text beze změny, `UPDATE` řádek přesto
„aktualizuje" a most hlásí **`OK · 1 řádků · G2007 KONSTRUKTIVNI`**. Otisk zůstane stejný.

**Návratovka tedy NEDOKAZUJE, že se text vyměnil — dokazuje jen, že seděl otisk.**

**Jak to dělat:** po každém zápisu spočítej v databázi výskyty **staré i nové** podoby.
Staré musí být 0, nové ≥ 1. Pozor na případ, kdy nový text starý obsahuje (pak stará
kotva zůstane 1 správně) — počítej tedy obojí a vyhodnoť to vědomě.

## 2) ⭐ Emoji se rozbije, když SQL píšeš přes příkazovou řádku

Dotaz zapsaný přes `cat > CLAUDE_SQL.sql <<'SQL'` v Bashi **poškodí čtyřbajtové emoji**
(🤝 🏢 🕒 📱 …). Trojbajtové znaky (⭐ → ✓) i česká diakritika projdou.

Projeví se to tak, že **kotva „nikde není"**, přestože ji na živé stránce vidíš.
5. 9. takhle tiše selhaly 3 ze 6 kontrol naráz — a vypadalo to jako chyba v datech.

**Jak to dělat:** obsah s emoji posílej **vždy přes base64**
(`convert_from(decode('…','base64'),'UTF8')`), nebo SQL zapiš editačním nástrojem, ne
příkazovou řádkou. Platí i pro `@@G2007ADD` s emoji v textu.

⚠️ V Pythonu nestačí psát `📅` — to jsou náhradní páry a `encode('utf-8')` na nich
spadne (`surrogates not allowed`). Buď piš `\U0001F4C5`, nebo oprav přes
`s.encode('utf-16','surrogatepass').decode('utf-16')`.

## 3) Rychlá dávka zápisů za sebou — jeden se ztratí

Sedm zápisů poslaných ve smyčce s pevným `sleep 10` mezi nimi: **šest prošlo, jeden ne.**
Most hlásil u všech úspěch, protože se četla **stará** návratovka — nový dotaz přepsal
`CLAUDE_SQL.sql` dřív, než hlídač stihl přečíst ten předchozí.

**Jak to dělat:** před spuštěním si zapamatuj **čas** souboru s výsledkem a po `sleep`
ověř, že se **změnil**. Když ne, výsledek je cizí nebo starý a nic nedokazuje.
Totéž platí pro všechny společné kanály (nasazení, srovnání s gitem, notifikace) —
ty linky nemají vůbec.

## Souvisí

- `doc-system-strategie-editace-fragmentu-mobilu-pres-most-bez-primeho-zapisu` — kolo base64
- `doc-system-strategie-mobil-publish-vypousti-i-cizi-zmeny-a-api-ma-metodu`

