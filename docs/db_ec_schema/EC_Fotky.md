# EC_Fotky

**Schema**: dbo · **Cluster**: HR · **Rows**: 1 · **Size**: 0.08 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev_Zdroj` | nvarchar(50) | ANO |  |  |
| 3 | `Nazev_Cil` | nvarchar(50) | ANO |  |  |
| 4 | `Cesta_Zdroj` | nvarchar(100) | ANO |  |  |
| 5 | `Cesta_Cil` | nvarchar(100) | ANO |  |  |
| 6 | `IDZarizeni` | nvarchar(100) | ANO |  | Například IMEI daného android zařízení |
| 7 | `DatPorizeni_Zdroj` | datetime | ANO |  | Kdy byla fotka vytvořena ve foťáku |
| 8 | `DatSynchronizace` | datetime | ANO | (getdate()) | Kdy byla fotka nahrána na server |
| 9 | `Autor_Zdroj` | nvarchar(10) | ANO |  | Kdo vyfotil |
| 10 | `Synchronizoval` | nvarchar(10) | ANO | (suser_sname()) | Kdo nahrál na server |
| 11 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 12 | `Typ` | tinyint | ANO |  | 1 = Rozvaděč, 2 = příbal, 3 = reklamace, ..... |
| 13 | `FileExists` | bit | ANO |  | Příznak, zda na cílové adrese existuje soubor |
| 14 | `AppNazev` | nvarchar(100) | ANO |  | Název aplikace ze které byla fotka vytvořena |
| 15 | `Poznamka` | nvarchar(MAX) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Fotky` (CLUSTERED) — `ID`
