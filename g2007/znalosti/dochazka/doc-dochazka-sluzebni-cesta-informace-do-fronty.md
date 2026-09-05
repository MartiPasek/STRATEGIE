# Služební cesta (činnost 9) posílá informaci do fronty „K vyřešení" — a co služební cesta NENÍ (Peťa 4. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Zadala Peťa 4. 9. 2026:** *„měl by mi chodit k vyřešení informace, když si někdo zadá činnost 9 služební cestu."*

## Co to dělá

Když je k uzavřenému píchnutí rozpad s **činností 9 (Služební cesta / montáž)**, založí se
do fronty „K vyřešení" položka `sluzebni_cesta` s textem ve tvaru
`27.05. služební cesta (činnost 9) 10.62 h — jen informace, vezmi na vědomí`.

**Není to nález o chybě.** Je to upozornění, že se k tomu dni budou řešit cestovní náhrady.
Proto má vlastní titulek zprávy **„🚗 Služební cesta"**, ne „⚠ Docházka — nesrovnalost".

**Člověku, který na cestě byl, zpráva nechodí** — on o své cestě ví. Jde jen editorům oprav
podle působnosti (kancelář/výroba), stejně jako ostatní položky fronty.

**Úklid:** když se činnost přepíše na jinou, informace se sama uzavře (`resolved_at`).

## ⛔ Číslo činnosti, ne interní id

Pravidlo se páruje na **`tenant.vyroba_cinnost.ec_cislo = 9`**, protože autoritativní je
číselník Centrály a Peťa pracuje s číslem činnosti (viz
`doc-dochazka-cinnosti-ciselnik-centrala-vs-strategie`).

**Past, do které jsem 4. 9. 2026 málem spadl:** interní `id` té činnosti je **16**.
Pod `id = 9` sedí u nás **Značení vodičů** (činnost 40) — běžná dílenská práce, 40 úseků
za samotný srpen. A v Centrále pod `ID = 9` sedí dokonce **Nemoc**. Kdo se sparuje na `id`,
zaplaví frontu nebo hlídá úplně jinou věc.

## Kde to je

`att_anomaly_scan` v `g2007.python`, **verze 27** (hot-swap, bez deploye). Tři místa:

1. **nové pravidlo** v hlavním `UNION ALL` (vedle `chybi_zakazka`, `chybi_cinnost`, `chybi_rozpad`),
   okno `GREATEST(current_date - 14, DATE '2026-08-01')` jako ostatní,
2. **úklid** nahoře mezi ostatními úklidy,
3. **výjimka z notifikace zaměstnanci** + vlastní titulek zprávy.

Záloha předchozí verze: `att_anomaly_scan__zaloha_20260904` (`inactive`, md5 `ff74ffb96df171e73054bce842b799d6`).

## Ověření (4. 9. 2026)

Logika vyzkoušena na skutečných datech z konce května (mimo okno pravidla, takže bez zápisu):
vrátila přesně 5 správných řádků — Zeman 27. 5., Porner a Valenta 28. a 29. 5.

⚠️ **Činnost 9 se naposledy použila 1. 6. 2026**, takže se nová informace ve frontě objeví až
tehdy, kdy si služební cestu někdo zase zadá. Není to porucha pravidla.

## Vedlejší nález, který zůstal otevřený

Rozpad z **1. 6. 2026** (dva úseky, Valenta a Porner, PR3984) odkazuje na docházkové záznamy
`att_entry` s id **16003 a 16004**, které v databázi **neexistují**. Osiřelý odkaz — pravidlo
se k takovým úsekům nedostane, protože vychází z docházkového záznamu. Nahlášeno Peti 4. 9. 2026,
neřešeno.

## ⛔ Co pod tohle pravidlo VĚDOMĚ nespadá (Peťa 4. 9. 2026)

Peťa dostala 4. 9. 2026 na výběr, jestli rozšířit záběr, a rozhodla: **„Nic, stačí činnost 9."**
Následující tři věci tedy informaci do fronty **neposílají** a **není to chyba k opravě**:

| Co | Objem | Proč ne |
|---|---|---|
| **Činnost 113** — Pracovní cesta – nákup / lakovna / ostatní | od června 34 úseků, v srpnu 5 u 4 lidí | jiná činnost, Peťa ji hlídat nechce |
| **Ohlášení z mobilu** „Na služební pochůzce do cca 15:01" | 15 případů od června | **NENÍ to služební cesta** — viz níž |
| **Činnost 14** — Služeb. cesta/montáž – čas na cestě | zatím nepoužita ani jednou | patří ke stejné věci, ale hlídat se nemá |

⚠️ **Činnost 9 se naposledy použila 1. 6. 2026.** Od té doby se z cestovních činností zapisuje
jen 113. Že fronta mlčí, tedy **neznamená, že pravidlo nefunguje** — znamená to, že si činnost 9
nikdo nezadal. Ověřeno 4. 9. 2026 spuštěním logiky na květnových datech: vrátila správných 5 řádků.

### ⚠️ Služební pochůzka NENÍ služební cesta (Peťa 4. 9. 2026)

Peťa doslova: *„pozor, služební pochůzka nebo něco podobného není služební cesta — to je jen
upozornění. Služební cesta je, když to někdo opravdu vybere jako činnost."*

| | Co to je | Kde se to bere |
|---|---|---|
| **Služební pochůzka** | jen **upozornění**, že člověk teď není v kanceláři | ohlášení v mobilu, poznámka „Na služební pochůzce do cca 15:01"; žádná činnost, žádný rozpad |
| **Služební cesta** | skutečná služební cesta | člověk si ji **vybere jako činnost 9** v rozpadu |

Nepleť si to a **neodvozuj služební cestu z poznámky ani z ohlášení** — jediné, co ji zakládá,
je vybraná činnost 9. Kdo by chtěl hlídat i pochůzky, hlídal by něco jiného, než Peťa zadala.

