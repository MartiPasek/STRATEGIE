# EC_ZamRFID

**Schema**: dbo · **Cluster**: Other · **Rows**: 147 · **Size**: 0.16 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Aktivni` | bit | NE | ((1)) |  |
| 3 | `CisloZam` | int | NE |  |  |
| 4 | `Typ` | nvarchar(1) | ANO |  |  |
| 5 | `RFIDtag` | nvarchar(50) | NE |  |  |
| 6 | `Poznamka` | text | ANO |  |  |
| 7 | `DatumVydani` | date | ANO | (getdate()) |  |
| 8 | `PlatnostDo` | date | ANO |  |  |

## Indexy

- **PK** `PK_EC_ZamRFID` (CLUSTERED) — `ID`
