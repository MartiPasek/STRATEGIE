# EC_Dochazka_AppLogPrihlaseni

**Schema**: dbo · **Cluster**: HR · **Rows**: 268,964 · **Size**: 30.39 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 3 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 4 | `CisloZam` | int | ANO |  |  |
| 5 | `Pass` | varchar(100) | ANO |  |  |
| 6 | `IdZarizeni` | int | ANO |  |  |
| 7 | `LoginMethod` | int | ANO |  |  |
| 8 | `MACAdress` | nvarchar(100) | ANO |  |  |
