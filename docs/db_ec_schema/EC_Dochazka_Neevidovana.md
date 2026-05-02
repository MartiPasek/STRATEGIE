# EC_Dochazka_Neevidovana

**Schema**: dbo · **Cluster**: HR · **Rows**: 0 · **Size**: 0.01 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatumPripadu` | datetime | NE |  |  |
| 3 | `DenVTydnu` | nvarchar(2) | ANO |  |  |
| 4 | `CisloZam` | int | NE |  |  |
| 5 | `DruhCinnosti` | smallint | NE |  |  |
| 6 | `CisloZakazky` | varchar(15) | NE |  |  |
| 7 | `CasZacatek` | datetime | ANO |  |  |
| 8 | `CasKonec` | datetime | ANO |  |  |
| 9 | `ZamPoznamka` | varchar(80) | ANO |  |  |
| 10 | `PozadPomocVed` | bit | ANO |  |  |
| 11 | `SefMontPoznamka` | varchar(80) | ANO |  |  |
| 12 | `VedPoznamka` | varchar(80) | ANO |  |  |
| 13 | `CasCelkemZakazka` | numeric(17,6) | ANO |  |  |
| 14 | `PraceAktivni` | bit | NE |  |  |
| 15 | `DenZacatek` | datetime | ANO |  |  |
| 16 | `Poznamka` | nvarchar(250) | ANO |  |  |
| 17 | `Autor` | nvarchar(50) | ANO | (suser_sname()) |  |
| 18 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 19 | `DatZmeny` | datetime | ANO |  |  |
| 20 | `Zmenil` | nvarchar(50) | ANO |  |  |
