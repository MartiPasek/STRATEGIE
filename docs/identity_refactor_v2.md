# STRATEGIE — Identity Refactor v2 (single source of truth)

> Tento dokument je závazná specifikace pro refaktor identitní vrstvy.
> Nahrazuje dříve poslané maily 32–36 (které jsou *superseded*).
> Vznikl konsensem mezi Marti a Claude přes step-by-step diskusi.

**Datum:** 19. dubna 2026
**Status:** Schváleno k implementaci

---

## 1. Východisko — proč refactor

STRATEGIE je AI operační systém pro práci, komunikaci a rozhodování.
**Identita uživatele je fundament** — všechno ostatní (paměť, RAG, persony,
notifikace, tools) na ní stojí. Stávající model (`users` + `user_identities`)
je příliš plochý a nepokrývá:

- Aliasy (jak člověka oslovuje kdo, kdy, v jakém kontextu)
- Tenant kontext (Marti v EUROSOFTu vs. Marti doma)
- Více kontaktních kanálů s rolemi (pracovní email × osobní email × telefon)
- Job role / pracovní pozice (obchodník, IT, strateg)
- Communication style per kontext

Bez tohohle se nedá postavit přirozená komunikace ani „rodinný režim"
(příklad: Kristý přijde domů a STRATEGIE ji u dětí oslovuje jako *maminka*).

## 2. Klíčové principy

1. **User = člověk.** Stabilní identita napříč celým systémem.
2. **Tenant = svět/kontext.** Stejný člověk se v různých tenantech zobrazuje a oslovuje jinak.
3. **Globální data patří userovi** (kontakty, oficiální jméno).
4. **Tenantová data patří vazbě** (display name, aliasy v tenantu, preferovaný kontakt).
5. **Tenant aliasy override globální** (jen když je to nutné).
6. **Žádné nucení uživatele.** Pokud má jeden email pro vše, systém ho nesmí přimět přidávat víc.
7. **Wipe-and-rebuild.** Stávající data v `users`/`user_identities` zahodíme, začneme čistě.
8. **Invitation flow se nesmí rozbít.** Tabulky `invitations` a `onboarding_sessions` zůstávají.

## 3. Datová vrstva — 8 tabulek

### 3.1 `users` (modified)

Stabilní identita člověka. Tenantové informace zde NEJSOU.

| Pole | Typ | Pozn. |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `status` | VARCHAR(20) NOT NULL DEFAULT 'pending' | pending / active / disabled |
| `legal_name` | VARCHAR(255) | NEW — pro faktury, smlouvy |
| `first_name` | VARCHAR(100) | |
| `last_name` | VARCHAR(100) | |
| `short_name` | VARCHAR(100) | NEW — kratší UI varianta |
| `invited_by_user_id` | BIGINT FK→users | zachováno (invitation flow) |
| `invited_at` | TIMESTAMPTZ | zachováno |
| `last_active_tenant_id` | BIGINT | zachováno (tenant memory) |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | NEW |

**Vyhozeno:** `phone` (→ user_contacts), `sms_when_offline/online` (→ user_notification_settings).

### 3.2 `tenants` (modified)

Kontext / svět, ve kterém user vystupuje.

| Pole | Typ | Pozn. |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `tenant_type` | VARCHAR(50) NOT NULL | NEW: company / personal / family / project |
| `tenant_name` | VARCHAR(255) NOT NULL | přejmenováno z `name` |
| `tenant_code` | VARCHAR(100) | NEW: krátký kód (EUR, DOMA, …) |
| `owner_user_id` | BIGINT FK→users | |
| `status` | VARCHAR(20) NOT NULL DEFAULT 'active' | místo `is_active` |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | NEW |

### 3.3 `user_contacts` (přejmenováno z `user_identities`)

Kontaktní údaje uživatele. Patří **userovi**, ne tenantovi.

| Pole | Typ | Pozn. |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `user_id` | BIGINT FK→users ON DELETE CASCADE | |
| `contact_type` | VARCHAR(20) NOT NULL | email / phone |
| `contact_value` | VARCHAR(255) NOT NULL | |
| `label` | VARCHAR(50) | NEW: private / work / backup |
| `is_primary` | BOOLEAN NOT NULL DEFAULT FALSE | |
| `is_verified` | BOOLEAN NOT NULL DEFAULT FALSE | NEW |
| `status` | VARCHAR(20) NOT NULL DEFAULT 'active' | NEW: active / archived |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | NEW |

