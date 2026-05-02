# EC_Workflow_Konektory

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 10 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 3 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | NE |  |  |
| 3 | `Typ` | nvarchar(50) | NE |  |  |
| 4 | `Konfigurace` | nvarchar(MAX) | ANO |  |  |
| 5 | `CredentialsSecret` | nvarchar(200) | ANO |  |  |
| 6 | `PrihlasovaciUdajeId` | int | ANO |  |  |
| 7 | `Kontrakt` | nvarchar(MAX) | ANO |  |  |
| 8 | `InterniKonfigurace` | nvarchar(MAX) | ANO |  |  |
| 9 | `IdTypKonektoru` | int | ANO |  |  |
| 10 | `Aktivni` | bit | NE | ((1)) |  |
| 11 | `DatumVytvoreni` | datetime | NE | (getdate()) |  |

## Cizí klíče (declared)

- `Typ` → [`EC_Workflow_TypyDriveru`](EC_Workflow_TypyDriveru.md).`Kod` _(constraint: `FK_Workflow_Konektory_Driver`)_
- `PrihlasovaciUdajeId` → [`EC_Workflow_PrihlasovaciUdaje`](EC_Workflow_PrihlasovaciUdaje.md).`Id` _(constraint: `FK_Workflow_Konektory_PrihlasovaciUdaje`)_
- `IdTypKonektoru` → [`EC_Workflow_TypyKonektoru`](EC_Workflow_TypyKonektoru.md).`Id` _(constraint: `FK_Workflow_Konektory_TypKonektoru`)_

## Indexy

- **PK** `PK__EC_Workf__3214EC0709C1E6F0` (CLUSTERED) — `Id`
