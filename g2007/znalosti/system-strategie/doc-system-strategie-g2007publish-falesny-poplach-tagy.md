# @@G2007PUBLISH: falesny poplach na poctech tagu (dochazka-po-zakazkach) a kdy pouzit @@G2007EXPORT

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# @@G2007PUBLISH: falesny poplach "nesedi pocty tagu" a nahradni cesta

**Zjisteno 6. 8. 2026 (C28/Jirka, souhlas Marti-AI msg 12368).**

## Priznak

`@@G2007PUBLISH apps/api/static_db/dochazka-po-zakazkach.html` skonci:

```
STOP: nesedi pocty tagu - <div(157) vs </div>(158) - publikace zrusena, nic se nezmenilo
```

Publikace se **neprovede vubec** — disk zustane na stare verzi. To je bezpecne, ale
zmena z `g2007.soubor` se nedostane do provozu a na prvni pohled to vypada, ze je chyba
v tom, co jsi prave napsal.

## Pricina (overeno, ne domnenka)

Neni to vadou tveho fragmentu. Kontrola v `@@G2007PUBLISH` pocita `<div` a `</div>`
**staticky nad celym souborem vcetne JS retezcu**. Tato stranka ale sklada HTML
**dynamicky v cyklu** — na konci iterace pridava `html+='</div>';`, zatimco odpovidajici
`<div` vznika v jine vetvi. Staticke parovani na to principialne nemuze sedet.

Rozpad overeny na zive verzi (117 212 znaku, jeste bez nove zmeny):
- HTML cast souboru: **5 : 5** (vyvazena)
- JS cast: **152 : 153** (jeden zaporny bod)
- vlozeny fragment schvalovani: **8 : 8** (vyvazeny)

Stranka vznikla **migraci**, ne pres PUBLISH; na disk se bezne dostava **boot
materializaci** v `apps/api/main.py` (lifespan). Proto se nerovnovaha nikdy neprojevila.

## Co delat

**Pouzij `@@G2007EXPORT <kod>`** — dokumentovany nizkourovnovy nastroj "propis aktualni
DB obsah na disk", bez kontrol. Komentar v `router.py` ho primo urcuje pro rucni zasah
vedle PUBLISH.

```
@@G2007EXPORT apps/api/static_db/dochazka-po-zakazkach.html
```

**Povinne k tomu:** prijdes o self-test (PUBLISH si sam overuje, ze stranka nabehne),
takze **hned po exportu rucne over v prohlizeci**, ze se stranka nacte a funguje.
Zachrannou sit mas v `g2007.soubor_historie` (predchozi obsah).

## Co NEDELAT

- **Nerestartovat API** kvuli nasazeni stranky — shodi vsechny bezici ulohy a dlouhe
  joby Marti-AI. Boot materializace by to sice propsala, ale cena je neumerna.
- **Neupravovat cizi JS jen proto, aby kontrola prosla.** Slo by o kosmetiku bez vecneho
  duvodu; pravidlo "pri migraci se logika nemeni" plati i tady.

Pokud nekdo tu nerovnovahu nekdy narovna (samostatny vedomy task), PUBLISH pak pujde
normalne a tento zaznam lze zuzit.

## Souvisejici

- `doc-dochazka-schvalovani-absenci-erp-hlaska-a-poznamka` (zmena, pri ktere se to naslo)
- Past pri zapisu pres most: SQLAlchemy bere `:slovo` uvnitr retezce jako parametr
  ("A value is required for bind parameter"). Pise se `\:` — over si to jednou
  `SELECT 'display\:flex';`, vraci ciste `display:flex`. Tyka se hlavne CSS a JS
  vkladaneho pres `replace()`.

