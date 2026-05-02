# EC_CestovniPrikazy

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 25 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatumPripadu` | datetime | NE | (getdate()) |  |
| 3 | `DenVTydnu` | nvarchar(2) | ANO |  |  |
| 4 | `CisloZam` | int | NE |  |  |
| 5 | `CisloZakazky` | varchar(15) | NE |  |  |
| 6 | `CasZacatek` | datetime | ANO | (dateadd(second,(60)-datepart(second,getdate()),getdate())) |  |
| 7 | `CasKonec` | datetime | ANO |  |  |
| 8 | `PocetDni` | int | ANO |  |  |
| 9 | `Zeme` | nvarchar(5) | ANO |  |  |
| 10 | `SazbaTuzem` | int | ANO |  |  |
| 11 | `SazbaZahran` | int | ANO |  |  |
| 12 | `Mesto` | nvarchar(50) | ANO |  |  |
| 13 | `Firma` | nvarchar(50) | ANO |  |  |
| 14 | `Hotel1EUR` | numeric(18,2) | ANO |  |  |
| 15 | `NedanoveEUR` | numeric(18,2) | ANO |  |  |
| 16 | `DanoveEUR` | numeric(18,2) | ANO |  |  |
| 17 | `DietyEUR` | numeric(18,2) | ANO |  |  |
| 18 | `KapesneEUR` | numeric(18,2) | ANO |  |  |
| 19 | `CelkemEUR` | numeric(18,2) | ANO |  |  |
| 20 | `DietyKC` | numeric(18,2) | ANO |  |  |
| 21 | `KapesneKC` | numeric(18,2) | ANO |  |  |
| 22 | `CelkemKC` | numeric(18,2) | ANO |  |  |
| 23 | `Kurz` | numeric(18,2) | ANO |  |  |
| 24 | `Vyplaceno` | numeric(18,2) | ANO |  |  |
| 25 | `DatumZaplaceni` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK__EC_CestovniPrikazy__TabCisZam`)_

## Indexy

- **PK** `PK_EC_CestovniPrizazy` (CLUSTERED) — `ID`
