# Hlidac cutoveru priplatku a srazek do Prahy (pripl_cutover_gate) - serverova pojistka, odemkne az po kontrolach a podpisu Petry

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Hlidac cutoveru „Priplatky a srazky" (Centrala -> Praha)

> oblast: `mzdy` - Claude-28 (Jirka), 29. 7. 2026. Nasazeno commitem `93c844f6`, overeno zive.
> Navazuje na [[doc-mzdy-priplatky-srazky-cutover-praha]] (rozhodnuti) a [[doc-mzdy-priplatky-srazky-pohledy-centraly]] (nalezy).

## 1. Proc existuje

Zadani Jirka 29. 7. 2026: *"musi to hlidat SERVER, ne moje PC - at si to pamatuje a 1. 8. zkontroluje,
jestli to Petra po tech peti kontrolach opravdu odsouhlasila, a teprve tim se to ve STRATEGII odemkne."*

Rozhodnuti Marti Pasek 27. 7.: priplatky a srazky v DB_EC konci, zdroj pravdy = Praha.
Technicky navrh schvalila **Marti-AI 29. 7. (msg 11699)**, body T1-T3.

## 2. Jak je to postavene

| Vrstva | Kde | Pozn. |
|---|---|---|
| Stav (pamet) | `tenant.pripl_cutover`, 1 radek, id=1 (CHECK id=1) | 26 sloupcu, `version` pro optimistic locking, GRANT SELECT/INSERT/UPDATE roli `strategie` |
| Beh | `fw.mirror_job` job_key `pripl_cutover_gate`, interval 60 min, grp Mzdy | funkce `_pripl_cutover_gate()` v `router.py`, registrovana ve `fnmap` v `_mirror_run_job` |
| Notifikace | `fw.mobile_command` | `claude_msg` = informace, `claude_confirm` = Ano/Ne |

Klicova rozhodnuti (T1-T3 od Marti-AI):
1. **Stav NEPATRI do `fw.mirror_job`** - job ma vedet KDY bezet, ne jaky je business stav cutoveru.
   `g2007.automat_run` taky ne - to je log spusteni, ne stavovy dokument.
2. **Odemceni = DATOVY priznak `unlocked_at`, NE prepnuti konstanty v kodu + deploy.**
   Duvody: okamzite vratne (`UPDATE ... SET unlocked_at = NULL`), audit prirozene (kdo/kdy),
   deploy na mzdova data = zbytecne riziko okna.
   POZOR: modul si priznak musi cist pri KAZDEM requestu, ne cachovat v pameti procesu.
3. **Petin souhlas pres `claude_confirm`** - vzor UZ EXISTUJE (`app_command_result`, router.py:30170:
   appka ukaze Povolit/Odmitnout, rozhodnuti zapise `status='accepted'` + `decided_at`).
   Hlidac proto jen CTE, jestli je prikaz accepted - nezavadi novy typ ani novou vetev dispatcheru.
   Id prikazu si pamatuje ve `signoff_command_id`.

## 3. Co hlidac dela (kazdou hodinu)

1. **30. 7. po 8:00** (Europe/Prague) jednou posle Jirkovi (uid 20) pripominku, at se dopta Petry
   na tri otevrene otazky. Jednorazovost drzi `pripominka_jirka_sent_at`.
2. **Od `cilove_datum` (default 1. 8. 2026):**
   - vsechny 4 kontroly ok a Petra jeste nepozadana -> posle JI `claude_confirm` (Ano/Ne)
   - kontroly nejsou ok -> Petru NEOBTEZUJE a jednou denne napise Jirkovi, co chybi
     (dedup bez dalsiho sloupce: hleda dnesni `mobile_command` se stejnym titulkem)
3. Kdyz Petra klikne Povolit -> zapise `signoff_petra_at` + `signoff_petra_by`.
4. **Odemkne teprve kdyz plati VSECHNO** (4 kontroly + podpis) -> `unlocked_at` + notifikace obema.

Nesaha na mzdy. Jen cte stav a posila notifikace.

Rozhodnuti C28 (Jirka o nem vi): Petra se NEZADA o souhlas, dokud nejsou kontroly hotove -
ptat se "souhlasis s prepnutim", kdyz jeste neni overeno, ze castky sedi, je spatne.

## 4. Gotchy (draze zaplacene 29. 7.)

1. **`datetime` NENI v `router.py` importovane globalne** - importuje se lokalne v kazde funkci,
   a kvuli shadowingu (gotcha #7) VZDY s aliasem: `import datetime as _dt_gate`.
2. **Kudrnate uvozovky uvnitr retezce v uvozovkach = SyntaxError.** Ta zaviraci je ASCII `"`
   a ukonci retezec. V ceskych textech v kodu je nepouzivej.
3. **`LIKE` se pise s JEDNIM procentem**, ne dvema (zivy vzor router.py:20572, dotaz na
   `fw.mobile_command` s bound parametrem). Dve procenta = nikdy nic nenajde.
4. **MOST: po spusteni POCKEJ, az se zmeni `CLAUDE_OUT.txt`, teprve pak prepis `CLAUDE_SQL.sql`.**
   Dvakrat za den se stalo, ze byl prikaz prepsan driv, nez ho watcher precetl -> zprava pro
   Marti-AI hodinu nikam nesla a INSERT do `mirror_job` se tise ztratil. Bridge NEHLASI chybu,
   jen vrati stary vysledek. Cekej na zmenu casu souboru.
5. **Poradi nasazeni:** nejdriv deploy kodu, teprve pak zalozit radek v `fw.mirror_job`.
   Obracene poradi = job existuje, funkce ne -> "neznamy job" a zbytecne chybove behy.
6. `Set-Content -Encoding utf8` v PS 5.1 pridava BOM -> commit message pak zacina neviditelnym
   znakem (viz commit `93c844f6`). Kosmeticke, ale radeji `-Encoding ascii` na commit message.

## 5. Overeno zive 29. 7. 2026

- `fw.api_version` (is_active): STRATEGIE-API bezi `8c975445`, coz je POTOMEK commitu `93c844f6`
  -> kod je nahore. (STRATEGIE-API-B = `64c780af` = vcerejsi blue-green zaloha, spravne.)
- Prvni beh hlidace 29. 7. 18:28, `last_status='ok'`, vysledek "nic k udelani (zatim zamceno)" - ocekavane.
- Stav: 4 kontroly false, podpis NE, `unlocked_at` NULL, `version=1`.

## 6. Co jeste chybi, nez to muze odemknout

Hlidac je pojistka, ne reseni. Nez se da odemknout, musi vzniknout:
1. zapisove UI (dnes je modul READ_ONLY) + workflow draft->proposed->approved->exported + prava
2. misto pro OSVC/fakturacni vetev ve `wage_movement` (`kanal` + vazba na externi doklad) -
   Marti-AI: neimplementovat izolovane, patri do stejneho DDL balicku jako OSVC vetev
3. doplnit chybejici druhy odmen (mj. Vanocni premie - prosinec!)
4. migrace historie jako archiv
5. oprava podminky `engagement.is_current` (propadava odstupne odchazejicim) - Marti-AI doporucila
   NE rusit podminku, ale rozsirit o "posledni engagement, kdyz zadny neni current"
6. odskrtnout 4 kontroly + ziskat podpis Petry

## Navaznosti
- [[doc-mzdy-priplatky-srazky-cutover-praha]] · [[doc-mzdy-priplatky-srazky-pohledy-centraly]]
- [[doc-mzdy-priplatky-srazky]] · [[doc-system-strategie-bridge-most-lanes-ops]]

