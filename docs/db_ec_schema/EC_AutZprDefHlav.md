# EC_AutZprDefHlav

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 36 · **Size**: 0.20 MB · **Sloupců**: 28 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Poradi` | int | NE | ((99999)) |  |
| 3 | `DruhDokladu` | int | ANO |  |  |
| 5 | `CisloOrg` | int | ANO |  |  |
| 6 | `KlicovyString1` | nvarchar(70) | ANO |  |  |
| 7 | `KlicovyString2` | nvarchar(70) | ANO |  |  |
| 8 | `KlicovyString3` | nvarchar(70) | ANO |  |  |
| 9 | `KlicovyString4` | nvarchar(70) | ANO |  |  |
| 10 | `TypDekodovani` | tinyint | NE | ((0)) |  |
| 11 | `TypEnkodovani` | tinyint | NE | ((0)) |  |
| 12 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 13 | `Mode` | tinyint | NE | ((1)) |  |
| 14 | `ModeText` | varchar(29) | NE |  |  |
| 15 | `CisloOddelovacTisicu` | nvarchar(1) | NE | (N'.') |  |
| 16 | `CisloDesetinnaCarka` | nvarchar(1) | NE | (N',') |  |
| 17 | `CilTabImport` | int | NE | ((0)) |  |
| 18 | `CilTabImportText` | varchar(12) | NE |  |  |
| 19 | `Aktivni` | bit | NE | ((1)) |  |
| 20 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 21 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 22 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 23 | `DatZmeny` | datetime | ANO |  |  |
| 24 | `Import` | bit | NE | ((1)) |  |
| 25 | `SelectDefiniceHlav` | nvarchar(MAX) | ANO |  |  |
| 26 | `SelectDefinicePol` | nvarchar(MAX) | ANO |  |  |
| 27 | `RadaDokladuPoslCis` | smallint | ANO |  |  |
| 28 | `ObsahujeSloucenePolozky` | bit | ANO |  |  |
| 29 | `DruhDokladuText` | varchar(14) | NE |  |  |

## Indexy

- **PK** `PK_EC_AutZprDokHlav` (CLUSTERED) — `ID`
