# Výchozí podmínky „na šířku“, historie změn smluv a skupin (21. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Výchozí podmínky na šířku + historie změn (21. 8. 2026)

> Zadal Jirka Honomichl, schválila Marti-AI (msg 13160, 13172, 13184). Postavil Claude-28.
> Navazuje na sloučení Podmínek se Smlouvou z 19. 8. 2026.

## Proč to vzniklo

Šárka Novotná 20. 8. hlásila, že se Šebkovi (9039) objevily 2 sick days a stravenka 82 Kč,
které nezadala. Dohledat, kdo je zapsal, **nešlo** — u podmínek si systém pamatoval jen
„kdo a kdy" u AKTUÁLNÍ hodnoty (`engagement.pod_meta`), takže přepis smazal předchozího
autora i původní hodnotu beze stopy. Ověřením v živém kódu (mobilní obrazovka i
`hr_conditions_save`) se ukázalo, že ukládání posílá vždy **jen jedno pole a jen to změněné**,
takže hodnota nejspíš nikdy zapsaná nebyla — karta zobrazovala systémový default s popiskem
„(systém)". Dokázat to ale zpětně nešlo, a proto vznikla historie.

## Co je nově v databázi

| Objekt | K čemu |
|---|---|
| `tenant.engagement_historie` | každá změna KAŽDÉHO sloupce smlouvy/úvazku/podmínek — sloupec, z čeho na co (jsonb), kdo, kdy. Plní `trg_engagement_historie` (AFTER I/U/D). Ze smyčky vynechány `pod_meta` a `changed_at` (šum). |
| `tenant.staff_group_member_historie` | zařazení/vyřazení/změna skóre ve skupině. Plní `trg_staff_group_member_historie`. |
| `tenant.podminky_skupin` | výchozí podmínky **na šířku** — řádek = skupina + jeden řádek `scope_kind='system'`, sloupce `pod_*` stejně jako ve smlouvě. Prázdná buňka = dědí se ze systémového řádku. |
| `tenant.podminky_vychozi` | **už není tabulka, ale POHLED** nad `podminky_skupin` (+ `podminky_osobni` pro osobní řádky lidí bez smlouvy). Starý tvar 1:1, aby všech deset čtenářů i mobil jely dál. Zápis přes `trg_podminky_vychozi_zapis` (INSTEAD OF). |
| ~~`tenant.podminky_vychozi__zaloha_20260821`~~ | původní tabulka před přepnutím — ⛔ **zrušena 25. 8. 2026** po uplynutí lhůty (zadal Jirka Honomichl, schválila Marti-AI, msg 13661). **Nehledej ji, už neexistuje.** ⚠️ Vlastnila sekvenci `staff_cond_id_seq`, ze které bere `id` živá `tenant.podminky_osobni` — sekvence byla před zrušením přepojena a přejmenována na `podminky_osobni_id_seq`. Detail: [[doc-dochazka-podminky-slouceny-se-smlouvou]]. |
| ERP přehled `hr.podminky_skupin` + formulář `hr.podminky_skupin_edit` | menu 🧑‍💼 HR & LIDÉ → „⚙️ Výchozí podmínky skupin". Šest záznamů ve `fw.*`, žádné nasazení. |

> **Doplněno 24. 8. 2026** (Jirka Honomichl + Claude-28, schválila Marti-AI msg 13586): věta
> „žádné nasazení" platila do 24. 8. 2026. Tehdy k přehledu přibyla **nástěnka dlaždic místo tabulky**
> (s přepínačem zpět na tabulku, přidáváním a mazáním řádků), a ta nasazení vyžadovala — vlastní
> soubor v ERP, napojení v `page_render.js` a dva tenké předavače v `router.py`; logika žije
> v `g2007.python` pod kódem `podminky_skupin_dlazdice`. Šest záznamů ve `fw.*` zůstalo beze změny.
> Detail: `doc-system-strategie-erp-prehled-jako-nastenka-dlazdic-podminky-skupin`.

## Kdo aktéra předává

Spouštěče berou „kdo to udělal" z nastavení relace `strategie.actor_user_id`. Kvůli tomu byl
endpoint `POST /app/skupiny/{gid}/clen` zmigrován z `router.py` do `g2007.python`
(kód `skupiny_clen`) — vkládá `set_config('strategie.actor_user_id', ...)` před zápisem.
Bez toho by u VYŘAZENÍ ze skupiny nešlo zjistit, kdo ho provedl (řádek se maže).

## Pasti, na které jsem narazil (a stály čas)

1. **GRANTy.** Tabulka založená přes SQL most patří roli `Marti-AI`; aplikace (role `strategie`)
   na ni **nemá práva**. U historie je to zákeřné: spouštěč běží pod právy volajícího, takže
   by spadl **každý zápis do smlouvy z aplikace**, ne jen práce s novou tabulkou.
   → po založení tabulky VŽDY `GRANT SELECT, INSERT, UPDATE, DELETE ... TO strategie`
   (+ `GRANT USAGE, SELECT ON SEQUENCE`).
