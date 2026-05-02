# EC_PrubehHospodareni_Ucty

**Schema**: dbo · **Cluster**: Finance · **Rows**: 19 · **Size**: 0.07 MB · **Sloupců**: 29 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `ROK` | int | NE |  |  |
| 3 | `Mesic` | int | ANO |  |  |
| 4 | `Vynosy001` | numeric(18,2) | ANO |  |  |
| 5 | `Vynosy002` | numeric(18,2) | ANO |  |  |
| 6 | `Vynosy900` | numeric(18,2) | ANO |  |  |
| 7 | `Vynosy920` | numeric(18,2) | ANO |  |  |
| 8 | `Vynosy` | numeric(18,2) | ANO |  |  |
| 9 | `Naklady001` | numeric(18,2) | ANO |  |  |
| 10 | `Naklady002` | numeric(18,2) | ANO |  |  |
| 11 | `Naklady900` | numeric(18,2) | ANO |  |  |
| 12 | `Naklady920` | numeric(18,2) | ANO |  |  |
| 13 | `Naklady` | numeric(18,2) | ANO |  |  |
| 14 | `Zustatek001` | numeric(18,2) | ANO |  |  |
| 15 | `Zustatek002` | numeric(18,2) | ANO |  |  |
| 16 | `Zustatek900` | numeric(18,2) | ANO |  |  |
| 17 | `Zustatek920` | numeric(18,2) | ANO |  |  |
| 18 | `Zustatek` | numeric(18,2) | ANO |  |  |
| 19 | `NakladyNedanove` | numeric(18,2) | ANO |  |  |
| 20 | `HV` | numeric(18,2) | ANO |  |  |
| 21 | `HV_1` | numeric(18,2) | ANO |  |  |
| 22 | `HV_2` | numeric(18,2) | ANO |  |  |
| 23 | `HV_po_dani` | numeric(18,2) | ANO |  |  |
| 24 | `Ucet581_ZmenaStavuNV001` | numeric(18,2) | ANO |  |  |
| 25 | `Ucet581_ZmenaStavuNV002` | numeric(18,2) | ANO |  |  |
| 26 | `Ucet591_Dan` | numeric(18,2) | ANO |  |  |
| 27 | `Ucet501000_VKM920` | numeric(18,2) | ANO |  |  |
| 28 | `Dat_PoslAkt` | smalldatetime | ANO |  |  |
| 29 | `Aktualizoval` | nvarchar(128) | ANO | (suser_sname()) |  |

## Indexy

- **PK** `PK_EC_PrubehHospodareni_Ucty` (CLUSTERED) — `id`
