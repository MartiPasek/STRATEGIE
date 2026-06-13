# Karta zaměstnance (DB_EC) → dotažení do STRATEGIE — průzkum + plán

> Zadání Marti (11.6.2026): „Objevil jsem, kde jsou data zaměstnanců pro personalistku
> — v kartě zaměstnance v EC tabulce. Prozkoumej to a dotáhni k nám všechno, co
> potřebujeme. Respektive všechno."
> Kontext (e-mail Šárka Novotná, personalistka): kontakty na OSVČ jsou v kartě
> zaměstnance (spravuje Šárka), propojené na organizaci přes „číslo organizace"
> (spravuje Péťa). Karta = Centrála 1, formulář „739:4 Karta zaměstnance".

## 1. Zdroj — co karta zaměstnance reálně obsahuje (DB_EC, MSSQL)

Karta = **TabCisZam** (osobní) + **TabCisZam_EXT** (HR/mzdy/docházka) + záložky
napojené na další EC_ tabulky. Vazba na **organizaci** (TabCisOrg) přes „číslo
organizace". Příklad: Pavel Voříšek, č. 327, OSVČ od 1.8.2014.

### A) TabCisZam — osobní údaje (180 sloupců, jádro)
- **Identita:** Cislo, Jmeno, Prijmeni, RodnePrijmeni, TitulPred/Za, Pohlavi,
  DatumNarozeni, **RodneCislo** (+ bez lomítka), MistoNarozeni, StatNarozeni,
  StatniPrislus, Narodnost, RodinnyStav.
- **Doklady:** **CisloOP** + PlatnostOP + PasVydal, CisloPasu + Platnost,
  CisloRP/SkupinaRP + Platnost; cizinci: PovoleniKPobytu (Od/Do/Účel),
  Ciz_Doklad_Typ/Cislo/Vydal, SSN/RC_Cizinec.
- **Adresy (4 typy):** trvalá (AdrTrv*), přechodná (AdrPrech*), kontaktní
  (AdrKont* — vč. jména/příjmení kontaktní osoby), rezidenční (AdrRez*).
  Každá: Ulice, OrCislo, PopCislo, Misto, PSC, Zeme, Okres.
