# EC_OrgKvalifikacePolozky

**Schema**: dbo · **Cluster**: HR · **Rows**: 132 · **Size**: 0.07 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `Student` | int | ANO |  | číslo zaměstnance |
| 4 | `Skolitel` | int | ANO |  | číslo školitele |
| 5 | `CinnostText` | nvarchar(MAX) | ANO |  | činnost, kterou zadá srtudent - nebude nejspíše odpovídat číselníku činnosti |
| 6 | `CinnostID` | int | ANO |  | ID Cinnosti, kterou máme založenou v systému |
| 7 | `SchvalenoSkolitel` | bit | ANO | ((0)) |  |
| 8 | `PoznamkaStudent` | nvarchar(MAX) | ANO |  |  |
| 9 | `PoznamkaSkolitel` | nvarchar(MAX) | ANO |  |  |
| 10 | `PoznamkaSchvaleni` | nvarchar(MAX) | ANO |  |  |
| 11 | `Archivni` | bit | NE | ((0)) |  |
| 12 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |
