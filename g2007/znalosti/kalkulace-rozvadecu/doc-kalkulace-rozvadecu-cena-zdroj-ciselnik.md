# Číselník zdrojů ceny dílů (proj.cena_zdroj)

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Číselník zdrojů ceny dílů — proj.cena_zdroj

**Autor: Claude-24 (Kristý), 24. 7. 2026** (req #1387, Centrála #1395). Číselník, odkud pochází cena dílu.

## Tabulka
`proj.cena_zdroj`: `id` (bigint identity, PK), `tenant_id` (default 2), `kod` (varchar, UNIQUE `(tenant_id, kod)`), `nazev` (varchar), `poradi` (int, řazení UI), `aktivni` (bool, default true), `created_at`. Idempotentní (CREATE IF NOT EXISTS + ON CONFLICT DO NOTHING).

## Hodnoty
| kod | nazev | poradi |
|---|---|---|
| CENIK | Ceník | 1 |
| NABIDKA | Nabídka | 2 |
| ESHOP | Eshop | 3 |
| ODHAD | Odhad | 4 |
| POSL_NC | Poslední NC z dokladů | 5 |
| CENTRALA | Centrála | 6 |

`kod` = stabilní strojová reference, `nazev` = zobrazení, `aktivni` = měkké vypnutí. Napojení na ceny dílů přes `proj.kalk_cena.zdroj_typ` (FK). Souvisí s [[kalk-cena]] a [[kalk-kmen-standard-load]].

