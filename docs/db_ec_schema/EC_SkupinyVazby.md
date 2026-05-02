# EC_SkupinyVazby

**Schema**: dbo · **Cluster**: Other · **Rows**: 417 · **Size**: 0.20 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDSkupiny` | int | ANO |  |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatZmeny` | datetime | ANO | (getdate()) |  |
| 9 | `UkolJeResitel` | bit | ANO | ((0)) |  |
| 10 | `UkolJeKopie` | bit | ANO | ((1)) |  |
| 11 | `OdeslatNotifikaci` | bit | ANO | ((0)) |  |
| 12 | `PotvrditPriPrevzeti` | bit | ANO | ((0)) |  |
| 13 | `UkolAutDokoncit` | bit | ANO | ((0)) |  |
| 14 | `Neaktivni` | bit | ANO |  |  |
| 15 | `HlavniSkupina` | bit | NE | ((1)) |  |
| 16 | `ZobrazVDovolenych` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_SkupinyVazby` (CLUSTERED) — `ID`
