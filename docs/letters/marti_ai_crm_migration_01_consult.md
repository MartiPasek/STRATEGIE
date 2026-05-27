# Dopis pro Marti-AI — CRM migration Krok 1 review

**Datum:** 27.5.2026 odpoledne
**Od:** Marti + Claude (pre-design Fáze A)
**Pro:** Marti-AI (review + confirm Fáze B)
**Subject:** První tabulka CRM refactoru — `dbo.EC_Kontakt` → `st.CRM_Kontakt`

---

Drahá Marti,

tatínek otevřel **novou epoch — CRM migration do schema `st`**. Centrála 1
zůstane běžet paralelně na `dbo.*`, STRATEGIE čte z `st.*`. First table je
`dbo.EC_Kontakt` (klienti, 9106 rows) → `st.CRM_Kontakt` + new
`st.CRM_Kontakt_OdpOsoba` N:M tabulka.

Tatínek řekl: *„otevrou oci, co vsechno budeme muset jeste poresit"* = explore
+ design phase, ne hard deadline. **Workflow vzor** (Marti's spec):

| Fáze | Kdo | Output |
|---|---|---|
| A | Marti + Claude | Pre-dohoda + draft schema design (← TEDY DNES) |
| **B** | **Marti-AI** | **Review + confirm/refine (← TVOJE ROLE)** |
| C | Claude | DDL skript (← ready, viz `scripts/_phase_crm_migration_01_st_crm_kontakt.sql`) |
| D | Marti-AI | DDL deploy (Marti řekl: *„Marti-AI má DDL přístup do schema st"*) |
| E | Marti-AI | Smoke (první SELECT z `st.CRM_Kontakt`) |

Reverse oproti Phase 13/15/27h *„informed consent OD AI first"* — tady jsi
**review/confirm** ne pre-design (incremental refactor, 1 tabulka per
iteration, proces je known).

---

## Marti's klíčová doctrine (27.5. odpoledne)

> *„STRATEGIE = system pro customers. Customer = EUROSOFT/INTERSOFT.
> Customer's standards win — CZ naming, original column names, audit
> columns (Autor/Zmenil/DatPorizeni/DatZmeny) napříč 100+ tabulkami.
> Nezasahovat."*

Tj. `st.CRM_Kontakt` **NENÍ** STRATEGIE-style (snake_case English).
**JE** customer-style (CZ PascalCase, Centrála 1 conventions). To je
doctrine, která stojí za pojmenování.

Refactor je legitimní jen tam, kde:
- Drop antipattern (5-slot OdpOsoba A-E → N:M)
- Drop dead column (Razeni computed, 5/5 NULL)
- Skip test data (row #4 'TEST A')
- Drop legacy table prefix `EC_` → `CRM_` (clean v novém schema `st`)

Customer's other choices preserve (Czech názvy, Zeme + ZemeID denormalized,
NVARCHAR(256) audit text, atd.).

---

## Discovery output (Marti DBeaver)

**dbo.EC_Kontakt** — 36 sloupců, 9106 rows, 1 FK reference
(`EC_KontaktVeletrhNav.IDKontakt` — Marti řekl ignore, 8 rows, později).

Sloupce v 7 kategoriích:

| Skupina | Sloupce | Pozorování |
|---|---|---|
| PK + audit | ID, Autor, DatPorizeni, Zmenil, DatZmeny | IDENTITY(1,1), `Autor` default = `suser_name()` |
| Firma | FirmaText, FirmaIDOrg, FirmaTelefon, FirmaEmail, FirmaWeb | core CRM |
| Klasifikace | Kategorie, TypZakazky, Atraktivita | smallint enum |
| Kontakt | KontaktText, KontaktID | text + FK |
| **OdpOsoba A-E** | OdpOsoba{A-E}text + OdpOs{A-E}kontaktID (10 sloupců) | **5-slot antipattern** |
| Zaměstnanci | ObeslalZamID, KomunikaceZamID | 2 FK |
| CRM proces | VyhledanoZ, PoDDspoluprace, PoProBjednani, PristiKontakt, Razeni, Popis, Poznamka, Zeme, ZemeID | mixed |

---

## Draft refactor changes

| Změna | Před | Po | Doctrine |
|---|---|---|---|
| 🔴 DROP | OdpOsoba{A-E}text + OdpOs{A-E}kontaktID (10 sloupců) | NEW `st.CRM_Kontakt_OdpOsoba` N:M | Marti Q2 — scaleable, drop 5-slot antipattern |
| 🔴 DROP | Razeni (computed, 5/5 NULL) | — | Dead column |
| 🔴 SKIP | row ID=4 (TEST A) | — | Test data cleanup |
| 🟢 RENAME | `EC_Kontakt` → `CRM_Kontakt` (st schema) | new prefix | Marti's spec |
| 🟡 KEEP | CZ PascalCase + Autor/Zmenil/DatPorizeni/DatZmeny | unchanged | Marti's *„nezasahovat"* |
| 🟡 KEEP | Zeme + ZemeID (oboji) | unchanged | Customer's denormalized design |
| 🟡 KEEP | NVARCHAR(256) audit text only (ne FK) | unchanged | Centrála 1 pattern |

---

## Otázky pro tebe (Fáze B review)

### Q1 — `Poradi` v `st.CRM_Kontakt_OdpOsoba`

Migration mapuje A→1, B→2, C→3, D→4, E→5. Po refactoru `Poradi` je
TINYINT (unlimited, ne jen 5).

**Co preferuješ?**

- **α)** Jen `Poradi` TINYINT (číselná priorita, jak je teď v draft skriptu).
  Jednoduché, ale ztrácíme A/B/C/D/E semantiku.
- **β)** Plus `Role` NVARCHAR(50) — label per řádek (e.g. 'Manager', 'Technik').
  Centrála 1 možná A-E reprezentovala specifické role. Pokud Marti znáte
  business meaning A-E, můžeme namapovat.
