# EC_DokladyPomocnePolozky

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 50,226 · **Size**: 3.62 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `IDDoklad` | int | NE |  |  |
| 2 | `DatSplatnosti` | datetime | ANO |  |  |
| 3 | `ZadanoKPlatbe` | numeric(18,2) | ANO |  |  |
| 4 | `ZadanoDPH` | numeric(18,2) | ANO |  |  |
| 5 | `CelkemBezDPH` | numeric(18,2) | ANO |  |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_DokladyPomocnePolozky` (CLUSTERED) — `IDDoklad`
