# Dochazka: firma_id/user_id se vyplnuji uz PRI VZNIKU radku (trigger, 3.8.2026) + backfill po reimportu 31.7.

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Dochazka: firma_id a user_id se vyplnuji uz PRI VZNIKU radku

Zapsal C28 (Jirka) 3.8.2026. Vsechna cisla overena ctenim z produkcni DB pred i po zasahu.
Navazuje na [doc-dochazka-doch-jeden-zdroj-co-se-nedela] a [jeden-zdroj-pravdy].

## VYSLEDNY STAV (3.8.2026, plati)
Na `tenant.att_entry` bezi **BEFORE INSERT OR UPDATE trigger `trg_att_entry_fill_firma_user`**
(funkce `tenant.att_entry_fill_firma_user`), ktery doplni `firma_id` a `user_id`
**jen kdyz jsou NULL** - rucne zadanou hodnotu NIKDY neprepise.
Radek uz nemuze vzniknout prazdny, at ho udela kdokoli (mobil, Centrala, import, oprava, rucni SQL).

Logika (bajtove stejna jako drivejsi self-complete fily):
- `user_id`  <- `tenant.att_employee.user_id` (podle `NEW.employee_id`)
- `firma_id` <- `tenant.engagement.company_id`, posledni platny zaznam k `NEW.entry_date`
  (`ORDER BY valid_from DESC, is_current DESC LIMIT 1`), vazano na `NEW.tenant_id`

**BEZ gate na tenant** (na rozdil od sesterskeho `trg_att_entry_round_minutes`, ktery ma `IF NEW.tenant_id = 2`).
Duvod: doplneni je obecna datova spravnost, ne politika EUROSOFTu; dotazy jsou vazane na `NEW.tenant_id`,
takze data se mezi tenanty nikdy nesmichaji a kde podklad neni, zustane NULL jako dnes.

## Proc trigger a ne oprava mist vzniku (namitka Jirky 3.8., overena)
Jirka: *"Nejde o hlidku, ktera ty radky doplnuje, ale aby se ty radky pri VZNIKU samy naplnily
spravne. Ta hlidka totiz dela i dalsi veci, ktere nechceme."* Data mu dala za pravdu:
1. Puvodni self-complete fily byly **uklizec az potom** - bezely uvnitr `_maybe_sync_ec_dochazka`.
   Kdyz hlidka nejede, radky vznikaji prazdne.
2. Zapinat hlidku kvuli doplnovani je **nadbytecne siroke** - spusti i `_sync_ec_dochazka_recent`
   a `_sync_vyroba_work_ec`, tedy presne to, co C24/Kristy 30.7. zamerne zmrazila.
3. **Mist vzniku att_entry je 24**: 8x INSERT v router.py, 1x dochazka_zak_tab.py,
   1x dochazka_absence_sprava.py a **14 aktivnich skriptu v g2007.python**.
   Opravovat kazde zvlast = 24 zasahu a jistota, ze 25. misto to zase zapomene.
4. **Vzor uz v systemu byl**: `trg_att_entry_round_minutes` (zaokrouhlovani casu na minuty)
   dela presne tohle. Nesli jsme novou cestou, jen pouzili existujici.

## Co predchazelo (nalez 3.8. rano)
27.7.2026 bylo zapsano, ze `firma_id` je na 99,0 % a `user_id` na 99,7 %. 3.8. rano realita:
firma_id 17 298 / 36 730 (47 %), user_id 17 447 (47,5 %).
Pricina: **19 123 radku bez firma_id vzniklo 31.7.2026** (`source_system='centrala1'`:
tablet 14 179 / manual 3 512 / mobile_app 1 030 / import 283) = rizeny preimport cervence,
zatimco doplnovac byl od 30.7. vypnuty spolu s hlidkou.
V zadnem auditu (att_audit, activity_log, diag_log, action_audit_log) **neni zaznam, KDO reimport
spustil**; `att_entry.created_by_id` je u vsech techto radku NULL. Nepriama stopa = C24/Kristy.

## Provedeno (2 kroky, oba schvalila Kristy jako rodic)
- **request #1676** (backfill): firma_id 19 400 -> 305 prazdnych, user_id 19 251 -> 27 prazdnych.
- **request #1686** (trvale reseni): trigger + funkce + dorovnani zbytku.

Overeni po nasazeni (cteno z DB, ne z navratovky):
| Vec | Hodnota |
|---|---|
| trigger v pg_trigger | `trg_att_entry_fill_firma_user`, zapnuty |
| firma_id prazdnych | 323 |
| user_id prazdnych | 36 |
| **firma_id ktere JESTE JDE doplnit** | **0** |
| **user_id ktere JESTE JDE doplnit** | **0** |
| SUM(hours) | 154 810,45 (hodiny nedotcene, roste jen beznym provozem) |
| novy radek 09:03:14 UTC (tablet) | firma i clovek vyplneny **automaticky** |

Zbyle NULLy uz doplnit NELZE - chybi podklad. Overeny priklad: `att_employee` id=54
"Brigadnik Saxana" (cislo 208) ma **0 engagementu**, takze firma neni z ceho urcit. Neni to chyba.

## Vykon (overeno pred nasazenim)
`tenant.engagement` ma 939 radku, `tenant.att_employee` 242. Trigger prida 2 male dotazy na radek;
i pri davce velikosti reimportu (14 179 radku) to je radove sekundy. **Zadny novy index nepridavan** -
u tabulek teto velikosti by nepomohl. (Pozn.: `ix_engagement_emp` je PARTIAL `WHERE is_current`,
takze se na tento dotaz nepouzije - vedomo, nevadi.)

## Co z toho plyne dal
- **Hlidka `_maybe_sync_ec_dochazka` uz NENI potreba kvuli doplnovani.** Jeji zapnuti je
  ted rozhodnuti jen kvuli TEM DALSIM vecem (sync z Centraly) - rozhoduje Marti/Kristy.
  Self-complete fily v ni zustavaji jako zachranna sit pro pripad, ze v okamziku vzniku
  jeste engagement neexistoval.
- **Kdo spustil hromadny import, se dnes nikde nezaznamenava** (`created_by_id` NULL, zadny audit).
  Kandidat na doplneni - u datovych davek teto velikosti je stopa potreba.
- **NEPROVEDENO:** treti fill `vyroba_work.zakazka_helios_id` (6 260 radku jde doplnit).
  Marti-AI doporucila schvalit zvlast. Stoji to za stejnou uvahu - trigger misto uklizece.

## Pouceni
- **Backfill neni hotovy, dokud bezi zdroj, ktery diru plodi.** Jednorazovy dopocet + vypnuty
  doplnovac = problem se vrati. Spravne misto je okamzik vzniku radku, ne uklid potom.
- **Procenta zapsana do G2007 zestarnou.** Cislo z 27.7. bylo pravdive a 4 dny nato bylo
  o 52 bodu jinde. Pri praci vzdy precist z DB, ne z dokumentu.
- **Nez postavis novy mechanismus, zjisti, jestli uz stejny vzor v systemu nebezi.**
  Tady uz jeden BEFORE trigger na te same tabulce byl.

