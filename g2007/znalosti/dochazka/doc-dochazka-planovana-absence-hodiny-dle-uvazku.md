# Plán nepřítomností z Centrály zapisoval 8 h i lidem se zkráceným úvazkem

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Hodiny plánované absence musí sedět na denní úvazek

**Ověřeno 10. 8. 2026** (Peťa + Claude-26) na reálném případu.

## Příznak

Zaměstnanec se zkráceným úvazkem má u dovolené (nebo jiné absence) zapsaných **8 hodin
na den**, přestože má úvazek např. 7 h. Nafoukne to absenci a přes ni fond pracovní doby,
Landmark náhrady i čerpání dovolené.

## Příčina

Chyba **nevzniká u nás — přichází už ze zdroje**. Do `tenant.att_planned_absence` dorazí
z Centrály hodiny rovnou jako 8,00. Přenos `sync_plan_to_dochazka` (g2007.python) je
jen převzal — denní úvazek nekontroloval. Kód navíc při prázdné hodnotě dosazoval 8,0
jako výchozí.

## Oprava (10. 8. 2026)

1. **Data**: dotčené dny srovnány na skutečný denní úvazek. Ověřeno čtením z DB.
2. **Kód**: do `sync_plan_to_dochazka` doplněna pojistka — hodiny z plánu se ořežou
   na denní úvazek platný k danému dni (`engagement.uvazek_tyden_h / 5`). **Jen zmenšuje,
   nikdy nezvětšuje**; koho úvazek nezná, nechá beze změny. Obalené try/except, aby
   pojistka nikdy neshodila samotný přenos.

Přenos má i starší pojistku „nepřepisuj obsazený den", takže **ruční oprava záznamu vydrží**
a další běh ji nepřepíše.

## ⭐ Past při kontrole: úvazek PLATNÝ K DATU, ne dnešní

Kdo poměřuje dnešním úvazkem, dostane **falešné nálezy** u lidí, kterým se úvazek během
roku měnil — jejich starší absence po 8 h je správně, protože tehdy 8h úvazek měli.
Správně se úvazek bere podle `entry_date`:

```sql
JOIN LATERAL (
   SELECT g2.uvazek_tyden_h FROM tenant.engagement g2
   WHERE g2.employee_id = ae.id
     AND (g2.valid_from IS NULL OR g2.valid_from <= a.entry_date)
     AND (g2.valid_to   IS NULL OR g2.valid_to   >= a.entry_date)
   ORDER BY (g2.valid_from IS NULL), g2.valid_from DESC NULLS LAST, g2.is_current DESC
   LIMIT 1) g ON true
WHERE a.hours > (g.uvazek_tyden_h/5.0) + 0.01
```

Tímhle dotazem se dá kdykoli přejet celý rok a najít všechny rozjeté hodiny absencí.

## Souvislost

Je to konkrétní případ obecného pravidla „sdílená hodnota → nejdřív mapa zapisovatelů
a čtenářů" (`doc-system-strategie-dopadova-mapa-sdilene-hodnoty`). Hodiny absence plní víc
cest (plán z Centrály, žádosti, ruční opravy, import docházky) a čte je ještě víc míst
(denní podklad, mzdy, náhrady, nárok dovolené) — oprava jen v datech bez pojistky v přenosu
by problém vrátila při dalším běhu.

