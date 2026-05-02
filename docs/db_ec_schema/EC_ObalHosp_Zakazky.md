# EC_ObalHosp_Zakazky

**Schema**: dbo · **Cluster**: Other · **Rows**: 3 · **Size**: 0.07 MB · **Sloupců**: 104 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(10) | NE |  |  |
| 3 | `Sestava1_Vyska` | int | ANO | ((0)) |  |
| 4 | `Sestava1_Sirka` | int | ANO | ((0)) |  |
| 5 | `Sestava1_Delka` | int | ANO | ((0)) |  |
| 6 | `Sestava1_Obvod` | numeric(18,6) | ANO | ((0)) |  |
| 7 | `Sestava1_Povrch` | numeric(18,6) | ANO | ((0)) |  |
| 8 | `Sestava1_Objem` | numeric(18,6) | ANO | ((0)) |  |
| 9 | `Sestava1_PotrDelkaStrecFolie` | numeric(18,6) | ANO | ((0)) |  |
| 10 | `Sestava1_HmotPouzStrecFolie` | numeric(18,6) | ANO | ((0)) |  |
| 11 | `Sestava1_PouzMnRole` | numeric(18,6) | ANO | ((0)) |  |
| 12 | `Sestava1_ObalMat_KartRittal` | numeric(18,6) | ANO | ((0)) |  |
| 13 | `Sestava1_ObalMat_VlnLepenkaJunker_delka` | numeric(18,6) | ANO | ((0)) |  |
| 14 | `Sestava1_ObalMat_VlnLepenkaJunker_hmot` | numeric(18,6) | ANO | ((0)) |  |
| 15 | `Sestava1_MnObalMat_VlnLepenkaJunker` | numeric(18,6) | ANO | ((0)) |  |
| 16 | `Sestava1_ObalMat_VlnLepenkaEC_delka` | numeric(18,6) | ANO | ((0)) |  |
| 17 | `Sestava1_ObalMat_VlnLepenkaEC_hmot` | numeric(18,6) | ANO | ((0)) |  |
| 18 | `Sestava1_MnObalMat_VlnLepenkaEC` | numeric(18,6) | ANO | ((0)) |  |
| 19 | `Sestava1_ObalMat_RohVystuze` | numeric(18,6) | ANO | ((0)) |  |
| 20 | `Sestava1_PocetKrabic1` | int | ANO | ((0)) |  |
| 21 | `Sestava1_PocetKrabic2` | int | ANO | ((0)) |  |
| 22 | `Sestava1_PocetKrabic3` | int | ANO | ((0)) |  |
| 23 | `Sestava1_PocetKrabic4` | int | ANO | ((0)) |  |
| 24 | `Sestava1_HmKrabicPribal` | numeric(18,6) | ANO | ((0)) |  |
| 25 | `Sestava1_PocetEuropalet` | int | ANO | ((0)) |  |
| 26 | `Sestava1_PocetPaletRittal` | int | ANO | ((0)) |  |
| 27 | `Sestava1_PocetPaletMensiZbozi` | int | ANO | ((0)) |  |
| 28 | `Sestava1_CelkHmPouzPalet` | numeric(18,6) | ANO | ((0)) |  |
| 29 | `Sestava2_Vyska` | int | ANO | ((0)) |  |
| 30 | `Sestava2_Sirka` | int | ANO | ((0)) |  |
| 31 | `Sestava2_Delka` | int | ANO | ((0)) |  |
| 32 | `Sestava2_Obvod` | numeric(18,6) | ANO | ((0)) |  |
| 33 | `Sestava2_Povrch` | numeric(18,6) | ANO | ((0)) |  |
| 34 | `Sestava2_Objem` | numeric(18,6) | ANO | ((0)) |  |
| 35 | `Sestava2_PotrDelkaStrecFolie` | numeric(18,6) | ANO | ((0)) |  |
| 36 | `Sestava2_HmotPouzStrecFolie` | numeric(18,6) | ANO | ((0)) |  |
| 37 | `Sestava2_PouzMnRole` | numeric(18,6) | ANO | ((0)) |  |
| 38 | `Sestava2_ObalMat_KartRittal` | numeric(18,6) | ANO | ((0)) |  |
| 39 | `Sestava2_ObalMat_VlnLepenkaJunker_delka` | numeric(18,6) | ANO | ((0)) |  |
| 40 | `Sestava2_ObalMat_VlnLepenkaJunker_hmot` | numeric(18,6) | ANO | ((0)) |  |
| 41 | `Sestava2_MnObalMat_VlnLepenkaJunker` | numeric(18,6) | ANO | ((0)) |  |
| 42 | `Sestava2_ObalMat_VlnLepenkaEC_delka` | numeric(18,6) | ANO | ((0)) |  |
| 43 | `Sestava2_ObalMat_VlnLepenkaEC_hmot` | numeric(18,6) | ANO | ((0)) |  |
| 44 | `Sestava2_MnObalMat_VlnLepenkaEC` | numeric(18,6) | ANO | ((0)) |  |
| 45 | `Sestava2_ObalMat_RohVystuze` | numeric(18,6) | ANO | ((0)) |  |
| 46 | `Sestava2_PocetKrabic1` | int | ANO | ((0)) |  |
| 47 | `Sestava2_PocetKrabic2` | int | ANO | ((0)) |  |
| 48 | `Sestava2_PocetKrabic3` | int | ANO | ((0)) |  |
| 49 | `Sestava2_PocetKrabic4` | int | ANO | ((0)) |  |
| 50 | `Sestava2_HmKrabicPribal` | numeric(18,6) | ANO | ((0)) |  |
| 51 | `Sestava2_PocetEuropalet` | int | ANO | ((0)) |  |
| 52 | `Sestava2_PocetPaletRittal` | int | ANO | ((0)) |  |
| 53 | `Sestava2_PocetPaletMensiZbozi` | int | ANO | ((0)) |  |
| 54 | `Sestava2_CelkHmPouzPalet` | numeric(18,6) | ANO | ((0)) |  |
| 55 | `Zasilka1_Vyska` | int | ANO | ((0)) |  |
| 56 | `Zasilka1_Sirka` | int | ANO | ((0)) |  |
| 57 | `Zasilka1_Delka` | int | ANO | ((0)) |  |
| 58 | `Zasilka1_Obvod` | numeric(18,6) | ANO | ((0)) |  |
| 59 | `Zasilka1_Povrch` | numeric(18,6) | ANO | ((0)) |  |
| 60 | `Zasilka1_Objem` | numeric(18,6) | ANO | ((0)) |  |
| 61 | `Zasilka1_ObalMat_KartRittal` | numeric(18,6) | ANO | ((0)) |  |
| 62 | `Zasilka1_ObalMat_VlnLepenkaJunker_delka` | numeric(18,6) | ANO | ((0)) |  |
| 63 | `Zasilka1_ObalMat_VlnLepenkaJunker_hmot` | numeric(18,6) | ANO | ((0)) |  |
| 64 | `Zasilka1_MnObalMat_VlnLepenkaJunker` | numeric(18,6) | ANO | ((0)) |  |
| 65 | `Zasilka1_ObalMat_VlnLepenkaEC_delka` | numeric(18,6) | ANO | ((0)) |  |
| 66 | `Zasilka1_ObalMat_VlnLepenkaEC_hmot` | numeric(18,6) | ANO | ((0)) |  |
| 67 | `Zasilka1_MnObalMat_VlnLepenkaEC` | numeric(18,6) | ANO | ((0)) |  |
| 68 | `Zasilka1_PocetEuropalet` | int | ANO | ((0)) |  |
| 69 | `Zasilka1_PocetPaletRittal` | int | ANO | ((0)) |  |
| 70 | `Zasilka1_PocetPaletMensiZbozi` | int | ANO | ((0)) |  |
| 71 | `Zasilka1_CelkHmPouzPalet` | numeric(18,6) | ANO | ((0)) |  |
| 72 | `Zasilka1_HmVystelMat_PevnPapir` | numeric(18,6) | ANO | ((0)) |  |
| 73 | `Zasilka1_HmVystelMat_VzduchPolstare` | numeric(18,6) | ANO | ((0)) |  |
| 74 | `Zasilka1_HmVystelMat_PolystKousky` | numeric(18,6) | ANO | ((0)) |  |
| 75 | `Zasilka2_Vyska` | int | ANO | ((0)) |  |
| 76 | `Zasilka2_Sirka` | int | ANO | ((0)) |  |
| 77 | `Zasilka2_Delka` | int | ANO | ((0)) |  |
| 78 | `Zasilka2_Obvod` | numeric(18,6) | ANO | ((0)) |  |
| 79 | `Zasilka2_Povrch` | numeric(18,6) | ANO | ((0)) |  |
| 80 | `Zasilka2_Objem` | numeric(18,6) | ANO | ((0)) |  |
| 81 | `Zasilka2_ObalMat_KartRittal` | numeric(18,6) | ANO | ((0)) |  |
| 82 | `Zasilka2_ObalMat_VlnLepenkaJunker_delka` | numeric(18,6) | ANO | ((0)) |  |
| 83 | `Zasilka2_ObalMat_VlnLepenkaJunker_hmot` | numeric(18,6) | ANO | ((0)) |  |
| 84 | `Zasilka2_MnObalMat_VlnLepenkaJunker` | numeric(18,6) | ANO | ((0)) |  |
| 85 | `Zasilka2_ObalMat_VlnLepenkaEC_delka` | numeric(18,6) | ANO | ((0)) |  |
| 86 | `Zasilka2_ObalMat_VlnLepenkaEC_hmot` | numeric(18,6) | ANO | ((0)) |  |
| 87 | `Zasilka2_MnObalMat_VlnLepenkaEC` | numeric(18,6) | ANO | ((0)) |  |
| 88 | `Zasilka2_PocetEuropalet` | int | ANO | ((0)) |  |
| 89 | `Zasilka2_PocetPaletRittal` | int | ANO | ((0)) |  |
| 90 | `Zasilka2_PocetPaletMensiZbozi` | int | ANO | ((0)) |  |
| 91 | `Zasilka2_CelkHmPouzPalet` | numeric(18,6) | ANO | ((0)) |  |
| 92 | `Zasilka2_HmVystelMat_PevnPapir` | numeric(18,6) | ANO | ((0)) |  |
| 93 | `Zasilka2_HmVystelMat_VzduchPolstare` | numeric(18,6) | ANO | ((0)) |  |
| 94 | `Zasilka2_HmVystelMat_PolystKousky` | numeric(18,6) | ANO | ((0)) |  |
| 95 | `DelkaMiralonu_SpecificZasilku` | numeric(18,6) | ANO | ((0)) |  |
| 96 | `HmotMiralonu_SpecificZasilku` | numeric(18,6) | ANO | ((0)) |  |
| 97 | `DelkaBubFolie_SpecificZasilku` | numeric(18,6) | ANO | ((0)) |  |
| 98 | `HmotBubFolie_SpecificZasilku` | numeric(18,6) | ANO | ((0)) |  |
| 99 | `Hotovo` | bit | ANO |  |  |
| 100 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 101 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 102 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 103 | `DatZmeny` | datetime | ANO |  |  |
| 104 | `Zeme` | nvarchar(3) | ANO |  |  |

## Indexy

- **PK** `PK_EC_OdpadHosp_Zakazky` (CLUSTERED) — `ID`
