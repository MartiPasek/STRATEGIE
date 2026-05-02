# EC_Kalk_PresunArchiv

**Schema**: dbo · **Cluster**: Production · **Rows**: 724 · **Size**: 0.21 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDZbosklad` | int | ANO |  |  |
| 3 | `RegCis` | nvarchar(30) | ANO |  |  |
| 4 | `MnozstviZdroj` | numeric(38,6) | ANO |  |  |
| 5 | `Stornovat` | numeric(38,6) | ANO |  |  |
| 6 | `Stornovano` | int | ANO |  |  |
| 7 | `Presunout` | numeric(38,6) | ANO |  |  |
| 8 | `CisloZakazkyOdkud` | nvarchar(15) | ANO |  |  |
| 9 | `CisloZakazkyKam` | varchar(11) | ANO |  |  |
| 10 | `ZbytekNaSklad` | bit | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | ANO |  |  |
| 12 | `DatPorizeni` | datetime | ANO |  |  |
| 13 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 14 | `IDPresunu` | int | ANO |  |  |
