# Správa docházky × Docházka new — co se překlápí a co ne (Peťa 30.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Správa docházky × Docházka new — co se překlápí a co ne

**Rozhodla Peťa 30. 7. 2026**, podle toho, jak to fungovalo v Centrále. Zapsal Claude‑26.
Nový slug schválně — `doc-dochazka-schvalovani-dovolene` (21.7.) popisuje model schvalování,
tohle je pravidlo o překlápění mezi dvěma přehledy. Nepřepisovat jeden druhým.

## Pravidlo

| Druh | Do Docházky new? | Proč |
|---|---|---|
| **Dovolená (D i DN), sick day** | **ANO, hned** | Peťa: „nemůže se nám to nepropisovat kvůli schválení, když ti lidi tu dovolenou měli." Dny se generují podle pravidel (pracovní dny z kalendáře × hodiny/den) **bez ohledu na `stav` žádosti**. Schvalování běží vedle, neblokuje zápis — jako v Centrále. |
| **Home office** | **NE, schválně** | V Centrále se HO zadával do Správy docházky jen jako **informace „nebudu ve firmě"** a do docházky se nikdy nepřeklápěl — tam si ho člověk zapsal znovu **podle skutečnosti** (z domova mohl odpracovat jinak, než plánoval). Držet stejně. Kdo bude v budoucnu „srovnávat" Správu s Docházkou new, tohle NENÍ nesrovnalost k opravě. |
| **Lékař, nemoc (PN), OČR** | z dokladů, ne ze žádosti ani z plánu | Zadává se z reálného dokladu (neschopenka, potvrzení). Do doladění s Kristý. |
| **Plán z Centrály** | ANO, ale jen do dneška | Viz níže. |

## Plán je plán jen dopředu

Peťa: *„plán je to dopředu; dovolená 31. 7.–8. 8. je plán, ale zítra už je plán jen 1.–8. 8.
a 31. 7. se musí ukazovat v Docházce new."*

Do 30. 7. Docházka new vynechávala **všechny** absence se `source='plan_ec'`. Dávalo to smysl,
dokud Centrála žila (plán vs. skutečnost by se zdvojily), ale po jejím zmrazení skutečnost
přestala chodit a zbyl **jen plán, který nikdo neukázal** → 59 dnů u 15 lidí (hlavně 23.–31. 7.)
nebylo vidět ani v práci, ani na dovolené. Filtr odstraněn z absenční větve datasetu
`dochazka.zakazky_vse_list` (30. 7., ověřeno: 0 minulých dnů má zároveň plán i skutečnost,
takže nehrozí zdvojení).

**Překlopení řeší samo datum** — přehled filtruje `d <= CURRENT_DATE`, počítané při každém
otevření stránky. Žádná noční úloha, není co selhat. Databáze běží v `Europe/Budapest`
(= náš čas), takže se to přepne **o naší půlnoci**.

## Gotchy (draze zaplacené 30. 7.)

- **⚠️ `ux_att_entry_source` dovoloval jen JEDEN den na žádost.** Unikát byl
  `(tenant_id, source_system, source_id)` bez `entry_date`, takže schválení **vícedenní**
  dovolené zapsalo první den a zbytek spadl — žádost se přitom označila jako vyřízená.
  Doloženo: z žádné žádosti se nikdy nepropsal víc než 1 den, a 3 vícedenní žádosti byly
  označené jako promitnuté. Opraveno na `ux_att_entry_source_den` (+ `entry_date`).
  **Kdo bude sahat na materializaci absencí, ať tenhle index nevrátí zpět.**
- **⚠️ `NOT EXISTS` uvnitř jednoho `INSERT ... SELECT` nevidí řádky, které sám zakládá.**
  Při zpětném promítnutí žádostí vzniklo 8 zdvojených dnů u lidí, kteří si tutéž dovolenou
  zadali víc žádostmi (Čiviš 3×). Při hromadném promítání **deduplikovat předem**
  (DISTINCT ON employee+den), ne spoléhat na `NOT EXISTS`.
- Žádost, která **není promítnutá** (`materialized=false`), je ve Správě docházky vidět
  jako řádek `Z:<id>`, ale v Docházce new být NEMŮŽE — neexistuje k ní žádný den.
  To není skrytí ani filtr.

## Co se 30. 7. udělalo

