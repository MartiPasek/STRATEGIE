# Sick day na budoucí den — v mobilu odblokováno, server kontrolu data nemá záměrně (25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Sick day na budoucí den (25. 8. 2026)

Zadal **Jirka Honomichl**, ověřil a provedl Claude-28, schválila **Marti-AI** (msg 13667 = změna, msg 13670 = způsob zápisu).

## Co se změnilo

V mobilu měl sick day **dvě cesty zadávání a chovaly se různě**:

| cesta | před 25. 8. | dnes |
|---|---|---|
| „Je mi blbě… sick day" → jednodenní / po hodinách | budoucí den **nešel** — vstup data měl natvrdo `max` na dnešek | **jde** |
| „…nebo sick day na víc dnů po sobě" → od–do (`dateRangePickIn`) | budoucí den šel (žádné omezení) | beze změny |

Změna je v `g2007.soubor`, dílek `apps/api/static/mobile_parts/60_dochazka.js`:
odstraněn atribut `max="'+_locDate(0)+'"` u vstupu `_sdDen` a popisek zkrácen
z „Který den (jde i zpětně):" na „Který den:" (kratší formulaci doporučila Marti-AI —
systém tím nic nezužuje). Publikováno do `apps/api/static_db/mobile.html`.

**Doloženo:** dílek 229 626 → 229 589 znaků, složená stránka 1 021 114 → 1 021 077,
tedy obojí kratší **přesně o 37 znaků** = součet obou náhrad. Nic jiného nezmizelo.
Otisk dílku před změnou `6f7c5562c0262216a8f69b751bfa0cbc`, po změně `1cedf9ad97d9190b6e0fdb88af2236de`.
Na živé `/mobile` ověřeno: nový popisek 1×, starý 0×, stránka naběhne bez chyby.

## ⚠️ Zbylé omezení data patří Opravám docházky — nesahat

V dílku zůstal **jeden** výskyt `max="'+_locDate(0)+'"` a **je správně** — patří vstupu
v Opravách docházky (`_opravaDenPovolen`, spolu s `min` na začátek opravitelného měsíce).
Kdo bude příště hledat „to omezení data", ať si ověří, že míří na sick day, ne na Opravy.

## Server kontrolu budoucího data NEMÁ — a je to záměr

Ověřeno v živém kódu 25. 8. 2026: **`att_absence` (v16) ani `att_absence_request` (v10)
nemají žádnou kontrolu na budoucí datum.** Obě `CURRENT_DATE` v nich se týkají
platnosti schvalovatele (`att_odpovednost.platnost_do`), ne dne absence.

**Není to mezera čekající na opravu** — je to vědomý stav (formulace Marti-AI: *„aby příští
vývojář věděl, že absence kontroly je vědomý stav"*). Budoucí absence je běžná: v žádostech
je 21 budoucích dovolených až do 30. 12. 2026, v docházce 165.

Hlídání stropu u sick day funguje dál (`att_limit_kontrola` v3, hláška „Sick day ti letos nezbývá").

## Že to prošlo i předtím

V `tenant.att_entry` byly už 25. 8. **tři budoucí sick days**, nejzazší **4. 9. 2026** —
Luboš Trunec, založeno 12. 8. přes `mobile_app`, později upravil Dušan Havlát přes Správu docházky.
**Neověřeno:** jestli to prošlo cestou od–do, nebo než se `max` do dílku dostal.

## Past při měření, na kterou jsem naletěl

Počty výskytů přes `(length - length(replace(...)))/N` **stojí a padají se správným `N`**.
U vzoru `max="'+_locDate(0)+'"` (délka **21**) jsem omylem dělil 22 → vyšlo **0** a chvíli to
vypadalo, že jsem smazal i omezení v Opravách. Celočíselné dělení chybu tiše spolkne.
**Délku vzoru si vždy nech spočítat databází** (`length('…')`), nepočítej ji v hlavě.

Souvisí: [[doc-dochazka-hlidani-stropu-dovolene-a-sick-day]] · [[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]]

