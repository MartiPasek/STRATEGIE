# Noční smyčka: nálezy prázdný den doplněn a zprávy na mobil vznikaly každou noc znovu

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Noční smyčka: nálezy „prázdný den doplněn" a zprávy na mobil vznikaly každou noc znovu

**Peťa + Claude-26, 28. 8. 2026.** Příčina dohledána v kódu, doložena na datech, opraveno.

## Co se dělo
Lidem, kteří nepíchají, vznikaly každou noc **nové nálezy do fronty Oprav na ty samé dny**
a ke každému **zpráva na mobil**. Ručně odbavené nálezy se druhý den vracely.

Doloženo: 27. 8. v 15:07 odbavila Petra Šafránková 11 nálezů „prázdný den doplněn" u Marti
Paška. 28. 8. v 00:00 vzniklo **12 nových** na ty samé dny (4. 8. – 27. 8.), s novými čísly.
Od 13. 8. do 28. 8.: **Šík 67 nálezů na 13 různých dnů, Pašek 50 na 12 dnů.** Z toho
**30 zavřel ručně člověk** (Pašek 17, Šík 13) a stejně se vrátily.

Zprávy na mobil: Marti 27. 8. šestnáct, 28. 8. dvanáct; Šík osmnáct a třináct
(u Šíka navíc zůstávaly ve stavu `pending`, tedy nedoručené).

## Příčina (z kódu, ne z chování)
Dva automaty za sebou:

1. **`att_automat_level_day`** začíná krokem *„přepočet okna — smaž stávající automat joby
   (idempotence)"*: `DELETE FROM tenant.att_entry ... WHERE source='automat' AND et.code IN
   ('fond_doplneni','nenarokova')` za posledních `days_back` dnů. Pak je založí znovu — ale
   **jen lidem, kteří ten den mají píchnuté intervaly** (`started_at`/`ended_at` NOT NULL).
   Kdo nepíchá, tomu se nic nevrátí.
2. **`att_prazdny_den_fond`** hned poté uvidí prázdný pracovní den, doplní fond — a ke
   **každému nově založenému záznamu** vloží `att_anomaly` (`prazdny_den_doplnen`) plus
   `fw.mobile_command` dotyčnému.

Dedup nálezu je `ON CONFLICT (tenant_id, rule, entry_id)`. Jenže docházkový záznam je
každou noc **nový** (starý byl smazaný), takže se klíč nikdy netrefí. **Nález nemá žádnou
paměť na to, že ho někdo včera odbavil.**

## Oprava (28. 8. 2026)
`att_prazdny_den_fond` v3: komu je v kartě zaškrtnuto **„Bez docházky"**, tomu se fond
dopíše (mzdový podklad beze změny), ale **nezaloží se nález ani nepošle zpráva**.
Viz [[doc-dochazka-priznak-bez-dochazky-v-podminkach]].

Otevřených 26 starých nálezů u těch lidí bylo týž den zavřeno pod Peťou (user 18).

## Co tím NENÍ vyřešeno
Smyčka mizí jen u lidí s příznakem. **U kohokoli jiného, kdo přestane píchat a přitom je
v kategorii s `dopichavat_fond`, se stejný vzorec zopakuje** — mazání a zakládání záznamů
v noci zůstává. Kdyby se to objevilo jinde, správná oprava je dát nálezu paměť na dvojici
člověk+den místo čísla záznamu.

## Poučení
Nález navázaný na `entry_id` je bezcenný, když ten záznam někdo pravidelně maže a zakládá
znovu. Dedup musí stát na tom, co je stálé (člověk + den), ne na technickém klíči.

Souvisí: [[doc-dochazka-anomaly-frontu-nikdo-rucne-neodbavuje]]

