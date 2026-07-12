# DOC-12 Bezpecnost dodavatelu

> oblast: `iso27001` · úroveň: obor · typ: smernice · verze: V1.0 · rozsah: globální (všichni tenanti)

DOC-12

Bezpečnost dodavatelů a cloudu

STRATEGIE - System s.r.o. — Systém řízení bezpečnosti informací (ISMS)

IČO 23365544 · Nad Týncem 1192/10, Doubravka, 312 00 Plzeň · sp. zn. C 46859, KS v Plzni

| Kód dokumentu | DOC-12 |

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

Politika stanovuje pravidla pro bezpečnost ve vztazích s dodavateli a poskytovateli služeb. Pokrývá opatření A.5.19–A.5.23 přílohy A.

# 2. Výběr a hodnocení

Před zahájením spolupráce se posuzuje bezpečnostní úroveň dodavatele přiměřeně rizikům (certifikace, smluvní záruky, reference).

U klíčových služeb se upřednostňují poskytovatelé s prokazatelnou úrovní zabezpečení (např. ISO 27001 / SOC 2).

# 3. Smluvní požadavky

Důvěrnost a ochrana osobních údajů (zpracovatelská smlouva dle GDPR, je-li relevantní).

Bezpečnostní povinnosti, hlášení incidentů a součinnost.

Vymezení odpovědností a ukončení (vrácení/výmaz dat).

# 4. Klíčoví dodavatelé

| Služba | Poskytovatel | Bezpečnostní aspekt |

| Cloud hosting | ČMIS, Praha (ČR) | Provoz serverů, fyzická bezpečnost DC, dostupnost |

| SMS brána | Vlastní (vlastní SIM) | Doručení ověřovacích a notifikačních SMS |

| E-mail / Exchange | [DOPLNIT] | Doručování e-mailů, magic-link přihlášení |

| AI / LLM služba | Anthropic – Claude (Sonnet, Opus 4.8) | Rozsah dat předávaných do modelu — viz bod 6 |

| Distribuce aplikací | Apple, Google | Publikace mobilních aplikací |

# 5. Monitorování a změny

Služby klíčových dodavatelů a jejich změny se průběžně sledují. Významné změny (rozsah služby, subdodavatelé, lokalita dat) se posuzují z pohledu rizik.

# 6. Cloud a AI služby

Provoz platformy probíhá v cloudu; odpovědnosti za bezpečnost jsou sdíleny s poskytovatelem (shared responsibility). U AI/LLM služeb se omezuje rozsah citlivých dat předávaných mimo prostředí a posuzují se podmínky zpracování dat — [DOPLNIT konkrétní pravidla].

# 7. Schválení

Schválil: Marti Pašek, jednatel             Datum: 15. 8. 2026             Podpis: ............................

