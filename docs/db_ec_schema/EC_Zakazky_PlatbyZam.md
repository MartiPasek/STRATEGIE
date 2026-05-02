# EC_Zakazky_PlatbyZam

**Schema**: dbo · **Cluster**: Finance · **Rows**: 6,049 · **Size**: 0.99 MB · **Sloupců**: 13 · **FK**: 1 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatumPorizeni` | datetime | NE | (getdate()) |  |
| 3 | `CisloZakazky` | varchar(15) | NE |  |  |
| 4 | `CisloZam` | int | NE |  |  |
| 5 | `HodSazba` | int | ANO |  |  |
| 6 | `PocetHodin` | numeric(8,2) | ANO |  |  |
| 7 | `Vyplaceno` | numeric(8,2) | NE | ((0)) |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `IDPolVobj` | int | ANO |  |  |
| 10 | `IDPolPF` | int | ANO |  |  |
| 11 | `Zaloha` | numeric(8,2) | ANO |  |  |
| 12 | `JsemZaloha` | bit | ANO | ((0)) |  |
| 13 | `IDHlav` | int | ANO |  |  |

## Cizí klíče (declared)

- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_Zakazky_PlatbyZam_TabCisZam`)_
