# EC_FrameWorkObjects

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 10,476 · **Size**: 120.41 MB · **Sloupců**: 33 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ObjectID` | int | ANO |  |  |
| 3 | `ObjectNazev` | nvarchar(100) | ANO |  |  |
| 4 | `ObjectDefinice` | nvarchar(MAX) | ANO |  |  |
| 5 | `ObjectDefiniceDate` | datetime | ANO |  |  |
| 6 | `ObjectDefiniceLast` | nvarchar(MAX) | ANO |  |  |
| 7 | `ObjectDefiniceErrText` | nvarchar(MAX) | ANO |  |  |
| 8 | `ObjectDefiniceNEW` | bit | NE | ((0)) |  |
| 9 | `ObjectDefiniceErr` | bit | NE | ((0)) |  |
| 10 | `ObjectTyp` | nvarchar(2) | ANO |  |  |
| 11 | `ObjectTypPopis` | nvarchar(50) | ANO |  |  |
| 12 | `ObjectCreateDate` | datetime | ANO |  |  |
| 13 | `ObjectModifyDate` | datetime | ANO |  |  |
| 14 | `ObjectModifyDateLast` | datetime | ANO |  |  |
| 15 | `ObjectInDB` | bit | NE | ((0)) |  |
| 16 | `ObjectInserted` | bit | NE | ((0)) |  |
| 17 | `ObjectDeleted` | bit | NE | ((0)) |  |
| 18 | `ObjectRenamed` | bit | NE | ((0)) |  |
| 19 | `ObjectChanged` | bit | NE | ((0)) |  |
| 20 | `ObjectNazevOrig` | nvarchar(100) | ANO |  |  |
| 21 | `FrameWork` | bit | NE | ((0)) |  |
| 22 | `ScriptPopis` | nvarchar(100) | ANO |  |  |
| 23 | `ScriptDefinice` | nvarchar(MAX) | ANO |  |  |
| 24 | `ScriptDefiniceLast` | nvarchar(MAX) | ANO |  |  |
| 25 | `ScriptPoradi` | int | ANO |  |  |
| 26 | `ScriptPreneseno` | bit | NE | ((0)) |  |
| 27 | `ScriptPrenesenoPoradi` | int | ANO |  |  |
| 28 | `ScriptErr` | bit | NE | ((0)) |  |
| 29 | `ScriptErrText` | nvarchar(200) | ANO |  |  |
| 30 | `ScriptAutor` | nvarchar(128) | ANO |  |  |
| 31 | `ScriptDatum` | datetime | ANO |  |  |
| 32 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 33 | `DatPorizeni` | datetime | NE | (getdate()) |  |