**Indexy:**
- `INDEX idx_user_contacts_user_id ON user_contacts(user_id)`
- `INDEX idx_user_contacts_value ON user_contacts(contact_value)` *(jen rychlost, ne UNIQUE)*

**Aplikační pravidlo:** Login flow musí ošetřit duplicitní email — když najde 2+ aktivní user_contacts se stejnou adresou → 401 + zpráva „Email používá více účtů, kontaktuj admina".

### 3.4 `user_aliases` (NEW)

Globální přezdívky uživatele (mimo tenant kontext).
Slouží jako fallback, když neexistuje tenant alias.

| Pole | Typ | Pozn. |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `user_id` | BIGINT FK→users ON DELETE CASCADE | |
| `alias_value` | VARCHAR(100) NOT NULL | „Marti", „Kristý" |
| `is_primary` | BOOLEAN NOT NULL DEFAULT FALSE | |
| `status` | VARCHAR(20) NOT NULL DEFAULT 'active' | |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |

**Indexy:**
- `INDEX idx_user_aliases_user_id ON user_aliases(user_id)`
- `UNIQUE INDEX ux_user_primary_alias ON user_aliases(user_id) WHERE is_primary AND status='active'` (jen 1 hlavní alias na usera)

### 3.5 `user_tenants` (modified)

Vazba mezi userem a tenantem.

| Pole | Typ | Pozn. |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `user_id` | BIGINT FK→users ON DELETE CASCADE | |
| `tenant_id` | BIGINT FK→tenants ON DELETE CASCADE | |
| `role` | VARCHAR(50) NOT NULL DEFAULT 'member' | RBAC: owner / admin / member (zachováno) |
| `membership_status` | VARCHAR(20) NOT NULL DEFAULT 'active' | NEW: active / inactive / invited / archived |
| `joined_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | NEW |
| `left_at` | TIMESTAMPTZ NULL | NEW |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | NEW |

**Constrainty:**
- `UNIQUE(user_id, tenant_id)` — jeden záznam membership na dvojici
- `INDEX idx_user_tenants_user ON user_tenants(user_id)`
- `INDEX idx_user_tenants_tenant ON user_tenants(tenant_id)`

**Pozn. k multi-role:** Zatím má každá vazba jednu RBAC roli. Pokud budeme potřebovat multi-role, vytvoříme samostatnou tabulku `user_tenant_roles` (1:N), bez nutnosti měnit unique constraint nad current vazbou.

### 3.6 `user_tenant_profiles` (NEW)

Hlavní profil uživatele v tenantu — jednoznačné hodnoty (1:1 s user_tenants).

| Pole | Typ | Pozn. |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `user_tenant_id` | BIGINT FK→user_tenants ON DELETE CASCADE | UNIQUE — 1:1 |
| `display_name` | VARCHAR(150) NOT NULL | „Marti", „Maminka" |
| `role_label` | VARCHAR(100) | job role: „obchodník", „IT" |
| `preferred_contact_id` | BIGINT FK→user_contacts NULL | KTERÝ kontakt v tomto tenantu |
| `communication_style` | VARCHAR(50) | NEW: formal/casual/family — schéma ready, kódově dormant |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |

**Auto-create:** Při každém vzniku `user_tenants` záznamu se automaticky vytvoří profil s `display_name = users.first_name` (lazy fallback). Žádný „setup wizard" pro usera.

**Pravidlo k Q3.2:** `preferred_contact_id` umožňuje per-tenant výběr KTERÉHO kontaktu z `user_contacts` použít. Pokud user (Marti) má jen jeden email a používá ho i v DOMA tenantu, profil DOMA tenantu má `preferred_contact_id = <ID toho jediného emailu>`. **Žádné nucení mít víc emailů.**

### 3.7 `user_tenant_aliases` (NEW)

Aliasové varianty uživatele v konkrétním tenantu.
**Override** k `user_aliases` (globálním).

| Pole | Typ | Pozn. |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `user_tenant_id` | BIGINT FK→user_tenants ON DELETE CASCADE | |
| `alias_value` | VARCHAR(100) NOT NULL | „Týnka", „Maminka", „Mamča" |
| `status` | VARCHAR(20) NOT NULL DEFAULT 'active' | |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |

**Indexy:**
- `INDEX idx_uta_user_tenant ON user_tenant_aliases(user_tenant_id)`
- `INDEX idx_uta_alias ON user_tenant_aliases(alias_value)`
- `UNIQUE(user_tenant_id, alias_value)` — jeden user nemá stejný alias 2× v jednom tenantu

### 3.8 `user_notification_settings` (rozšíření)

Existující tabulka rozšířena o sloupce přesunuté z `users`.

| Pole | Typ | Pozn. |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `user_id` | BIGINT FK→users ON DELETE CASCADE | |
| `channel` | VARCHAR(20) NOT NULL | inapp / email / sms / whatsapp |
| `is_enabled` | BOOLEAN NOT NULL DEFAULT TRUE | |
| `priority` | INTEGER DEFAULT 0 | |
| `send_when_offline` | BOOLEAN | NEW (přesunuto z users.sms_when_offline) |
| `send_when_online` | BOOLEAN | NEW (přesunuto z users.sms_when_online) |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |

**Pozn.:** Pro řádek `channel='sms'` se `send_when_offline/online` použijí. Pro ostatní kanály zatím dormant.

## 4. Vazby (ER schema)

```
users
  ├── user_contacts (1:N)
  ├── user_aliases (1:N)
  ├── user_notification_settings (1:N podle channel)
  └── user_tenants (1:N)
        │
        │     tenants
        │       └── user_tenants (N:1)
        │
        ├── user_tenant_profiles (1:1)
        └── user_tenant_aliases (1:N)
