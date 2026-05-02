# EC_DELPHI_TabObecnyPrehled_ARCHIV

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 0 · **Size**: 0.45 MB · **Sloupců**: 42 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `GUID` | uniqueidentifier | NE | (newid()) |  |
| 3 | `Skupina` | nvarchar(30) | NE | ('DELPHI') |  |
| 4 | `Cislo` | int | NE |  |  |
| 5 | `Nazev` | nvarchar(50) | NE |  |  |
| 6 | `MaxRecords` | int | NE | ((0)) |  |
| 7 | `DefView` | ntext | ANO |  |  |
| 8 | `DefViewSQLite` | ntext | ANO |  |  |
| 9 | `BeforeOpenSQL` | ntext | ANO |  |  |
| 10 | `InsertSQL` | ntext | ANO |  |  |
| 11 | `UpdateSQL` | ntext | ANO |  |  |
| 12 | `DeleteSQL` | ntext | ANO |  |  |
| 13 | `CopySQL` | ntext | ANO |  |  |
| 14 | `DefText` | text | ANO |  |  |
| 15 | `PolCislo` | int | ANO |  |  |
| 16 | `TiskSkupina` | int | ANO |  |  |
| 17 | `ID_Edit` | int | ANO |  |  |
| 18 | `AdresarKod` | nvarchar(20) | ANO |  |  |
| 19 | `AdresarSkupina` | nvarchar(20) | ANO | ('') |  |
| 20 | `Autor` | nvarchar(128) | ANO |  |  |
| 21 | `DatPorizeni` | datetime | ANO |  |  |
| 22 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 23 | `DatZmeny` | datetime | ANO |  |  |
| 24 | `DatPorizeni_D` | int | ANO |  |  |
| 25 | `DatPorizeni_M` | int | ANO |  |  |
| 26 | `DatPorizeni_Y` | int | ANO |  |  |
| 27 | `DatPorizeni_Q` | int | ANO |  |  |
| 28 | `DatPorizeni_W` | int | ANO |  |  |
| 29 | `DatPorizeni_X` | datetime | ANO |  |  |
| 30 | `CanRequery` | bit | ANO | ((1)) |  |
| 31 | `MasterFieldName` | nvarchar(100) | ANO | (N'ID') |  |
| 32 | `FooterCalculateString` | nvarchar(255) | ANO | ('') |  |
| 33 | `InsertBeforeOpen` | bit | ANO | ((0)) |  |
| 34 | `CopyFieldsString` | nvarchar(500) | ANO |  |  |
| 35 | `RefreshType` | tinyint | ANO | ((0)) |  |
| 36 | `RowMem` | bit | ANO | ((1)) |  |
| 37 | `DeleteDir` | bit | ANO | ((0)) |  |
| 38 | `Upraveno` | bit | ANO | ((0)) |  |
| 39 | `IDPuvodni` | int | ANO |  |  |
| 40 | `Archivoval` | nvarchar(126) | ANO | (suser_sname()) |  |
| 41 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 42 | `LogTrvani` | bit | ANO |  |  |