2. **`updated_by_id` / `updated_by_text`.** Editační formulář frameworku je při uložení zapisuje
   vždy — tabulka bez nich vrátí HTTP 500 „column does not exist".
3. **Změna typu sloupce, na kterém visí pohled**, vyžaduje pohled napřed zrušit a znovu postavit
   — a s ním i jeho INSTEAD OF spouštěč a GRANTy.
4. **Dvojtečka v SQL** posílaném přes most je parametr — `WHERE id = :ID` se musí skládat
   jako `'... WHERE id = ' || chr(58) || 'ID'`.
5. **`fw.data_set.created_by` a `fw.data_source.created_by` jsou čísla** (user id), zatímco
   `fw.core`/`comp_def`/`menu_node` mají textové `created_by_text` — a `menu_node.updated_by_text`
   je NOT NULL.

## Otevřené (přeověřeno 24. 8. 2026)

- ✅ **VYŘEŠENO — podmínky jsou otypované.** *(Do 24. 8. 2026 tu stálo „všech 15 sloupců `pod_*`
  je text v obou tabulkách … čeká na rozhodnutí Marti-AI" — to už neplatilo.)*
  Ověřeno **přímo v `information_schema.columns` 24. 8. 2026** (Claude-28, ne převzato):
  `tenant.engagement` má 9 `numeric`, 3 `boolean`, 2 `time`, 1 `text` (`pod_prac_dny`)
  a `jsonb pod_meta`; `tenant.podminky_skupin` totéž plus `pod_uvazek_h_tyden` jako `numeric`.
  Na to navázala i **políčka editačního formuláře** — ve `fw.comp_def` (jádro 236) byla
  **22. 8. 2026 v 7:50** přepnuta na 9× `number`, 4× `combobox`, 2× `timeedit`
  a 2× `label_readonly` (`id` a počítadlo `pod_dovolena_dni`).
- ✅ **VYŘEŠENO 24. 8. 2026 — výběr skupiny sjednocen se zbytkem systému.**
  Obě funkce (`engagement_pod_defaults`, `engagement_doplneni_pri_zarazeni`) berou skupinu
  nově přes **`ORDER BY sg.sort_order, sg.id LIMIT 1`**, stejně jako **osm živých míst
  v `g2007.python`** (`hr_conditions`, `my_conditions`, `plan_generate_effective`,
  `plan_my_default`, `sickday_lekar_apply`, `att_med_start`, `att_narok_cerpani`,
  `att_sick_balance_h`). Rozhodl Jirka Honomichl, schválila Marti-AI (msg 13628);
  ověřeno přes `pg_get_functiondef` (starý tvar 0 výskytů) a porovnáním starého a nového
  výběru u **všech 76 lidí ve skupinách: shoda 76, rozdíl 0**.
  ⚠️ **POZOR — dřívější tvrzení v této odrážce bylo CHYBNÉ a stálo tu jen pár hodin.**
  Do 24. 8. 2026 tu bylo, že obě funkce *„textové řazení dál obsahují"*. **Nebyla to pravda** —
  textové řazení opravili Kristý a Jirka už **23. 8. 2026** (poznámka je přímo v kódu obou
  funkcí) a od té doby se řadilo podle čísla. Chyba vznikla tím, že se v definici funkce
  hledal **podřetězec `id::text`**, ten se našel v **přetypování při ukládání do textové
  proměnné** a byl vyhodnocen jako řazení; celý kód se přečetl až potom. Poučení: ověřená
  ingredience není ověřený závěr — u funkce se čte celá definice, ne výskyt slova.
- ✅ **VYŘEŠENO 21. 8. 2026 — editace výchozích hodnot už v mobilu není.**
  *(Do 24. 8. 2026 tu stálo „je zatím i v mobilu — po dokončení ERP obrazovky se má zrušit".)*
  Ověřeno **přímo v `g2007.soubor` 24. 8. 2026**, a to na obou místech: dílek
  `apps/api/static/mobile_parts/48_hr_podminky_me.js` i sestavená stránka
  `apps/api/static_db/mobile.html` nesou hlášku „🔒 Jen ke čtení. Výchozí hodnoty se upravují
  v ERP: HR & LIDÉ → ⚙️ Výchozí podmínky skupin", políčka mají `f.disabled = true`
  a žádné uložení tam nezbylo.

> **Srovnáno 24. 8. 2026** (Claude-28, zadal Jirka Honomichl, schválila Marti-AI msg 13619).
> Sekce vedla jako nedodělané dvě věci, které byly hotové — přesně ta zastaralost, kterou
> zakazuje bod 14 pravidel práce. Všechna tvrzení výše jsou ověřená **přímým čtením
> z databáze** téhož dne, ne převzatá.

