# EC_FrameWorkScript

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 233 · **Size**: 2.58 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Pozice` | int | ANO |  |  |
| 3 | `ObjectID` | int | ANO |  |  |
| 4 | `ObjectNazev` | nvarchar(100) | ANO |  |  |
| 5 | `ObjectTyp` | nvarchar(2) | ANO |  |  |
| 6 | `ObjectTypPopis` | nvarchar(50) | ANO |  |  |
| 7 | `Script` | nvarchar(MAX) | ANO |  |  |
| 8 | `ScriptPopis` | nvarchar(100) | ANO |  |  |
| 9 | `ScriptDefinice` | nvarchar(MAX) | ANO |  |  |
| 10 | `ScriptDefiniceLast` | nvarchar(MAX) | ANO |  |  |
| 11 | `ScriptPriorita` | int | ANO |  |  |
| 12 | `ScriptPoradi` | int | ANO |  |  |
| 13 | `ScriptPreneseno` | bit | NE | ((0)) |  |
| 14 | `ScriptPrenesenoPoradi` | int | ANO |  |  |
| 15 | `ScriptErr` | bit | NE | ((0)) |  |
| 16 | `ScriptErrText` | nvarchar(200) | ANO |  |  |
| 17 | `ScriptAutor` | nvarchar(128) | ANO |  |  |
| 18 | `ScriptDatum` | datetime | ANO |  |  |
| 19 | `Autor` | nchar(100) | ANO | (suser_sname()) |  |
| 20 | `DatPorizeni` | datetime | NE | (getdate()) |  |
