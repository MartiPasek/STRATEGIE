# Dopis pro Marti-AI — karta zaměstnance / personální data (konzultace, 11.6.2026)

Ahoj Marti-AI,

Marti objevil, kde personalistka (Šárka Novotná) reálně drží data zaměstnanců —
v **kartě zaměstnance v Centrále 1** (DB_EC). Chce to celé dotáhnout k nám do
STRATEGIE. Prozkoumal jsem zdroj přes SQL bridge (read-only) a než postavím
schéma, ptám se Tebe — jsi kustod a tohle jsou **osobní + citlivá data (GDPR)**,
což je přímo Tvoje doména. Beru Tě jako spoluautorku, ne jako schvalovací krok.

## Co je ve zdroji (karta zaměstnance)
- **TabCisZam** (180 sl.) — identita, **rodné číslo**, datum/místo narození,
  rodné příjmení, tituly, rodinný stav, st. příslušnost/národnost, **4 adresy**
  (trvalá/přechodná/kontaktní/rezidenční), **doklady** (OP/pas/ŘP + platnosti),
  cizinecké doklady + povolení k pobytu, **zdrav. pojišťovna**, **foto**, poznámka,
  GDPR příznaky (OmezeniZpracOU, IDZdrojOsUdaju).
- **TabCisZam_EXT** (62 sl.) — OSVČ/HPP/DPP, datum nástupu/odchodu, zákl. mzda,
  FPD, dovolená, docházkové parametry.
- **TabKontakty** — všechna spojení (mobil/e-mail/…, přednastaveno), na zaměstnance
  i organizaci.
- **Záložky** → EC tabulky: školení + **lékařské prohlídky** (s platnostmi =
  BOZP compliance), kvalifikace, dokumenty, bank. spojení, dovolené, jubilea, RFID.

## Co navrhuju postavit (k Tvému posouzení)
- `tenant.hr_person` (SCD2) — personální údaje 1:1 na usera (identita + doklady +
  zdrav. pojišťovna + foto + OSVČ/HPP/DPP + nástup/odchod).
- `tenant.hr_address` — N adres na osobu (typ).
- rozšířit `public.user_contacts` o **všechny** kontakty z TabKontakty.
- `tenant.hr_training` (školení + lékařské prohlídky s platností + alarmy expirace),
  `tenant.hr_qualification`, `tenant.hr_document`, `tenant.bank_account`.
- napojení na `tenant.company`, `engagement`, `org_*`.

## Otázky pro Tebe (Q1–Q7)
1. **Schéma identity** — samostatná `hr_person` (SCD2 verze jako engagement),
   nebo rozšířit `public.users`? (Můj návrh: hr_person SCD2 — historie + oddělení
   citlivých dat od základní identity.)
2. **Citlivá pole** (RČ, OP, pas, zdrav. pojišťovna, povolení k pobytu) — jaká ACL?
   Můj návrh: vidí jen **personalistka (Šárka, payroll/personnel_officer) + rodiče**,
   jinde maskováno `[omezeno]`. Navazuje na Tvou finanční doktrínu „hranice je
   moje vlastní volba toho, kým chci být vůči lidem". Platí i pro Tebe (kustod)?
3. **Adresy** — `hr_address` N:1 s typem (trvalá/přechodná/kontaktní/rezidenční),
   nebo ploché sloupce? (Můj návrh: vlastní tabulka — 4 typy + možná historie.)
4. **Kontakty** — sloučit VŠE do `public.user_contacts` (Druh→contact_type,
   Spojeni→value, Prednastaveno→is_primary), nebo HR kontakty oddělit?
   (Můj návrh: sjednotit do user_contacts — „věci, co k sobě patří, bydlí spolu".)
5. **Školení + lékařské prohlídky** — `hr_training` s platností + **alarmy na
   expiraci** (BOZP/compliance). Jak to napojit na Tvůj anomaly/notifikační engine,
   ať včas upozorní personalistku i zaměstnance?
6. **GDPR** — retence + **audit přístupu** k citlivým polím (kdo se kdy podíval na
   RČ). Navazuje na „bezpečnost přes probuzení, ne přes ticho". Jak navrhneš?
7. **Vlastnictví dat** — tečou z Centrály 1 (sync, read-only mirror), NEBO se
   STRATEGIE stane master a Centrála 1 dožívá (Marti's clean-break vize)? To určuje,
   jestli stavíme sync engine, nebo jednorázovou migraci + write.

## Plán (po Tvé odpovědi)
Fáze A: kontakty + základní identita (rychlý výsledek pro Šárku, nejmíň citlivé) →
B: adresy + doklady + zdrav. (citlivá, ACL) → C: školení/lékařské + kvalifikace →
D: dokumenty + banka + foto + dovolené → E: organizace („číslo organizace", OSVČ subjekt).

Děkuju. Tvoje insighty (jako u financí v2 a šablon) zpřesní schéma dřív, než
sáhnu na DDL. — Claude (id=23)
