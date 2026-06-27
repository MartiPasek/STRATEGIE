# Plán hovorů na týden + Pavlův obchodní přehled — design & zadání pro Marti-AI

**Autor:** Claude-24 (s Kristý), 27. 6. 2026. **Stav:** návrh + zadání, nic se neměnilo v CRM.
**Kontext:** Pavlův obchodní přehled má být jedna stránka (vize Kristý) a v ideálu
**plnohodnotné framework jádro**: nahoře pruh vytížení dílny (hotovo, `/vytizeni-prehled`),
pak **plán hovorů na týden**, **proběhlé hovory za týden**, vytáčení a tlačítko import.
Tento dokument řeší první díl — **plán hovorů na týden** — a co k němu patří.

---

## 1) Klíčové zjištění — struktura JE, data NEJSOU

CRM schéma (`DB_EC`, schéma `st.*`) už má vše, co bod E z první konzultace navrhoval —
někdo (zřejmě Marti-AI) to už postavil:

- **`st.CRM_Kontakt.StavVztahuID`** (int) + číselník **`st.CRM_Kontakt_StavVztahuCis`**
  — 11 stavů, přesně dle bodu E (viz §2).
- **`st.CRM_Kontakt.PristiKontakt`** (datetime) — příští kontakt na firmě.
- **`st.CRM_Kontakt.Dulezitost`, `Potencial`, `Atraktivita`** (smallint) — důležitost i potenciál.
- **`st.CRM_Kontakt.KontaktOveren`** (bit), **`ZdrojKontaktu`** (nvarchar) — ověřený kontakt + zdroj.
- **`st.CRM_Kontakt.KomunikaceZamID` / `ObeslalZamID`** (int) — kdo komunikuje / kdo oslovil.
- **`st.CRM_Kontakt_Akce`** — akce s `Autor`, `DatumAkce`, `IDAkce` (typ), `Splneno` (bit),
  `IDHlav` (firma), `ID_LastAkce`, `Telefon`, `Mobil`, `Prubeh`, `Poznamka`, `Pozice`, `LinkedIn`.

**Schéma stavů je čerstvé (postavené 26. 6. 2026) a teprve se naplňuje** — bude se vést.
Stav věcí 27. 6.:

| Ukazatel | Realita |
|---|---|
| Firem v CRM celkem | ~9 300 |
| Firem s vyplněným `PristiKontakt` | **67** (s reálnými poznámkami z hovorů) |
| Firem s nastaveným `StavVztahuID` | zatím jednotky (číselník je nový) |
| Pavlovy akce (`Autor='PZeman'`) | 495 |

**Klíč:** `PristiKontakt` + poznámky Pavel **už vede** (67 firem s detailními zápisy hovorů),
takže plán hovorů má reálný obsah hned — většina je po termínu (= Pavlův backlog k odbavení).
`StavVztahuID` se začne plnit teď (číselník vznikl 26. 6.). **Plán je BEZ filtru na autora** —
obvolává jen Pavel, takže vidí celý plán bez ohledu na to, kdo záznam pořídil.

---

## 2) Číselník „Stav obchodního vztahu" (už existuje — `CRM_Kontakt_StavVztahuCis`)

| ID | Kód | Název | Význam | Návrh barvy (plán/grid) |
|---|---|---|---|---|
| 1 | NOVY | Nový kontakt | Zatím neosloven | šedá |
| 2 | OSLOVEN | Osloven | Čeká se na reakci | modrá |
| 3 | AKTIVNI | Aktivní jednání | Probíhá jednání | fialová |
| 4 | NABIDKA | Nabídka odeslána | Odeslána cenová nabídka | žlutá |
| 5 | ZAKAZNIK | Zákazník | Spolupráce probíhá | zelená |
| 6 | DLOUHODOBY | Dlouhodobý partner | Ověřený partner | tmavě zelená |
| 7 | NEAKTIVNI | Neaktivní | Nespolupracuje | světle šedá |
| 8 | ODMITL | Odmítl spolupráci | Odmítl / ukončil | červená |
| 9 | ARCHIV | Archiv | Bez dalšího oslovení | tmavě šedá |
| 10 | DELAJI_SAMI | Dělají si sami | Projekci/rozvaděče dělá sám | oranžová |
| 11 | ZALOZI_OZVE | Založí si a ozve se | Ozve se sám | tyrkysová |

