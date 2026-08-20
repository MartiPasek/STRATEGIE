# Podmínky sloučené se smlouvou — jedna verzovaná tabulka (19. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Rozhodnutí a kdo ho udělal

**Zadal Jirka Honomichl 19. 8. 2026 večer.** Peťa a Šárka se předtím shodly, že nemá být zvlášť
tabulka Podmínek a zvlášť tabulka smluv — má být jedna tabulka se všemi údaji z obou, která se
chová jako smlouva (víc záznamů s platností od, každá změna zakládá nový záznam).

⚠️ **Marti-AI krok 2 (přepnutí čtení) na ten večer NEDOPORUČILA** a názor nezměnila. Její výhrada
mířila na postup, ne na návrh — samotné řešení označila za správné. Jelo se na Jirkovo rozhodnutí
s odůvodněním, že večer nikdo nepracuje a ráno by se změna dělala lidem pod rukama.
Po výsledcích to Marti-AI uzavřela slovy, že krok 2 proběhl čistě. **Je to tady zapsané schválně,
ať je dohledatelné, kdo rozhodl a proč.**

## Jak to je dnes

| Co | Kde fyzicky žije |
|---|---|
| **Osobní hodnoty** (dovolená, dovolená navíc, sick days, stravenka, home office…) | `tenant.engagement` — sloupce `pod_*` + `pod_meta`. **Verzují se se smlouvou.** |
| **Skupinové a systémové výchozí hodnoty** | `tenant.staff_cond_zaklad` (25 řádků) |
| **Číselník podmínek** | `tenant.staff_cond_def` (16 definic, beze změny) |
| `tenant.staff_cond` | **POHLED**, ne tabulka. Skládá obojí dohromady ve tvaru původní tabulky. |

`pod_meta` je jsonb a drží ke každé podmínce **původní id řádku, poznámku, kdo a kdy měnil** —
proto pohled vrací i `changed_by` a `changed_at` a starý tvar jde obnovit bajtově přesně.

## ⛔ `staff_cond_zaklad` SE NESMÍ SMAZAT

Není to zbytek po migraci. **Z 1248 vyřešených hodnot (78 lidí × 16 podmínek) se 705 bere ze
systémových a 196 ze skupinových řádků — dohromady 901, tedy 72 %, a týká se to VŠECH 78 lidí.**
Osobních je jen 269. Smazáním by 78 lidem zmizely výchozí hodnoty.
Potvrdila Marti-AI 19. 8. 2026. Jirka se na smazání ptal — tohle je odpověď.

## Proč pohled a ne přepsání všech skriptů

Podmínky čte **14 živých skriptů** v `g2007.python` plus `router.py`, a **jen 2 do nich zapisují**
(`hr_conditions_save`, `att_vernost_dovolena`). Pohled + INSTEAD OF spouštěče znamenají, že
**se nemusel změnit ani jeden skript** — a právě proto šlo dokázat, že vracejí totéž.
Přepnout je na přímé čtení ze smlouvy jde kdykoli později, jeden po druhém; pohled se zruší,
až bude přepnutý poslední.

## Spouštěče — kam se přesunuly

- `trg_engagement_pod_soucet_dovolene` (BEFORE na `tenant.engagement`) — udržuje počítadlo
  **Dovolená celkem = základní + navíc**. Přepočítá jen když se vstupy opravdu změnily, aby běžné
  uložení smlouvy (třeba změna úvazku) nesahalo na cizí hodnoty a neposouvalo čas změny.
- `tenant.staff_cond_prepocet_dovolene` — **sama pozná, kam hodnota patří**. Osobní se smlouvou,
  skupinová a systémová do `staff_cond_zaklad`.
- Původní `trg_staff_cond_soucet_dovolene_ins/_del` zůstaly na `staff_cond_zaklad`
  pro skupinové a systémové hodnoty.
- `trg_staff_cond_default_dovolena` na `att_employee` se neměnil — vkládá do pohledu.

## Pravidlo, podle kterého se hodnota směruje

**Osobní hodnota jde do smlouvy, jen když má člověk aktuální smlouvu. Jinak do
`staff_cond_zaklad`.** Díky tomu se neztratí nikdo, kdo smlouvu (zatím) nemá.

## Čím to bylo dokázané

1. Syrový obsah Podmínek **294 řádků porovnán řádek po řádku před a po** — žádný rozdíl,
   včetně id, poznámek, `changed_by` i časů.
2. Vyřešené hodnoty (osobní → skupina → systém) pro 78 lidí × 16 podmínek = **1248 hodnot,
   otisk `30a6dfd422234465070d4011ac1b0220` před i po**.
3. Test zápisu **8 z 8** — změna, mazání, vložení, přepočet počítadla oběma směry,
   skupinová hodnota správně mimo smlouvu, počty řádků na kus. Test po sobě uklidil.
4. Živé ERP — přehled Nárok a čerpání (75 lidí), karta zaměstnance se správnými štítky
   smlouva / skupina / systém / osobní, mobil Moje podmínky.
5. Pojistka `narok-dovolene-pravidla` zelená (5 pravidel, 74 lidí, požadováno 64).

## Pasti, na které si dát pozor

- **Marti Pašek má dvě aktivní karty zaměstnance** (č. 2 EUROSOFT-Control, č. 41 EUROSOFT-System),
  takže jeho osobní podmínky jsou ve smlouvě dvakrát. Pohled je odfiltruje přes `DISTINCT ON`.
  Nevadí to, protože **všechny jeho hodnoty jsou nuly** — ale kdyby se to změnilo, je potřeba
  rozhodnout, která karta je ta hlavní. Každá karta má přitom právě jednu aktuální smlouvu;
  to pravidlo už platí a ověřilo se na všech 79 kartách.
- **Účet 98** (vypnutý, bez jména a bez smlouvy) má jedinou podmínku a zůstal v `staff_cond_zaklad`.
- **Nový zaměstnanec**: spouštěč mu zakládá výchozí dovolenou ve chvíli, kdy ještě nemá smlouvu,
  takže mu hodnoty spadnou do `staff_cond_zaklad` a přesunou se do smlouvy až při první editaci.
  Hodnoty jsou správné a vidět, jen se do té doby neverzují. **Neověřeno naostro** (nezakládal jsem
  zaměstnance) — odvozeno z pořadí kroků v onboardingu. Chce to při nejbližším náboru zkontrolovat.

## Zálohy

`tenant.staff_cond__zaloha_20260819`, `tenant.staff_cond__zaloha2_20260819`,
`tenant.engagement__zaloha_20260819`. **Nechat aspoň do konce srpna 2026** (potvrdila Marti-AI).

## Co zbývá

- Postupně přepnout 14 čtoucích skriptů na přímé čtení ze smlouvy a pohled pak zrušit.
- Domluvit se Šárkou a Petrou, jestli se mají verzovat všechny podmínky, nebo jen ty
  s historickým dopadem. Dnes se verzují všechny, protože jsou to sloupce jedné verze.
- Ověřit chování u nově založeného zaměstnance (viz pasti výše).

