# DOC-09 Politika rizeni pristupu

> oblast: `iso27001` · úroveň: obor · typ: smernice · verze: V1.0 · rozsah: globální (všichni tenanti)

DOC-09

Politika řízení přístupů

STRATEGIE - System s.r.o. — Systém řízení bezpečnosti informací (ISMS)

IČO 23365544 · Nad Týncem 1192/10, Doubravka, 312 00 Plzeň · sp. zn. C 46859, KS v Plzni

| Kód dokumentu | DOC-09 |

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

Politika stanovuje pravidla pro přidělování, používání a odebírání přístupů. Pokrývá A.5.15–A.5.18, A.8.2–A.8.5.

# 2. Zásady

Princip nejnižších oprávnění.

Role a oprávnění (zaměstnanec / člen / rodič-admin) a ACL na úrovni tenantu a dat.

Jednoznačná identita; sdílené účty se nepoužívají.

Need-to-know — citlivá data mimo kontext zobrazena omezeně („[omezeno]“).

# 3. Životní cyklus přístupu

Vznik — při nástupu dle role; aktivace přes e-mail/SMS ověření.

Změna — při změně role se práva upraví bez odkladu.

Zánik — při ukončení do 24 hodin.

# 4. Autentizace

Vícefaktorové ověření (magic-link e-mailem / SMS).

Tajemství a tokeny uloženy šifrovaně (trezor); nelogují se v čitelné podobě.

Citlivé operace chráněny dodatečným PIN / 2FA.

# 5. Privilegované přístupy

Administrátorská a rodičovská oprávnění oddělena a přidělena jen nezbytným osobám. Citlivé změny přes schvalovací proces se stopou, zaznamenány v audit logu.

# 6. Přezkum přístupů

Přístupová práva se přezkoumávají nejméně jednou za 6 měsíců a po každé organizační změně. Nepotřebné účty a práva se odebírají.

# 7. Schválení

Schválil: Marti Pašek, jednatel             Datum: 15. 8. 2026             Podpis: ............................

