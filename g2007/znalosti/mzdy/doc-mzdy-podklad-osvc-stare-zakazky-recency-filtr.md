# Podklad OSVČ tahá staré uzavřené zakázky — chybí filtr „od poslední fakturace"

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## ✅ NASAZENO 2.9.2026 (podklad_vyplaceni_pdf verze 10)
Minimální fix je v PRODUKCI: podklad přeskočí zakázky BEZ práce v posledních 12 měsících. Ověřeno na datech i v podkladu — Voříšek (327): staré VR8xxx (2018–2022) zmizely; Lev (371) a Kilberger (346): aktivní zakázky zůstaly, nic navíc (jejich malé/nulové zbytky jsou správně = po backfillu plně objednané). Implementace: recent_zak = množina zakázek z EC_Dochazka, kde CasZacatek >= DATEADD(MONTH,-12,GETDATE()); ve smyčce přeskoč zak, když recent_zak není None a zak není v hod_map (nedávné PG hodiny) ani v recent_zak. Fallback: při chybě dotazu recent_zak=None → NEfiltruje (bezpečné). Okno 12 měsíců je laditelné. Nasazeno chirurgicky přes base64 replace() na g2007.python.
## ⚠ SLEPÁ ULICE (nedělat)
Filtr „hodiny PO poslední objednávce" NEFUNGUJE — objednávka bývá datumově až po poslední práci i u AKTIVNÍ zakázky (Voříšek VR10670: práce 23.6., objednávka 1.7., reálný zbytek 23 698 Kč) → chybně by vyhodil aktivní. Rozlišuje se STÁŘÍ poslední práce (okno), ne vztah práce↔objednávka.
## Nález (ověřeno 2.9.2026)
Podklad fakturace OSVČ ukazoval i zakázky, na kterých člověk roky nedělal. Voříšek (327): VR8885 naposledy 15.12.2021, VR8922 22.8.2022, VR8120 2018 — 0 hodin v 2026, přesto v podkladu 9/2026 s hodinami a částkou (VR8885 = 12 524 Kč). Týkalo se kohokoli se starými zakázkami.
## Root cause
Zakázkové hodiny (i pro staré zakázky, které v PG vyroba_work nejsou) vstupují přes fin_map/EC_Dochazka, vzorec = Σ(všechny hodiny)×sazba − už_objednáno(PlatbyZam), BEZ filtru na nedávnost. U staré zakázky je už_objednáno menší než hodnota všech historických hodin → zbyde kladný „zbytek", i když je zakázka roky uzavřená.
## Pozor (obecné, platí dál)
NEpřepínat zdroj „už objednáno" z PlatbyZam na doklady — PlatbyZam schválně odděluje reálné pracovní objednávky od předgenerovaných/nepracovních (Voříškova objednávka EOS960056 do PlatbyZam nepatří, doklady obsahují oboje). Reálné pracovní objednávky mimo generování se doplňují do PlatbyZam (viz backfill_platbyzam_OSVC_18-8.sql). Detail i v repo NALEZ_podklad_stare_zakazky.md.
## Zbývá (větší rework, nehořelo)
U dlouhoběžících zakázek, co zůstanou, se stále počítá „všechny hodiny − už_objednáno". Pravé „od poslední fakturace" = jen hodiny odpracované od poslední objednávky × sazba. Do budoucího přepisu.

