# EC_ZamestMesicni_prehled

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 15 · **FK**: 1 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatumPorizeni` | datetime | NE | (getdate()) |  |
| 3 | `MesicObdobi` | varchar(4) | NE |  |  |
| 4 | `CisloZam` | int | NE |  |  |
| 5 | `HodSazba` | int | ANO |  |  |
| 6 | `FixPremie` | int | ANO |  |  |
| 7 | `OdpracPocetHodin` | numeric(4,2) | ANO |  |  |
| 8 | `MelOdpracovat` | numeric(4,2) | ANO |  |  |
| 9 | `Vyplatit` | int | ANO |  |  |
| 10 | `Vyplaceno` | int | NE |  |  |
| 11 | `ZbyvaVyplatitAkt` | int | ANO |  |  |
| 12 | `DatPosledniPlatby` | datetime | ANO |  |  |
| 13 | `PrescasKontoMinule` | numeric(3,2) | ANO |  |  |
| 14 | `PrescasKontoPrirustek` | numeric(3,2) | ANO |  |  |
| 15 | `PrescasKontoAktual` | numeric(3,2) | ANO |  |  |

## Cizí klíče (declared)

- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_ZamestMesicni_prehled_TabCisZam`)_
