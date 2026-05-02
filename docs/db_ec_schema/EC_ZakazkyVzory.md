# EC_ZakazkyVzory

**Schema**: dbo · **Cluster**: Finance · **Rows**: 3 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloOrg` | int | ANO |  |  |
| 3 | `Typ` | smallint | ANO |  | 1 = Mustr pro průběh zakázky |
| 4 | `Nazev` | nvarchar(100) | ANO |  |  |
| 5 | `Poznamka` | nvarchar(255) | ANO |  |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
