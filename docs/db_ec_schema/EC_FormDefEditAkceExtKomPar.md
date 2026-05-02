# EC_FormDefEditAkceExtKomPar

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 2,801 · **Size**: 1.02 MB · **Sloupců**: 18 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE | ([dbo].[EC_GET_NewID_2]('EC_FormDefEditAkceExtKomPar')) |  |
| 2 | `IdFormDefEditAkce` | int | NE |  |  |
| 3 | `Cislo` | int | NE |  |  |
| 4 | `Popis` | nvarchar(40) | NE |  |  |
| 5 | `Typ` | int | NE |  |  |
| 6 | `TextDefault` | nvarchar(100) | ANO |  |  |
| 7 | `DateDefault` | datetime | ANO |  |  |
| 8 | `CisloDefault` | numeric(19,6) | ANO |  |  |
| 9 | `CheckDefault` | bit | NE | ((0)) |  |
| 10 | `Atribut` | nvarchar(40) | ANO |  |  |
| 11 | `DefPrehled` | int | ANO |  |  |
| 12 | `Podminka` | ntext | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |
| 17 | `Typ2` | int | ANO |  |  |
| 18 | `NTextDefault` | ntext | ANO |  |  |

## Cizí klíče (declared)

- `IdFormDefEditAkce` → [`EC_FormDefEditAkce`](EC_FormDefEditAkce.md).`ID` _(constraint: `FK_EC_FormDefEditAkceExtKomPar_EC_FormDefEditAkce`)_

## Indexy

- **PK** `PK_EC_FormDefEditAkceExtKomPar` (CLUSTERED) — `ID`
