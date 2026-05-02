# EC_Workflow_PinyKonektoru

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 90 · **Size**: 0.07 MB · **Sloupců**: 16 · **FK**: 1 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `IdTypuKonektoru` | int | NE |  |  |
| 3 | `CisloPinu` | int | NE |  |  |
| 4 | `Smer` | nvarchar(3) | NE |  |  |
| 5 | `Nazev` | nvarchar(100) | NE |  |  |
| 6 | `TypPinu` | nvarchar(50) | NE |  |  |
| 7 | `Skupina` | nvarchar(50) | ANO |  |  |
| 8 | `Povinny` | bit | NE | ((0)) |  |
| 9 | `ZavislyNa` | nvarchar(100) | ANO |  |  |
| 10 | `Uroven` | nvarchar(10) | NE | ('step') |  |
| 11 | `Moznosti` | nvarchar(MAX) | ANO |  |  |
| 12 | `VychoziHodnota` | nvarchar(500) | ANO |  |  |
| 13 | `Popis` | nvarchar(500) | ANO |  |  |
| 14 | `Placeholder` | nvarchar(200) | ANO |  |  |
| 15 | `Schema` | nvarchar(MAX) | ANO |  |  |
| 16 | `SchemaTyp` | nvarchar(20) | ANO |  |  |

## Cizí klíče (declared)

- `IdTypuKonektoru` → [`EC_Workflow_TypyKonektoru`](EC_Workflow_TypyKonektoru.md).`Id` _(constraint: `FK_Workflow_PinyKonektoru_Typ`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC07A748380E` (CLUSTERED) — `Id`
- **UNIQUE** `UQ_Workflow_PinyKonektoru_NazevTyp` (NONCLUSTERED) — `IdTypuKonektoru, Nazev, Smer`
