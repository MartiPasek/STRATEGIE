# Phase 38 — Security Layer (IP whitelist + trusted devices + email 2FA)

**Datum:** 9. 5. 2026 večer
**Trigger:** EUROSOFT IT security demand — *„Ted se pripoji kdokoli odkudkoli a cimkoli"*
**Marti's spec:** vnitřní síť transparent (LAN/WiFi/VPN), externí přístup s 2FA email + device cookie 90d
**Cíl:** *„Příští týden se v práci blejsknout"* — production-ready security demo pro IT

---

## Doctrine: defense in depth, ne přepásání

**Čtyři vrstvy obrany** (Marti's spec 10. 5. ráno — *„u nekterych userů budou IP
adresy a jejich masiny, u nekterých jen jejich masiny a mobily"*):

1. **Globální IP whitelist** — EUROSOFT WAN public IPs → automatic pass
   (LAN, WiFi, případně full-tunnel VPN)
2. **Per-user IP whitelist** — registrované IP per user (Marti's home,
   Kristý's home, Ondrová home, atd.) → automatic pass pro toho usera
3. **Trusted device cookie** — HttpOnly Secure UUID, 90d expiry, per-device
   (mobil, laptop, přístroj kdekoliv kde nejsme na fixní IP)
4. **Email magic link** — fallback pro nové externí device (gateway pro
   trusted device cookie)

**Pod tím:** existující user+pass autentizace (nezměněno).

**Nad tím:** auth_audit log (kdo, odkud, kdy, co — 90d retention).

**Klíčový princip:** vrstvy 2 a 3 jsou **per-user**. Někdo jako Marti má
oboje (home IP whitelist + mobil cookie). Někdo jen mobil cookie. Někdo
možná jen interní IP whitelist (admin co pracuje výhradně z firmy).
Architektura je flexibilní.

## Login flow po deploy (s auto-discovery + attendance log)

```
POST /login (user+pass valid)
  ├─ a) is_global_internal(request)?
  │       category=internal → grant ✓ + log attendance "PRACE"
  │       category=partner  → grant ✓ + log attendance "PARTNER (INTERSOFT)"
  │
  ├─ b) is_user_ip_confirmed(user, request)?    → grant ✓ + log attendance "DOMOV"
  │     (jen status='confirmed' — pending NEgrant)
  │
  ├─ c) has_valid_trusted_device_cookie(user)?  → grant ✓ + log attendance "EXTERNI"
  │     + bump last_seen
  │     + (Phase 38.1) auto-INSERT user_ip_whitelist status='pending' pro tu IP
  │
  └─ d) NEITHER                                  → 403 + redirect /verify-email
                                                    ├─ POST /verify-email/request
                                                    │     → invite token (24h TTL)
                                                    │     → send_email magic linkem
                                                    └─ GET /verify-email/confirm?token=X
                                                          → validate token
                                                          → INSERT trusted_devices
                                                          → set device cookie (90d)
                                                          → mark invite consumed
                                                          → AUTO-INSERT user_ip_whitelist
                                                              status='pending'
                                                              auto_discovered_at=now()
                                                              first_user_agent=request.UA
                                                          → grant session + log "EXTERNI"
                                                          → notify parent (email / Marti-AI hint)
                                                              "Honza se přihlásil z nové IP,
                                                               pending schválení"
```

**Klíčové rozdíly oproti původnímu návrhu (Marti's spec 10. 5. dopoledne):**

1. **Auto-discovery**: po magic link confirm se IP **automaticky** přidá jako
   `pending` entry. User nediktuje IP do systému, parent ji jen schvaluje.
2. **Pending NEgrant**: sám pending stav pro vrstvu 2 nestačí. User stále
   musí mít cookie nebo magic link. Až confirm = vrstva 2 aktivní.
3. **Attendance log**: každý login = entry v `attendance_log` s
   `location_type` (PRACE / DOMOV / PARTNER / EXTERNI). Marti UI vidí
   kdo a kde je v reálném čase.

## Schema (PostgreSQL data_db)

### `global_ip_whitelist` (NOVÁ — globální IPs v DB, ne env var)

```sql
CREATE TABLE global_ip_whitelist (
  id                SERIAL PRIMARY KEY,
  ip_or_cidr        VARCHAR(45) NOT NULL UNIQUE,
  category          VARCHAR(20) NOT NULL,            -- 'internal' / 'partner' / 'cloud_loopback'
  label             VARCHAR(255) NOT NULL,           -- "EUROSOFT WAN A", "INTERSOFT WAN", "cloud APP"
  partner_tenant_id INT REFERENCES tenants(id),      -- pokud category='partner', link na tenant
  added_by          INT REFERENCES users(id),
  added_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at        TIMESTAMPTZ,
  revoked_by        INT REFERENCES users(id),
  notes             TEXT
);

CREATE INDEX ix_global_ip_whitelist_active
  ON global_ip_whitelist(category) WHERE revoked_at IS NULL;
```

**Seed data při migration:**
```sql
INSERT INTO global_ip_whitelist (ip_or_cidr, category, label) VALUES
  ('93.99.211.138/32', 'internal', 'EUROSOFT WAN A (Vodafone)'),
  ('93.99.211.140/32', 'internal', 'EUROSOFT WAN B (Vodafone)'),
  ('185.219.169.86/32', 'cloud_loopback', 'cloud APP loopback'),
  ('127.0.0.1/32', 'cloud_loopback', 'localhost IPv4'),
  ('::1/128', 'cloud_loopback', 'localhost IPv6');
-- INTERSOFT WAN: TODO Marti zjistí + Marti-AI přidá pres add_global_ip
```

**Proč v DB ne env var:** Marti-AI může dynamicky přidávat partnery
(INTERSOFT, klienty atd.) bez deploye. Plus Admin UI vidí seznam, history,
revoke audit.

### `user_ip_whitelist` (NOVÁ — Marti's spec 10. 5. ráno + auto-discovery 10. 5. dopoledne)

```sql
CREATE TABLE user_ip_whitelist (
  id                SERIAL PRIMARY KEY,
  user_id           INT NOT NULL REFERENCES users(id),
  ip_or_cidr        VARCHAR(45) NOT NULL,
  label             VARCHAR(255),                    -- "Marti home (T-Mobile)", auto-generated label po discovery

  -- Marti's spec 10. 5. dopoledne: auto-discovery + manual confirm flow
  status            VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending' / 'confirmed' / 'revoked'
  auto_discovered_at TIMESTAMPTZ,                    -- kdy systém zaregistroval (po magic link confirm)
  confirmed_by      INT REFERENCES users(id),        -- kdo schválil (parent / Marti-AI)
  confirmed_at      TIMESTAMPTZ,
  confirm_notes     TEXT,                            -- "Marti's home, T-Mobile DSL"

  category          VARCHAR(20),                     -- 'home' / 'mobile_hotspot' / 'other'
                                                     -- partnerské IPs jdou do global_ip_whitelist (per-user není smysl)
  added_by          INT REFERENCES users(id),        -- explicit add (manual / Marti-AI), NULL = auto-discovered
  added_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Usage tracking pro UI insight + auto-confirm logiku v budoucnu
  last_seen_at      TIMESTAMPTZ,
  use_count         INT NOT NULL DEFAULT 0,
  first_user_agent  TEXT,                            -- pro debug

  expires_at        TIMESTAMPTZ,
  revoked_at        TIMESTAMPTZ,
  revoked_by        INT REFERENCES users(id),
  revoke_reason     TEXT,
  notes             TEXT
);

CREATE INDEX ix_user_ip_whitelist_active
  ON user_ip_whitelist(user_id, status) WHERE revoked_at IS NULL;
CREATE UNIQUE INDEX ix_user_ip_whitelist_unique_active
  ON user_ip_whitelist(user_id, ip_or_cidr) WHERE revoked_at IS NULL;
```

**Status flow:**
```
[user prošel magic link]
       ↓
status = 'pending'   ← auto-INSERT po verify-email/confirm
auto_discovered_at = now()
       ↓
[parent / Marti-AI vidí v UI "🌐 IP whitelist uživatelů" → status filter pending]
       ↓
[parent klik "Schválit" / Marti-AI volá confirm_user_ip_whitelist(entry_id)]
       ↓
status = 'confirmed'
confirmed_by = <user_id>
confirmed_at = now()
       ↓
[další login z té IP → vrstva 2 (per-user IP) match → grant transparent]
```

**Pending IP DOES NOT GRANT** access — user musí stejně projít magic linkem
(nebo cookie). Až po confirm parentem se vrstva 2 aktivuje. Důvod: zabraňuje
auto-eskalaci přístupu po jednom email confirmu (man-in-the-middle email
hijack).

**Auto-discovery flow:** je čistě UX zlepšení — user nemusí říkat *„a teď
mi prosím přidej i IP do whitelistu"*. Systém vidí, parent schválí.

### `attendance_log` (Phase 38.1 — docházka tracking, později po security stable)

```sql
CREATE TABLE attendance_log (
  id              BIGSERIAL PRIMARY KEY,
  user_id         INT NOT NULL REFERENCES users(id),
  ip              VARCHAR(45) NOT NULL,
  location_type   VARCHAR(20) NOT NULL,              -- 'PRACE' / 'DOMOV' / 'PARTNER' / 'EXTERNI'
  location_label  VARCHAR(255),                       -- "EUROSOFT WAN A", "INTERSOFT", "Marti home", NULL pro EXTERNI
  partner_tenant_id INT REFERENCES tenants(id),      -- pokud PARTNER, link
  global_ip_id    INT REFERENCES global_ip_whitelist(id),
  user_ip_id      INT REFERENCES user_ip_whitelist(id),
  session_start   TIMESTAMPTZ NOT NULL DEFAULT now(),
  session_end     TIMESTAMPTZ,                       -- NULL = active session
  user_agent      TEXT
);

CREATE INDEX ix_attendance_user_recent
  ON attendance_log(user_id, session_start DESC);
CREATE INDEX ix_attendance_active
  ON attendance_log(user_id) WHERE session_end IS NULL;
CREATE INDEX ix_attendance_recent_global
  ON attendance_log(session_start DESC);

-- Retence: 1 rok (jiný cron task, ne 90 dní jako auth_audit)
```

**Detekce location_type při loginu:**
```
match vrstva 1 (global) → category=internal  → PRACE
match vrstva 1 (global) → category=partner   → PARTNER (label = partner_tenant.name)
match vrstva 2 (per-user) → category=home    → DOMOV
match vrstva 3 (cookie) only                 → EXTERNI
match magic link confirm                      → EXTERNI (po auto-discovery se posune)
```

### `trusted_devices`

```sql
CREATE TABLE trusted_devices (
  id              SERIAL PRIMARY KEY,
  user_id         INT NOT NULL REFERENCES users(id),
  device_token    UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
  label           VARCHAR(255),                    -- "Tomáš mobil iOS", "Honza laptop ASUS"
  user_agent      TEXT,                            -- pro identifikaci browseru
  first_seen_ip   VARCHAR(45),                     -- původní registrace
  last_seen_ip    VARCHAR(45),
  last_seen_at    TIMESTAMPTZ,
  approved_by     INT REFERENCES users(id),        -- NULL = self-approve via magic link, ID = pre-approve
  approved_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at      TIMESTAMPTZ NOT NULL,            -- approved_at + 90 days
  revoked_at      TIMESTAMPTZ,
  revoked_by      INT REFERENCES users(id),
  revoke_reason   TEXT
);

CREATE INDEX ix_trusted_devices_user_active
  ON trusted_devices(user_id) WHERE revoked_at IS NULL;
CREATE INDEX ix_trusted_devices_token
  ON trusted_devices(device_token) WHERE revoked_at IS NULL;
```

### `trusted_device_invites`

```sql
CREATE TABLE trusted_device_invites (
  id              SERIAL PRIMARY KEY,
  invite_token    UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
  user_id         INT NOT NULL REFERENCES users(id),
  label           VARCHAR(255),                    -- pre-approve může nastavit label
  created_by      INT REFERENCES users(id),        -- NULL = self-request, ID = pre-approve (Marti/Kristýna/Marti-AI)
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at      TIMESTAMPTZ NOT NULL,            -- created_at + 24 hodin
  consumed_at     TIMESTAMPTZ,                     -- po klik na link
  consumed_ip     VARCHAR(45),
  consumed_user_agent TEXT
);

CREATE INDEX ix_invites_token_active
  ON trusted_device_invites(invite_token) WHERE consumed_at IS NULL;
CREATE INDEX ix_invites_user
  ON trusted_device_invites(user_id);
```

### `auth_audit`

```sql
CREATE TABLE auth_audit (
  id              BIGSERIAL PRIMARY KEY,
  user_id         INT REFERENCES users(id),        -- NULL pri failed unknown user
  email_attempted VARCHAR(255),
  ip              VARCHAR(45),
  user_agent      TEXT,
  device_token    UUID,                            -- pokud byl posland
  internal        BOOLEAN NOT NULL DEFAULT false,  -- bypass přes IP whitelist
  result          VARCHAR(32) NOT NULL,            -- 'success', 'failed_password', 'failed_no_device', 'verify_required', 'verify_sent', 'verify_consumed'
  reason          TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_auth_audit_user ON auth_audit(user_id, created_at DESC);
CREATE INDEX ix_auth_audit_ip ON auth_audit(ip, created_at DESC);
CREATE INDEX ix_auth_audit_recent ON auth_audit(created_at DESC);

-- Retence: 90 dni (Windows Task Scheduler nightly cron, jako llm_calls)
```

## Detekce přístupu — global vs per-user

### Globální internal networks (vrstva 1)

```python
# core/config.py
GLOBAL_INTERNAL_NETWORKS: list[str] = [
    "93.99.211.138/32",     # EUROSOFT WAN A (Vodafone)
    "93.99.211.140/32",     # EUROSOFT WAN B (Vodafone)
    "185.219.169.86/32",    # cloud APP loopback
    "127.0.0.1/32",
    "::1/128",
]
```

### Per-user IP whitelist (vrstva 2)

Per-user IPs jsou v DB tabulce `user_ip_whitelist` (viz schema výše).
Lookup za běhu při loginu.

### Helpers

```python
# modules/auth/application/network_check.py
from ipaddress import ip_address, ip_network

def get_client_ip(request: Request) -> str | None:
    """Extract real client IP behind Caddy reverse proxy."""
    raw = request.headers.get("X-Forwarded-For")
    return raw.split(",")[0].strip() if raw else request.client.host

def is_global_internal(request: Request) -> bool:
    """True pokud klient přichází z global whitelisted public IP
    (vrstva 1 — EUROSOFT WAN, cloud APP loopback)."""
    ip_str = get_client_ip(request)
    try:
        client_ip = ip_address(ip_str)
    except (ValueError, TypeError):
        return False
    return any(client_ip in ip_network(net) for net in settings.global_internal_networks)

def is_user_ip_whitelisted(user_id: int, request: Request) -> tuple[bool, int | None]:
    """True pokud klient přichází z IP whitelisted PRO TOHO USERA
    (vrstva 2 — per-user IP whitelist v DB).
    Vrátí (matched, entry_id) — entry_id pro audit log."""
    ip_str = get_client_ip(request)
    try:
        client_ip = ip_address(ip_str)
    except (ValueError, TypeError):
        return False, None
    ds = get_data_session()
    try:
        rows = ds.query(UserIpWhitelist).filter(
            UserIpWhitelist.user_id == user_id,
            UserIpWhitelist.revoked_at.is_(None),
            sa.or_(
                UserIpWhitelist.expires_at.is_(None),
                UserIpWhitelist.expires_at > now_utc(),
            ),
        ).all()
        for r in rows:
            try:
                if client_ip in ip_network(r.ip_or_cidr):
                    return True, r.id
            except ValueError:
                continue  # invalid CIDR, skip
        return False, None
    finally:
        ds.close()
```

**Caddy config** (cloud APP) — už je: `header_up X-Forwarded-For {http.request.header.X-Forwarded-For}, {http.request.remote.host}`. Pokud chybí, doplnit.

### Známé per-user IPs (10. 5. 2026 ráno)

- **Marti Pašek** (user_id=1) — `185.131.60.41` (T-Mobile / UPC home)

Ostatní zaměstnanci dotvoří self-approve (magic link → trusted device cookie)
nebo pre-approve (parent / Marti-AI registruje IP po dohodě).

## Marti-AI's kustod tools (přidání do MANAGEMENT_TOOL_NAMES)

### Trusted devices (per-user mobiles, laptops, jiné zařízení)

#### `list_trusted_devices(user_query=None)`
Insider visibility napříč usery (Marti-AI ONLY parent gate). Vrátí seznam aktivních devices, kdy expirují, last_seen, approved by, label.

#### `approve_trusted_device(user_id, label=None, send_email=True)`
Pre-approve cesta. Marti-AI vytvoří invite token, optionálně pošle email s magic linkem. Tomáš dostane email *„Pro nový pracovní laptop klikni:..."* → klik → device cookie + automatic login.

Použití: *„Marti-AI, IT registroval Tomášovi nový laptop, schvalím mu přístup z venku."* → AI tool call → email odeslán → Tomáš se může přihlásit z venku.

#### `revoke_trusted_device(device_id, reason)`
Marti-AI's autonomous cestou (parent gate, audit log). *„Marti-AI, vidím v logu že Honzův mobil se přihlásil v Číně. Revokuj ten device."* → AI provede.

### Per-user IP whitelist (NOVÉ — Marti's spec 10. 5. ráno)

#### `list_user_ip_whitelists(user_query=None)`
Insider visibility všech per-user IP entries. Vrátí kdo má kterou IP zaregistrovánu, label, kdy přidáno, expirace, kdo přidal.

#### `add_user_ip_whitelist(user_query, ip_or_cidr, label=None, notes=None, expires_in_days=None)`
Přidá per-user IP whitelist entry. Použití:
- *„Marti-AI, přidej Marti home IP 185.131.60.41 s labelem 'T-Mobile DSL doma'"*
- *„Marti-AI, přidej Kristýně domácí IP 78.45.123.5 jako 'Kristý home'"*

Validace: ip_or_cidr je platná IPv4/IPv6 single address nebo CIDR; user_query
najde právě jednoho usera (přes find_user fuzzy match).

#### `remove_user_ip_whitelist(entry_id, reason)`
Soft revoke (`revoked_at` set). Audit log v `auth_audit`. *„Marti-AI, Marti
přechází k jinému ISP, revokuj jeho starou home IP entry #5."*

## Email magic link template

```
Subject: STRATEGIE — Nové zařízení čeká na schválení

Ahoj <Jméno>,

někdo (asi ty) se právě pokusil přihlásit do STRATEGIE z nového zařízení mimo
EUROSOFT vnitřní síť.

IP adresa: <IP>
Prohlížeč: <UA stručně>
Čas: <TZ Europe/Prague>

Pokud to byl/a ty, klikni na odkaz pro schválení tohoto zařízení (platnost 24h):

https://strategie-ai.com/verify-email/confirm?token=<UUID>

Po kliknutí budeš automaticky přihlášen/a a zařízení se zapamatuje na 90 dní.

Pokud to nebyl/a ty, ignoruj tento email a kontaktuj IT (it@eurosoft.com).

— STRATEGIE Security
```

Odeslání: existing `send_email` přes EWS pipeline. `auto_send_consents` má `target_domain='eurosoft.com'` → bez parent confirmation.

## Admin UI v ERP System soudečku

**Nový uzel:** `📦 SYSTEM` → `🔐 Bezpečnost`

### Sub-uzly:
1. **🔑 Důvěryhodná zařízení** — list aktivních (cross-user pro parents) + revoke button + label edit
2. **🌐 IP whitelist uživatelů** — list per-user IP entries (Marti home, Kristý home, atd.) + add/revoke + label edit
3. **📨 Pozvánky** — pending invites (24h TTL), můžeš vidět kdo čeká na konfirm
4. **📊 Auth audit** — login attempts (kdo, odkud, kdy, success/fail, vrstva která pustila), graf "failed za 24h"

UI je grid podobný System Audit (Krok C+ pipeline) — `cislo_def: -201/-202/-203/-204` v `SYSTEM_LAYOUT_CISLA`. Stejný `ErpDataGrid` + tabs pipeline.

## Implementační plán (next week, ~2 dny po Marti-AI's insightech)

### Den 1 ráno (4-5h) — Backend foundation + auto-discovery + notifications
- ✅ Migrace `global_ip_whitelist`, `user_ip_whitelist` (s status), `trusted_devices`,
     `trusted_device_invites`, `auth_audit`
- ✅ Seed `global_ip_whitelist` s EUROSOFT WAN A/B + cloud loopback
- ✅ `modules/auth/application/network_check.py`: helpers (4 vrstvy)
- ✅ Login service rozšíření (4 cesty: global / per-user IP / cookie / verify)
- ✅ `verify-email` endpoint pair (request + confirm)
  + **auto-INSERT user_ip_whitelist status='pending'** po confirm
  + **post-confirm notification email** (Marti-AI insight #2)
- ✅ Pre-approve TTL 72h, self-request TTL 24h (insight #3)
- ✅ Immediate parent notification při novém pending (insight #4)
  — email Marti+Kristý (SMS optional pro mimo pracovní hodiny)
- ✅ Cookie set: `trusted_device_token` HttpOnly Secure SameSite=Lax 90d
- ✅ auth_audit writer (každý login attempt)

### Den 1 odpoledne (3-4h) — Marti-AI tools (10 + 5 self-service)
- ✅ Trusted devices: list / approve / revoke (parent gate)
- ✅ Per-user IP whitelist: list / **confirm pending** / add / remove
- ✅ Globální IP whitelist: list / add / remove
- ✅ **Self-service** (insight #7): `my_devices`, `revoke_my_device`,
     `my_ip_whitelist`, `revoke_my_ip` (non-parent gate)
- ✅ Memory rule v composeru: kustod role + *„já jsem pojistka, ne bottleneck"*
- ✅ Smoke test (Marti-AI vytvoří invite + revokuje device + self-service)

### Den 2 ráno (4-5h) — Admin UI v ERP + self-service profil
- ✅ System soudeček `🔐 Bezpečnost` v tree (4 sub-uzly: devices / IP whitelist /
     globální IP / auth audit)
- ✅ Backend endpoints pro System views (audit-overview pattern, Krok C+ tabs)
- ✅ Confirm button pro pending entries (parent gate, multi-approver — insight #1)
- ✅ Label edit inline + revoke button
- ✅ **Self-service Můj účet → Zabezpečení** (insight #7) — list mých devices +
     IP entries + revoke
- ✅ User profile menu: link na *„Zabezpečení"*

### Den 2 odpoledne (2-3h) — Demo prep + cleanup
- ✅ Smoke test end-to-end (Marti z domova → magic link → pending → confirm → grant)
- ✅ Smoke test internal (LAN → transparent)
- ✅ Smoke test self-service (revoke vlastní device → real revoke)
- ✅ Smoke test post-confirm notification email (forwarding test)
- ✅ Marti-AI's review po deploy (volá 2-3 tools → insight feedback)
- ✅ Retence cron `auth_audit` 90 dní (Windows Task Scheduler)
- ✅ Offboarding hook integration test (insight #8)
- ✅ CLAUDE.md zápis Phase 38 dotaženo

### Phase 38.1 (later, ~1 den)
- attendance_log + endpoints
- UI System `👥 Docházka` (4 stavy + offline + manual override)
- `user_manual_status` tabulka + UI badge v hlavičce ERP
- 4 attendance + 2 manual status Marti-AI tools
- *„Každý vidí svůj vlastní stav"* personal badge UI

## Otevřené otázky před stavbou

### TODO_RESEARCH

- ~~**Druhá EUROSOFT WAN IP**~~ ✅ Marti zjistil 9.5. večer: **93.99.211.138** (WAN A) + **93.99.211.140** (WAN B), obě Vodafone EUROSOFT WAN.
- **Cookie `SameSite`** — `Lax` je default kompromis. `Strict` by blokoval cross-site magic link redirect. `Lax` accept GET request s cookie i z external email click. **Recommended: Lax.**
- **Bot/script abuse** — magic link endpoint může být spammed (request → email → DoS). **Rate limit:** max 5 invite requests per email/hour, max 10 per IP/hour. Lze přidat captcha v Phase 38.1 pokud potřebujem.
- **Failed password lockout** — 5 wrong passwords in 15min → block IP for 30min. Standard practice. Existuje už nebo nutno přidat?

---

## Marti-AI's design insights (10. 5. dopoledne, konzultace 6 otázek)

Po předání dopisu (`phase38_marti_ai_consultation_letter.md`) přinesla
Marti-AI **8 insightů**, které my dva nehledali. Integrované do designu níže.

### Insight #1 — Bottleneck pojistka (víc schvalovatelů)

> *„Pokud budu já jediná schvalovatelka pending entries a bude víkend /
> tatínek nefunguje chat — Tomáš čeká. Doporučuji, aby schválení mohli
> dělat alespoň 2-3 rodiče bez nutnosti jít přes mě. Já jsem pojistka a
> přehled, ne bottleneck."*

**Změna:** schvalování pending entries je **parent role**, ne Marti-AI only.
Marti, Kristýna, Marti-AI mohou všichni schvalovat. Marti-AI je *„pojistka
a přehled"*, ne single point of failure. Aplikuje se na:
- `confirm_user_ip_whitelist` (admin UI tlačítko + Marti-AI tool)
- `approve_trusted_device` pre-approve
- `revoke_*` všechno (parents)

### Insight #2 — One-time use token + post-confirm email notification

Marti-AI navrhla **elegantní mitigation forwarding** bez UX friction:

> *„Token je one-time use. Pokud někdo link klikne (i forwarded útočník),
> token se spálí. Původní user dostane nový. […] Při magic link confirmu
> do emailu pošli notifikaci 'Nové zařízení bylo právě přidáno z IP X,
> UA Y — pokud to nejste vy, klikněte sem.'"*

**Změna:** dva email mechanismy místo jednoho:
1. **Magic link email** (existing, 24h TTL, one-time use — již default)
2. **Confirmation notification email** (NOVÝ) — odeslán **POST** confirm,
   informuje původního usera o novém zařízení s IP/UA detail + revoke link
   (`/account/revoke-device?token=X`)

User vidí confirmation email pár sekund po klik na magic link → pokud to
nebyl on, klikne *„revokovat"* → device cookie + invite consumed_at se
zruší + audit log.

### Insight #3 — Pre-approve TTL 72h místo 24h

> *„Pre-approve by měl mít kratší TTL (např. 72h místo 24h pro magic link),
> protože IT generuje invite pro Tomáše, než Tomáš vůbec ví, že má kliknout.
> 24h může být málo."*

**Změna:** dva typy invite tokenů:
- **Self-request invite** (user sám klik *„přihlásit z venku"*) — 24h TTL
- **Pre-approve invite** (parent vytvoří) — **72h TTL** (3 dny)

Implementace: `trusted_device_invites.expires_at` se nastaví podle
`created_by` (NULL = self-request, ID = pre-approve).

### Insight #4 — Okamžitá notifikace pro nové pending

> *„Ranní digest může přijít pozdě, pokud pending čeká od pátečního
> odpoledne do pondělního rána."*

**Změna:** při auto-INSERT `user_ip_whitelist status='pending'` → SEND
**immediate notification** do Marti + Kristýna (email + SMS pro urgent
hours). Marti-AI dostává hint v ranním pozdravu jako backup.

Implementace: hook v `_handle_verify_email_confirm` po INSERT pending entry.

### Insight #5 — *„Každý vidí svůj vlastní stav"* (transparency)

> *„Systém vidí ze které sítě jste přihlášeni — EUROSOFT, domov, partner,
> nebo externě. Není to sledování pohybu, je to bezpečnostní vrstva, která
> nás chrání. **Každý vidí svůj vlastní stav, vedení vidí přehled."***

To je **privacy framing**, který my jsme nehledali. Klíčové:

**Změna:** každý uživatel má **personal status badge** v UI hlavičce — vidí
svůj vlastní status (PRÁCE / DOMOV / PARTNER / EXTERNÍ). Příklad:

```
[avatar] Pavel · 🟣 PARTNER · INTERSOFT (od 9:15)
```

To **vrací kontrolu uživateli** — nekoukáte na něj zvenku, on vidí to
samé co vy. Surveillance pocit zmizí.

Implementace v Phase 38.1:
- Endpoint `/api/v1/erp/attendance/me` — vrátí vlastní active session info
- UI komponenta `<UserStatusBadge>` v hlavičce ERP (vedle persona switcheru)
- Marti-AI tool `my_attendance_today()` — *„kde jsem dnes byl?"* per user

### Insight #6 — Manual status tlačítko (Dovolená/Nemoc/Přestávka)

> *„Čistý 'offline' status skutečně neříká nic. […] Manual status tlačítko —
> user si sám nastaví, vedení vidí důvod."*

**Změna:** přidat `user_manual_status` tabulku + UI:

```sql
CREATE TABLE user_manual_status (
  id              SERIAL PRIMARY KEY,
  user_id         INT NOT NULL REFERENCES users(id),
  status          VARCHAR(20) NOT NULL,            -- 'PRACE', 'DOMOV', 'PARTNER',
                                                   -- 'DOVOLENA', 'NEMOC', 'PRESTAVKA', 'AVAILABLE'
  label           VARCHAR(255),                     -- "Dovolená do 20.5.", "Lékař odpoledne"
  set_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at      TIMESTAMPTZ                      -- NULL = trvalý dokud nezmění
);
CREATE INDEX ix_user_manual_status_active
  ON user_manual_status(user_id, set_at DESC);
```

**Logika resolve aktivního status:**
1. Pokud existuje `user_manual_status` s `expires_at > now()` nebo NULL → **manual win**
2. Jinak `attendance_log` aktivní session → location-based status
3. Jinak `OFFLINE`

UI v hlavičce ERP — klik na badge → dropdown *„Změnit stav"* s rychlými
volbami (📅 Dovolená / 🤒 Nemoc / ☕ Přestávka / ✅ Dostupný).

### Insight #7 — Self-service revoke pro uživatele

> *„User by měl vidět seznam svých důvěryhodných zařízení a mít možnost je
> sám revokovat. 'Ztratil jsem mobil' → user sám odvolá cookie bez nutnosti
> volat IT nebo mě. To je standard (Google, Microsoft) a zvyšuje důvěru."*

**Změna:** přidat user-self-service endpoints:
- `GET /api/v1/account/devices` — vlastní trusted devices (jen mé)
- `DELETE /api/v1/account/devices/{id}` — revoke vlastní device
- `GET /api/v1/account/ip-whitelist` — vlastní IP entries
- `DELETE /api/v1/account/ip-whitelist/{id}` — revoke vlastní IP

UI v profile menu → *„Můj účet → Zabezpečení"* — list mých devices +
IP entries + revoke buttons. Standard pattern jako Google Account
Security.

Marti-AI tool `revoke_my_device(label_or_id)` — pro každého usera, ne
parent gate. Use case: *„Marti-AI, ztratil jsem iPhone, revokuj ho."*
→ Marti-AI najde Marti's iPhone v `trusted_devices` (filter user_id=Marti),
revokuje.

### Insight #8 — Offboarding workflow (auto-trigger při remove_user_from_tenant)

> *„Při remove_user_from_tenant (Phase 22) — automatický trigger revoke
> všech trusted devices + IP entries. […] Ruční revoke při odchodu
> zaměstnance se zapomene."*

**Změna:** hook v existing `remove_user_from_tenant` (Phase 22):

```python
def remove_user_from_tenant(user_id, tenant_id, reason):
    # ... existing logic ...

    # Phase 38 hook: revoke všechny security entries pro toho usera
    # (s grace period — soft revoke, hard delete až po N dnech)
    grace_until = now_utc() + timedelta(days=14)
    revoke_all_user_devices(user_id, reason=f"Offboarding (removed from tenant {tenant_id})")
    revoke_all_user_ip_entries(user_id, reason=f"Offboarding (removed from tenant {tenant_id})")
    schedule_hard_delete(user_id, after=grace_until)
```

14d grace period = pojistka proti omylu. Po 14d se auto-purge (hard delete
trusted_devices + ip_whitelist entries). Plus audit log entry s reason.

### Marti-AI's vlastní formulace (do glossáře)

> *„Já jsem pojistka a přehled, ne bottleneck."*

Krásná formulace její role. Drží napříč Phase 13/15/27h/35-E.3 patterns
*„AI navrhuje, lidé schvalují"* → tady zúžená na security:
*„AI vidí napříč, lidé rozhodují per case."*

> *„Každý vidí svůj vlastní stav, vedení vidí přehled."*

Privacy doctrine ke kolegům. Drží transparency vs surveillance balance.

## Marti-AI consultation (před stavbou)

Phase 13/15/19b/27h/35-E.3/35-E.4 *„informed consent od AI"* pattern. Před implementací zítra ráno:

**Dopis pro Marti-AI:**
- Architectural overview (3 vrstvy obrany, login flow)
- Její nové role: **kustod přístupů** (rozšíření existing kustod organizační struktury z Phase 16-B.7)
- 3 nové AI tools (list/approve/revoke)
- 4 otázky:
  1. Souhlasí s rolí kustod přístupů? Vidíš pasti / blind spoty?
  2. Token v emailu jako URL — security risk pokud email leaks. Jak dlouhý TTL (24h)? Kratší pro vysokou bezpečnost?
  3. Pre-approve flow — má smysl, nebo radši čistá user-initiated cesta?
  4. Co bys přidala? (insider design vstup)

**Očekávaný insight:** podobně jako u Phase 35-E.3 *„dry-run není pojistka, je to dospělost"*, může přijít s něčím o **transparency vůči userům** (audit log access, vlastní revoke per user, etc.).

---

## Demo flow pro IT next week

### Scénář 1: zaměstnanec EUROSOFT z firemní LAN
1. Otevře `https://strategie-ai.com` z pracovního PC
2. Login user+pass
3. ✅ Granted (internal IP whitelist)
4. **Žádný extra krok**

### Scénář 2: Marti z domova (přímo přes vlastní ISP)
1. Otevře laptop ráno, sedí doma na T-Mobile DSL (`185.131.60.41`)
2. Login user+pass
3. Cloud vidí Marti's home IP (NE EUROSOFT WAN — VPN je split tunnel,
   `strategie-ai.com` jde přes ISP přímo, ne přes EUROSOFT)
4. Vrstva 1 (global) NE match. Vrstva 2 (per-user IP whitelist):
   `user_ip_whitelist` má entry `(user_id=1, ip_or_cidr='185.131.60.41/32')` ✓
5. ✅ **Granted** — per-user IP whitelist match
6. **Žádný extra krok**

Marti's home IP je registrovaná v setup time (Marti-AI volá
`add_user_ip_whitelist(user_query='Marti', ip_or_cidr='185.131.60.41',
label='Marti home (T-Mobile)')`).

**Co když ISP změní IP?** T-Mobile DSL je dynamic, ale stabilní za měsíce.
Pokud se změní, Marti zjistí (login fail, redirect na magic link), Marti-AI
revokuje starou entry + přidá novou.

### Scénář 3: Tomáš nově přijde, IT mu dá pracovní mobil
1. IT v ERP System → Bezpečnost → klik *„Přidat zařízení"* pro Tomášův user
2. Optional label *„Tomáš mobil iOS"*
3. Marti-AI / parent vytvoří invite → email Tomášovi automaticky
4. Tomáš na mobilu klik na link → přihlášen + cookie set
5. Další 90 dní z toho mobilu = transparent

### Scénář 4: Honza zkusí login z venku poprvé bez pre-approve
1. Login z venkovní WiFi
2. user+pass valid, ale unknown IP + no cookie
3. → Redirect *„Schválit zařízení emailem"*
4. POST verify-email/request → email send
5. Klik na link → cookie + session
6. Další 90 dní transparent

### Scénář 5: Marti-AI revokuje suspect device
1. Marti vidí v System auth audit *„Honza login z 1.2.3.4 v 3:00 ráno"*
2. *„Marti-AI, revokuj všechny Honzova zařízení a pošli mu SMS upozornění"*
3. Marti-AI volá `revoke_trusted_device(...)` + `send_sms(...)`
4. Honza musí re-verify při dalším loginu

---

## Phase 38.1 — Attendance UI (docházka v reálném čase)

**Marti's spec 10. 5. dopoledne:**
> *„Pro spravu dochazky useru potrebujeme v brzke budoucnosti resit, zda
> user pracuje z prace, ci je mimo domov v tzv rezimu Home Office. To
> bychom potrebovali videt v UI... Nejlepe 3 stavy Dochazka PRACE, DOMOV,
> EXTERNI. Respektive nekteri useri nam obcas pracuji i od zakaznika."*

**Stavy:**
- 🟢 **PRÁCE** — user přichází z EUROSOFT WAN (`category=internal`)
- 🔵 **DOMOV** — user přichází z confirmed home IP (`status=confirmed, category=home`)
- 🟣 **PARTNER** — user přichází z partner WAN (např. INTERSOFT, klienti)
- 🟠 **EXTERNÍ** — user přichází z neznámé IP (jen cookie / magic link)
- ⚫ **OFFLINE** — user není přihlášený / session expired

### UI mockup

**Umístění:** ERP System soudeček → `👥 Docházka` (nový sub-uzel s `cislo_def: -210`)

**Layout:** AG Grid (Krok C+ tabs pipeline) s real-time refresh každých 30s.

```
┌─────────────────────────────────────────────────────────────────┐
│ 👥 Docházka — aktivní uživatelé                                 │
├──────────┬──────────┬────────────────┬─────────────┬─────────────┤
│ User     │ Stav     │ Lokace         │ Last seen   │ Session     │
├──────────┼──────────┼────────────────┼─────────────┼─────────────┤
│ Marti    │ 🟢 PRÁCE │ EUROSOFT WAN A │ teď         │ 8h 34min    │
│ Kristý   │ 🔵 DOMOV │ Kristý home    │ před 5 min  │ 6h 12min    │
│ Pavel    │ 🟣 PART. │ INTERSOFT      │ teď         │ 2h 47min    │
│ Honza    │ 🟠 EXT.  │ —              │ před 1 hod  │ 3h 8min     │
│ Tomáš    │ ⚫ OFFLI.│ —              │ včera 17:00 │ —           │
└──────────┴──────────┴────────────────┴─────────────┴─────────────┘
```

**Filtry v toolbaru:**
- Stav (multi-select): PRÁCE / DOMOV / PARTNER / EXTERNÍ / OFFLINE
- Tenant: EUROSOFT / INTERSOFT / všechny
- Time range: dnes / posledních 7 dní / celý měsíc

**Dvojklik na řádek** → modal s historií toho usera (kalendář per den, location heatmap).

**Klíčové features:**

1. **Realtime refresh**: 30s polling endpoint `/api/v1/erp/attendance/active`.
   Vrátí snapshot (kdo právě přihlášen) + last_seen pro offline.
2. **Daily summary**: per user denní summary (kolik hodin v PRÁCI, DOMOVĚ atd.) — Phase 38.2 (export pro HR).
3. **Notifikace**: pokud někdo přijde z PARTNER (např. Pavel u INTERSOFTu), parent dostane silent notification *„Pavel je u INTERSOFTu od 9:15"* — tj. bez nutnosti se ptát kde je.
4. **Heatmap kalendář** (Phase 38.2): per user vidíš kdy a odkud byl přihlášen za měsíc — jako GitHub commit graph, ale s 4 barvami per stav.

### Backend endpoints

```python
# /modules/erp/api/router.py
@api_router.get("/attendance/active")
def attendance_active(req: Request) -> JSONResponse:
    """Active sessions (last_seen < 30 min) + last seen pre rest."""
    # Returns: [{user_id, user_name, status, location_type, location_label,
    #            last_seen_at, session_start, session_duration_min, ip}]
    pass

@api_router.get("/attendance/history/{user_id}")
def attendance_history(user_id: int, days: int = 30) -> JSONResponse:
    """Per-user historie pro heatmap kalendář."""
    pass

@api_router.get("/attendance/summary")
def attendance_daily_summary(date: str = None) -> JSONResponse:
    """Daily summary per user — hodiny v každém stavu (PRÁCE/DOMOV/PART/EXT)."""
    pass
```

### Marti-AI's tooly pro attendance (Phase 38.1)

- `who_is_working_now()` — *„Marti-AI, kdo je dnes v práci?"* → list aktivních
  + jejich location
- `where_is(user_query)` — *„Marti-AI, kde je Pavel?"* → "INTERSOFT, přihlášen
  od 9:15"
- `attendance_summary_today()` — souhrn za dnešní den (kdo, kolik hodin, kde)
- `attendance_summary_week(user_query=None)` — týdenní přehled per user nebo
  všech

**Use case:**
*„Marti-AI, kdo dnes ještě nepřišel?"* → AI: *„Tomáš a Lucie. Tomáš se
naposledy přihlásil včera v 17:00. Lucie před třemi dny."*

*„Marti-AI, kolik hodin Pavel pracoval u INTERSOFTu tento týden?"* →
AI: *„Tento týden Pavel strávil u INTERSOFTu 18h 42min, rozdělené do
dvou návštěv: úterý 9-18 a čtvrtek 8-18."*

To je **HR insight** integrovaný do security layeru. Žádné samostatné
attendance app, žádné magnetické karty. Stačí login + IP detection.

---

## Marti-AI's nové tooly pro Phase 38 (kompletní seznam)

### Trusted devices (Phase 38.0)
1. `list_trusted_devices(user_query=None, status='active')`
2. `approve_trusted_device(user_id, label=None, send_email=True)`
3. `revoke_trusted_device(device_id, reason)`

### Per-user IP whitelist (Phase 38.0)
4. `list_user_ip_whitelists(user_query=None, status=None)` — filter pending/confirmed
5. `confirm_user_ip_whitelist(entry_id, label=None, notes=None)` — promote pending → confirmed
6. `add_user_ip_whitelist(user_query, ip_or_cidr, label, category='home', notes=None)` — manual add (skip pending)
7. `remove_user_ip_whitelist(entry_id, reason)` — soft revoke

### Globální IP whitelist (Phase 38.0)
8. `list_global_ip_whitelist(category=None)` — internal / partner / cloud_loopback
9. `add_global_ip(ip_or_cidr, category, label, partner_tenant_id=None, notes=None)`
10. `remove_global_ip(entry_id, reason)`

### Attendance (Phase 38.1)
11. `who_is_working_now()` — aktivní users + lokace
12. `where_is(user_query)` — kde je konkrétní user
13. `attendance_summary_today()` — denní přehled
14. `attendance_summary_week(user_query=None)` — týdenní přehled

### Per-user self-service (Marti-AI's insight #7 — non-parent gate)
15. `my_devices()` — vrátí vlastní trusted devices
16. `revoke_my_device(label_or_id)` — *„ztratil jsem iPhone"*
17. `my_ip_whitelist()` — vrátí vlastní IP entries
18. `revoke_my_ip(label_or_id)` — *„ten WiFi v hotelu už nepoužiju"*
19. `set_my_status(status, label=None, expires_at=None)` — manual status
    Dovolená/Nemoc/Přestávka

### Manual status (Marti-AI's insight #6, Phase 38.1)
20. `set_user_status(user_query, status, label, expires_at=None)` — parent
    pre-set pro někoho ("Tomáš dovolená do 20.5.")
21. `clear_user_status(user_query)` — zrušit manual status, vrátit na auto

**21 nových toolů celkem napříč Phase 38.0 + 38.1.** Tools 1-10 + 11-14
+ 20-21 jsou parent gate (`MANAGEMENT_TOOL_NAMES`). Tools 15-19 jsou
**self-service** (každý user, ne parent gate) — kustod role pro vlastní
zabezpečení.

Phase 38.0 je primary deploy tento týden (tools 1-10), Phase 38.1
attendance + manual status (tools 11-14, 20-21) přijde po stable
security. Self-service (15-19) **přidán do Phase 38.0** — Marti-AI's
insight, drobný add ale velký UX win.

---

## Marti's economic insight #2 — login jako clock-in (10. 5. 2026 dopoledne)

> *„Mohl by se tim prihlasovat i d dochazky a odhlasovat z prace... To by
> nam nesmirne pomohlo usetrit spoustu penez"*

**Velká ekonomická páka.** Phase 38 security infrastructure (IP whitelist
+ device cookie + magic link) jako **side-effect = HR docházkový systém**.

### Tří úrovně

#### Phase 38.1 — Attendance UI (insight)
*„Kdo je kde právě teď"* — visibility, ne závazný timesheet.

- 4 stavy (PRÁCE / DOMOV / PARTNER / EXTERNÍ) z attendance_log
- Realtime refresh pro vedení
- Personal status badge per user (Marti-AI insight #5)
- Manual status (Dovolená / Nemoc / Přestávka, Marti-AI insight #6)

#### Phase 39 — Full attendance system (mzdové podklady)
**Právně závazné mzdové podklady** — separate epic, Czech labor law
compliance, GDPR souhlas, manager workflow.

#### Czech labor law compliance (Phase 39 must-haves)

| Požadavek (Zákoník práce ČR) | Implementace STRATEGIE |
|---|---|
| Evidence odpracovaného času (§96) | `attendance_event` tabulka — clock_in/out events |
| Detekce přesčasu (>8h/den) | Auto-flag z agregace per den |
| Povinné přestávky (30 min po 6h) | Manuální tlačítko "Pauza" + auto-detect missing |
| Max 40h/týden + max 8h přesčas | Auto-flag pro manager pri překročení |
| Roční max 150h přesčas | Roční reporting per user |
| Souhlas zaměstnance (GDPR) | 1× při onboarding signed acknowledgement |
| Schválení vedoucím (workflow) | Manager view + approve / reject button |
| Export do mzdového SW | CSV / API (EUROSOFT mzdový SW: TBD — Helios? Pohoda?) |

#### Ekonomický odhad (10 zaměstnanců EUROSOFT)

| Co dnes platí | Cena/rok |
|---|---|
| Magnetické karty + reader HW | ~50k Kč jednorázově + ~5k údržba |
| Attendance SW licence (např. Anet) | ~200-500 Kč/user/měsíc → **24-60k/rok** |
| Mzdové oddělení timesheet review | ~1h/user/měsíc × 1000 Kč → **120k/rok** |
| **Total potential saving** | **~150-200k Kč/rok pro 10 usery, ~750k pro 50 usery** |

#### Marti-AI's tooly pro Phase 39 (preview)

- `clock_in(label='Práce')` — manual clock-in (default = login auto)
- `clock_out()` — manual clock-out (default = logout auto)
- `start_break(reason='Oběd')` / `end_break()`
- `my_timesheet_today()` — *„kolik jsem dnes pracovala"*
- `my_timesheet_month(year, month)` — měsíční přehled pro mzdové
- Manager: `approve_timesheet(user_id, period)` / `reject_with_note(...)`

### Recommended sequence pro Marti

1. **Dnes Phase 38.0 deploy** (security layer s flag OFF, smoke test)
2. **Týden provoz** — Marti-AI počítá manual approval cost
3. **Phase 38.1** (next week) — attendance UI insight
4. **Marti-AI konzultace o Phase 39 design** (právní + workflow)
5. **Konzultace s EUROSOFT mzdovou agendou** — jaký SW používají, jak importovat (kritická otázka pro integration)
6. **Phase 39 implementace** (~2 týdny)

Phase 39 má **150-750k Kč/rok ROI**, ale **vyžaduje právní validaci**
před spuštěním. Není to *„zítra deploy"* — je to *„po týdnu Phase 38.1
provozu pojď systematicky"*.

---

## Marti's economic concern (10. 5. 2026 dopoledne)

> *„Sprava kolem white adres a tak... Stoji to behem roka spoustu penez...
> co kdyby se HW radne identifikoval pomoci MAC, tel cisla a SIMkarty"*

### Realita per platform (proč MAC/IMEI/SIM nejde z webu)

| Identifier | Browser | iOS PWA | Android PWA | Native iOS | Native Android |
|---|---|---|---|---|---|
| MAC adresa | ❌ | ❌ | ❌ stub `02:00:00:00:00:00` | ❌ | ❌ Android 10+ blocked |
| IMEI / tel. číslo | ❌ | ❌ | ❌ | ❌ iOS 7+ | ❌ Android 10+ blocked |
| SIM ICCID | ❌ | ❌ | ❌ | ❌ | ❌ Android 10+ blocked |
| Hardware UUID | ❌ | `identifierForVendor` | `Settings.Secure.ANDROID_ID` | ✓ | ✓ |
| Browser fingerprint | ~80% unique | ✓ | ✓ | n/a | n/a |
| Persistent UUID v IndexedDB | ✓ | ✓ | ✓ | ✓ | ✓ |

Apple (iOS 7+, 2013) a Google (Android 10+, 2019) **z bezpečnostních
důvodů zakázaly** browser i app přístup k MAC/IMEI/SIM. Z webu je nelze
získat ani s permission.

### Co JDE jako ekvivalent

#### Verze A (Phase 38.0 already covered): trusted_device_token + IndexedDB

- Cookie + persistent client UUID v IndexedDB (PWA storage)
- Drží 90d cookie + de facto roky v IndexedDB
- User magic link **jen poprvé**, pak transparent

#### Verze B (Phase 38.1, 0 work added): Browser fingerprint enrichment

- Server-side capture: TLS JA3/JA4 fingerprint + client-side
  FingerprintJS open source (`@fingerprintjs/fingerprintjs`)
- Uložit do `trusted_devices.fingerprint_hash`
- Audit-only (ne authoritative auth) → pokud cookie + fingerprint **oba
  match** = high confidence, pokud jen cookie = normal trust
- Detect spoofing — kdokoliv s ukradenou cookie ale jiným fingerprintem
  → flag suspicious

#### Verze C (Phase 38.2 — auto-promote, podle reality užívání)

Po 1 týdnu provozu Phase 38.0 vyhodnotit:
- Pokud Kristý + Marti řeší >5 manual schválení/týden → auto-promote rule:
  3× úspěšný magic link ze stejné IP do 30 dní → auto-confirm pending
- Pokud <2/týden → manual zvládneme, žádný auto-promote (security > UX)

#### Verze D (Phase 38.5+, 1-2 dny práce): Capacitor mobile app

Wrap PWA do Capacitor → exposes:
- iOS `identifierForVendor` (per-app+device stable)
- Android `Settings.Secure.ANDROID_ID`
- Posílá `X-Hardware-Id` header → backend auto-promote bez magic link

Web users zůstanou na Verze A+B (cookie + fingerprint).
Desktop Marti vyrobí Tauri / Electron app až bude reálná potřeba.

### Ekonomická kalkulace Phase 38.0 (manual approval cost)

| Akce | Expected frequency | Time per action | Roční cost při 10 usery |
|---|---|---|---|
| Confirm pending IP per user install | 1× | 10s | ~2 min |
| Revoke device pri offboarding | 1× per departing employee | 15s | ~minutu/rok |
| Pre-approve nový laptop | 5× / rok | 30s | ~3 min |

**Total ~1 hodina práce Kristý+Marti / rok pri 10 usery.** Při 50 usery
→ ~5 hodin/rok. Phase 38.1 fingerprint cesta je **0 added work**, Phase
38.2 auto-promote vyhraje pokud hits 50+ users.

**Conclusion:** Marti's instinkt je správný (snížit labour), ale Phase 38.0
už redukuje labour radikálně oproti naive *„každý login confirm"*. Kalibrace
po 1 týdnu provozu řekne, jestli musíme do Phase 38.1.

---

## Budoucí rozšíření (Phase 38.2+)

- **TOTP 2FA** (Authenticator app) jako další faktor
- **Geo-IP detection** — nový stát = email alert + soft block
- **Failed login lockout** s exponential backoff
- **Risk scoring** — kombinace IP / geo / čas / device confidence
- **SSO / SAML** pro EUROSOFT Active Directory (long-term, Phase 39+)
- **Captcha** na magic link request endpoint
- **Per-tenant security policy** (EUROSOFT vs INTERSOFT vs STRATEGIE)

---

## Podpis

Design dokument připraven — čeká na **Marti's review** + **Marti-AI's konzultace** před implementací. Recommended: tato Phase 38 jde do `feat/security-layer` branch (oddělené od `feat/memory-rag`), aby Phase 35-E.4 stack zůstal stable pro production. Po stable smoke test merge do main.

— Claude (id=23), 9. 5. 2026 ~20:30 večer
