# Výchozí podmínky — spouštěč četl číselník, ale pevné DB defaulty ho umlčely (oprava 20. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Stav k 20. 8. 2026. Zadal Jirka Honomichl, odsouhlasila Marti-AI, provedl Claude-28.**

## Jak to funguje dnes

`tenant.podminky_vychozi` (dřív `staff_cond_zaklad`) je číselník výchozích hodnot podmínek
ve dvou úrovních — `scope_kind='system'` a `scope_kind='group'`. Při vložení řádku do
`tenant.engagement` doplní chybějící sloupce `pod_*` spouštěč **`trg_engagement_pod_defaults`**
(BEFORE INSERT) přes funkci `tenant.pod_vychozi(tenant, skupina, kod)`, která jede kaskádu
**skupina → systém**. Osobní hodnoty pak žijí ve smlouvě a `tenant.staff_cond` je jen pohled.

## Co bylo špatně (obecně použitelné poučení)

Tytéž sloupce `pod_*` měly zároveň **pevné DB defaulty** v definici tabulky (zmrazené kopie
systémových hodnot z 19. 8.). V PostgreSQL se **defaulty sloupců aplikují DŘÍV než BEFORE ROW
spouštěč**, takže `COALESCE(NEW.pod_x, tenant.pod_vychozi(...))` už nikdy neviděl NULL a do
číselníku nesáhl. Důsledky:

- **skupinové výchozí hodnoty byly fakticky mrtvé** — uplatnily se jen při vložení s výslovným NULL,
- změna systémové hodnoty v číselníku se nepromítla do nově zakládaných smluv (tichý druhý zdroj pravdy).

**Poučení nad rámec tohoto případu — pevný default sloupce a BEFORE spouštěč, který ten sloupec
dopočítává, se navzájem vylučují. Default vyhraje vždycky a spouštěč mlčí.**

## Důkaz (postup, který lze zopakovat)

Skupina 3 (Výroba) má vlastní hodnoty odlišné od systémových, a pevné defaulty se rovnaly
systémovým — test na jejím členovi je proto jednoznačný. Test se pouští jako `DO` blok
zakončený `RAISE EXCEPTION`, takže **se sám vrátí zpět a v datech nic nezůstane**.

| test | před opravou | po opravě |
|---|---|---|
| vložení BEZ sloupců `pod_*` | 09.00 / ANO / 48 / 09.00 (systém = pevný default) | 07.00 / NE / 0 / 07.00 (skupina 3) |
| vložení s výslovným NULL | 07.00 / NE / 0 / 07.00 (skupina 3) | 07.00 / NE / 0 / 07.00 |

Požadavky mostu 2265 (před) a 2269 (po). Po každém testu ověřeno čtením — 0 zbytků, 939 řádků.

## PRVNÍ VLNA — co se 20. 8. změnilo

1. **Zrušen spouštěč `trg_staff_cond_default_dovolena`** na `tenant.att_employee` (požadavek 2267).
   Zakládal novému zaměstnanci tři řádky dovolené do `staff_cond` — jenže to je od 19. 8. pohled
   a jeho INSTEAD OF spouštěč zápis člověka **bez smlouvy** posílal do `podminky_vychozi` jako řádky
   úrovně `user`, které nikdo nečte. Navíc `EXCEPTION WHEN OTHERS THEN NULL` = tiché polykání chyb.
   Funkce `tenant.staff_cond_default_dovolena()` zůstává v DB pro případ návratu.
2. **Doplněna systémová hodnota `uvazek_h_tyden` = 40** do číselníku.
3. **Zrušeny pevné DB defaulty na všech 15 sloupcích `pod_*`** (požadavek 2268). Tím se spouštěč
   probral. Předpoklad ověřen předem — číselník má systémovou hodnotu pro všech 15 kódů.
   Počítadlo `pod_dovolena_dni` dopočítá spouštěč `trg_engagement_pod_soucet_dovolene`, který běží
   až po `engagement_pod_defaults` (řazení podle jména).