- Sloupce **Zdroj** a **Číslo řádku** ve Správě docházky (dataset Jirka) + české popisky zdrojů.
- **Úprava / přidání / smazání absencí** přímo v přehledu →
  `modules/erp/api/dochazka_absence_sprava.py` (endpointy `/app/dochazka-abs/{meta,save,new,delete}`).
  Storno nasazuje `local_lock=true` (jinak synchronizace řádek oživí = dvojité hodiny, viz Jirka).
- Dovolená a sick day se **promítají hned** — `abs_promitni_zadost()` volané ze
  `/app/attendance/absence/request`. Idempotentní, pozdější schválení si materializaci přepíše.
- Zpětně promítnuto **23 nepromítnutých žádostí** (14 lidí, nejstarší z 22. 6.).

## Otevřené

- **Když vedoucí žádost po propsání zamítne** — den v docházce zůstane. Peťa 30. 7.:
  „to budeme řešit, až to někdo bude řešit."
- **Lékař / nemoc / OČR z dokladů** — dořešit s Kristý.
- **Nárok na dovolenou se nepočítá** — `holiday_balance` má všem plochých 200 h. Pravidla
  (`entitlement_rule`: 200 h + 8 po 10/15/20 letech) i individuální nároky
  (`engagement_entitlement`) v DB jsou, jen je nikdo nespojil. Porovnáno s tabulkou od Šárky:
  **60 z 62 lidí sedí** (neshoda jen u dvou nováčků, kterým Šárka krátí nárok podle nástupu).
  Proto přepočet mění jen `cerpano_h`, `zbytek_h` se schválně nesahá.
## DOPLNĚNO 25. 8. 2026 — pravidlo o home office se rok nedodržovalo (Peťa + Claude-26)

Pravidlo z tabulky výše (*„home office se do Docházky new nepřeklápí, schválně"*) **v přehledu
„vše" nikdy zapojené nebylo.** Ohlášení home office tam visela mezi odpracovanou prací.

### Jak se ohlášení pozná — PODLE DAT, ne podle značky

| Co to je | Jak vypadá v datech | Kam patří |
|---|---|---|
| **Ohlášení** „nebudu v práci, budu doma" | typ home office, **bez hodin i bez času** | jen Správa docházky, tam šedě |
| **Reálně odpracovaný home office** | typ home office, **má čas nebo hodiny** | Docházka new i Opravy — edituje se a počítá |

**Proč podle dat a ne podle značky původu:** mobilní aplikace značku `ohlaseni` často nezapíše.
24. a 25. 8. 2026 tak přibylo **pět ohlášení Veverkových** úplně bez značky — a ta by přes
kontrolu podle značky prošla. Rozlišení podle dat funguje vždycky, bez ohledu na to,
co appka zapíše.

### Kde to je zapojené (tři místa, každé jinak)

- **Opravy docházky** (`att_fix_day`) — vylučuje podle **značky** (`absence_req`, `ohlaseni`), od 19. 8. 2026
- **Správa docházky** (`dochazka.zakazky_budoucnost_list`) — podle **značky**, od 19. 8. 2026
- **Docházka new** (`dochazka.zakazky_vse_list`) — podle **dat** (bez hodin a bez času), **od 25. 8. 2026**

Hlídá to pojistka **`ho-ohlaseni-nepatri-do-oprav`** (kontroluje všechna tři místa)
a **`ho-ohlaseni-z-mobilu-ma-znacku`** (že nová ohlášení dostávají značku).

### Gotcha, která to způsobila

24. 8. 2026 se filtr doplňoval do obou přehledů příkazem, který **nahrazuje text**. Do přehledu
„budoucnost" se doplnil, do „vše" ne — ten hledaný text tam totiž vůbec nebyl (přehled „vše"
má úplně jinou podmínku). Příkaz přesto ohlásil **„2 řádky dotčeny"**, protože se řádků
opravdu dotkl, jen v jednom nic nezměnil.

> **Poučení:** „N řádků dotčeno" u příkazu s nahrazením textu **neznamená, že se něco změnilo.**
> Vždy ověřit čtením, že tam nová podoba opravdu je. Tahle chyba stála týden, kdy pojistka
> neexistovala a nikdo o tom nevěděl.

### Zálohy

`tenant.zaloha_data_set_vse_20260825` (definice přehledu před změnou),
`tenant.zaloha_ho_ohlaseni_20260825` (pět záznamů před doplněním značky),
`tenant.zaloha_ho_ohlaseni_20260824` (17 záznamů z pondělní opravy).