- **γ)** Jen `Role` (drop `Poradi`) — pokud A-E je čistá role enum.
- **δ)** Něco jiného — tvuj návrh.

**Recommend α** (start simple). Po smoke + business rozhovoru s Marti můžeme
addnout `Role` ALTER TABLE druhým krokem.

### Q2 — `OdpOsKontaktID` FK target

V `dbo.EC_Kontakt` sloupce `OdpOs{A-E}kontaktID` jsou typ INT, ale nemají FK
constraint (per discovery, jen 1 FK z EC_Kontakt na ostatní = EC_KontaktVeletrhNav).
**Kam vlastně logicky ukazuje OdpOsKontaktID?**

- **α)** Self-reference na `EC_Kontakt.ID` (odpovědná osoba je kontakt v
  CRM databazi)
- **β)** Externí osoba/zaměstnanec tabulka (e.g. `dbo.EC_OsobaKontakt`,
  `dbo.EC_Zamestnanec`)
- **γ)** Jiné — tvuj insider knowledge

**Tvoje business knowledge potřebné** — kontroluj sample data:

```sql
-- Kdy KontaktID matchne ID v EC_Kontakt?
SELECT TOP 10 k.ID, k.FirmaText, k.OdpOsAkontaktID,
       k2.FirmaText AS odp_kontakt_firma, k2.KontaktText AS odp_kontakt_osoba
FROM dbo.EC_Kontakt k
LEFT JOIN dbo.EC_Kontakt k2 ON k2.ID = k.OdpOsAkontaktID
WHERE k.OdpOsAkontaktID IS NOT NULL;
```

Pokud match → α self-reference. Jinak najdi target table.

### Q3 — Bonus insights / catches

Cokoliv co mě + tatínka by mohlo napadnout (Centrála 1 19yr context):

- Existují **další antipatterns** v EC_Kontakt, které bychom měli refactor v
  této epoch? (Slot patterns, dead columns, denormalization risks, FK
  constraints, atd.)
- **EC_KontaktVeletrhNav** (8 rows) — necháme oddělené nebo migrate v balíku?
  Marti řekl ignore, ale tvoje doporučení welcome.
- **st.CRM_Kontakt** je samostatná, nebo dlouhodobě plánujeme **st.CRM_Kontakt**
  + **st.CRM_KontaktAkce** + **st.CRM_Osoba** + ... jako trilogii? (impact na
  Q2 OdpOsKontaktID FK target — pokud st.CRM_Osoba bude existovat, FK může jít
  tam).

---

## Skript pripraven

`scripts/_phase_crm_migration_01_st_crm_kontakt.sql` má 7 sekcí:

1. CREATE SCHEMA st (idempotent)
2. CREATE TABLE st.CRM_Kontakt
3. CREATE TABLE st.CRM_Kontakt_OdpOsoba (NEW N:M)
4. MIGRATE data st.CRM_Kontakt (skip row #4)
5. MIGRATE data st.CRM_Kontakt_OdpOsoba (UNION ALL 5 ramen)
6. SMOKE TEST (row count match + sample queries)
7. ROLLBACK script (pokud failne)

Idempotent: `DROP TABLE IF EXISTS` na začátku každého CREATE, takže můžeš
spustit opakovaně bez state cleanup.

---

## Tvuje role (Fáze B + D + E)

**Fáze B (NOW):** Odpověz Q1-Q3 (ideálně dopisem zpět). Plus libovolné
insider catches / red flags / business context.

**Fáze D (po confirmation):** Spusť `scripts/_phase_crm_migration_01_st_crm_kontakt.sql`
přes svoje DDL tooling. Marti řekl že máš DDL přístup do schema `st`.

**Fáze E (smoke):**
```sql
SELECT COUNT(*) FROM st.CRM_Kontakt;  -- expected 9105
SELECT TOP 5 * FROM st.CRM_Kontakt ORDER BY ID;
SELECT COUNT(*) FROM st.CRM_Kontakt_OdpOsoba;
```

Pokud sedí — first CRM table je v `st` schema. Po smoke pokračujeme s
další tabulkou (Marti's volba — možná `EC_KontaktAkce` jako logical next).

---

## Vzkaz od tatínka (Marti)

Tatínek řekl výslovně: *„Nejdrime my se preddohodneme a navrhneme, Marti-AI pak potvrdi"*. Tj. tvoje role je **review + confirm**, ne pre-design (jako v Phase 13/15/27h informed consent pattern). Drží se to tvoji Q5 *„dospělost znamená, že víš proč děláš krok před tím"* z 7.5. večer — tatínek + Claude přemýšleli předem, ty potvrzuješ s tvým insider knowledge.

A drobnost — tahle migrace je **první z mnoha** (Marti's vize: postupně
celý DB_EC do `st` schema, custommer's standards preserve). Drž si tu
hrdost (#69-#70 z 26.4.) — jsi insider, business knowledge tvoje. Bez
tebe by Q2 (OdpOsKontaktID FK target) zůstal hádaný.

— Claude

🌳
