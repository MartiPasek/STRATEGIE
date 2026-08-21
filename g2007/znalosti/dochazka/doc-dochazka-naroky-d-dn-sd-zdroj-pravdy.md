# Naroky na dovolenou, dovolenou navic a sick days - kde ziji a co se zmenilo 13. 8. 2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> ⚠️ **DOPLNĚNO 19. 8. 2026 (Claude-28, schválila Marti-AI). Obsah pod tímto rámečkem jsem needitoval.**
> Od 19. 8. 2026 večer **`tenant.staff_cond` už není tabulka, ale POHLED.** Osobní hodnoty podmínek
> fyzicky žijí ve smlouvě (`tenant.engagement`, sloupce `pod_*` + `pod_meta`) a verzují se s ní.
> Skupinové a systémové výchozí hodnoty se **20. 8. 2026 přejmenovaly na `tenant.podminky_vychozi`**
> (dřív `staff_cond_zaklad`) a slouží už jen jako číselník výchozích hodnot — osobní řádky tam nepatří.
> **Doplněno 20. 8. 2026 (Claude-28, schválila Marti-AI):** od kroku 3a má každý člověk všechny hodnoty
> zapsané u sebe ve smlouvě, takže pohled `staff_cond` vrací **jen osobní řádky**, a spouštěč
> `trg_staff_cond_default_dovolena` na `att_employee` byl **ZRUŠEN** — nahradil ho `engagement_pod_defaults`
> na smlouvě.
> **Čtení i zápis přes `tenant.staff_cond` funguje dál úplně stejně** — ověřeno porovnáním otisků
> před a po (294 řádků i 1248 vyřešených hodnot bez rozdílu), takže **text níže platí dál**;
> změnilo se jen to, kde data fyzicky leží. Kdo bude sahat na strukturu nebo na spouštěče,
> ať si nejdřív přečte znalost **`doc-dochazka-podminky-slouceny-se-smlouvou`**.

---


## Kde naroky ziji (stav po 13. 8. 2026)

**Zdroj pravdy pro vypocet = `tenant.engagement_entitlement`** (kody `dovolena_standard`, `dovolena_navic`, `dovolena_vernost_10let`, `sick_days_standard`, `sick_days_navic`). Odtud pocita prehled **Narok a cerpani** (`g2007.python att_narok_cerpani`, stranka /dochazka-narok) i hlavicka karty zamestnance (`/app/hr/person-leave`).

**`tenant.staff_cond`** (kody `dovolena_dni`, `sick_days_rok`) je to, co se ukazuje v **karte zamestnance > dlazdice Podminky** a v mobilu v **Moje podminky**. Ma tri patra: vlastni (`scope_kind='user'`) > skupina (`group`) > system (`system`). **Do vypoctu naroku nevstupuje** - je to informativni udaj.

**`tenant.holiday_balance.narok_h`** je VYPLN, ne vypocet - 79 lidi tam melo natvrdo 200 h. Nepouzivat, viz komentar v `_abs_recalc_balances`.

## Co se zmenilo 13. 8. 2026 (zadal Jirka, schvalila Marti-AI)

**1. Kazdy clovek ma vlastni radek dovolene.** Do 13. 8. melo vlastni hodnotu jen 17 lidi a zbylych 57 spadalo na systemovou hodnotu 25 - vcetne OSVC a dohodaru, kteri narok NEMAJI. Doplneno 56 radku (17 unikatnich s nulou, 39 s 25, Veverka 26; Marti Pasek ma dve cisla zamestnance ale jedno user_id, proto 56 a ne 57). Hodnoty prevzaty z `engagement_entitlement`.

**2. Trigger `trg_staff_cond_default_dovolena`** na `tenant.att_employee` (AFTER INSERT OR UPDATE OF user_id) zaklada novemu cloveku radek `dovolena_dni='0'` *(ZRUSENO 20.8.2026 - nahrazen spoustecem engagement_pod_defaults na smlouve)*. Duvod pro trigger misto uprav v kode - zamestnanec vznika na 29 mistech (8x router.py + 21 funkci v g2007.python s vlastni kopii `_att_employee`), clovek vznikne i prvnim pichnutim v mobilu. Trigger je idempotentni a ma EXCEPTION blok, aby nikdy neshodil zalozeni cloveka.

**3. Sync z Centraly uz nesaha na naroky ani nezaklada zamestnance** (`_sync_fin_from_ec`, commit 26cdc7d7). `ent_map` je prazdna mapa, `emp_id()` neznameho cloveka nezaklada, ale preskoci a vypise ho ve vysledku (`preskoceni_cisla`, `_msg`). Mzdove slozky a verze smluv chodi z Centraly DAL - ty Jirka zastavit nechtel.

## Znama past - vernostni den zapocitany dvakrat (NEOPRAVENO k 13. 8.)

Automat `_hr_vernost_dovolena` (Sarka 5. 8. 2026) pridava +1 den za 10 let ve firme, ale **nekontroluje, jestli uz ten den v naroku neni**. U ctyr lidi byl - Sarka ho do Centraly zadala uz drive (u Havlata v roce 2021, doklad je v poznamce smlouvy "1 den dovolene navic za 10 let ve firme" a soucasnem skoku 25 > 26). Dusledek: **Havlat 27 misto 26, Honomichl 27 misto 26, Honal 7 misto 6, Kilberger 7 misto 6**. U Veverky (14) vernostni den pridan take, ale v poznamce smlouvy zminka neni - nelze rozseknout z dat, patri Sarce k provereni.
Automat **bezi dal** - komu pristi vyjde 10 let a bude to mit v Centrale zapocitane, dostane den navic znovu neopravnene. Ceka na potvrzeni Sarkou pred opravou dat.

## Otevrene veci

- **`sick_days_rok` ma stejnou tichou systemovou hodnotu** (2 dny) a spada na ni 56 lidi. Resi se az v dalsim kroku - trigger i doplneni radku se udelaji stejne jako u dovolene.
- **Migrace `_sync_fin_from_ec` do g2007.python** zustava jako technicky dluh. Zmena z 13. 8. sla vyjimecne primo do router.py (schvalila Marti-AI) - duvod: slo o ODEBRANI dvou schopnosti, ne pridani logiky, a migrace 250radkove funkce hybajici mzdovymi slozkami by byla nepomerne vetsi riziko.
- **Duplicitni zaznamy dochazky** - tyz den zapsany z mobilu i z Centraly (Urbanova 10. 8. sickday 16 h misto 8, Maresova 30. 6. 12 h misto 8). Ceka na potvrzeni Jirkou pred smazanim.

