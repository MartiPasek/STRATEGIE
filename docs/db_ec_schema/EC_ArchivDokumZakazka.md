# EC_ArchivDokumZakazka

**Schema**: dbo · **Cluster**: CRM-Documents · **Rows**: 2,904 · **Size**: 0.40 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 3 | `Archivoval` | int | ANO |  |  |
| 4 | `DatumArchivace` | datetime | ANO | (getdate()) |  |
| 5 | `CisloSanonu` | int | ANO |  |  |
| 6 | `ArchivNezarazeno` | int | ANO |  |  |
| 7 | `Poznamka` | nvarchar(100) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_ArchivDokumZakazka` (CLUSTERED) — `id`
