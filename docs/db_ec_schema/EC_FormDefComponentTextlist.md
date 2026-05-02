# EC_FormDefComponentTextlist

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 726 · **Size**: 0.20 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE | ([dbo].[EC_Get_NEWID_2]('EC_FormDefComponentTextlist')) |  |
| 2 | `SQLdef_Cislo` | int | ANO |  |  |
| 3 | `SQLdef_Field` | nvarchar(50) | ANO |  |  |
| 4 | `Value` | nvarchar(50) | NE |  |  |
| 5 | `Text` | nvarchar(50) | NE |  |  |
| 6 | `CisloPrehleduProVyber` | int | ANO |  |  |
| 7 | `Poradi` | int | ANO | ((100)) |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |
| 12 | `FMX` | tinyint | ANO | ((1)) | 1 = VLC, 2 = FMX |

## Indexy

- **PK** `PK_EC_FormDefComponentTextlist` (CLUSTERED) — `ID`