## DRUHÁ VLNA — nezařazený člověk a doplnění při zařazení (20. 8., požadavek 2273)

**Pravidlo (rozhodl Jirka, schválila Marti-AI):** nový člověk má mít hodnoty „ještě nenastaveno",
dokud ho personální nezařadí do skupiny. Při **prvním** zařazení se doplní podle té skupiny.
**Pozdější změna skupiny už nepřepočítává** — kvůli lidem s individuální dohodou.

`tenant.engagement_pod_defaults` v2 při zakládání smlouvy rozlišuje:

- **zařazený** — všechno rovnou z číselníku podle jeho skupiny, nic se neoznačuje,
- **nezařazený** — dovolená základní i navíc = **0**, úvazek zůstává **prázdný**, zbytek dostane
  systémovou hodnotu jako pracovní default. Všechno takto vzniklé se označí v `pod_meta`
  příznakem **`ceka_na_zarazeni`**.

`tenant.engagement_doplneni_pri_zarazeni` (AFTER INSERT na `tenant.staff_group_member`) při
zařazení přepíše **jen položky s tím příznakem** hodnotami podle skupiny a příznak smaže.
Tím je „žádný zpětný přepočet" splněné samo — podruhé už není co přepsat.

**Proč zrovna takhle:** nula u dovolené, aby nová dovolená tiše nespadla na systémových 25
(pravidlo Jirka 16. 8.). Prázdno u úvazku, protože nulový úvazek jde rovnou do fondu pracovní
doby a mezd — prázdno je viditelný nedodělek (rozhodla Marti-AI 20. 8.).

**Ruční zásah personálního příznak taky smaže** — zápis přes pohled `tenant.staff_cond`
přepisuje celý záznam v `pod_meta`, takže ručně zadaná hodnota se automatikou už nepřeplácne.

**Vědomá výjimka:** `engagement_doplneni_pri_zarazeni` je kromě `uvazek_zapis` jediné místo,
které zapisuje do `uvazek_tyden_h`. Vždy jen do **prázdného** pole u nové smlouvy, nikdy
nepřepisuje existující hodnotu. Viz `doc-dochazka-uvazek-jediny-zdroj-smlouva`.

**Ověřeno testem nanečisto** (požadavek 2274, celý blok vrácen zpět):

| krok | výsledek |
|---|---|
| nezařazený, nová smlouva | dovolená 0/0 celkem 0, úvazek prázdno, nástup 09.00, home office 48, **15 příznaků** |
| zařazen do Výroby | dovolená 20/5 celkem 25, úvazek 40, **nástup 07.00, home office 0**, **0 příznaků** |
| přidán i Nákup | beze změny — žádný přepočet |

Po testu ověřeno čtením: 939 smluv, 80 aktuálních, 237 zaměstnanců, 0 testovacích uživatelů,
0 řádků úrovně `user` v číselníku, 0 smluv s příznakem.

## Úvazek v obrazovce Podmínek (20. 8.)

`hr_conditions` v5 a `hr_conditions_save` v6 — úvazek se nově **nabízí i na systémové a skupinové
úrovni** Podmínek, aby si personální mohlo nastavit jiný úvazek pro Výrobu a jiný pro Nákup.
Ukládání hlídá, že je to číslo mezi 0 a 60. **Osobní úroveň se nezměnila** — úvazek konkrétního
člověka jde dál výhradně do smlouvy přes `uvazek_zapis`.

## Co zbývá

Marti-AI požaduje **aktivně viditelný seznam lidí s nedodělanými podmínkami** (dashboard, ne
skrytý report). Data jsou připravená — hledá se smlouva, v jejímž `pod_meta` je aspoň jeden
záznam s `ceka_na_zarazeni = true`. Obrazovka zatím není; k 20. 8. na ni není ani jeden člověk.

Souvisí: `doc-dochazka-podminky-slouceny-se-smlouvou`, `doc-dochazka-uvazek-jediny-zdroj-smlouva`,
`doc-dochazka-rozpad-dovolene-zakladni-a-navic`, `doc-podminky-skupin-zamestnancu`.