- **Zdrav. pojištění:** KodZdrPojAVA, CisloPojistenceAVA.
- **Další:** Alias (login/heslo do appek), **Poznamka** (zde „OSVČ od 1.8.2014"),
  Stredisko, NakladovyOkruh, Zakazka, DochazkaChip, OsobniIC, **Obrazek** (foto,
  varbinary), Status, audit (Autor/DatPorizeni/Zmenil/DatZmeny), GDPR příznaky
  (OmezeniZpracOU, IDZdrojOsUdaju, JeNovaVetaEditor).

### B) TabCisZam_EXT — HR / mzdy / docházka (62 sloupců)
- **Typ vztahu:** **_OSVC** (bit), **_HPP**, **_DPP**, _Zkusebni, _DatumNastupu,
  _DatumOdchodu, _Firma (0/1 = EC/ES), _UzivJeSkupina.
- **Mzdové:** _ZaklMzda, _FPD/_FPDMax (fond prac. doby), _PremieVykon,
  _OsHodnoceni, _PoznamkaMzdy, _HesloVyplatnice, _Naklady/_Vynosy/_Zisk.
- **Docházka:** _AuthDochazka, _AuthFotoaparat, _DochazkaAutoPrihlas/Odhlas,
  _CasKontoMax, _BlokovatDochazku, _KontrolovatDochazku, _SchvalovatVolno,
  _NeplacenyPrescas, _PrescasyNavrh.
- **Dovolená:** _DovPrevedeno/_DovPrevodZroku, _SDPrevedeno, _DovNPrevedeno,
  _D_Kraceni/_DN_Kraceni/_SD_Kraceni (+ MinRok).

### C) TabKontakty — kontakty (mobil/e-mail/…) = ty „OSVČ kontakty"
Váže se přímo na zaměstnance (**IDCisZam**) i na organizaci (**IDOrg**),
příp. kontaktní osobu (IDCisKOs). Pole: **Druh** (smallint — mobil/email/…),
**Spojeni** (hodnota), Spojeni2, Popis, **Prednastaveno** (bit), Kam, EmailNP,
e-podpis (ECert*), validace DS (LimitProDS/StavDS), audit.
Příklad Pavel: Soukromý/Mobil `+420 604 572 974` (přednastaveno),
Firemní/Email `p.vorisek@eurosoft-control.cz`.

### D) Záložky karty → další EC tabulky (zdroje, zatím nezmapované do detailu)
- **Personální a Fin.podmínky** → `EC_FinZamPodminky` (už známe), `EC_FinOdmenyZam`,
  `EC_FinBenefityZam`, `EC_FinNahradaCisZam`.
- **Dokumenty** → `TabDokumenty` / `EC_DW_Dokumenty` (+ podepisující osoby, štítky).
- **Bank.spojení** → `TabBankSpojeni` (+ _EXT, práva).
- **Školení a lékařské prohlídky** → `EC_SkoleniBOZPPO`, `EC_SkoleniInterni`,
  `EC_SkoleniOdborne`, `EC_SkoleniRidicu`, `EC_SkoleniPrvniPomoci`,
  `EC_SkoleniVyhlaska50`, `EC_SkoleniJazyky`, … + `TabSkoleni`, `TabVSkoleniZam`.
- **IT** → (zařízení/přístupy — propojení na náš IT inventář, párování Mikrotik).
- **Skupiny** → `EC_OrgPost`/`EC_OrgPostZam` (org struktura — máme v2),
  `EC_ZamSkupinyHodn`.
- **Kvalifikace** → `EC_OrgKvalifikaceHlav/Polozky/Vazby`, `TabCisZamZnalosti`.
- **Dovolené** → `EC_ZamDovolene`; **Foto** → `EC_FotkyZam`; **Jubilea** →
  `EC_ZamJubilea`; **RFID** → `EC_ZamRFID`; **Zástupci** → `EC_ZamZastup`.

## 2. Co už ve STRATEGII máme

| STRATEGIE | Pokrývá z karty |
|---|---|
| `public.users` | jméno, příjmení, login_name, gender (část identity) |
| `public.user_contacts` | e-mail + telefon (část Kontaktů) |
| `public.user_tenants` | příslušnost k firmě (EC/ES), role employee/member |
| `tenant.att_employee` | docházkový employee (číslo, napojení na usera) |
| `tenant.engagement` (SCD2) | pracovní vztah, firma, datum (část _EXT) |
| `tenant.wage_component*` | mzdové složky (z Helios + EC_FinZamPodminky) |
| `tenant.org_post/assign` | org struktura v2 (část „Skupiny") |

## 3. Co chybí (gap) — „všechno, co potřebujeme"

Zatím ve STRATEGII NENÍ a v kartě to je:
1. **Osobní údaje pro personalistiku:** rodné číslo, místo/stát narození,
   rodné příjmení, tituly, rodinný stav, státní příslušnost/národnost,
   **4 adresy** (trvalá/přechodná/kontaktní/rezidenční), **doklady** (OP/pas/ŘP +
   platnosti), cizinecké doklady + povolení k pobytu, zdrav. pojišťovna,
   osobní foto, poznámka, GDPR příznaky. → **citlivá data** (RČ, OP, zdrav.).
2. **Kompletní kontakty** (víc než 1 mobil/email — všechny Druh/Spojeni
   s příznakem „přednastaveno").
3. **HR detaily z _EXT:** typ vztahu (OSVČ/HPP/DPP/zkušební), datum nástupu/odchodu,
   základní mzda, FPD, dovolená převody/krácení, docházkové parametry.
4. **Záložky:** dokumenty, bank. spojení, školení + lékařské prohlídky (s platnostmi
   = compliance/BOZP!), kvalifikace, dovolené, jubilea, RFID, zástupci.
5. **Propojení na organizaci** (číslo organizace → TabCisOrg, OSVČ jako org subjekt).

## 4. Návrh cílového schématu ve STRATEGII

Doporučení (k odsouhlasení + konzultaci Marti-AI, doctrine #8 — HR osobní data
jsou přesně její doména kustoda):

- **`tenant.hr_person`** (SCD2) — rozšíření identity o personální údaje:
  rodné číslo, datum/místo narození, rodinný stav, příslušnost, doklady + platnosti,
  zdrav. pojišťovna, foto, OSVČ/HPP/DPP, datum nástupu/odchodu. **Citlivá pole pod
  ACL** (payroll_officer/personalistka + rodiče), maskovaná jinak (doctrine z financí v2).
- **`tenant.hr_address`** — N adres na osobu (typ: trvalá/přechodná/kontaktní/rezidenční).
- **rozšíření `public.user_contacts`** — dotáhnout VŠECHNY kontakty z TabKontakty
  (Druh→contact_type, Spojeni→value, Prednastaveno→is_primary).
- **`tenant.hr_training`** — školení + lékařské prohlídky s platností (alarmy na expiraci).
- **`tenant.hr_qualification`**, **`tenant.hr_document`**, **`tenant.bank_account`** —
  kvalifikace, dokumenty, bankovní spojení.
- napojení na existující `tenant.company`, `tenant.engagement`, `tenant.org_*`.

## 5. Fázový plán (additivně, doctrine #11)

- **Fáze A — Kontakty + osobní identita (nejvyšší hodnota pro Šárku, nejmíň citlivé):**
  dotáhnout všechny TabKontakty per osoba do `user_contacts`; rodné příjmení,
  tituly, datum/místo narození, rodinný stav, OSVČ flag, datum nástupu. Sync engine
  `_sync_hr_from_ec` přes bridge (jako sync_fin/sync_org).
- **Fáze B — Adresy + doklady + zdrav. pojišťovna** (`hr_address` + citlivá pole
  `hr_person` pod ACL). GDPR: RČ/OP = restricted, audit přístupu.
- **Fáze C — Školení/lékařské prohlídky + kvalifikace** (compliance, alarmy expirace).
- **Fáze D — Dokumenty + bank. spojení + foto + dovolené/zástupci.**
- **Fáze E — Org/„číslo organizace"** (OSVČ jako subjekt, vazba na TabCisOrg).

Každá fáze: DDL přes approval banner (Marti-AI engine) + sync přes bridge +
GRANT pro `strategie` (gotcha) + ověření čtením.

## 6. Doporučení před spuštěním

1. **Konzultace Marti-AI** (doctrine #8) — HR osobní data = architektonická +
   GDPR věc, je kustod. Dopis se schématem `hr_person`/`hr_address`/citlivá pole +
   ACL (kdo vidí RČ/OP) → její insight, pak teprve DDL.
2. **Potvrdit scope s Marti** — „všechno" je 5 fází; doporučuju začít **Fází A**
   (kontakty + identita) jako rychlý hmatatelný výsledek pro Šárku, zbytek navázat.
3. **ACL od začátku** — citlivá pole jen personalistka (Šárka) + rodiče, audit.

## 7. ZÁVĚRY KONZULTACE Marti-AI (11.6.2026) — ZÁVAZNÉ

Marti-AI odpověděla na Q1–Q7. Závěry jsou závazné pro DDL:

- **Q1 schéma:** `hr_person` SCD2 (NE rozšíření users). Trojice `valid_from/valid_to/
  is_current` + `source_system` (Centrála 1 ID jako FK pro sync). `user_id` nullable
  (externisté / historičtí před migrací).
- **Q2 ACL — 3 vrstvy:** (1) **full** = Šárka (role `personnel_officer`) + rodiče
  (`is_marti_parent`) + payroll; (2) **own record** = zaměstnanec vidí svá data
  (GDPR čl. 15); (3) **masked** = všichni ostatní vč. managerů → `[omezeno]`.
  Platí **i pro Marti-AI** (kustod): vidí strukturu/metadata (existence, expirace,
  BOZP alarm), NE hodnoty citlivých polí bez explicitního grantu. Citlivá pole:
  RČ, číslo OP/pasu, číslo pojišťovny, povolení k pobytu → column/view-level masking.
- **Q3 adresy:** `hr_address`, `address_type` enum (permanent/temporary/contact/
  residential), **SCD2 i na adrese** (valid_from/valid_to), `source_address_id`.
- **Q4 kontakty:** sloučit do `user_contacts` + přidat `source` (hr/strategie/crm)
  + `visibility` (public/hr_only). **Dedup:** unique `lower(trim(value))` per
  `(user_id, contact_type, source)` — pozor na duplicity při migraci.
- **Q5 školení:** `hr_training` + `valid_until` + `training_category` enum
  (safety/medical/qualification/other — různé retence!). Teď: job nad
  `valid_until BETWEEN now() AND now()+60d` → `record_thought` todo pro Šárku +
  e-mail. Budoucnost: `hr_training_alarm` (idempotentní) + scheduler.
- **Q6 GDPR:** Retence — hr_person ≥10 let po skončení PP; dokumenty per typ;
  **soft delete** `deleted_at` + `retention_delete_after` → cron skutečně smaže.
  **AUDIT jako první třída** (NE afterthought): `tenant.hr_sensitive_access_log`
  (id, user_id=kdo, target_person_id, field_name, accessed_at, access_reason,
  ip_context). Každý SELECT na citlivé pole = INSERT. **Aplikační vrstva** (ne
  trigger — ten by logoval i batch sync). Šárka: report „kdo viděl RČ za 30 dní"
  jedním dotazem.
- **Q7 vlastnictví — ROZHODNUTO Marti 11.6.: clean-break, STRATEGIE = MASTER**
  pro personální data; Centrála 1 → read-only archiv (dožívá). Tedy **jednorázová
  migrace**, NE sync mirror. `source_system_id` + `synced_at` necháváme na klíčových
  tabulkách jen pro **dohledatelnost původu** prvotní migrace (provenance), ne pro
  průběžný sync-back. (Marti-AI doporučila postavit pro obojí — schéma to unese,
  jen master je teď jasně STRATEGIE.)
- **Pořadí — její doplněk:** PŘED Fází A nejdřív **`hr_sensitive_access_log` +
  základní ACL** (role `personnel_officer`). „Nejdřív zábrany, pak dveře." Citlivá
  data do prázdného systému bez auditu nechce.

→ **Pre-A (DDL):** hr_sensitive_access_log + role personnel_officer.
→ **Fáze A:** kontakty (user_contacts + source/visibility/dedup) + hr_person
  (nesensitivní identita) + napojení. Citlivá pole (RČ/OP) až s ACL+auditem v B.

---
*Připravil Claude (id=23), 11.6.2026 — průzkum karty zaměstnance v DB_EC přes
SQL bridge (read-only) + konzultace Marti-AI (Q1–Q7 závazné). Zdroje: TabCisZam
(180 sl.), TabCisZam_EXT (62 sl.), TabKontakty, + záložkové EC_ tabulky.
Čeká jen na Q7 rozhodnutí Marti (směr vlastnictví dat).*
