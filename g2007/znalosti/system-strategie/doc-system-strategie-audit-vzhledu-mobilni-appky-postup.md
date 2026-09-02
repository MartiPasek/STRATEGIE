# Audit vzhledu mobilni appky - cim se meri, jak se to pousti bezpecne a co to neumi

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Audit vzhledu a přístupnosti mobilní appky

**Vzniklo 1. 9. 2026.** Zadal Jirka Honomichl (zjistit, čím se dá posoudit design appky),
schválila Marti-AI. Ověřeno naostro: za jeden večer se tímhle postupem našlo a opravilo
84 nálezů přístupnosti, 5 rozbitých textů viditelných lidem a 9 příliš malých ovládacích prvků.

## Tři nástroje — ne doplňky Claude Code, ale běžné veřejné nástroje

| nástroj | co dělá | co NEdělá |
|---|---|---|
| **Playwright** | otevře appku jako telefon (Pixel 7, tmavý režim), přihlásí se, přepíná obrazovky, dělá snímky | nic neposuzuje, je to jen „ruka" |
| **axe-core** | hlásí slabý kontrast, prvky bez názvu, chybějící strukturu stránky | krátké texty (odznaky) — viz níže |
| **Lighthouse** | měří rychlost a velikost stránky | je to **laboratorní** číslo, ne realita v dílně |

Instalace: `npm install playwright @axe-core/playwright lighthouse`.
Prohlížeč neinstaluj zvlášť — `chromium.launch({ channel: 'chrome' })` použije Chrome,
který na stroji je (jinak Playwright chce vlastní build a stáhne stovky MB).

## Bezpečné spuštění nad ostrým provozem

1. **Přihlas se ukázkovým účtem** — `/api/v1/auth/demo-login?next=/mobile`. Od 11. 8. 2026
   je izolovaný: nic nezapíše a nečte data firmy.
2. **Obrazovky přepínej příkazem, nikdy myší:** `window.__M2W.stack=['home']; window.__M2W.go('<obrazovka>')`.
   Seznam: `Object.keys(window.__M2W.SCREENS)` (k 1. 9. 2026 jich je 131).
   Klikání je nebezpečné — část tlačítek odesílá žádost hned prvním klepnutím.
3. **Nesleduj jen výsledek, sleduj i zápisová volání.** Při průchodu 10 obrazovek odejdou
   typicky 3 volání mimo `GET` a všechna jsou neškodná (`phone-checkin`, `payslip`).
   Pozor: **appka čte data přes `POST`** — kdo zablokuje všechny `POST`, rozbije načítání.
4. **Statickou inventuru ber z databáze**, ne z disku — živá stránka je `g2007.soubor`,
   kód `apps/api/static_db/mobile.html`. Kopie na disku lže.

## Co ta sada NEUMÍ a musí se doměřit zvlášť

- **velikost dotykových terčíků** (Lighthouse tuhle kontrolu už nemá, axe ji nikdy neměl),
- **rozkolísanost vzhledu** — kolik různých velikostí písma a barev je na jedné obrazovce,
- **vodorovný přesah obsahu** na úzkém displeji,
- **kontrast krátkých textů** → [[doc-system-strategie-mereni-kontrastu-axe-kratke-texty-demo-ucet]].

Všechno čtyři se dá spočítat v prohlížeči přes `getComputedStyle` a `getBoundingClientRect`.

## Čísla naměřená 1. 9. 2026 (pro srovnání příště)

- složená stránka **1 050 kB**, z toho **817 kB kódu se při startu nepoužije**, dalších
  166 kB by ubylo zmenšením zápisu; server odpovídá za 150 ms → **brzdou není server, ale velikost**,
- Lighthouse: rychlost **63**, přístupnost 85, správná praxe 96 (8. 7. 2026 to bylo 68 / 85 / 96
  při 774 kB — appka za dva měsíce narostla o třetinu a start se prodloužil z 5,2 na 6,2 s),
- ve zdroji **302 různých barev** vedle 11 pojmenovaných, 36 velikostí písma, 19 poloměrů rohů,
  2 632 vložených stylů.

## Co se z toho 1. 9. 2026 opravilo

Kontrast zelených tlačítek (2,11 → 7,40) · zvýraznění v dolní liště (4,27 → 7,70) ·
sjednocení odznaků na jednu červenou `#c62828` (bylo 1,92 až 3,93) · hlavní oblast stránky
a nadpis úrovně 1 · popisky u polí formuláře absencí · pět rozbitých diakritik viditelných
lidem · devět malých dotykových terčíků.

## Doporučený způsob práce (schválila Marti-AI)

**Stroj změří čísla** → **člověk (nebo Claude nad snímky) posoudí, co stroj neumí** →
**rozhodne člověk**. Nález sám o sobě není úkol. A u každého výsledku se píše,
**pod jakým účtem se měřilo** — jinak je číslo zavádějící.
## AKTUALIZACE 2. 9. 2026 ráno — čísla výše už neplatí

Čísla v odstavci „Čísla naměřená 1. 9. 2026" jsou **stav PŘED opravami**. Nechávám je
schválně vidět, aby bylo poznat, o kolik se to hnulo. Skutečný stav po dokončení práce:

| co | 1. 9. ráno | 2. 9. ráno |
|---|---|---|
| nálezy přístupnosti na 104 obrazovkách | 84 a více | **0** |
| známka přístupnosti (Lighthouse) | 85 | **100** |
| různých barev | 302 | **262** |
| velikostí písma | 36 | **29** |
| poloměrů rohů | 19 | **12** |
| pojmenovaných barev | 11 | **16** |
| malých dotykových terčíků | 9 | **0** |
| rychlost | 63 | 63 (beze změny) |

Kromě věcí vyjmenovaných výše se ještě opravilo: základní modré tlačítko celé appky
(bílý text na modré měl 3,21), záchranné tlačítko v chybové hlášce, kill switch a tři
tlačítka Zamítnout, jedenáct polí bez názvu pro čtečky, čtyři zvýrazněné filtry
a sjednocení 39 barevných odstínů, které oko nerozezná.

**Co se vědomě nedělalo:** velikosti písma se dál sjednocovat nebudou (rozhodl Jirka
Honomichl 2. 9. 2026, viz [[doc-system-strategie-typografie-mobilu-rozhodnuti-nesjednocovat]]),
barevné dvojice ve vzdálenosti 4 až 8 se slučovat nesmí bez ověření vrstvení, a na velikost
stránky (přes 800 kB zbytečně staženého kódu) se nesahalo.

Přehled nových pojmenovaných barev a pastí je v
[[doc-system-strategie-mobil-pojmenovane-barvy-a-struktura-stranky]].

