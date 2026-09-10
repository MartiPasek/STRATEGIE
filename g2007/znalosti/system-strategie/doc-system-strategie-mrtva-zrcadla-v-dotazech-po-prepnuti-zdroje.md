# Prepnuti modulu na nase tabulky neprepne DOTAZY - zustanou viset na zrcadlech s jednim radkem

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Kdyz se modul prepne na nase tabulky, dotazy se neprepnou samy

**Nasla C24 (Kristy) 10. 9. 2026** pri reseni "Dusan vidi stara data". Neni to chyba jedne
zakazky - je to vzorec, ktery se v systemu bude opakovat.

## Co se stalo

6. 8. 2026 se modul Vyhodnoceni zakazek prepnul na nase tabulky. Zapsalo se, ze
*"zadna z 12 funkci schematu `ec` uz nesaha na zadne zrcadlo Centraly"* - a to platilo.
Prepnuly se ale **FUNKCE**, ne **DOTAZY PREHLEDU** (`fw.data_set`).

Dataset `ec.vyhodnoceni_prehled_list` cetl dal z `ec.tab_zakazka` a `ec.tab_zakazka_ext`.
Ta zrcadla maji po **JEDNOM radku**. Dusledek: sloupec **Sefmonter byl prazdny u 1 864
z 1 865 zakazek** a nikdo si toho mesic nevsiml, protoze prazdny sloupec nevypada jako chyba -
vypada jako "sefmonter neni vyplneny".

## Proc to nikdo neodhalil

Prazdna hodnota **nehlasi chybu**. `LEFT JOIN` na tabulku s jednim radkem vrati NULL
a grid ukaze prazdno. Zadny log, zadna vyjimka, zadny cerveny ramecek. Odhalilo se to
az pri uplne jine praci (proc jsou v prehledu stara cisla).

## Jak si takovou tabulku overit DRIV, nez na ni postavis dotaz

Nez neco pripojis, zeptej se **kolik ma ta tabulka radku** a **kolika radkum tveho hlavniho
dotazu se skutecne naparuje**. Ne jestli existuje - existovat bude.

```sql
SELECT 'ec.tab_zakazka' AS zdroj, count(*)::text FROM ec.tab_zakazka
UNION ALL
SELECT 'hlavicek, kterym se naparuje', count(*)::text
  FROM ec.vyhodnoceni_zakazka z
 WHERE EXISTS (SELECT 1 FROM ec.tab_zakazka tz WHERE tz.cislozakazky = z.cislo_zakazky);
```

Kdyz druhe cislo neni radove stejne jako prvni, je neco spatne.

## Znama mrtva a ziva zrcadla (stav 10. 9. 2026)

| tabulka | radku | pouzitelna |
|---|---|---|
| `ec.tab_zakazka` | 1 | NE |
| `ec.tab_zakazka_ext` | 1 | NE |
| `ec.dochazka` | 3 | NE (uz drive znamo) |
| `ec.dochazka_neevidovana` | 0 | NE (uz drive znamo) |
| `tenant.oz_zakazky` | 5 702, obnova a 30 min | ANO |
| `ec.cis_zam` | 430 | ano, ale jen prijmeni |
| `tenant.att_employee` | 239 | ANO - nase, plna jmena |

## Jak se to opravilo

Prehled cte nazev, kalkulaci, sefmontera i slouceni z `tenant.oz_zakazky` +
`tenant.zakazka_meta`, tedy **z tychz zdroju, ze kterych uz pocitaji funkce modulu**.
Zadna nova synchronizace nebyla potreba - cerstva data v systemu byla, jen se na ne
prehled nedival. Cely prehled (1 865 radku) se nacita za **64 ms**.

## Dve pravidla, ktera z toho plynou

1. **Kdyz prepinas modul na jiny zdroj, projdi i `fw.data_set`.** Funkce a dotazy jsou
   dve nezavisle vrstvy a prepnuti jedne nic nerika o druhe.
2. **Prazdny sloupec je podezrely stejne jako chybovy.** Kdyz je neco prazdne u vsech
   nebo skoro vsech radku, over si zdroj - nespolehej na to, ze "to tam proste neni vyplnene".

## Souvisejici pouceni k jmenum

Jmeno k osobnimu cislu ber pres **deduplikovane CTE**, ne primym joinem na
`tenant.att_employee` - doktrina #24 (jeden clovek muze mit vic karet, join zdvoji radky
a nikdo si toho nevsimne). Vzor: `DISTINCT ON (cislo_zam) ... ORDER BY cislo_zam,
is_active DESC NULLS LAST, id`, tedy stejne pravidlo jako `_att_employee` po oprave z 2. 9. 2026.