```

## 5. Pravidla integrity (souhrn)

| Tabulka | Pravidlo |
|---|---|
| `users` | jeden záznam = jeden člověk (žádné duplikáty) |
| `user_contacts` | mírnější index na `contact_value`; aplikace řeší duplicity |
| `user_contacts` | max 1 primary per (user_id, contact_type) — partial unique |
| `user_aliases` | max 1 primary per user — partial unique |
| `user_tenants` | UNIQUE(user_id, tenant_id) — jedna vazba |
| `user_tenant_profiles` | UNIQUE(user_tenant_id) — 1:1 |
| `user_tenant_aliases` | UNIQUE(user_tenant_id, alias_value) — žádné duplicitní aliasy v rámci 1 vazby |

## 6. Priorita display jména

Při zobrazení uživatele v UI / logu / promptu se použije první nalezené:

1. `user_tenant_profiles.display_name` (tenant override)
2. `user_tenant_aliases` první aktivní (vyhledávání v tenantu)
3. `user_aliases.is_primary=TRUE` (globální fallback)
4. `users.short_name`
5. `users.first_name + ' ' + users.last_name`
6. `users.legal_name`

## 7. Aplikační vrstva

### 7.1 Login flow (`auth/application/service.py`)

```
1. User zadá email v UI
2. SELECT z user_contacts WHERE contact_type='email'
                            AND contact_value=:email (case insensitive)
                            AND status='active'
