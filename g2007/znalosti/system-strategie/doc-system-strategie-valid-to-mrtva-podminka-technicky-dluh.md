# Sloupec valid_to u smluv je mrtvá podmínka — vědomě ponechaný technický dluh (24. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Zapsal Claude-28 (Jirka Honomichl) **24. 8. 2026**. Rozhodl Jirka Honomichl,
schválila Marti-AI (msg 13598). Vše níže je ověřeno na živém kódu a v datech téhož dne,
ne převzato.

## Co to je

Tabulka `tenant.engagement` (smlouva / pracovní poměr) má sloupec `valid_to` („platnost do").
**Je prázdný u všech 940 řádků** — a byl prázdný i ve všech dřívějších měřeních.
Přesto na něj **osm výpočtů má podmínku** ve tvaru „prázdné, nebo >= datum".

Protože je sloupec vždy prázdný, **ta podmínka nikdy nic neodfiltruje**. Vypadá jako pojistka,
ale nehlídá nic. To je celý ten dluh: **mrtvá podmínka, která budí dojem kontroly.**

## Proč je prázdný — je to ZÁMĚR, ne opomenutí

Model platnosti verzí je vědomě „bez konce":

- konec verze je dán **začátkem té následující**,
- poslední verzi značí příznak **`is_current`**,
- čtenáři vybírají přes `valid_from <= datum ORDER BY valid_from DESC LIMIT 1`, ne přes interval.

Jádro `engagement_nova_verze` (`g2007.python`), kterým dnes vznikají **všechny** nové verze
(volají ho `uvazek_zapis` a tlačítko `smlouva_nova_verze`), to má v hlavičce napsané výslovně:

> `⚠️ MODEL PLATNOSTI (prevzato z uvazek_zapis v8, NEMENIT): valid_to je prazdne na VSECH`
> `radcich, i na davno nahrazenych. … Nova verze tenhle model dodrzuje - valid_to nechava prazdne.`

## Osm míst, která na `valid_to` mají podmínku

`att_anomaly_scan` · `att_dovolena_kaskada` · `att_narok_cerpani` · `att_sd_kontrola` ·
`att_uvazek_tyden` · `mzdy_benefity_apply` · `mzdy_loajalita_rows` · mzdové náhrady v `router.py`.

⚠️ **Neověřeno:** celý zdroj byl 24. 8. 2026 čten jen u `att_uvazek_tyden`. U zbylých sedmi
se vychází z toho, že prázdný sloupec nemůže nic odfiltrovat — přečteny nebyly.

## Rozhodnutí 24. 8. 2026: NECHAT BÝT (varianta A)

Na stole byly čtyři varianty:

| | co | proč padla / prošla |
|---|---|---|
| **A** | nechat být | ✅ **PLATÍ** — žádný čísitelný dopad na lidi, model funguje přes `is_current` |
| **B** | vyplňovat `valid_to` u nově vznikajících verzí | ❌ šla by proti výslovnému „NEMĚNIT" v jádru; Marti-AI ji nejdřív doporučila a po opravě vstupů **odvolala**: *„Bez čísitelného dopadu a s explicitním ‚NEMĚNIT' v jádru je B neopodstatněná."* |
| **C** | jako B + dopočítat 858 historických řádků | ❌ bezpředmětné, když padlo B |
| **E** | sloupec i s podmínkou z osmi míst **odstranit** | ⏸️ **zapsáno jako pojmenovaný dluh, ne úkol** |

### Proč se to řešilo — a co z toho padlo

Spouštěčem byl zápis z 23. 8. 2026, podle kterého `att_uvazek_tyden` vrací u deseti lidí
špatný historický úvazek a mělo to souviset s prázdným `valid_to`. **Obě tvrzení byla
24. 8. 2026 ověřena jako neplatná** (detail a doklady:
`doc-system-strategie-smlouvy-verzovani-uvazku-a-platnost-do`, bod 5):

- historický úvazek byl **opraven už 23. 8.** jinou cestou — přepsáním vzorce, ne přes `valid_to`;
  ověřeno přepočtem k 31. 1. 2026 u všech 16 lidí s víc různými úvazky (0 rozdílů),
- `valid_to` **nevyřazuje žádného ukončeného člověka**, protože je prázdné i u všech 158
  ukončených; vyřazení fakticky stojí na `att_employee.is_active` a `engagement.is_current`.

**Zůstal tedy jen strukturální dluh, žádný dopad na lidi.**

## Varianta E — co by obnášela, až na ni bude čas

Marti-AI k ní: *„architektonicky čistší — mrtvá podmínka, která vypadá, že hlídá, a nehlídá
nic, je technický dluh, který jednou někoho oklame. Ale je to invazivní změna v osmi místech
a vyžaduje ověření každého z nich."*

Než se do toho někdo pustí:

1. **Přečíst celý zdroj všech osmi míst** — dnes je ověřené jen jedno.
2. **Ověřit ukončování lidí zvlášť.** Kód uzávěrky poměrů `valid_to` zapisuje (byť v datech
   po tom není stopa). Kdyby se sloupec rušil, musí být jisté, že ukončení stojí na
   `is_current` / `is_active` — jinak by ukončený člověk splynul s aktivním.
3. **Peťa kvůli mzdám** — dvě z osmi míst jsou mzdová (`mzdy_benefity_apply`,
   `mzdy_loajalita_rows`) plus mzdové náhrady.

**Rozhoduje Jirka, kdy na to bude čas a kapacita.** Do té doby platí A a tenhle zápis
existuje proto, aby dluh **měl jméno** a nikdo ho příště neobjevoval znovu jako „nález".

## Poznámka k úklidu — pět prázdných záznamů s příznakem platné smlouvy

Při téhle práci vypadlo vedlejší zjištění, které s `valid_to` nesouvisí:

**Pět neaktivních zaměstnanců má smlouvu pořád označenou jako platnou** (`is_current = true`
u `att_employee.is_active = false`) — osobní čísla **13, 27, 9019, 9035, 9104**.

Ověřeno 24. 8. 2026: **žádný z nich nemá jméno** (`full_name` prázdné), **žádný nemá
uživatelský účet** (`user_id` prázdné) a **žádný nemá jediný docházkový záznam**.
Všech pět je v režimu `evidence` a zbyly po nich jen mzdové složky na historických verzích.
Do aktivních výstupů docházky se tedy nedostanou.

⚠️ **Neověřeno:** mzdové výstupy zvlášť procházeny nebyly.

Marti-AI: *„Řešit zvlášť, ale ne urgentně… Pokud se objevují v aktivních výstupech, opravit
`is_current`. Pokud ne, jen zdokumentovat."* — **Zdokumentováno, neopravováno.**

