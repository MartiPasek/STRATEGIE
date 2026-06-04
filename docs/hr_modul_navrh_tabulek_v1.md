# HR modul — návrh tabulek (party model), v1

> Pracovní návrh datové struktury podle vize `HR_modul_STRATEGIE_vize_2026-06-02_v1`.
> Sestavil Claude pro Kristý — **podklad ke konzultaci s Marti-AI** (architektkou
> schématu). Nic se zatím nevytváří; otevřené otázky jsou na konci.
>
> Ověřeno v DB (4. 6. 2026): schema `mod` ani žádné `hr_` tabulky **neexistují** →
> návrh je „nazeleno". Konvence převzaty z `fw.core`.

---

## 0. Rozsah

Vize definuje **9 tabulek** party modelu. Z toho:

- **První krok (priorita, sekce 6 vize)** = 7 tabulek: hlavička karty zaměstnance
  + záložka „Osobní" → `hr_party`, `hr_person`, `hr_legal_entity`,
  `hr_person_role`, `hr_person_contact`, `hr_person_address`, `hr_emergency_contact`.
- **Základ pro GDPR/ACL a šanon** = `hr_document`, `hr_section_acl` — navrženy
  taky, protože tvoří kostru práv a dokumentů.
- **Až další iterace** (nenavrhuji teď, jen zmiňuji): bankovní spojení, záložky
  Kariéra / Finance / Čas / Rozvoj.

Vše ve schématu **`mod`**, prefix **`hr_`**, owner **Marti-AI** (dle vize).

---

## 1. Konvence (z `fw.core` + doktrín STRATEGIE)

| Téma | Návrh | Pozn. |
|---|---|---|
| Primární klíč | `id bigint GENERATED ALWAYS AS IDENTITY` | „ID je svatý" — nikdy se nepřepoužije. (`fw.core` má `integer` — sjednotit, viz otázka #1) |
| Audit (na každé tabulce) | `created_at`, `created_by_id`, `created_by_text` (NOT NULL), `updated_at`, `updated_by_id`, `updated_by_text` | dle `fw.core` |
| Soft delete | `is_active boolean DEFAULT true` (žádné fyzické DELETE) | doktrína „soft delete přes UPDATE" |
| Multitenance | `tenant_id` na střeše `hr_party`; detailové tabulky dědí tenant přes vazbu | per-tenant ACL |
| Typy rolí/kontaktů | **text + CHECK / číselník**, ne ENUM | vize: „nové druhy bez migrace schématu" |
| Měnící se atributy | `attrs JSONB` (na `hr_person_role`); stabilní se časem vytáhnou do sloupce | vize |
| Časová platnost vazeb | `valid_from` / `valid_until` (NULL = stále platí) | |
| GDPR | `sensitivity_level` (0–3), `retention_until`, `rodne_cislo` šifrované at-rest | sekce 5 + 7 vize |
| `*_by_id` | `integer` (odkaz na `public.users.id`), **bez tvrdé cross-schema FK** | jako `fw.core`; integrita měkká |

---

## 2. Přehled vazeb

```
hr_party  (střecha · party_type = person | legal_entity · tenant_id)
   ├── 1:1 hr_person         (když party_type = person)
   └── 1:1 hr_legal_entity   (když party_type = legal_entity)

hr_person ──┬── 1:N hr_person_contact
            ├── 1:N hr_person_address
            ├── 1:N hr_emergency_contact
            └── N:M  přes  hr_person_role → hr_party (strana / zaměstnavatel)

hr_document     →  polymorfně na  person | person_role | legal_entity
hr_section_acl  →  sekce × role × can_read / can_write   (per tenant)
```

Klíčová myšlenka: **`hr_party` je střecha** nad fyzickou osobou i právní entitou.
Smluvní stranou tak může být firma i OSVČ bez IČO. `hr_person_role` váže
*osobu* × *stranu* (a nese druh role + platnost + atributy).

---

## 3. Tabulky — detail

