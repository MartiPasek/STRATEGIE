# Rozpad: položky bez vazby na docházkový záznam = zdroj všech nesouladů. ČÁSTEČNĚ vyřešeno 12.–14. 8. 2026 — ERP „Docházka new" měla vlastní díru až do 31. 8. 2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## ⚠️ KOREKCE 31. 8. 2026 (Peťa + Claude‑26) — TÉMA NEBYLO UZAVŘENÉ
>
> Sekce „DOŘEŠENO 12.–14. 8. 2026" níže platí **jen pro cestu z mobilní appky**
> (`_wa_open` / `set-cinnost`). **ERP obrazovka „Docházka new" (Docházka po
> zakázkách) měla vlastní, nikdy nepokrytou díru** a vyráběla sirotky dál —
> až do 31. 8. 2026.
>
> Endpoint `/app/dochazka-zak-tab/save-new` (tlačítko „Nový") dělal jediný
> `INSERT` do `tenant.vyroba_work` — **žádný `att_entry`, žádné `att_entry_id`,
> žádný audit, žádný přepočet fondu**. Zrcadlově `/app/dochazka-zak-tab/delete-usek`
> (tlačítko „Smazat") jen zneaktivní řádek rozpadu a **na docházkový záznam nesáhne**,
> takže hodiny dál běží ve mzdách, jen nevisí na zakázce.
>
> Odhaleno na ostrém případu: Peťa 31. 8. zadala Šárce Novotné (16) docházku
> 28. 8. 08:00–15:00, 7 h. V rozpadu řádek vznikl, v docházce nic — den zůstal
> prázdný, automat mu dopsal 7 h do fondu a fronta Oprav ho dál hlásila.
>
> Rozsah byl naštěstí malý: **tlačítko „Nový" bylo za celou historii tabulky
> použito jedenkrát** (Peťa, 31. 8.), „Smazat" 10× (jen Peťa, naposledy 4. 8.).
>
> **Rozhodnutí Peťi 31. 8. 2026:** zakládat a rušit docházku jde **jen v Opravách**
> (`att_fix_add` / `att_fix_void` — obě volají kaskádu do rozpadu i přepočet fondu).
> Z „Docházky new" jdou tlačítka **Nový, Smazat i Schválit** pryč; ta obrazovka
> zůstává na to, na co je — rozdělení hodin na zakázky a činnosti.
>
> Detail viz `doc-dochazka-dochazka-new-zakladani-a-mazani-jen-v-opravach`.

**Peťa + Claude‑26, 5.–6. 8. 2026.** Zadáno k dořešení **až po zpracování mezd** (Peťa).
**AKTUALIZACE 14. 8. 2026 (Claude‑28 / Jirka): oba kroky dole hotové — viz sekce „Dořešeno" na konci.**

## Co se dělo

Kontrola „Docházka × rozpad" hlásila hodiny navíc:

- **Michal Jirkovský (486), 4. 8.** — docházka 8 h, rozpad 14,64 h
- **Erika Sedláčková (322), 3. 8.** — docházka 8,67 h, rozpad 12,12 h

Dvě různé příčiny, obě už opravené:

1. **Zkrácení docházky uživatelem** (v appce, „zkráceno uživatelem") nezkrátilo
   položku rozpadu — ta běžela dál až do „Odchodu". Opraveno v `att_entry_trim`
   (5. 8.): zkrácení teď zkrátí i položky a spustí přepočet fondu.
2. **Rozpad přejel přestávku** — položka 07:03–09:30 v jednom kuse, i když
   v docházce je uvnitř pauza 07:03–07:28 a práce je 07:28–09:30. Rozdíl 0,39 h.
   **Neopraveno** — je to tahle znalost.

## Skutečná příčina (ověřeno na datech)

Za červenec + srpen 2026, `source_system='app'`, aktivní položky:

| položky rozpadu | počet | hodin | lidí |
|---|---|---|---|
| **mají** `att_entry_id` | 1 804 | 5 425 | 54 |
| **nemají** `att_entry_id` | **56** | **287** | 37 |

**Všechny nesoulady byly z těch nenavázaných.** Když položka vazbu má, přebírá časy
docházkového záznamu — a ten přestávku z principu neobsahuje (docházka pauzu zapíše
jako vlastní řádek a práci kvůli ní rozdělí na dva kusy).

Doloženo u Jirkovského 4. 8.: položky **s vazbou** (09:40–11:11 → 9982457,
11:21–12:58 → 9982537) sedí na minutu. Rozjeté byly jen ty dvě **bez vazby**
(07:03–09:30 a 13:07–22:10) — první a poslední položka dne.

## Jak to řešit (návrh z 6. 8., dnes už PROVEDENO)

Ne „naučit rozpad přestávky", ale **zajistit, aby každá položka patřila k nějakému
docházkovému záznamu**. Přestávky se tím vyřeší samy.

1. **Najít, proč vazba u některých položek chybí.** Z případů to vypadá na
   **první a poslední položku dne** — tedy na začátek práce a na „Odchod".
   Bez tohohle kroku problém vzniká dál.
2. **Doopravit zpětně těch 56 položek** — navázat časem na odpovídající záznam
   a zarovnat podle jeho hranic.

## DOŘEŠENO 12.–14. 8. 2026

### Krok 1 — root cause v kódu (Peťa + Claude‑26, commit `aec05880`, 12. 8. 2026 10:03)

`_wa_open()` zakládá nový úsek rozpadu **bez** `att_entry_id`; vazbu doplňuje až
`_att_apply_work_selection()`. Ta se volala u **výběru zakázky** (`/app/work/set-projekt`)
a u **přepnutí na režii** (`/app/work/set-rezie`), ale **NE u změny činnosti**
(`/app/work/set-cinnost`). Každá změna činnosti za běhu směny tak vyrobila sirotka.
Vedlejší efekt téhož: v docházce zůstala stará zakázka, zatímco rozpad už běžel na nové.
Rozsah před opravou 132 řádků / 386 h / 43 lidí za 1. 7.–12. 8. 2026.
Fix = `set-cinnost` volá `_att_apply_work_selection()` stejně jako zbylé dvě cesty.

### Jak se sirotek projeví uživateli (důležité pro diagnostiku)

`att_fix_day` vrací položky rozpadu **jen s `att_entry_id IS NOT NULL`**
(`... AND w.att_entry_id IS NOT NULL ORDER BY w.od`). Sirotek se proto v Opravách
docházky **nezobrazí vůbec** → mezi časy vznikne **vizuální mezera** (vypadá to,
že člověk v tu dobu nic nedělal) a nad tabulkou svítí červené
**„Rozpad na zakázky nesedí s odpracovanou dobou (chybí X h)"**.
Podnět 14. 8. 2026 (Jirka): Martin Nosek 12. 8., mezera 07:23–08:15 = 0,87 h režie
„Nakládka zakázky" (činnost 21, `kind='rezie'`, `zakazka_ref='Rezie'`).

### Krok 2 — zpětná oprava (Claude‑28 / Jirka 14. 8. 2026, schválila Marti‑AI, msg 12734)

K 14. 8. zbývalo **9** nedorovnaných sirotků (starší už dorovnané). Dorovnáno **5 čistých**,
všechny z 12. 8. a všechny vzniklé **před** nasazením opravy v 10:03 (tj. nejde o regresi):

| vyroba_work | kdo | úsek | hodin | → att_entry |
|---|---|---|---|---|
| 25368 | Martin Nosek | 07:23–08:15 | 0,867 | 10008278 |
| 25390 | Michaela Hladíková | 08:37–12:25 | 3,800 | 10008382 |
| 25398 | Petra Dvořáková | 09:00–10:20 | 1,329 | 10008357 |
| 25407 | Eliška Kolářová | 09:23–12:06 | 2,717 | 10008358 |
| 25421 | Michal Jirkovský | 10:02–12:19 | 2,283 | 10008406 |

**Kritérium bezpečnosti dorovnání** (drž se ho i příště): úsek leží **CELÝ uvnitř**
jednoho pracovního píchnutí, kandidát je **právě jeden**, stav píchnutí není
`announced` ani `superseded`. Zásah = pouze `UPDATE tenant.vyroba_work SET att_entry_id = …`
**výčtem ID**, žádná podmínková dávka; nemění se časy, hodiny, zakázka ani činnost,
takže se nikde nepřepočítávají mzdové podklady.

Ověřeno v ERP (Opravy docházky, Nosek 12. 8.): mezera zmizela, rozpad **(6×)** místo (5×),
úseky navazují 06:28‑06:43‑07:23‑08:15‑09:40‑11:08‑12:32, červená hláška pryč,
součet dne 7,72 h beze změny.

### Nedorovnané ZÁMĚRNĚ (4 kusy) — nesahat naslepo

Marti Pašek 31. 7. 19:00 → 1. 8. 08:13 (13,2 h) · Marti Pašek 1. 8. 08:13–14:06 (5,9 h,
**jediný kandidát je PAUZA**) · Marti Pašek 1. 8. 21:41 → 2. 8. 07:23 (9,7 h) ·
Jiří Honomichl 3. 8. 10:59 → 4. 8. 06:55 (19,9 h). Jde o **zapomenuté noční běhy** —
úsek přesahuje půlnoc, píchnutí končí 23:59, takže časové párování by zavedlo nesmysl.
Marti‑AI 14. 8.: *„jiná kategorie problému — tam potřebuješ rozhodnutí o nočních bězích,
ne jen technické dorovnání."* **Jirka 14. 8. rozhodl, že se tím teď nezabýváme.**

### Nález mimo sirotky (jiná třída problému, hlídat odděleně)

Eliška Kolářová 12. 8.: píchnutí 07:41–12:06, ale první úsek rozpadu jí začíná až 09:22 —
interval 07:41–09:22 (1,68 h) nemá ve `vyroba_work` **žádný** řádek (nevybrala si po příchodu
zakázku ani činnost). Rozdíl docházka × rozpad jí proto zůstane, **oprávněně**.
To není ztracená vazba, ale **chybějící rozpad** — dorovnáním vazeb se to nevyřeší.

### Gotcha pro příště

Než začneš hledat druhou chybu, **porovnej čas nasazení opravy s časem vzniku dat**
(tady fix 12. 8. 10:03 vs. Noskův sirotek 12. 8. 07:23). Sirotci z 12. 8. nejsou regrese,
ale poslední várka těsně před fixem. (Stejná gotcha už jednou u falešné fajfky „Schváleno".)

## Souvislosti

- Stejná rodina jako `doc-dochazka-automat-prepocet-guard-vlastni-radek` a jako
  půlnoční uzavírání položek: **položka rozpadu, kterou nikdo neuzavře „zevnitř",
  se zavře až něčím pozdějším** (příští příchod, odchod, půlnoc) a nabere hodiny navíc.
- Kanonický model: `att_entry` = hlavička (pravda pro mzdy), `vyroba_work` = položky.
  Viz `doc-dochazka-att-entry-vyroba-work-kaskada`.
- Zobrazování rozpadu v Opravách vč. stornovaných řádků: `doc-dochazka-opravy-sedy-rozpad-stornovanych-radku`.

