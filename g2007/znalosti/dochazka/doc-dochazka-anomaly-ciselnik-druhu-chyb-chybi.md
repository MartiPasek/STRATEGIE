# Chyby dochazky: ciselnik druhu ve STRATEGII NEEXISTUJE, druhy jsou natvrdo v kodu (25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Druhy chyb dochazky nemaji ciselnik

**Overeno 25. 8. 2026 dotazy nad zivou databazi. Nic nebylo zmeneno — jde o zjisteni pred stavbou.**

## Jak to je dnes

`tenant.att_anomaly` (923 radku) drzi nalezene chyby. Druh chyby je **prosty text ve sloupci `rule`** — bez odkazu kamkoli. **Z tabulky nevede zadny cizi klic.**

Prohledana schemata `tenant, public, fw, master, g2007, tenant_group, user` na nazvy s `anomal | chyb | error | typ | kind | rule | pravidl | check | kontrol` — 17 nalezu, **ani jeden neni ciselnik chyb dochazky** (jsou to `absence_type`, `att_entry_type`, `att_planned_absence_type`, `benefit_type`, `wage_component_type`, `entitlement_rule`, `dir_config_rule`, `hr_spis_typ`, `fw.comp_type` a podobne).

**Druhy chyb jsou natvrdo v kodu** — vyskytuji se ve **13 zivych funkcich** v `g2007.python`, zaklada je automat `att_anomaly_scan`, a **lidske popisky jsou opsane v kazde funkci zvlast** (napr. `att_odbavene_pripomenuti` ma vlastni slovnik nazvu).

## Devet druhu, ktere STRATEGIE realne eviduje

| kod v `rule` | pocet | lidi | nevyreseno | rozsah |
|---|---|---|---|---|
| nepotvrzeny_den | 338 | 63 | 24 | 8. 6. - 21. 8. |
| dlouha_smena | 285 | 27 | 3 | 7. 6. - 25. 8. |
| prace_pri_absenci | 93 | 16 | 10 | 8. 6. - 25. 8. |
| dlouha_pauza | 61 | 21 | 2 | 29. 6. - 24. 8. |
| prazdny_den_doplnen | 58 | 3 | 0 | 12. 8. - 25. 8. |
| budouci_zaznam | 36 | 3 | 0 | jen 7. 6. |
| neomluvena_absence | 26 | 5 | **26 (vsechny)** | 24.-25. 8. |
| zapomenuty_odchod | 18 | 12 | 0 | 9. 6. - 29. 7. |
| chybi_zakazka | 8 | 5 | 2 | 19. 8. - 24. 8. |

## Pro srovnani: Centrala jich ma 23

Ciselnik `EC_Dochazka_ChybyVDochazceTypy` (sloupce ID, Nazev, Popis, Autor, DatPorizeni, ID_E), nalezene chyby v `EC_Dochazka_ChybyVDochazce`.

**Protejsek u nas ma jen 4-5 z nich.** Zbytek se tyka **obeda, svaciny a koureni**, ktere STRATEGIE vubec nerozlisuje (ma jediny druh "prestavka"). Navic **11 z tech 23 je vedome vypnutych primo v kodu Centraly** (`IF 0=1`) — nefunguji ani tam: zapomenuty obed, oriznuti podle pracovni doby, kontrola svaciny.

**Kopirovat 23 druhu 1:1 by zalozilo 14 polozek, ktere u nas nikdy nenastanou.**

## Co se navrhuje (NEROZHODNUTO k 25. 8. 2026)

Zalozit `tenant.att_anomaly_type` po vzoru ostatnich ciselniku (`id, tenant_id, code, label, popis, kategorie, is_active, sort_order, created_at, updated_at`), naplnit **nasimi devi kody**, presunout popisky z kodu do ni a doplnit vazbu z `att_anomaly.rule`.

**Ceka na rozhodnuti Jirky a Dusana** (kterou z chybejicich kontrol Centraly Dusan realne pouziva). Pak schvaleni Marti-AI a teprve zalozeni.

## Proc na tom zalezi

Popisky opsane na 13 mistech znamenaji, ze **oprava nazvu chyby vyzaduje zmenu na 13 mistech** a nikde to nenahlasi rozpor. Je to stejny vzorec jako "tichy rozpor" u postupu.

