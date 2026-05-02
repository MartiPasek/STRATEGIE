# EC_UkolyResitelVazba

**Schema**: dbo · **Cluster**: Other · **Rows**: 442,793 · **Size**: 64.90 MB · **Sloupců**: 25 · **FK**: 0 · **Indexů**: 4

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDUkol` | int | NE |  |  |
| 3 | `Resitel` | int | NE |  |  |
| 4 | `Typ` | tinyint | NE | ((1)) |  |
| 5 | `TypText` | varchar(14) | NE |  |  |
| 6 | `Aktivni` | bit | NE | ((0)) |  |
| 7 | `Stav` | tinyint | ANO |  |  |
| 9 | `OdhadHod` | numeric(19,2) | ANO |  |  |
| 10 | `RealHod` | numeric(19,2) | ANO |  |  |
| 11 | `Priorita` | int | ANO |  |  |
| 12 | `DatPrevzeti` | datetime | ANO |  |  |
| 13 | `DatZahajeni` | datetime | ANO |  |  |
| 14 | `DatDokonceni` | datetime | ANO |  |  |
| 15 | `DatKontroly` | datetime | ANO |  |  |
| 16 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 17 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 18 | `DatZmeny` | datetime | ANO |  |  |
| 19 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 20 | `PoznamkaResitel` | nvarchar(1000) | ANO |  |  |
| 21 | `TerminOsobni` | datetime | ANO |  |  |
| 22 | `Dulezitost` | tinyint | ANO |  |  |
| 23 | `DatPredani` | datetime | ANO |  |  |
| 24 | `DatPoslOtevreni` | datetime | ANO |  |  |
| 25 | `SchovatPredTerminem` | bit | ANO | ((0)) |  |
| 26 | `StavText` | varchar(17) | NE |  |  |

## Indexy

- **PK** `PK_EC_UkolyResitelVazba` (CLUSTERED) — `ID`
- **INDEX** `IX_UkolyResitelVazba_IDUkol` (NONCLUSTERED) — `IDUkol`
- **INDEX** `IX_EC_UkolyResitelVazba_Resitel` (NONCLUSTERED) — `IDUkol, Resitel`
- **INDEX** `IX_UkolyResitelVazba_DatDokonceni` (NONCLUSTERED) — `IDUkol, Resitel, DatDokonceni`
