# DOC-14 Bezpecny vyvoj a zmeny

> oblast: `iso27001` · úroveň: obor · typ: smernice · verze: V1.0 · rozsah: globální (všichni tenanti)

DOC-14

Bezpečný vývoj a řízení změn

STRATEGIE - System s.r.o. — Systém řízení bezpečnosti informací (ISMS)

IČO 23365544 · Nad Týncem 1192/10, Doubravka, 312 00 Plzeň · sp. zn. C 46859, KS v Plzni

| Kód dokumentu | DOC-14 |

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

Dokument stanovuje zásady bezpečného vývoje a řízení změn. Pokrývá A.8.25–A.8.29, A.8.31, A.8.32, A.8.33, A.8.4.

# 2. Zásady bezpečného vývoje

Security by design; bezpečnost součástí požadavků.

Validace vstupů, citlivá data dle role, tajemství se neukládají do kódu.

Řízený přístup ke zdrojovému kódu (git, osobní tokeny).

# 3. Oddělení prostředí

Produkce oddělena od testu.

Testovací a demo data bez reálných osobních údajů (demo tenant).

# 4. Řízení změn

Citlivé změny přes schvalovací proces se stopou.

Nasazení (deploy) řízené a zaznamenané; dohledatelné v auditu.

Kontrola před nasazením; chybné nasazení lze vrátit (blue-green).

# 5. Zranitelnosti a závislosti

Knihovny a běhové prostředí aktualizované; sledování zranitelností (A.8.8).

Bezpečnostní testování před vydáním. Externí pentest zatím neproběhl — plánováno (do 30. 9. 2026). Kritické zranitelnosti se opravují v rámci dne.

# 6. Schválení

Schválil: Marti Pašek, jednatel             Datum: 15. 8. 2026             Podpis: ............................

