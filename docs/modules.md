# STRATEGIE — Přehled modulů

## Implementované moduly

### `modules/ai_processing`
Analýza textu přes LLM. Vstup: text. Výstup: summary, action_items, persons, recommendations.
Endpoint: `POST /api/v1/analyse`

### `modules/auth`
Přihlášení, pozvánky, onboarding.
- Login přes email (MVP bez hesla)
- Pozvánky s tokenem (48h platnost)
- Přijetí pozvánky přes link
Endpointy: `POST /api/v1/auth/login`, `POST /api/v1/auth/invite`, `GET /api/v1/auth/accept/{token}`

### `modules/audit`
Systémový audit log. Zapisuje do `css_db.audit_log`.
Loguje: analýzy textu, akce AI, systémové operace.

### `modules/conversation`
Jádro chat systému.
- **composer** — skládá prompt z vrstev (system → persona → summary → zprávy)
- **service** — orchestrace chatu + execution layer
- **tools** — nástroje pro AI (send_email, find_user)
- **repository** — přístup k css_db a data_db
Endpoint: `POST /api/v1/conversation/chat`, `GET /api/v1/conversation/last`

### `modules/identity`
Správa uživatelů a jejich identit (email, telefon).
Používá modely z `modules/core/infrastructure/models_core.py`.

### `modules/memory`
Automatická extrakce pamětí z konverzace po každé odpovědi AI.
Ruční uložení přes API.
Endpointy: `POST /api/v1/memory/`, `GET /api/v1/memory/`

### `modules/notifications`
Email přes Exchange Web Services (EWS).
- `email_service.py` — odesílání emailů přes exchangelib

### `modules/core`
SQLAlchemy modely pro obě databáze.
- `models_core.py` → css_db (users, tenants, projects, personas, agents, audit...)
- `models_data.py` → data_db (conversations, messages, memories, documents...)

---

## Plánované moduly (zatím jen v DB)

### `modules/context`
Projekty, tenant kontext, vícevrstvá izolace dat.

### `modules/knowledge`
Dokumenty, chunking, embedding, RAG vyhledávání.
Modely hotové (`documents`, `document_chunks`, `document_vectors`).
Čeká na pgvector instalaci.

### `modules/tasks`
Akční body, přiřazení uživatelům, stavy a termíny.

### `modules/communication`
Návrh emailů, notifikace, šablony.

### `modules/automation`
Workflow triggery, podmíněné akce, scheduling.

### `modules/integration`
Helios ERP, Exchange, soubory, externí API.
Primárně pro LOCAL systém.

---

## Databázové schéma

### css_db (DB_Core)
Systémová pravda — stabilní, strukturální data.

| Tabulka | Popis |
|---|---|
| users | Uživatelé (člověk, ne email) |
| user_identities | Email, telefon, OAuth |
| tenants | Organizace / firmy |
| user_tenants | Vazba user ↔ tenant + role |
| projects | Projekty v rámci tenantu |
| user_projects | Vazba user ↔ projekt + role |
| system_prompts | Globální system prompty |
| personas | Definice person (Marti-AI...) |
| agents | Digitální dvojčata a experti |
| invitations | Pozvánky s tokeny |
| onboarding_sessions | SMS ověření při onboardingu |
| user_sessions | Online stav uživatelů |
| user_notification_settings | Kanály notifikací per user |
| user_contacts | Kontakty mezi uživateli |
| contact_requests | Žádosti o kontakt |
| kill_switches | Vypínač AI na různých úrovních |
| elevated_access_log | Auditovaný přístup do cizích projektů |
| audit_log | Systémový audit všech akcí |

### data_db (DB_Data)
Provozní a obsahová data — dynamická, objemná.

| Tabulka | Popis |
|---|---|
| conversations | Konverzace uživatelů |
| messages | Zprávy v konverzacích |
| conversation_summaries | Shrnutí starší historie |
| conversation_shares | Sdílení konverzací |
| memories | Dlouhodobá paměť uživatelů |
| documents | Nahrané dokumenty |
| document_chunks | Rozdělené chunky dokumentů |
| document_vectors | Embeddingy (čeká na pgvector) |
| action_logs | Logy akcí AI (tools) |
| pending_actions | Čekající akce čekající na potvrzení |
