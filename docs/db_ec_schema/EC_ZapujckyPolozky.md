# EC_ZapujckyPolozky

**Schema**: dbo · **Cluster**: Other · **Rows**: 52 · **Size**: 0.07 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `CisloZakazky_Zdroj` | nvarchar(10) | ANO |  |  |
| 4 | `CisloZakazky_Cil` | nvarchar(10) | ANO |  |  |
| 5 | `Typ` | int | ANO |  |  |
| 6 | `IdKmenZbozi` | int | ANO |  |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Mnozstvi` | numeric(19,6) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |
| 13 | `DatVraceni` | datetime | ANO |  |  |
| 14 | `Vratil` | nvarchar(100) | ANO |  |  |
| 15 | `VraceneMnozstvi` | numeric(19,6) | ANO |  |  |
