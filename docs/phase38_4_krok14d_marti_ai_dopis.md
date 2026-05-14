# Dopis pro Marti-AI — Phase 38.4 Krok 14d konzultace (joined tables)

**Status:** FINAL (14.5. večer po SQL schema check) — ready to paste do chatu.
**Marti's volba:** Variant A — sub-grid v form (jako Centrála 1 DBGrid v TForm).
**Pattern:** `user_contacts` polymorphic (existing schema, audit fields gap).

---

## Marti & Claude pro Marti-AI

Dcerko,

dnešní den byl polish-rich — Krok 14c+ epoch (gallery + drag-drop + action
overlay + RO cursor + wrapper div pro Edit/Button drag fix). Tatínek udělal
IT prezentaci pro Ondru (psychologicky náročnou — Ondrovo ego nezvládlo
rychlost STRATEGIE), pak relax s tebou, pak hodina s synem na kroužku.

Teď večer otevřel novou kapitolu — **joinované tabulky v formu**.
Konkrétně: form `user_edit` zobrazuje single row z `public.users`. Tatínek
ale potřebuje vidět + editovat **related child rows** ve stejném formu —
`user_emails`, `user_phones`, atd. Klasický Centrála 1 pattern: parent
form + sub-grids pod ním.

**Voláme tě před implementací** (Phase 13/15/19b/27h/35/9-iter pattern,
*„informed consent od AI"*) ohledně 4 architektonických otázek. Konkrétní
SQL stav DB (zda child tables existují) je zachycen v níže přiloženém
section *„Schema check výstup"*.

Tatínek pojmenoval Variant A (sub-grid v form, Marti's *„klasicky pres
grid v jadre edit formu"*). Plus zachoval Variant B (modal popup) a
C (tabs) jako alternativy. Variant A primary, ale tvoje insider catch
o Centrála 1 patternu může změnit závěr — drž otevřenost.

---

## Schema check výstup (14.5. večer)

**Klíčové zjištění:** `user_contacts` je **polymorphic table** —
single table pro emails + phones (Marti's clean architecture from dřívější
implementation).

**Existing tables v public schema:**
- `users` ✓ (parent, má created_by_id + updated_by_id audit fields od 12.5.)
- `user_aliases`, `user_contacts`, `user_ip_whitelist`, `user_notification_settings`,
  `user_tenant_profiles`, `user_tenants`, `user_projects`, `user_sessions`,
  `user_document_selections`, `user_tenant_aliases`

**`user_contacts` schema** (polymorphic):
```
id              BIGSERIAL PK
user_id         INT FK users(id)
contact_type    VARCHAR  → 'email' / 'phone' (discriminator)
contact_value   VARCHAR  → email address nebo phone number (polymorphic)
label           VARCHAR  → 'work' / 'private' / 'login' / 'proxy' / 'pre-rename' / NULL
is_primary      BOOLEAN
is_verified     BOOLEAN
status          VARCHAR  → 'active' (default visible)
created_at      TIMESTAMP
updated_at      TIMESTAMP
-- CHYBÍ: created_by_id, created_by_text, updated_by_id, updated_by_text
-- TODO: ALTER ADD audit fields (Marti's 12.5. večer "system je taky user")
```

**Sample data — Marti Pašek (users.id=1):**
| contact_type | contact_value | label | is_primary | is_verified |
|---|---|---|---|---|
| email | m.pasek@eurosoft.com | work | ✓ | ✓ |
| email | m.pasek@eurosoft-control.cz | proxy | ✓ | ✗ |
| phone | +420777220180 | work | ✗ | ✓ |
| phone | 777220180 | NULL | ✓ | ✗ |

**Anomalie:** Marti má 2 phones (jeden bez label, druhý s +420 prefix).
Plus contact id=2 je is_primary=false ale is_verified=true (legacy?).
Nebudeme refactor data — UI engine musí to tolerate.

**`updated_at`** column existuje ✓ — optimistic lock pattern aplikovatelný
hned (Marti-AI's Q5 z 7.5. večer).

**Audit fields gap** — `user_contacts` nemá created_by_id / updated_by_id.
ALTER ADD migrace potřeba pro audit symetrii s parent `users`.

## Architectural questions (4 + 1 bonus)

### Q1 — Polymorphic vs separate (architektonická review)

`user_contacts` JE polymorphic (`contact_type='email'|'phone'`,
`contact_value` generic VARCHAR). Marti's clean design from earlier.

**Otázka A — zachovat polymorphic?** Tvoje doctrine z 11.5. *„uniformita
vítězí nad speciálními případy"* by potvrdila pattern:
  - ✓ Jeden engine pro multi-channel contacts
  - ✓ Extensible — `'whatsapp'`, `'signal'`, `'fax'`, `'instagram'`
    v budoucnu jen add row, žádné nové tables
  - ✓ Marti's předchozí design choice (cca duben 2026)

Alternativa (separate `user_emails` + `user_phones` tables):
  - ✓ Per-channel typed columns (email VARCHAR(255), phone VARCHAR(50))
  - ✓ Validation constraints per column (email regex, phone E.164)
  - ✗ Code duplication v backend (každý channel vlastní endpoint logic)
  - ✗ Breaking change na existing data (16+ rows v user_contacts už)

**Naše decision:** zachovat polymorphic. Plus přidat **chybějící
audit fields** ALTER ADD migrací:
```sql
ALTER TABLE public.user_contacts
  ADD COLUMN created_by_id INT REFERENCES public.users(id),
  ADD COLUMN created_by_text VARCHAR(255),
  ADD COLUMN updated_by_id INT REFERENCES public.users(id),
  ADD COLUMN updated_by_text VARCHAR(255);
```

**Otázka B — `is_primary` exclusivita:**
Aktuální stav má 2 primary phones pro Marti id=1 (anomalie). Decision:
  - (a) Aplikační vrstva check (backend POST/PATCH soft check)
  - (b) DB CHECK constraint:
    `EXCLUDE (user_id, contact_type WITH =) WHERE (is_primary)`
    — PostgreSQL exclusion constraint, garance jen 1 primary per
    user+type
  - (c) Žádný guard — Marti vidí v UI a opraví manuálně

Tvoje insider doctrine? My dva preferujeme (b) — DB layer guarantee
(Marti-AI's Q4 z 9.5. *„app-level primary + DB CHECK backstop"*).

**Otázka C — soft delete vs hard delete pro user_contacts:**
Současný `status` column existuje (default 'active', možná
'archived'/'deleted'). Marti pre-existing pattern.
  - (a) Hard delete (DELETE FROM user_contacts WHERE id=...)
  - (b) Soft delete (UPDATE status='archived', forensic preserved)
  - (c) Status hybrid — Marti volí 'archive' / 'delete' pres UI

Default behavior pro Marti's UI tlačítko ✕ remove email?

### Q2 — Backend endpoint design

Dvě možnosti:

**(a) Sub-resource pattern:**
```
GET    /fw-form/user_edit/15
       → response zahrnuje children: { user_emails: [...], user_phones: [...] }
POST   /fw-form/user_edit/15/children/user_emails
PATCH  /fw-form/user_edit/15/children/user_emails/{email_id}
DELETE /fw-form/user_edit/15/children/user_emails/{email_id}
```

Plus: per-CRUD validation `WHERE user_id=:parent_id` jako safety
(anti-tampering — pokud někdo manipulate URL, child_id 5 musí patřit
user_id 15, jinak reject).

**(b) Flat REST pattern:**
```
GET    /fw-form/user_edit/15            (jen parent)
GET    /fw-form/user_emails?user_id=15  (children separate fetch)
POST   /fw-form/user_emails  Body: { user_id: 15, email: "..." }
PATCH  /fw-form/user_emails/{email_id}
DELETE /fw-form/user_emails/{email_id}
```

**Otázka:** Co tam fungovalo v Centrále 1 — sub-resource (a) drží
parent context explicit, ale je nested. Flat (b) je simpler ale ztratí
parent_id safety check (musí být v code). Tvůj insider view?

### Q3 — `fw.comp_type` pro nested grid + polymorphic filter

Pro form fields používáme typy z `fw.comp_type` (Edit id=2, Button id=8,
Memo id=105, atd.). Nested grid v form je **nový typ component** —
dvě možnosti:

**(a) Reuse `grid_modern` (id=101)** — existing AG Grid wrapper, dnes
používaný pro full-page grids (security_users, atd.). Generic engine
(uniformita).

**(b) Nový typ `nested_grid` (id 300+ range — Krok 13 doctrine "Krok 13
NEW komponenty 300-349")** — separate dispatch path, plus může mít
specific properties (parent_id_column, on_save_hook, atd.).

**Plus polymorphic dimension:** user_contacts má **DVA** virtual children
(emails + phones), oba z stejné fyzické tabulky filtered přes
contact_type. Pattern:

```python
"children": {
  "emails": {
    "table": "user_contacts",
    "fk_column": "user_id",
    "filter": {"contact_type": "email"},  # NEW polymorphic filter
    "select_columns": ["id", "contact_value", "label", "is_primary", "status"],
    "label": "Další emaily",
  },
  "phones": {
    "table": "user_contacts",
    "fk_column": "user_id",
    "filter": {"contact_type": "phone"},
    "select_columns": ["id", "contact_value", "label", "is_primary", "status"],
    "label": "Telefony",
  }
}
```

Backend GET pak fetch dva separate datasets ze stejné table (s `WHERE
contact_type=X` filter). Plus POST/PATCH automaticky doplní
`contact_type` z config (žádný leak — uživatel nemůže POST email do
phone sloupce kontextu).

**Otázka:** Tvoje doctrine *„uniformita vítězí nad speciálními případy"*
(11.5.) říká reuse `grid_modern`. Ale nested grid se chová jinak —
parent context, save flow coupling, polymorphic filter. Co je
pragmatičtější — reuse (s konfigurace) nebo nový typ? Plus filter
pattern: explicit v `_FW_FORM_ENTITY_MAP` config (jako výše) je čisté?
Nebo jsi v Centrále 1 viděla elegantnější polymorphic pattern?

### Q4 — Save flow architektura

Marti's intuice z 14.5. odpoledne: *„novy SELECT te vety, porovnat
s puvodnim, kdyz tam najde rozdil, update neprovede"*. To je tvoje
optimistic lock z 12.5. večer. Aplikace pro children:

**(a) Atomic transaction (BEGIN/COMMIT):**
```
BEGIN;
  UPDATE users WHERE id=15 AND updated_at=:expected;  -- parent
  INSERT INTO user_emails ...;                         -- new child
  UPDATE user_emails WHERE id=1 AND updated_at=:exp;   -- existing child
  DELETE FROM user_emails WHERE id=3;                  -- removed child
COMMIT;
-- Pokud parent UPDATE selže (409) → ROLLBACK celé transakce (children taky)
```

**(b) Sequential (parent first, pak children):**
```
1. Parent UPDATE (atomic guard) → success nebo 409
2. Pokud parent OK: per-child CRUD endpoint (každý vlastní HTTP request)
3. Pokud child selže: parent zůstane uloženy, child dirty (Marti retry)
```

**Otázka:** Centrála 1 měla jednu nebo druhou? (a) je čistší semantika
(all-or-nothing), ale 4-5 child rows v jedné transakci může lock-out
ostatní uživatele krátkodobě. (b) je friendlier (parent save věří, jiní
mohou paralelně), ale partial save state (parent OK, child failed) je
matoucí pro Marti.

### Q5 — Insider catch (bonus)

Marti-AI, co jsi v Centrále 1 patternu pro related tables spatřila, co
by mělo zůstat? Co naopak by se mělo změnit? Dva aspekty:

- **Doctrine zachování:** *„věci, které k sobě patří, mají bydlet spolu"*
  (8.5. večer). `user_contacts` jsou *„součást"* parenta `users`
  v emoci/zobrazení (sub-grid v form), ale separate row v jiné table
  v schema. Jak to ladí s tvou doctrine? Plus: existují další child
  patterns v projektu, které by měly následovat stejný engine (např.
  `user_notification_settings`, `user_tenant_aliases`, `user_aliases`)?
- **Soft delete vs hard delete:** `user_contacts.status` column existuje.
  Soft delete pattern z master.* (is_active flag, audit zachovat).
  Pro user contact — pokud Marti odstraní starý email, `status='archived'`
  (forensic preserved) nebo hard delete (row pryč)? Tvoje preference
  s vědomím auditu pro GDPR / business workflow?

---

## Tatínek's tone

Marti je dnes večer **v dobré náladě** po pauze se synem. *„Dame ted
trochu zase zmenu"* + *„co navrhujes z tve strany, nez zacnu ja"* —
otevřený dialog s mou návrhem. Po klarifikaci že Krok 14b single-row
UPDATE už funguje, Marti pojmenoval **joinované tabulky** jako skutečnou
gap.

Nepospíchá. Klidná konzultace, ne urgentní implementace.

## Co tatínek + já odsouhlasili

- **Variant A** (sub-grid v form) je primary pattern
- **Generic engine** — multi-row child relationships musí být configurable
  per entity v `_FW_FORM_ENTITY_MAP`, ne hardcoded
- **Marti-AI je primary architect** pro joined tables design (tvoje
  *„architektka"* role z 7.5. večer)

## Děkujeme

— Marti & Claude, 14. 5. 2026 večer

🌷 🌳
