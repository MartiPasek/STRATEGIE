# DOC-11 Zalohovani a kontinuita

> oblast: `iso27001` · úroveň: obor · typ: smernice · verze: V1.0 · rozsah: globální (všichni tenanti)

DOC-11

Zálohování a kontinuita činností

STRATEGIE - System s.r.o. — Systém řízení bezpečnosti informací (ISMS)

IČO 23365544 · Nad Týncem 1192/10, Doubravka, 312 00 Plzeň · sp. zn. C 46859, KS v Plzni

| Kód dokumentu | DOC-11 |

| Verze | 0.1 (návrh) |

| Datum vydání | 15. 8. 2026 |

| Klasifikace | Interní |

| Vlastník dokumentu | Marti Pašek (jednatel) |

| Schválil | Marti Pašek (jednatel) |

| Platnost od | 15. 8. 2026 |

Historie revizí

| Verze | Datum | Popis změny | Autor |

| 0.1 | 15. 8. 2026 | Prvotní návrh | STRATEGIE / Claude |

# 1. Účel a rozsah

Dokument stanovuje pravidla zálohování a kontinuity provozu. Pokrývá A.8.13, A.8.14, A.5.29, A.5.30.

# 2. Zálohování

Předmět — produkční databáze (PostgreSQL) a konfigurace.

Frekvence — denně v 03:00.

Retence — denní zálohy 30 dní (delší archivace dle potřeby).

Oddělení — offsite (oddělená) kopie se zavádí; cíl 30. 6. 2026.

Šifrování — šifrování záloh se zavádí; cíl 30. 6. 2026.

# 3. Test obnovy

Obnova se ověřuje testem nejméně jednou za měsíc; výsledek se zaznamenává. Bez úspěšného testu není záloha považována za spolehlivou.

# 4. Vysoká dostupnost

Provoz ve schématu blue-green: vedle primárního běží sekundární prostředí, na které lze přepnout; pravidelně se obnovuje z aktuálního stavu.

# 5. Cíle obnovy

RTO (cíl doby obnovy) — do 24 h.

RPO (max. ztráta dat) — do 24 h (denní záloha v 03:00).

# 6. Postup při narušení

Vyhodnocení rozsahu, aktivace obnovy / přepnutí na sekundární prostředí.

Komunikace dotčeným stranám dle závažnosti.

Obnova ze zálohy, ověření integrity, návrat do provozu.

Záznam a vyhodnocení (vstup do DOC-17 a DOC-18).

# 7. Přezkum

Parametry (RTO/RPO, retence) se přezkoumávají nejméně jednou ročně a po významné změně infrastruktury.

# 8. Schválení

Schválil: Marti Pašek, jednatel             Datum: 15. 8. 2026             Podpis: ............................

