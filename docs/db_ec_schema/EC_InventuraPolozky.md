# EC_InventuraPolozky

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 315,789 · **Size**: 41.23 MB · **Sloupců**: 22 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | NE |  |  |
| 3 | `IDKmenZbozi` | int | NE |  |  |
| 4 | `Umisteni_Predpoklad` | nvarchar(15) | NE |  |  |
| 5 | `Mnozstvi_Predpoklad` | numeric(19,6) | NE |  |  |
| 6 | `Mnozstvi_Realne` | numeric(19,6) | NE |  |  |
| 7 | `Umisteni_Realne` | nvarchar(15) | NE |  |  |
| 8 | `Shoda_Umisteni` | int | NE |  |  |
| 9 | `Schazi` | numeric(20,6) | ANO |  |  |
| 10 | `Prebyva` | numeric(20,6) | ANO |  |  |
| 11 | `Celkem_Predpoklad` | numeric(19,6) | NE |  |  |
| 12 | `Celkem_Realne` | numeric(19,6) | NE |  |  |
| 13 | `Shoda_Celkem` | int | NE |  |  |
| 14 | `Celkem_Schazi` | numeric(20,6) | ANO |  |  |
| 15 | `Celkem_Prebyva` | numeric(20,6) | ANO |  |  |
| 16 | `Objednano` | numeric(19,6) | NE |  |  |
| 17 | `MnPoslInv` | numeric(19,6) | ANO |  |  |
| 18 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 19 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 20 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 21 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 22 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_InventuraPolozky` (CLUSTERED) — `ID`
