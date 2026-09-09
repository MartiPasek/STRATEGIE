# Kontrola docházky — srpen 2026 (ruční, nezávislá)

**Zadala:** Peťa, 3. 9. 2026 večer — *„zkontroluj docházku za srpen, ne z automatu, ne z kontrol, ale ty celé."*
**Provedl:** Claude‑26, vlastními dotazy nad živými daty.

## Metoda

Celé období **1.–31. 8. 2026**, jedenáct nezávislých kontrol napsaných od nuly.
**Záměrně jsem nepoužila frontu „K vyřešení" ani existující hlídače** — ty mají
14denní okno, práh a nález na jeden záznam zakládají jen jednou za život, takže
by ukázaly jen výřez. Tohle je pohled přímo na data.

## Výsledek — co je čisté (nula nálezů)

| Kontrola | Výsledek |
|---|---|
| Úsek rozpadu bez zakázky | **0** |
| Úsek rozpadu bez činnosti | **0** |
| Úsek rozpadu s nulou hodin | **0** |
| Rozpad bez vazby na píchnutí (sirotci) | **0** |
| Překryv časů v rámci dne | **0** |
| Dny bez potvrzení člověkem | **0** |
| Rozporované dny dosud otevřené | **0** |
| Otevřené nálezy za srpen | **0** |

První čtyři byly ještě dnes ráno špinavé — srovnaly jsme je během dneška.

## Výsledek — co zbývá

### 1. Hlavička docházky bez zakázky — 17 záznamů, 7 lidí, 36,29 h

| Člověk | Záznamů | Hodin | Poznámka |
|---|---|---|---|
| Jiří Honomichl | 9 | 21,82 | „bez docházky", zakázka není ani v rozpadu |
| Marti Pašek | 3 | 14,40 | „bez docházky", zakázka není ani v rozpadu |
| Saad Jarrar | 1 | 0,03 | **zakázku v rozpadu má** — jde doplnit nahoru |
| Václav Vápeník | 1 | 0,02 | **zakázku v rozpadu má** — jde doplnit nahoru |
| Eliška Kolářová | 1 | 0,02 | **zakázku v rozpadu má** — jde doplnit nahoru |
| Michal Jirkovský | 1 | 0,00 | nulový záznam, neškodí |
| Zdeněk Diviš | 1 | 0,00 | nulový záznam, neškodí |

**Návrh:** u těch tří minutových propsat zakázku z rozpadu do hlavičky — stejná
operace, jakou dnes přes den udělala druhá session u sedmi jiných záznamů.
Honomichl a Pašek se nekontrolují, zůstávají.

### 2. Píchnutí končící 23:59 — 16 záznamů, 3 lidé, 186,42 h

Deset Honomichl, čtyři Marti Pašek — **oba „bez docházky"**, u sedmi z nich je
navíc poznámka o opravě od Týnky. Dva jsou tvoje vlastní (4. a 6. 8.) a u obou
sis do poznámky napsala, že konec o půlnoci **souhlasí**.

**Nic k řešení.**

### 3. Píchnutí s nulou hodin — 149 záznamů, 37 lidí

Píchnutí a hned odpíchnutí. Do hodin ani do mezd nejde nic, ale zaneřáďuje to
data. **Toto je bod na pondělní jednání s Jirkou a Týnkou** (Lukáš Horký takhle
osmkrát za měsíc — vypadá to na chování appky, ne na nešikovnost).

### 4. Práce v den nahlášené absence — 18 dnů, 15 lidí

Většina je v pořádku — půl dne lékař a půl dne práce, součet vychází na fond.
**Tři případy ale mají absenci na CELÝ den a k tomu odpracované hodiny:**

| Člověk | Den | Absence | Odpracováno |
|---|---|---|---|
| Kristýna Marešová | 31. 8. | Dovolená 8,00 h | 5,67 h |
| Radek Hellmayer | 18. 8. | Dovolená 8,00 h | 1,93 h |
| Petr Beneš | 13. 8. | Dovolená 8,00 h | 0,55 h |

Čerpá se jim celý den dovolené a zároveň mají odpracováno. **Doporučuju projít
před mzdami** — buď zkrátit dovolenou, nebo tu práci zrušit, podle toho, co se
opravdu stalo.

### 5. Rozdíl mezi docházkou a rozpadem — jen dva lidé

| Člověk | Dnů | Rozdíl |
|---|---|---|
| Marti Pašek | 6 | 76,95 h |
| Jiří Honomichl | 7 | 38,58 h |

**U všech ostatních sedí docházka s rozpadem na desetinu hodiny za celý srpen.**
Tihle dva se nekontrolují a rozpad si nevedou.

## Kontrola z obrazovek

Do aplikace se přihlásit nemůžu (přihlašovací údaje nikdy nepoužívám), takže
„z obrazovky" jsem to vzala dvěma způsoby, které jsou v mých silách:

**1. Živá stránka se načte a běží.** Ověřeno přímo na `strategie-ai.com` —
Opravy docházky se načtou, JavaScript naběhne bez chyby, dnešní změny jsou
opravdu venku (oranžový štítek při překryvu, štítek „rozporoval", jeden datum).

**2. Prošla jsem, z čeho jsou docházkové obrazovky poskládané** — právě takhle
se dnes odhalilo „Zam 21", které v datech neexistovalo a vyrábělo ho až
zobrazení. Prověřila jsem **všech 25 aktivních datových sad**, které sahají na
docházkové karty, na tutéž třídu chyby (napojení přes `user_id` na člověka,
který má víc karet → násobené řádky a falešná jména):

| Sada | Stav |
|---|---|
| `dochazka.zakazky_vse_list` (Docházka new) | **byla vadná — dnes opravena** |
| `vyroba.dusan_dochazka_vse_list` (Dušanova Docházka) | v pořádku, napojení 1:1 |
| `vyroba.dusan_att_entries_list` | v pořádku, napojení 1:1 |
| `dochazka.zakazky_budoucnost_list` | v pořádku, napojení 1:1 |
| `dochazka.prehled_dnu_clovek` | v pořádku |
| `system_new.hr_presence_board_list`, `hr_att_monthly_list`, `hr_kdo_kde_dnes_list` | v pořádku, napojení 1:1 |
| `system_new.hr_benefits_list` | v pořádku (jednoznačný výběr jedné karty) |
| `vyroba.dusan_att_balances_list`, `dusan_att_employees_list`, `dusan_org_*`, `dusan_work_params_list` | v pořádku |

**Závěr: vadná byla jediná sada a je opravená.** Ostatní obrazovky lidi nenásobí
ani si jména nevymýšlejí.

## Co jsem NEkontrolovala

Ať je jasné, kam kontrola nesahá:

- **mzdové dopady** — nesrovnávala jsem s výplatními podklady ani s Heliosem
- **nárok na dovolenou a jeho čerpání** — jen jsem našla ty tři kolize s prací
- **data z Centrály** — jen naše
- **jiné měsíce než srpen**
- **správnost zakázek** — jen jestli tam jsou, ne jestli jsou ty správné

## Shrnutí

Srpen je po dnešní práci v dobrém stavu. K rozhodnutí zbývají **tři případy
dovolené s odpracovanými hodinami** (bod 4) a k doplnění **tři minutové zakázky
do hlavičky** (bod 1). Zbytek jsou buď lidé, kteří se nekontrolují, nebo věci
na pondělní jednání o appce.
