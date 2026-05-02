# EC_Dochazka_PrevodPrescasu_PocetHodin

**Schema**: dbo · **Cluster**: HR · **Rows**: 1,454 · **Size**: 0.14 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `PocetHodin` | numeric(19,2) | ANO |  |  |
| 4 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 5 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
