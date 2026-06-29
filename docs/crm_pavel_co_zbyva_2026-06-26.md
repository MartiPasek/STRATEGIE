# CRM pro Pavla — co je hotové a co ještě chybí

**Stav k 26. 6. 2026** (sessions Kristý + Claude-24). Řazeno podle Pavlova původního seznamu připomínek (A–H z `crm_pripominky_pavel_overeni.md`).

Legenda: ✅ hotovo · 🟡 částečně / dolaďuje se · ❌ chybí / nezačato

---

## A. Statistika práce obchodníka — ✅ z velké části hotovo
**Hotovo:** přehled „Aktivity obchodníka" (firma / typ akce / datum / splněno / je poslední / průběh) + barevné odlišení + filtrování; nad ním souhrnný pruh **„Moje CRM čísla"** (počty za obchodníka, default přihlášený uživatel).
**Chybí / ověřit:** „Je poslední" počítat **automaticky** (přes `ID_LastAkce`/`Poradi`), ať to Pavel nevyplňuje ručně.

## B. LinkedIn v číselníku akcí — 🟡 skoro hotovo
**Hotovo:** Akce grid bere **živý číselník** akcí včetně **LinkedIn (ID 21)** → Pavel ho v nabídce uvidí.
**Chybí:** doplnit LinkedIn akci **„hodnotu/skóre"**, aby se započítávala do statistiky.

## C. Formuláře akcí podle typu — ✅ hotovo (jádro), kosmetika v UI
**Hotovo:** grid „CRM Akce" má **Nový → picker typu akce → příslušné edit jádro** s automatickým seedem firmy (IDHlav) + typu (IDAkce). Per-typ jádra: 82 Osobní jednání, 129 Info o zákazníkovi, 130 Telefonát na firmu, 131 Telefonát na OO, 132 Email na info, 133 Email OO, 134 Získání firmy obecně, 135 Sem zavolej, 81 Získání kontaktu.
**Dolaďuje se:** která pole u kterého typu skrýt (memo/checkbox/výška) — řeší Kristý v UI Design.
**Odloženo:** **Zakázka (1499)** + **Poptávky (1497)** — nestavět na `dbo`, čekají na čistý zdroj v `st.`/PostgreSQL.

## D. Atraktivita / Důležitost / Potenciál — 🟡 částečně
**Hotovo:** u **Atraktivity** doplněn srozumitelný popis škály (1 nejnižší … 5 střední …).
**Chybí (na holdu):** pole **Důležitost/Priorita** + dopočítaný **Potenciál** — počká, až to Kristý probere s Pavlem (přidání nového pole do `st.` = konzultace s Marti-AI).

## E. Stav obchodního vztahu — 🟡 jádro hotové, doděláváme
**Hotovo:** pole **Stav obchodního vztahu** na kartě (ukládá + zobrazuje), sloupec **Obchodní stav** v přehledu Kontakty + **barevné odlišení** firem podle stavu.
**Chybí:**
- **2 ze 3 Pavlových extra stavů** — „Založí si a ozve se", „Nezájem – obvolat za rok". (Marti-AI zatím přidala 1/3: „Dělají si sami". Číselník je MSSQL = její doména.)
- **Automatika příštího kontaktu:** po „NE/Neaktivní/Archiv" → datum příštího kontaktu **smazat**; po „obvolat za rok" → nastavit **+1 rok**.

## F. Ověřený kontakt + zdroj kontaktu — ✅ hotovo
**Hotovo:** na kartě **Ověřený kontakt** (zaškrtávátko) + **Zdroj kontaktu** (web / telefon / LinkedIn / veletrh / e-mail / doporučení / jiné); oba sloupce i v přehledu Kontakty.

## G. Externí integrace D&B / LinkedIn — ❌ nezačato (rozhodnutí Marti)
**Strategické / nákladové:**
- **Dun & Bradstreet** — proveditelné přes oficiální placené API (licence) → AI by doplňovala firmy i kontakty.
- **LinkedIn** — scraper **nestavět** (proti podmínkám + riziko). Místo toho AI-asistovaný research + legální placené B2B zdroje (Apollo/Cognism…) + dobrá evidence LinkedIn a **veletrhů** přímo v CRM.

## H. Kampaňový nástroj (hromadné maily) — 🟡 základ hotový
**Hotovo:** funkce **„Oslovit vybrané"** — výběr firem → náhled (komu / info@ / nemá e-mail / odhlásil se) → výběr **šablony** → odesílatel **Pavel** → eviduje datum oslovení + **odhlašovací odkaz**.
**Chybí:**
- **Sledování otevření** mailu (tracking pixel) — místo nespolehlivých read-receiptů (pozor GDPR).
- **Automatický follow-up za ~14 dní** (kdo otevřel → druhý mail s obměněnou nabídkou + prezentací; kdo ne → jiná větev).
- **Ostrá hromadná rozesílka** — čeká na **právní odsouhlasení** cold-mailingu; na **německé** firmy zatím ne.

---

## Shrnutí — co reálně zbývá

**Hotovo:** C (formuláře podle typu), F (ověřený + zdroj), A a E z velké části, B skoro.

**Nejblíž k dotažení (rychlé):**
1. **E** — 2 zbývající stavy (čeká na Marti-AI) + automatika příštího kontaktu.
2. **A** — „Je poslední" automaticky.
3. **B** — skóre LinkedIn akce.
4. **C** kosmetika polí (Kristý v UI) + Zakázka/Poptávky až bude čistý `st.` zdroj.

**Vyžaduje rozhodnutí / konzultaci:**
5. **D** — Důležitost/Potenciál (Pavel + Marti-AI).
6. **H** — tracking otevření + auto follow-up + ostrý go-live (právní OK).
7. **G** — D&B licence + směr LinkedIn/veletrhy (Marti).
