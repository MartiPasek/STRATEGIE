# EC_PresunPolozek_Log

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,987 · **Size**: 0.91 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `IDLogu` | int | NE |  |  |
| 2 | `NazevProcedury` | nvarchar(100) | ANO |  |  |
| 3 | `CisloZakazkyOdkud` | nvarchar(10) | ANO |  |  |
| 4 | `CisloZakazkyKam` | nvarchar(10) | ANO |  |  |
| 5 | `UniqueIdentifier` | nvarchar(100) | ANO |  |  |
| 6 | `IDKalk` | int | ANO |  |  |
| 7 | `IDPol` | int | ANO |  |  |
| 8 | `ID_E` | int | ANO |  |  |
| 9 | `IDDoklad` | int | ANO |  |  |
| 10 | `DruhPol` | nvarchar(100) | ANO |  |  |
| 11 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 13 | `IDPresunu` | int | ANO |  |  |
| 14 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 15 | `Mnozstvi` | numeric(19,2) | ANO |  |  |
| 16 | `Typ` | int | ANO |  |  |
| 17 | `ID` | int | ANO |  |  |
