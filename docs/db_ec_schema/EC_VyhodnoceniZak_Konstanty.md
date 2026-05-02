# EC_VyhodnoceniZak_Konstanty

**Schema**: dbo · **Cluster**: Other · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `PlatnostOd` | datetime | ANO |  |  |
| 3 | `PlatnostDo` | datetime | ANO |  |  |
| 4 | `SazbaPremie` | numeric(6,2) | ANO |  |  |
| 5 | `SazbaSrazka` | numeric(6,2) | ANO |  |  |
| 6 | `KonstCasRezerva` | numeric(5,2) | ANO |  |  |
| 7 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(126) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |
| 11 | `PremieSefmonterHod` | numeric(19,6) | ANO |  |  |
| 12 | `PremieSefmonter` | numeric(19,6) | ANO |  |  |
| 13 | `PremieSefmonterKoef` | numeric(19,6) | ANO |  |  |
| 14 | `VKM` | numeric(5,2) | ANO |  |  |
