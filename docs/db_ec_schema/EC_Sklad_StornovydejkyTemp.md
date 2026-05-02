# EC_Sklad_StornovydejkyTemp

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 142 · **Size**: 0.21 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Poradi` | int | ANO |  |  |
| 3 | `RegCis` | nvarchar(30) | ANO |  |  |
| 4 | `Nazev1` | nvarchar(100) | ANO |  |  |
| 5 | `Poznamka` | ntext | ANO |  |  |
| 6 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 7 | `MnozstviPuvodni` | numeric(19,6) | ANO |  |  |
| 8 | `MnozstviVracene` | numeric(19,6) | ANO |  |  |
| 9 | `StavSkladu` | numeric(19,6) | ANO |  |  |
| 10 | `MJ` | nvarchar(10) | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 12 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 13 | `Umisteni` | nvarchar(15) | ANO |  |  |
| 14 | `nezobrazuj` | bit | ANO | ((0)) |  |
| 15 | `SV_ID` | int | ANO |  |  |
| 16 | `MnozstviStornoVydej` | numeric(19,6) | ANO |  |  |
| 17 | `IDKmenZbozi` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Sklad_StornovydejkyTemp` (CLUSTERED) — `ID`
