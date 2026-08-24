# Historie smluv nezaznamenávala, KDO změnu udělal — devět cest a proč se 939 řádků nedopočítalo (24. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Nález i oprava Claude-28, zadal Jirka Honomichl 24. 8. 2026, schválila Marti-AI (msg 13580).**

## Nález

Spouštěč `tenant.engagement_historie_zapis` bere autora z nastavení relace **`strategie.actor_user_id`**:

```
v_kdo := NULLIF(current_setting('strategie.actor_user_id', true), '')::bigint;
```

Jenže **žádná cesta zapisující do `tenant.engagement` tu proměnnou nenastavovala**, takže spouštěč do sloupce `kdo` psal prázdno. Vzor, jak to dělat správně, přitom existoval od 21. 8. v `skupiny_clen`.

## Dopadová mapa — devět zapisovatelů do tenant.engagement

Ověřeno v `g2007.python` i v repu, nejde o výběr.

| kde | co dělá | kdo za tím stojí |
|---|---|---|
| `engagement_nova_verze` (živý kód) | zakládá i mění | člověk |
| `hr_conditions_save` (živý kód) | mění podmínky v platném řádku | člověk |
| `att_vernost_dovolena` (živý kód) | věrnostní dny | **automat** |
| `app_hr_employee_create` (jádro) | nový zaměstnanec | člověk |
| `app_hr_terminate` (jádro) | ukončení poměru | člověk |
| `app_hr_person_work_save` (jádro) | pozice, poznámka | člověk |
| `app_hr_pomer_zmena` (jádro) | změna poměru | člověk |
| `app_hr_finance_pozice_save` (jádro) | pozice ve financích | člověk |
| `_sync_fin_from_ec` (jádro) | sync ze staré Centrály | **automat** |

## Řešení

Do všech devíti cest přibylo těsně před zápisem:

```
SELECT set_config('strategie.actor_user_id', <uid>, true)
```

V jádru přes společnou pomocnou funkci `_set_actor(s, uid)` (`router.py`), v živém kódu inline. Automaty dostávají **0 = systém**, ne prázdno — Marti-AI: *„Prázdno říká ‚nevím kdo to byl', značka říká ‚byl to systém, záměrně'."* Sloupec `kdo` nemá cizí klíč, takže 0 je značka, ne odkaz na uživatele. Commit `fd873b61`.

## ⚠️ Proč NE centrální řešení

Nabízí se nastavit to jednou po otevření spojení. **Je to past a Marti-AI to potvrdila:**

- třetí parametr `true` = platí jen do konce **transakce**, takže po prvním uložení by to tiše přestalo platit,
- `false` = platí pro **spojení**, a to se přes pool přelije do cizího požadavku a připíše změnu jinému člověku.

Marti-AI: *„Explicitní volání těsně před zápisem je průhledné a bezpečné, i když je to víc míst."*

## ⚠️ Proč se 939 historických řádků NEDOPOČÍTALO

Vypadalo to jako 939 záznamů o zakládání smlouvy bez autora. **Není to tak.** Jsou to řádky z **jednorázového zpětného dopisu z 21. 8. 2026**, kdy se historie zaváděla, a všechny nesou text *„doplněno zpětně při zavedení historie 21. 8. 2026 — starší změny už dohledat nejdou (poslední zápis: X)"*.

Těch „X" je 18 různých a **ani jedno nesedí na skutečného uživatele**: „Sarka", „Kristyna", „Marie", „SNovotna", ale i „Vyplatnice" nebo „pozice z auditu (Claude-25)". Marti-AI podmínila dopočet jednoznačnou shodou: *„Masová oprava s nejistými daty je horší než prázdné pole — audit trail má hodnotu jen když mu lze věřit."* Shoda není, **prázdno u nich zůstává a je správně.**

Poučení: než něco označíš za „chybějící data", přečti si, **co v těch řádcích doopravdy stojí**.

## Kde se to dá vidět (a kde ne)

- **Karta zaměstnance → Historie změn (N)** ukazuje seznam verzí poměru a u nich jméno — bere se ze `engagement.changed_by_text`, ne z téhle tabulky.
- **`tenant.engagement_historie`** (podrobnost po jednotlivých sloupcích) **nemá v aplikaci žádnou obrazovku** — ověřeno, že ji nečte ani jeden živý skript ani nic v repu. Autor se do ní od 24. 8. zapisuje, ale podívat se na to jde zatím jen dotazem do databáze.

## Ověřeno naostro 24. 8. 2026

Zkouška na Jirkovi: šest nových řádků historie, **u všech `kdo` = 20 (Jiří Honomichl)** — tři z cesty v jádru (uložení karty) a tři ze společného jádra (nová verze). Před opravou by tam bylo prázdno. Vše po zkoušce uklizeno a data vrácena do původního stavu.

Souvisí: [[doc-dochazka-smlouva-nova-verze-rucne]] · [[doc-system-strategie-podminky-vychozi-na-sirku-a-historie-zmen]] · [[doc-dochazka-podminky-slouceny-se-smlouvou]]

