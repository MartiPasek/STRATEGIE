# EC_PrubehHospodareniMesicne

**Schema**: dbo · **Cluster**: Finance · **Rows**: 72 · **Size**: 0.07 MB · **Sloupců**: 28 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `Rok` | int | NE |  |  |
| 3 | `Mesic` | int | NE |  |  |
| 4 | `HVRokDoMes_Celkem` | numeric(19,6) | ANO |  |  |
| 5 | `HVRokDoMes001` | numeric(19,6) | ANO |  |  |
| 6 | `HVRokDoMes002` | numeric(19,6) | ANO |  |  |
| 7 | `HV` | numeric(19,6) | ANO |  |  |
| 8 | `HV_1_900` | numeric(23,8) | ANO |  |  |
| 9 | `HV_2_900` | numeric(23,8) | ANO |  |  |
| 10 | `Naklady001` | numeric(19,6) | ANO |  |  |
| 11 | `Vynosy001` | numeric(19,6) | ANO |  |  |
| 12 | `Zustatek001` | numeric(20,6) | ANO |  |  |
| 13 | `Naklady002` | numeric(19,6) | ANO |  |  |
| 14 | `Vynosy002` | numeric(19,6) | ANO |  |  |
| 15 | `Zustatek002` | numeric(20,6) | ANO |  |  |
| 16 | `Naklady900` | numeric(19,6) | ANO |  |  |
| 17 | `Vynosy900` | numeric(19,6) | ANO |  |  |
| 18 | `Zustatek900` | numeric(20,6) | ANO |  |  |
| 19 | `Naklady` | numeric(19,6) | ANO |  |  |
| 20 | `Vynosy` | numeric(19,6) | ANO |  |  |
| 21 | `Zustatek` | numeric(20,6) | ANO |  |  |
| 22 | `Naklady1_900` | numeric(22,8) | ANO |  |  |
| 23 | `Vynosy1_900` | numeric(22,8) | ANO |  |  |
| 24 | `Naklady2_900` | numeric(22,8) | ANO |  |  |
| 25 | `Vynosy2_900` | numeric(22,8) | ANO |  |  |
| 26 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 27 | `Dat_PoslAkt_mes` | smalldatetime | ANO |  |  |
| 28 | `Dat_PoslAkt_HV` | smalldatetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_PrubehHospodareniMesicne` (CLUSTERED) — `id`
