# DOC-05 Registr rizik

> oblast: `iso27001` · úroveň: obor · typ: smernice · verze: V1.0 · rozsah: globální (všichni tenanti)

DOC-05

Registr rizik

STRATEGIE - System s.r.o. — Systém řízení bezpečnosti informací (ISMS)

IČO 23365544 · Nad Týncem 1192/10, Doubravka, 312 00 Plzeň · sp. zn. C 46859, KS v Plzni

| Kód dokumentu | DOC-05 |

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

Registr eviduje rizika bezpečnosti informací, jejich hodnocení (dle DOC-04) a strategii ošetření. Je živým dokumentem. Míra rizika = Dopad (D) × Pravděpodobnost (P), stupnice 1–5.

# 2. Registr rizik

| ID | Riziko / hrozba | D | P | Míra | Strategie a opatření |

| R-01 | Únik osobních / mzdových dat (neoprávněný přístup) | 5 | 3 | 15 | Snížit: role/ACL, šifrovaný trezor, MFA, audit log |

| R-02 | Ztráta nebo poškození dat v databázi | 5 | 2 | 10 | Snížit: denní zálohy + test obnovy, HA |

| R-03 | Výpadek dostupnosti platformy | 4 | 3 | 12 | Snížit: blue-green HA, monitoring |

| R-04 | Kompromitace účtu (phishing, krádež přihlášení) | 4 | 3 | 12 | Snížit: MFA (magic-link/SMS), nejnižší oprávnění |

| R-05 | Zranitelnost v aplikaci / závislostech | 4 | 3 | 12 | Snížit: bezpečný vývoj, aktualizace, sken |

| R-06 | Ransomware / malware na pracovní stanici | 4 | 2 | 8 | Snížit: antivir ESET (EUROSOFT-System), zálohy; šifrování disku [plánováno] |

| R-07 | Výpadek / selhání cloud poskytovatele (ČMIS) | 4 | 2 | 8 | Přenést/snížit: SLA, zálohy mimo prostředí |

| R-08 | Neobnovitelná nebo chybějící záloha | 5 | 2 | 10 | Snížit: pravidelný test obnovy, oddělená kopie |

| R-09 | Lidská chyba (smazání / chybná změna dat) | 3 | 3 | 9 | Snížit: schvalování změn, audit log, zálohy |

| R-10 | Riziko dodavatele / třetí strany | 3 | 3 | 9 | Snížit: výběr a hodnocení, smlouvy (DOC-12) |

| R-11 | Únik dat přes AI/LLM (Anthropic) | 4 | 3 | 12 | Snížit: omezení dat do LLM (Claude Sonnet/Opus), smluvní podmínky |

| R-12 | Ztráta klíčové osoby (bus factor) | 4 | 3 | 12 | Snížit: dokumentace, znalostní báze, sdílení přístupů |

| R-13 | Fyzická ztráta / krádež zařízení | 3 | 2 | 6 | Sníženo: na stanicích nejsou zákaznická data; ESET; šifrování [plánováno] |

| R-14 | Nesoulad s GDPR / legislativou | 4 | 2 | 8 | Snížit: zpracovatelské smlouvy, klasifikace, retence |

# 3. Souhrn

Přednostně se ošetřují rizika s mírou 15 (R-01) a 12 (R-03, R-04, R-05, R-11, R-12). Žádné riziko nesmí zůstat na 15–25 bez opatření nebo akceptace vedením. Hodnoty D/P jsou prvotním návrhem a budou zpřesněny při hodnocení rizik s vedením.