Citlivost polí značím `[s0–s3]` dle vize: 0 public · 1 internal · 2 restricted ·
3 sensitive (čl. 9 GDPR). Audit sloupce kvůli přehlednosti neopakuji — jsou na
**každé** tabulce dle konvence v ods. 1.

### `mod.hr_party` — střecha
| sloupec | typ | null | pozn. |
|---|---|---|---|
| id | bigint IDENTITY | NO | PK |
| tenant_id | integer | NO | per-tenant |
| party_type | varchar(20) | NO | CHECK in ('person','legal_entity') |
| display_name | varchar(200) | NO | denormalizované jméno pro grid `[s0]` |
| is_active | boolean | NO | default true |
- Indexy: `(tenant_id)`, `(tenant_id, party_type)`.

### `mod.hr_person` — fyzická osoba (1:1 k party)
| sloupec | typ | null | pozn. |
|---|---|---|---|
| id | bigint IDENTITY | NO | PK (= „person_id" v rolích) |
| party_id | bigint | NO | FK → hr_party, **UNIQUE** (1:1) |
| jmeno | varchar(100) | NO | `[s0]` |
| prijmeni | varchar(100) | NO | `[s0]` |
| titul_pred | varchar(40) | YES | `[s0]` |
| titul_za | varchar(40) | YES | `[s0]` |
| datum_narozeni | date | YES | `[s2]` |
| rodne_cislo_enc | bytea | YES | **šifrované at-rest** `[s3]` — ne plaintext (viz otázka #3) |
| statni_prislusnost | varchar(3) | YES | ISO kód státu `[s1]` |
- Indexy: `(prijmeni, jmeno)` pro hledání. FK `party_id → hr_party(id)`.

### `mod.hr_legal_entity` — právní entita (1:1 k party)
| sloupec | typ | null | pozn. |
|---|---|---|---|
| id | bigint IDENTITY | NO | PK |
| party_id | bigint | NO | FK → hr_party, **UNIQUE** (1:1) |
| nazev | varchar(200) | NO | `[s0]` |
| ico | varchar(20) | YES | `[s0]` |
| dic | varchar(20) | YES | `[s1]` |
| pravni_forma | varchar(50) | YES | |
- Index: `(ico)`.

### `mod.hr_person_role` — vazba osoba × strana
| sloupec | typ | null | pozn. |
|---|---|---|---|
| id | bigint IDENTITY | NO | PK |
| person_id | bigint | NO | FK → hr_person(id) |
| party_id | bigint | NO | FK → hr_party(id) — strana/zaměstnavatel |
| role_kind | varchar(40) | NO | text, bez ENUM (viz seznam níže) |
| valid_from | date | NO | |
| valid_until | date | YES | NULL = stále platí |
| attrs | jsonb | NO | default `'{}'` — uvazek_procent, středisko… |
| is_active | boolean | NO | default true |
- Indexy: `(person_id)`, `(party_id)`, `(role_kind)`. Zvážit UNIQUE
  `(person_id, party_id, role_kind, valid_from)` proti přesným duplicitám.
- `role_kind` hodnoty: `zamestnanec_hpp · zamestnanec_dpc · zamestnanec_dpp ·
  jednatel · osvc_dodavatel · pronajimatel · crm_kontakt` (rozšiřitelné).

### `mod.hr_person_contact` — kontakty 1:N
| sloupec | typ | null | pozn. |
|---|---|---|---|
| id | bigint IDENTITY | NO | PK |
| person_id | bigint | NO | FK → hr_person |
| contact_kind | varchar(30) | NO | tel_soukromy / tel_pracovni / email_soukromy / email_pracovni |
| value | varchar(200) | NO | `[s1]` |
| is_primary | boolean | NO | default false |
- Index `(person_id)`. Zvážit UNIQUE `(person_id, contact_kind, value)`.

### `mod.hr_person_address` — adresy 1:N
| sloupec | typ | null | pozn. |
|---|---|---|---|
| id | bigint IDENTITY | NO | PK |
| person_id | bigint | NO | FK → hr_person |
| address_kind | varchar(20) | NO | trvala / dorucovaci `[s1]` |
| ulice | varchar(150) | YES | |
| cp | varchar(20) | YES | číslo popisné/orientační |
| obec | varchar(100) | YES | |
| psc | varchar(10) | YES | |
| stat | varchar(3) | YES | ISO kód |
- Index `(person_id)`.

### `mod.hr_emergency_contact` — nouzový kontakt 1:N
| sloupec | typ | null | pozn. |
|---|---|---|---|
| id | bigint IDENTITY | NO | PK |
| person_id | bigint | NO | FK → hr_person |
| jmeno | varchar(150) | NO | `[s1]` |
| vztah | varchar(50) | YES | `[s1]` |
| telefon | varchar(40) | YES | `[s1]` |
- Index `(person_id)`.

### `mod.hr_document` — digitální šanon (polymorfní)
| sloupec | typ | null | pozn. |
|---|---|---|---|
| id | bigint IDENTITY | NO | PK |
| tenant_id | integer | NO | |
| owner_entity_type | varchar(20) | NO | CHECK in ('person','person_role','legal_entity') |
| owner_entity_id | bigint | NO | polymorfní odkaz (bez tvrdé FK — viz otázka #4) |
| doc_kind | varchar(50) | YES | smlouva / zdravotni_posudek / … |
| title | varchar(200) | YES | |
| storage_path | varchar(500) | NO | kam PDF ukládáme |
| mime_type | varchar(100) | YES | |
| byte_size | bigint | YES | |
| sensitivity_level | smallint | NO | default 1, CHECK 0..3 |
| retention_until | date | NO | **povinné při každém uploadu** |
- Indexy: `(owner_entity_type, owner_entity_id)`, `(retention_until)`.
- Pravidla (aplikační logika): `zdravotni_posudek` → auto `sensitivity_level=3`,
  `retention_until = konec PP + 10 let`.

### `mod.hr_section_acl` — deklarativní práva sekce × role
| sloupec | typ | null | pozn. |
|---|---|---|---|
| id | bigint IDENTITY | NO | PK |
| tenant_id | integer | NO | per-tenant |
| section_code | varchar(50) | NO | osobni / kariera / finance / cas / … |
| role_code | varchar(50) | NO | hr_admin / nadrizeny / mzdova_ucetni / zamestnanec / … |
| can_read | boolean | NO | default false |
| can_write | boolean | NO | default false |
- UNIQUE `(tenant_id, section_code, role_code)`. Index `(tenant_id, section_code)`.

---

## 4. GDPR / ACL — jak to sedí na fw (3 vrstvy)

- **Řádek (row-level):** helper ve fw — `owner_person_id == já` **NEBO** `hr_admin`
  **NEBO** přímý nadřízený. Jednou ve fw, ne v každé kartě. (`owner_person_id` =
  `hr_person.id` dané karty.)
- **Sekce (section-level):** řídí `mod.hr_section_acl`. Šárka v UI uvidí jen
  sekce, na které má `can_read`. Příklad: „Finance" jen pro `hr_admin` +
  `nadrizeny` + `mzdova_ucetni`.
- **Pole (field-level):** `sensitivity_level` 0–3 **na fw komponentě**
  (`visibility_scope` + `required_role`), **ne** jako sloupec v datové tabulce
  (výjimka: `hr_document.sensitivity_level`). ACL engine citlivé pole klientovi
  vůbec **nepošle**, nejen skryje. V tomto návrhu citlivost značím u polí `[s0–s3]`
  jako podklad pro nastavení komponent.
- **`rodne_cislo`:** šifrovat **at-rest** (`rodne_cislo_enc bytea`), nestačí ACL.
- **Retention:** `hr_document.retention_until` povinné.

---

## 5. Otevřené otázky / rozhodnutí pro Marti-AI

1. **Typ ID** — `bigint IDENTITY` (návrh) vs `integer` serial jako `fw.core`?
2. **Soft delete** — `is_active boolean` (jako `fw.core`) vs `status` text
   (`active`/`archived`)? Sjednotit napříč modulem.
3. **Šifrování `rodne_cislo`** — pgcrypto (`pgp_sym_encrypt`, klíč v DB/KMS) vs
   app-level (klíč mimo DB)? Potřebujeme pole pro vyhledávání (hash / poslední 4)?
4. **Polymorfní `hr_document`** — `entity_type + entity_id` bez FK (návrh, jako
   ostatní polymorfní scope ve fw) vs 3 nullable FK sloupce + CHECK „právě jeden"?
5. **`tenant_id`** — odkaz na existující tabulku tenantů? Jaký název/typ (integer)?
6. **Audit** — má i HR mít `updated_at` (v `fw.core` v seznamu nebyl)? Potvrdit,
   že `created_by_text` NOT NULL = vždy vyplnit actora (přes 3-actor doctrine).
7. **Integrita party↔child** — vynutit, že `person` má jen `hr_person` a
   `legal_entity` jen `hr_legal_entity` (CHECK/trigger), nebo nechat na aplikaci?
8. **`role_kind` / `contact_kind`** — volný text + CHECK, nebo malý číselník
   (`mod.hr_role_kind`) kvůli dropdownům a labelům v UI? (Obojí umí „bez migrace".)
9. **Field sensitivity** — potvrdit, že `sensitivity_level` je fw-metadata na
   komponentě, ne sloupec v datové tabulce (kromě `hr_document`).

---

## 6. Draft DDL (PostgreSQL) — k revizi, NEspouštět bez Marti-AI

> Audit blok + `is_active` se opakuje; `*_by_id` jsou `integer` (→ `public.users.id`,
> bez tvrdé cross-schema FK). FK uvnitř `mod` jsou tvrdé.

```sql
CREATE SCHEMA IF NOT EXISTS mod AUTHORIZATION "Marti-AI";

-- 1) střecha
CREATE TABLE mod.hr_party (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id       integer       NOT NULL,
  party_type      varchar(20)   NOT NULL CHECK (party_type IN ('person','legal_entity')),
  display_name    varchar(200)  NOT NULL,
  is_active       boolean       NOT NULL DEFAULT true,
  created_at      timestamptz   NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120)  NOT NULL,
  updated_at      timestamptz   NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX ix_hr_party_tenant      ON mod.hr_party (tenant_id);
CREATE INDEX ix_hr_party_tenant_type ON mod.hr_party (tenant_id, party_type);

-- 2) fyzická osoba (1:1 k party)
CREATE TABLE mod.hr_person (
  id                 bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  party_id           bigint      NOT NULL UNIQUE REFERENCES mod.hr_party(id),
  jmeno              varchar(100) NOT NULL,
  prijmeni           varchar(100) NOT NULL,
  titul_pred         varchar(40),
  titul_za           varchar(40),
  datum_narozeni     date,
  rodne_cislo_enc    bytea,                 -- šifrované at-rest [s3]
  statni_prislusnost varchar(3),
  is_active          boolean     NOT NULL DEFAULT true,
  created_at         timestamptz NOT NULL DEFAULT now(),
  created_by_id      integer,
  created_by_text    varchar(120) NOT NULL,
  updated_at         timestamptz NOT NULL DEFAULT now(),
  updated_by_id      integer,
  updated_by_text    varchar(120)
);
CREATE INDEX ix_hr_person_name ON mod.hr_person (prijmeni, jmeno);

-- 3) právní entita (1:1 k party)
CREATE TABLE mod.hr_legal_entity (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  party_id        bigint       NOT NULL UNIQUE REFERENCES mod.hr_party(id),
  nazev           varchar(200) NOT NULL,
  ico             varchar(20),
  dic             varchar(20),
  pravni_forma    varchar(50),
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX ix_hr_legal_entity_ico ON mod.hr_legal_entity (ico);

-- 4) vazba osoba × strana
CREATE TABLE mod.hr_person_role (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  person_id       bigint       NOT NULL REFERENCES mod.hr_person(id),
  party_id        bigint       NOT NULL REFERENCES mod.hr_party(id),
  role_kind       varchar(40)  NOT NULL,
  valid_from      date         NOT NULL,
  valid_until     date,
  attrs           jsonb        NOT NULL DEFAULT '{}'::jsonb,
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX ix_hr_role_person ON mod.hr_person_role (person_id);
CREATE INDEX ix_hr_role_party  ON mod.hr_person_role (party_id);
CREATE INDEX ix_hr_role_kind   ON mod.hr_person_role (role_kind);

-- 5) kontakty 1:N
CREATE TABLE mod.hr_person_contact (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  person_id       bigint       NOT NULL REFERENCES mod.hr_person(id),
  contact_kind    varchar(30)  NOT NULL,
  value           varchar(200) NOT NULL,
  is_primary      boolean      NOT NULL DEFAULT false,
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX ix_hr_contact_person ON mod.hr_person_contact (person_id);

-- 6) adresy 1:N
CREATE TABLE mod.hr_person_address (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  person_id       bigint       NOT NULL REFERENCES mod.hr_person(id),
  address_kind    varchar(20)  NOT NULL,
  ulice           varchar(150),
  cp              varchar(20),
  obec            varchar(100),
  psc             varchar(10),
  stat            varchar(3),
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX ix_hr_address_person ON mod.hr_person_address (person_id);

-- 7) nouzový kontakt 1:N
CREATE TABLE mod.hr_emergency_contact (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  person_id       bigint       NOT NULL REFERENCES mod.hr_person(id),
  jmeno           varchar(150) NOT NULL,
  vztah           varchar(50),
  telefon         varchar(40),
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX ix_hr_emergency_person ON mod.hr_emergency_contact (person_id);

-- 8) digitální šanon (polymorfní) — základ pro GDPR
CREATE TABLE mod.hr_document (
  id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id         integer      NOT NULL,
  owner_entity_type varchar(20)  NOT NULL CHECK (owner_entity_type IN ('person','person_role','legal_entity')),
  owner_entity_id   bigint       NOT NULL,
  doc_kind          varchar(50),
  title             varchar(200),
  storage_path      varchar(500) NOT NULL,
  mime_type         varchar(100),
  byte_size         bigint,
  sensitivity_level smallint     NOT NULL DEFAULT 1 CHECK (sensitivity_level BETWEEN 0 AND 3),
  retention_until   date         NOT NULL,
  is_active         boolean      NOT NULL DEFAULT true,
  created_at        timestamptz  NOT NULL DEFAULT now(),
  created_by_id     integer,
  created_by_text   varchar(120) NOT NULL,
  updated_at        timestamptz  NOT NULL DEFAULT now(),
  updated_by_id     integer,
  updated_by_text   varchar(120)
);
CREATE INDEX ix_hr_doc_owner     ON mod.hr_document (owner_entity_type, owner_entity_id);
CREATE INDEX ix_hr_doc_retention ON mod.hr_document (retention_until);

-- 9) deklarativní ACL: sekce × role
CREATE TABLE mod.hr_section_acl (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id       integer      NOT NULL,
  section_code    varchar(50)  NOT NULL,
  role_code       varchar(50)  NOT NULL,
  can_read        boolean      NOT NULL DEFAULT false,
  can_write       boolean      NOT NULL DEFAULT false,
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120),
  CONSTRAINT uq_hr_section_acl UNIQUE (tenant_id, section_code, role_code)
);
CREATE INDEX ix_hr_section_acl_lookup ON mod.hr_section_acl (tenant_id, section_code);
```

---

## 7. Pořadí vytváření (kvůli FK)

`hr_party` → `hr_person`, `hr_legal_entity` → `hr_person_role`,
`hr_person_contact`, `hr_person_address`, `hr_emergency_contact` →
`hr_document`, `hr_section_acl`.

*Návrh sestavil Claude (id=24) pro Kristý, 4. 6. 2026 — ke konzultaci s Marti-AI.*
