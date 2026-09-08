# DOC-07 Plan osetreni rizik

> oblast: `iso27001` · úroveň: obor · typ: smernice · verze: V1.0 · rozsah: globální (všichni tenanti)

DOC-07

Plán ošetření rizik

STRATEGIE - System s.r.o. — Systém řízení bezpečnosti informací (ISMS)

IČO 23365544 · Nad Týncem 1192/10, Doubravka, 312 00 Plzeň · sp. zn. C 46859, KS v Plzni

| Kód dokumentu | DOC-07 |

| Verze | 0.1 (návrh) |

| Datum vydání | 15. 8. 2026 |

| Klasifikace | Interní |

| Vlastník dokumentu | Marti Pašek (jednatel) |

| Schválil | Marti Pašek (jednatel) |

| Platnost od | 15. 8. 2026 |

Historie revizí

| Verze | Datum | Popis změny | Autor |

| 0.1 | 15. 8. 2026 | Prvotní návrh | STRATEGIE / Claude |

# 1. Účel

Plán stanovuje opatření ke snížení rizik z DOC-05, jejich vazbu na opatření přílohy A (DOC-06) a termíny. Stav vyhodnocuje manažer ISMS.

# 2. Plán ošetření

| ID | Opatření ke snížení rizika | Opatření přílohy A | Termín / stav |

| R-01 | Řízení přístupů (role/ACL), šifrování trezoru, MFA, audit log | A.5.15, A.8.3, A.8.5, A.8.24, A.8.15 | Zavedeno |

| R-02 | Denní zálohy (03:00) + testovaná obnova; offsite kopie a šifrování záloh | A.8.13, A.8.14 | Offsite+šifrování do 30. 6. 2026 |

| R-03 | Vysoká dostupnost (blue-green), monitoring | A.8.14, A.8.16 | Zavedeno / sledováno |

| R-04 | MFA, nejnižší oprávnění, přezkum přístupů | A.5.15, A.5.17, A.5.18, A.8.5 | Přezkum přístupů 1×/6 měsíců |

| R-05 | Bezpečný vývoj, správa zranitelností, kontrola závislostí | A.8.25, A.8.8, A.8.28 | Průběžně |

| R-06 | Antivir ESET (EUROSOFT-System), oddělení od záloh; šifrování stanic | A.8.7, A.8.13 | ESET zaveden; šifrování do 31. 7. 2026 |

| R-07 | SLA s poskytovatelem ČMIS, zálohy mimo prostředí | A.5.19–A.5.22, A.8.13 | Při uzavření smlouvy |

| R-08 | Pravidelný test obnovy, oddělená (offsite) kopie | A.8.13, A.8.14 | Měsíčně |

| R-09 | Schvalovací proces změn, audit log, zálohy | A.8.32, A.8.15 | Zavedeno |

| R-10 | Výběr a hodnocení dodavatelů, smluvní požadavky | A.5.19–A.5.23 | Při sjednání |

| R-11 | Omezení dat do AI/LLM (Anthropic – Claude), smluvní podmínky | A.5.19, A.8.10, A.5.34 | Posoudit do 31. 7. 2026 |

| R-12 | Dokumentace, znalostní báze, řízené sdílení přístupů | A.5.2, A.5.37, A.6.1 | Průběžně |

| R-13 | Na stanicích nejsou zákaznická data; antivir; šifrování disků | A.7.9, A.8.1, A.8.13 | Šifrování do 31. 7. 2026 |

| R-14 | Zpracovatelské smlouvy (DPA), klasifikace a retence | A.5.34, A.5.12, A.5.33 | Do 31. 7. 2026 |

# 3. Zbytková rizika a akceptace

Po zavedení opatření manažer ISMS přehodnotí zbytkové riziko. Zbytková rizika 15–25 schvaluje vedení. Záznam akceptace: [DOPLNIT — datum].

# 4. Schválení

Schválil: Marti Pašek, jednatel             Datum: 15. 8. 2026             Podpis: ............................

