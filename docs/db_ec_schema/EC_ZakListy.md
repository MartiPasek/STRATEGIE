# EC_ZakListy

**Schema**: dbo · **Cluster**: Other · **Rows**: 3,417 · **Size**: 1.73 MB · **Sloupců**: 155 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(10) | NE |  |  |
| 3 | `PocetHodin` | int | ANO |  |  |
| 4 | `TerminDodaniMaterialu` | datetime | ANO |  |  |
| 5 | `TerminDoruceniKZak` | datetime | ANO |  |  |
| 6 | `KompletniObjednani` | bit | ANO |  |  |
| 7 | `Barva` | nvarchar(20) | ANO |  |  |
| 8 | `TerminDodaniSkrine` | datetime | ANO |  |  |
| 9 | `ViceSvorek` | bit | ANO |  |  |
| 10 | `ViceSvorekPoznamka` | nvarchar(255) | ANO |  |  |
| 11 | `ViceVyvodek` | bit | ANO |  |  |
| 12 | `ViceVyvodekPoznamka` | nvarchar(255) | ANO |  |  |
| 13 | `NestBarvyVod` | bit | ANO |  |  |
| 14 | `NestBarvyVodPoznamka` | nvarchar(255) | ANO |  |  |
| 15 | `ProdlozenaZaruka` | bit | ANO |  |  |
| 16 | `ProdlozenaZarukaPoznamka` | nvarchar(255) | ANO |  |  |
| 17 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 18 | `KontaktniOsobaZak` | nvarchar(30) | ANO |  |  |
| 19 | `Beistellung` | nvarchar(255) | ANO |  |  |
| 20 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 21 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 22 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 23 | `DatZmeny` | datetime | ANO |  |  |
| 24 | `Napeti` | int | ANO |  |  |
| 25 | `PracovniNapeti` | int | ANO |  |  |
| 26 | `IzolacniNapeti` | int | ANO |  |  |
| 27 | `ImpulzniVydrzneNapeti` | int | ANO |  |  |
| 28 | `ProudRozvadece` | int | ANO |  |  |
| 29 | `ProudObvodu` | int | ANO |  |  |
| 30 | `VydrznyProud` | nvarchar(50) | ANO |  |  |
| 31 | `ZkratovyProud` | nvarchar(50) | ANO |  |  |
| 32 | `SoucinitelSoudobosti` | numeric(19,6) | ANO |  |  |
| 33 | `Kmitocet` | int | ANO |  |  |
| 34 | `UzemnovaciSoustava` | nvarchar(10) | ANO |  |  |
| 35 | `StupenOchrany` | nvarchar(100) | ANO |  |  |
| 36 | `UrceniPouzivani` | nvarchar(100) | ANO |  |  |
| 37 | `StupenZnecisteni` | nvarchar(20) | ANO |  |  |
| 38 | `ElektromagnetickaKompatibilita` | nvarchar(50) | ANO |  |  |
| 39 | `VnejsiKonstrukce1` | nvarchar(20) | ANO |  |  |
| 40 | `VnejsiKonstrukce2` | nvarchar(20) | ANO |  |  |
| 41 | `TypSkrine` | nvarchar(50) | ANO |  |  |
| 42 | `UmisteniInstalace` | nvarchar(20) | ANO |  |  |
| 43 | `Stabilita` | nvarchar(20) | ANO |  |  |
| 44 | `TypKonstrukce` | nvarchar(30) | ANO |  |  |
| 45 | `Jisteni` | nvarchar(20) | ANO |  |  |
| 46 | `OchranaPredUrazem` | nvarchar(100) | ANO |  |  |
| 47 | `Rozmery` | nvarchar(100) | ANO |  |  |
| 48 | `Hmotnost` | numeric(19,6) | ANO |  |  |
| 49 | `Teplota` | nvarchar(20) | ANO |  |  |
| 50 | `ProvozníPodmínky` | nvarchar(100) | ANO | ('Žádné') |  |
| 51 | `Par_1` | bit | ANO | ((1)) |  |
| 52 | `Par_2` | bit | ANO | ((1)) |  |
| 53 | `Par_3` | bit | ANO | ((1)) |  |
| 54 | `Par_4` | bit | ANO | ((1)) |  |
| 55 | `Par_5` | bit | ANO | ((1)) |  |
| 56 | `Par_6` | bit | ANO | ((1)) |  |
| 57 | `Par_7` | bit | ANO | ((1)) |  |
| 58 | `Par_8` | bit | ANO | ((1)) |  |
| 59 | `Par_9` | bit | ANO | ((1)) |  |
| 60 | `Par_10` | bit | ANO | ((1)) |  |
| 61 | `Par_11` | bit | ANO | ((1)) |  |
| 62 | `Par_12` | bit | ANO | ((1)) |  |
| 63 | `Par_13` | bit | ANO | ((1)) |  |
| 64 | `Par_14` | bit | ANO | ((1)) |  |
| 65 | `Par_15` | nvarchar(100) | ANO | ('30-35cm') |  |
| 66 | `Par_16` | bit | ANO | ((1)) |  |
| 67 | `Par_17` | bit | ANO | ((0)) |  |
| 68 | `Par_18` | nvarchar(1000) | ANO |  |  |
| 69 | `Par_19` | nvarchar(1000) | ANO |  |  |
| 70 | `Par_20` | nvarchar(1000) | ANO |  |  |
| 71 | `Par_21` | nvarchar(1000) | ANO |  |  |
| 72 | `Par_22` | nvarchar(1000) | ANO |  |  |
| 73 | `Par_23` | nvarchar(1000) | ANO |  |  |
| 74 | `Par_24` | nvarchar(1000) | ANO |  |  |
| 75 | `Par_25` | nvarchar(1000) | ANO |  |  |
| 76 | `Par_26` | nvarchar(1000) | ANO |  |  |
| 77 | `Par_27` | nvarchar(1000) | ANO |  |  |
| 78 | `Par_28` | nvarchar(1000) | ANO |  |  |
| 79 | `Par_29` | nvarchar(1000) | ANO |  |  |
| 80 | `Par_30` | nvarchar(1000) | ANO |  |  |
| 81 | `Par_31` | nvarchar(1000) | ANO |  |  |
| 82 | `Par_32` | nvarchar(1000) | ANO |  |  |
| 83 | `Par_33` | nvarchar(1000) | ANO |  |  |
| 84 | `Par_34` | nvarchar(1000) | ANO |  |  |
| 85 | `Par_35` | nvarchar(1000) | ANO |  |  |
| 86 | `Par_36` | nvarchar(1000) | ANO |  |  |
| 87 | `Par_37` | nvarchar(1000) | ANO |  |  |
| 88 | `Par_38` | nvarchar(1000) | ANO |  |  |
| 89 | `Par_39` | nvarchar(1000) | ANO |  |  |
| 90 | `Par_40` | nvarchar(1000) | ANO |  |  |
| 91 | `Par_41` | nvarchar(1000) | ANO |  |  |
| 92 | `Par_42` | nvarchar(1000) | ANO |  |  |
| 93 | `Par_43` | nvarchar(1000) | ANO |  |  |
| 94 | `Par_44` | nvarchar(1000) | ANO |  |  |
| 95 | `Par_45` | nvarchar(1000) | ANO |  |  |
| 96 | `Par_46` | nvarchar(1000) | ANO |  |  |
| 97 | `Par_47` | nvarchar(1000) | ANO |  |  |
| 98 | `Par_48` | nvarchar(1000) | ANO |  |  |
| 99 | `Par_49` | nvarchar(1000) | ANO |  |  |
| 100 | `Par_50` | nvarchar(1000) | ANO |  |  |
| 101 | `Par_51` | nvarchar(1000) | ANO |  |  |
| 102 | `Par_52` | nvarchar(1000) | ANO |  |  |
| 103 | `Par_53` | nvarchar(1000) | ANO |  |  |
| 104 | `Par_54` | nvarchar(1000) | ANO |  |  |
| 105 | `Par_55` | nvarchar(1000) | ANO |  |  |
| 106 | `Par_56` | nvarchar(1000) | ANO |  |  |
| 107 | `Par_57` | nvarchar(1000) | ANO |  |  |
| 108 | `Par_58` | nvarchar(1000) | ANO |  |  |
| 109 | `Par_59` | nvarchar(1000) | ANO |  |  |
| 110 | `Par_60` | nvarchar(1000) | ANO |  |  |
| 111 | `Par_61` | nvarchar(1000) | ANO |  |  |
| 112 | `Par_62` | nvarchar(1000) | ANO |  |  |
| 113 | `Par_63` | nvarchar(1000) | ANO |  |  |
| 114 | `Par_64` | nvarchar(1000) | ANO |  |  |
| 115 | `Par_65` | nvarchar(1000) | ANO |  |  |
| 116 | `Par_66` | nvarchar(1000) | ANO |  |  |
| 117 | `Par_67` | nvarchar(1000) | ANO |  |  |
| 118 | `Par_68` | nvarchar(1000) | ANO |  |  |
| 119 | `Par_69` | nvarchar(1000) | ANO |  |  |
| 120 | `Par_70` | nvarchar(1000) | ANO |  |  |
| 121 | `Par_71` | nvarchar(1000) | ANO |  |  |
| 122 | `Par_72` | nvarchar(1000) | ANO |  |  |
| 123 | `Par_73` | nvarchar(1000) | ANO |  |  |
| 124 | `Par_74` | nvarchar(1000) | ANO |  |  |
| 125 | `Par_75` | nvarchar(1000) | ANO |  |  |
| 126 | `Par_76` | nvarchar(1000) | ANO |  |  |
| 127 | `Par_77` | nvarchar(1000) | ANO |  |  |
| 128 | `Par_78` | nvarchar(1000) | ANO |  |  |
| 129 | `Par_79` | nvarchar(1000) | ANO |  |  |
| 130 | `Par_80` | nvarchar(1000) | ANO |  |  |
| 131 | `Par_81` | nvarchar(1000) | ANO |  |  |
| 132 | `Par_82` | nvarchar(1000) | ANO |  |  |
| 133 | `Par_83` | nvarchar(1000) | ANO |  |  |
| 134 | `Par_84` | nvarchar(1000) | ANO |  |  |
| 135 | `Par_85` | nvarchar(1000) | ANO |  |  |
| 136 | `Par_86` | nvarchar(1000) | ANO |  |  |
| 137 | `Par_87` | nvarchar(1000) | ANO |  |  |
| 138 | `Par_88` | nvarchar(1000) | ANO |  |  |
| 139 | `Par_89` | nvarchar(1000) | ANO |  |  |
| 140 | `Par_90` | nvarchar(1000) | ANO |  |  |
| 141 | `Par_91` | nvarchar(1000) | ANO |  |  |
| 142 | `Par_92` | nvarchar(1000) | ANO |  |  |
| 143 | `Par_93` | nvarchar(1000) | ANO |  |  |
| 144 | `Par_94` | nvarchar(1000) | ANO |  |  |
| 145 | `Par_95` | nvarchar(1000) | ANO |  |  |
| 146 | `Par_96` | nvarchar(1000) | ANO |  |  |
| 147 | `Par_97` | nvarchar(1000) | ANO |  |  |
| 148 | `Par_98` | nvarchar(1000) | ANO |  |  |
| 149 | `Par_99` | nvarchar(1000) | ANO |  |  |
| 150 | `Par_100` | nvarchar(1000) | ANO |  |  |
| 151 | `Vzor` | bit | ANO | ((0)) |  |
| 152 | `NazevVzoru` | nvarchar(100) | ANO |  |  |
| 153 | `OvereniNavrhuUzavreno` | bit | ANO | ((0)) |  |
| 154 | `Chlazeni` | nvarchar(100) | ANO |  |  |
| 155 | `ChlazeniText` | nvarchar(100) | ANO |  |  |

## Indexy

- **PK** `PK_EC_ZakListy` (CLUSTERED) — `ID`
