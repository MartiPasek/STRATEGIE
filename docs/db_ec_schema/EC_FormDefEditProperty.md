# EC_FormDefEditProperty

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 124,294 · **Size**: 13.14 MB · **Sloupců**: 19 · **FK**: 1 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE | ([dbo].[EC_GET_NewID_2]('EC_FormDefEditProperty')) |  |
| 2 | `ID_FormDefEdit` | int | ANO |  |  |
| 3 | `EditCislo` | tinyint | NE | ((0)) |  |
| 4 | `Property` | nvarchar(30) | ANO |  |  |
| 5 | `PropertyFMX` | nvarchar(30) | ANO |  |  |
| 6 | `Value` | nvarchar(255) | ANO |  |  |
| 7 | `ValueFMX` | nvarchar(255) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |
| 12 | `Smazana` | bit | NE | ((0)) |  |
| 13 | `Smazal` | nvarchar(128) | ANO |  |  |
| 14 | `Systemova` | bit | NE | ((0)) |  |
| 15 | `PrevodVCLFMX` | bit | NE | ((0)) |  |
| 16 | `PrevodFMXVCL` | bit | NE | ((0)) |  |
| 17 | `DisableFMX` | bit | NE | ((0)) |  |
| 18 | `ID_FormDefEdit_OLD` | int | ANO |  |  |
| 19 | `FMX` | tinyint | ANO | ((1)) | 1 = VLC, 2 = FMX |

## Cizí klíče (declared)

- `ID_FormDefEdit` → [`EC_FormDefEdit`](EC_FormDefEdit.md).`ID` _(constraint: `FK_EC_FormDefEditProperty_EC_FormDefEdit`)_

## Indexy

- **PK** `PK_EC_FormDefEditProperty` (CLUSTERED) — `ID`
- **INDEX** `ID_FormDefEdit_Systemova_Includes` (NONCLUSTERED) — `EditCislo, Property, Value, Smazana, ID_FormDefEdit, Systemova`