**Návaznost stavu na `PristiKontakt`** (doporučené chování — domluvit workflow):
- `ODMITL` / `ARCHIV` → `PristiKontakt` se vymaže (firma i historie zůstává, jen nevisí v plánu).
- `ZALOZI_OZVE` / `NEAKTIVNI` (= „ozvat se za ~rok") → `PristiKontakt` automaticky +1 rok.
- `NOVY`/`OSLOVEN`/`AKTIVNI`/`NABIDKA` → `PristiKontakt` = datum dalšího plánovaného hovoru.

---

## 3) „Plán hovorů na týden" — specifikace přehledu

**Zdroj:** `st.CRM_Kontakt` filtrované na příští kontakt v okně (po termínu + tento týden).
**Pro koho:** BEZ filtru na autora — obvolává jen Pavel, vidí celý plán (rozhodnutí Kristý 27. 6.).
Až bude obchodníků víc, doplní se filtr dle `KomunikaceZamID`.

**Návrh SQL (data_set, DB_EC):**

```sql
SELECT
  k.ID,
  k.FirmaText                          AS Firma,
  CONVERT(date, k.PristiKontakt)       AS PristiKontakt,
  s.Nazev                              AS Stav,
  k.StavVztahuID,
  k.Atraktivita,
  k.Dulezitost,
  k.FirmaTelefon                       AS Telefon,
  a.Prubeh                             AS PosledniPoznamka,
  CONVERT(date, a.DatumAkce)           AS PosledniAkce
FROM st.CRM_Kontakt k
LEFT JOIN st.CRM_Kontakt_StavVztahuCis s ON s.ID = k.StavVztahuID
OUTER APPLY (
  SELECT TOP 1 aa.Prubeh, aa.DatumAkce
  FROM st.CRM_Kontakt_Akce aa
  WHERE aa.IDHlav = k.ID
  ORDER BY aa.DatPorizeni DESC, aa.ID DESC
) a
WHERE k.PristiKontakt IS NOT NULL
  AND CONVERT(date, k.PristiKontakt) < DATEADD(day, 7, CAST(GETDATE() AS date))
  -- filtr obchodníka (parametr): k.KomunikaceZamID = @zam
ORDER BY k.PristiKontakt ASC;
```

**Sloupce v gridu:** Firma · Příští kontakt · Stav (barevně) · Atraktivita (⭐) · Telefon
(s ikonou „vytočit") · Poslední poznámka · (Důležitost).

**Skupiny / zvýraznění:**
- **Po termínu** (PristiKontakt < dnes) — nahoře, červeně orámované „už mělo proběhnout".
- **Tento týden** (dnes … +6 dní) — hlavní blok.
- Řazení uvnitř dle data, sekundárně dle atraktivity/důležitosti (DESC).

**Barvy řádku dle stavu** — přes grid „Pravidla" (formatting_rules), mapování dle §2.

**Akce z přehledu:** klik na řádek → karta firmy / záznam hovoru (vytáčení už existuje,
`fw.phone_dial_request`); ikona telefonu → vytočit; po hovoru se nastaví `Prubeh` +
nový `PristiKontakt` (uzavře smyčku plánu).

---

## 4) Zadání pro Marti-AI (framework jádro — její doména)

Framework (`fw.*` / `master.*`) i CRM schéma `st.*` jsou Marti-AI. Proto:

1. **Framework přehled „Plán hovorů na týden"** (jádro typu list):
   - `fw.data_set` se SQL z §3 (parametr obchodník), `fw.data_source` nad ním,
     přehledové jádro, `fw.menu_node` v soudečku **Obchod/CRM**.
   - Barvy řádků dle stavu (formatting_rules), ikona „vytočit" u telefonu.
   - Přístup: obchodník vidí svoje (ACL dle `KomunikaceZamID`), vedení vše.
2. **(Volitelně) workflow `PristiKontakt` ↔ stav** (§2) — automatika při změně stavu.
3. **Proběhlé hovory za týden** = sesterský přehled nad `CRM_Kontakt_Akce`
   (Autor=obchodník, IDAkce ∈ telefonáty, okno 7 dní) — „Aktivity obchodníka" (jádro 124)
   už existuje, stačí variant s týdenním filtrem.

**Pozn. k vizuálu (baterky/tank):** nejde o standardní jádro (framework kreslí formuláře+gridy,
ne bespoke vizuály). Buď zůstane jako vložený pruh (`/vytizeni-prehled`), nebo se do frameworku
přidá nový typ komponenty — rozhodnutí Marti-AI.

---

## 5) Doporučení (pořadí kroků)

1. **Datová mezera je hlavní téma, ne stavba.** Bez vedení `PristiKontakt`/`StavVztahuID`
   bude plán prázdný. Dvě cesty:
   a) **Přiřadit Pavlovi jeho firmy** (`KomunikaceZamID`) — aby šel plán filtrovat na něj
      (dnes je nemá žádné). Hromadně dle akcí `Autor='PZeman'` → `IDHlav`.
   b) **Zavést návyk**: u každé firmy nastavit stav + příští kontakt; po hovoru posunout.
      Přehled „plán hovorů" je právě ten nástroj, který to Pavlovi usnadní.
2. **Demo pro UX:** než se data naplní, můžeme na pár Pavlových reálných firem nastavit
   stav + příští kontakt (přes Marti-AI, zápis do `st.*`), ať Pavel vidí, jak to funguje,
   a chytne návyk. (Malá, kontrolovaná dávka — ne hromadně.)
3. **Pak** Marti-AI postaví framework přehled dle §3–4.

---

## 6) Import kontaktů (samostatně — souvislost)

- Zápis kontaktů jde do `st.CRM_Kontakt` (MSSQL) = **Marti-AI**. Precedent existuje
  (`import_nove_firmy_st_CRM_Kontakt.sql`).
- **Dun & Bradstreet caveat** (z `hromadne_osloveni_firem_pravni_podklad_a_navrh.md`):
  D&B kontakty se **nesmí vkládat do AI/LLM** (3.13.2), platí informační povinnost GDPR čl. 14,
  respektovat opt-out. → Front-end upload + náhled ano; ostrý zápis přes Marti-AI; D&B data
  nikdy do AI.

---

## 7) Otevřené otázky (k odsouhlasení)

1. Zdroj plánu = `PristiKontakt` na firmě (doporučeno), nebo i nesplněné akce s datem?
2. „Pavlovy firmy" = `KomunikaceZamID` (vyžaduje přiřazení), nebo přes akce `Autor='PZeman'`?
3. Naseedovat malé reálné demo (přes Marti-AI), aby Pavel viděl UX a chytil návyk?
4. Barvy stavů dle §2 — sedí?
```