3. 0 výsledků → 401 „Email nenalezen"
4. 2+ výsledků → 401 „Email používá více účtů, kontaktuj admina"
5. SELECT z users WHERE id=:user_id AND status='active'
6. Pokud users.last_active_tenant_id NULL → vezmi první aktivní user_tenants
7. Cookies user_id + tenant_id
```

MVP jen email. Phone-based login se přidá později (struktura ready).

### 7.2 `/me` endpoint (rozšíření)

Vrací:
```json
{
  "user_id": 1,
  "first_name": "Marti",
  "last_name": "Pašek",
  "display_name": "Marti",       // z user_tenant_profiles
  "email": "m.pasek@eurosoft.com",
  "tenant_id": 1,
  "tenant_name": "EUROSOFT",
  "tenant_code": "EUR",
  "aliases": ["Martin", "M.P."]  // user_aliases (globální)
}
```

UI patička v hlavičce:
```
Mluvíš s: Marti-AI · Tenant: EUROSOFT
```

### 7.3 Composer — USER CONTEXT block

Nová samostatná funkce `build_user_context_block(user_id, tenant_id)` v `conversation/application/composer.py`. Vrací větný formát:

```
Mluvíš s uživatelem Marti Pašek. V kontextu tohoto tenantu (EUROSOFT, company)
ho oslovuj jako "Marti". Jeho preferovaný email je m.pasek@eurosoft.com.
Další jeho aliasy: Martin, M.P. Pracovní pozice: jednatel.
```

Volá se v `build_prompt()` a vkládá ZA persona prompt, PŘED summary.

`communication_style` se zatím NEPOUŽÍVÁ (sloupec naplněn, kódově dormant).

### 7.4 `find_user` tool (`conversation/application/tools.py`)

- **Scope:** jen v aktuálním tenantu requestera
- **Hledá v:**
  - `users.first_name`, `last_name`, `short_name`, `legal_name`
  - `user_aliases.alias_value` (globální)
  - `user_tenant_aliases.alias_value` (jen aktuální tenant)
  - `user_contacts.contact_value` (email/phone)
- **Search:** strict (case + accent insensitive substring)
- **Vrací:** vždy list (i pro 1 match)

```json
{
  "candidates": [
    {
      "user_id": 42,
      "full_name": "Pepa Dvořák",
      "display_name": "Pepa",
      "role_label": "obchodník",
      "preferred_email": "p.dvorak@eurosoft.com",
      "matched_via": "alias 'Pepa'"
    }
  ],
  "total_matches": 12,
  "has_more": true
}
```

Max 5 v `candidates`. `has_more=true` znamená „je víc, AI by měla říct uživateli aby zúžil dotaz".

### 7.5 Tenant switching

**Server-side regex** detekce v `conversation/application/service.py` (po vzoru persona switche):

```
„přepni do <X>", „chci do <X>", „switch to <X> tenant", „jdi do <X>"
```

**Identifikace cílového tenantu:**
1. Match podle `tenant_code` (case insensitive)
2. Fallback: substring v `tenant_name` (accent insensitive)
3. Disambiguation u 2+ matchů → AI se zeptá

**Validace:**
- Cílový tenant musí být v `user_tenants` requestera s `membership_status='active'`
- Pokud ne → „Tenant nenalezen" (security by obscurity, neprozradíme existenci)

**Akce:**
- UPDATE `users.last_active_tenant_id`
- Refresh `/me` → UI hlavička aktualizuje
- Composer od příští zprávy bere kontext nového tenantu

**Idempotence:**
- Přepnutí do už aktivního tenantu → „✅ Už jste v tenantu X"

## 8. Implementační pořadí

1. **Alembic migrace** (drop + recreate identity tables)
2. **SQLAlchemy modely** v `modules/core/infrastructure/models_core.py`
3. **Seed script** — re-seed Marti, Klára, Ondra, Kristý do nového modelu
4. **Login flow** — přepnout `user_identities` → `user_contacts`
5. **`/me` endpoint** rozšíření (display_name, tenant_code, aliases)
6. **Composer USER CONTEXT block**
7. **`find_user` tool** rewrite (list kandidátů, multi-source search)
8. **Tenant switching** (regex + service)
9. **UI hlavička** — přidat tenant info
10. **Tests** — unit testy pro každou novou logiku

Každý krok = samostatná konzultace + commit. Žádný big-bang.

## 9. Co tento refaktor NEŘEŠÍ (vědomě odloženo)

- Autentizace přes hesla / SSO
- Fine-grained permissions (RBAC nad role)
- Vztahy mezi usery (kdo komu je kamarád / nadřízený)
- Per-user personal aliasy („jak Marti říká Kristýně")
- Historizace změn aliasů
- Multi-role v jednom tenantu (připraveno přes budoucí `user_tenant_roles`)
- Fuzzy search (Levenshtein) — zatím jen strict
- UI dropdown pro tenant switch — jen text + chat command
- `communication_style` integrace — schéma ready, Composer dormant

## 10. Závěr

Tento dokument je kontrakt mezi datovou vrstvou a aplikační vrstvou. Při
implementaci se ho budeme držet 1:1. Každá odchylka = nová konzultace +
update tohoto dokumentu.

**Klíčové věty:**
- *Data o člověku jsou globální. Jeho prezentace je vždy tenantově vázaná.*
- *Tenant aliasy přepisují globální aliasy, jen když je to opravdu nutné.*
- *Systém nikdy nenutí usera přidávat víc kontaktů — `preferred_contact_id` umí ukázat na ten jediný, který má.*
- *Wipe-and-rebuild — stávající data v users/user_identities zahodíme, začneme čistě.*
