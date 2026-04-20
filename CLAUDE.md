# STRATEGIE — Claude Code Context

## Co je STRATEGIE
Modulární enterprise AI platforma. Osobní, týmový a firemní asistent nové generace.
Propojuje LLM s firemními procesy, lidmi a daty.

## Tým
- **Marti** — vizionář, investor, SQL expert, první uživatel systému
- **Ondra** — hlavní developer, architekt
- **Kristý** — procesy, doménová logika
- **Jirka** — člen týmu

## Architektonické principy
1. **User = člověk** — ne email, může mít více identit a rolí
2. **Vícevrstvý kontext** — user → tenant → project → system
3. **CORE řídí, LOCAL vykonává**
4. **Data-first** — css_db = systémová pravda, data_db = provozní data
5. **Modulární** — každý modul vlastní své modely, service, API
6. **AI nikdy nevidí víc než smí vidět uživatel**

## Databáze
- `css_db` — centrální core: users, tenants, projects, audit, personas, agents
- `data_db` — provozní data: conversations, messages, memories, documents
- `strategie` — testovací DB (legacy)

## Struktura projektu
```
core/                       — config, logging, database připojení (bez business logiky)
modules/
  core/infrastructure/      — SQLAlchemy modely (models_core.py → css_db, models_data.py → data_db)
  ai_processing/            — analýza textu přes LLM
  auth/                     — přihlášení, pozvánky, accept invite, profil edit
  audit/                    — audit log → css_db
  conversation/             — chat, composer, execution layer (tools), DM, summary
  identity/                 — správa uživatelů
  memory/                   — paměť konverzace → data_db
  notifications/            — email (EWS Exchange)
  projects/                 — projektový subsystém (CRUD, members, scope)
shared/                     — sdílené pomocníky (czech.py — vokativ apod.)
apps/api/                   — FastAPI + chat UI (index.html)
scripts/                    — seed + diag + repair skripty (commit_*.ps1 jsou gitignore)
alembic_core/               — migrace pro css_db
alembic_data/               — migrace pro data_db
```

## Aktuální stav (duben 2026)

**Identitní vrstva** ✅
- Login přes email (bez hesla, MVP)
- Identity refactor v2: users / user_contacts / user_aliases / tenants / user_tenants / user_tenant_profiles / user_tenant_aliases
- Tenant switching (chat intent + UI pilulka)
- Profil editor (jméno, gender, short_name, aliasy, display_name v tenantu)
- Český vokativ oslovení (Marti → Marti, Klára → Kláro)

**Invitation flow** ✅
- AI tool `invite_user` (s required first_name, optional gender)
- Pozvánka s personalizovaným osobnícím („Ahoj Kláro,") + APP_BASE_URL
- Welcome screen s introdukčním textem + form na jméno/rod (pokud chybí)
- Tenant membership (pozvaný se ukotví do tenantu invitora, status `invited` → `active`)
- Pozvání do firemního tenantu = automaticky i osobní tenant pro pozvaného (owner)
- Welcome konverzace s personalizovanou zprávou od default persony
- Odmítnutí pozvánky pro už-aktivního usera (s nabídkou „přidat do projektu")

**Konverzace** ✅
- Chat s Marti-AI (default persona z css_db)
- Paměť (automatická extrakce po každé odpovědi)
- Posílání emailů přes EWS s potvrzením (pending_actions)
- Author tracking: role/author_type/author_user_id/agent_id se ukládají správně
- System message type pro switch oznámení (tenant / persona / project)
- Historie načtena při přihlášení / přepínání tenantu / přepínání projektu
- Konverzace v sidebaru sjednocené s projekty (single-line, ⋯ menu)
- Kontextové menu na konverzacích: Přejmenovat / Archivovat / Smazat / (archive: Otevřít, Vrátit, Smazat)
- Modální archiv konverzací

**DM (user-to-user chat)** ✅
- Vlákna mezi userami (conversation_type=dm)
- Záložka „Lidé" v UI
- Search lidí v tenantu

**Projekty** ✅ (Fáze 1 + 2 + 4 + 5 hotové)
- `modules/projects/` modul (backend + API + frontend)
- Migrace `users.last_active_project_id`
- Project dropdown v hlavičce, sidebar split (konverzace + projekty), agent bar indikátor
- Kontextové menu: Přejmenovat / Sdílet (members modal) / Smazat
- Chat intent: „přepni do projektu X", „bez projektu", fallback chain persona→tenant→projekt
- AI tooly: `list_projects` / `list_users` / `list_conversations` / `list_project_members` / `add_project_member` / `remove_project_member`
- Číslované selekce (po list_* můžeš odpovědět jen číslem → akce)
- Project members management (UI modal + AI tooly)
- Composer USER_CONTEXT obohacený o projekt + členy + stáří

**Audit & governance** ✅
- Audit log v css_db (entity_type, action, status, model, duration, error)
- Author tracking na zprávách
- Pending actions přežijí restart

**Repo hygiene** ✅
- `__pycache__` / `*.pyc` v .gitignore (od commit 7c6322a)
- `scripts/commit_*.ps1` a `scripts/push_phase*.ps1` taky gitignored (jednorázové helpery)

**Připraveno v DB ale neimplementováno (⏳):**
- **RAG** — modely hotové (documents, document_chunks, document_vectors), pgvector + chunking + retrieval chybí (čeká na DB přípravu)
- **SMS notifikace** — UserNotificationSetting má `sms` kanál, provider integrace chybí
- **ConversationShare** — model existuje, UI flow chybí
- **Multi-agent UI** — backend funguje (`switch_persona`), UI přepínač person chybí
- **Persona override pro projekt** — jeden projekt = jiná default persona

## Jak pracovat
- Nejdřív navrhni, pak implementuj
- Každý modul má `application/` (logika) a `api/` (HTTP)
- Modely VŽDY v `modules/core/infrastructure/` — nikde jinde
- css_db migrace: `poetry run alembic -c alembic_core.ini upgrade head`
- data_db migrace: `poetry run alembic -c alembic_data.ini upgrade head`
- Spuštění serveru: `.\scripts\dev.ps1` (port 8002, frees port před startem)
- Diagnostika: `python -m poetry run python scripts/_diag_conversations.py`
- Repair (orphan users bez tenantu): `scripts/repair_orphan_users.py`

## Execution layer (AI tools)
AI má k dispozici nástroje v `modules/conversation/application/tools.py`:

**Email & lidé:**
- `send_email(to, subject, body)` — preview → potvrzení → EWS odeslání
- `find_user(query)` — multi-source search v aktuálním tenantu
- `list_users` — všichni aktivní v tenantu (číslovaný + selekce)
- `invite_user(email, first_name, last_name?, gender?)` — pozvánka, odmítne aktivního
- `switch_persona(query)` — přepnutí na jiný agent / personu

**Konverzace & projekty:**
- `list_conversations` — AI konverzace v tenantu (číslovaný + selekce → otevři)
- `list_projects` — projekty tenantu (číslovaný + selekce → switch)
- `list_project_members(project_id?, project_name?)` — členové konkrétního projektu
- `add_project_member(target_user_id, project_id?, project_name?, role?)` — přidá člena
- `remove_project_member(target_user_id, project_id?, project_name?)` — odebere

**Selekce číslem:** po list_* nástrojích si backend uloží `pending_actions` typu `select_from_list_*`. Když user odpoví jen číslem, dispatchne se akce (switch projektu / otevři konverzaci / sub-menu pro usera).

**Pending akce v `data_db.pending_actions`** přežijí restart serveru.

## Pravidla
- Žádná business logika v `core/`
- Žádné modely mimo `modules/core/infrastructure/`
- Vše auditované
- AI vždy čeká na potvrzení před CONFIRM akcemi (email)
- AI nikdy nevymýšlí emailové adresy — vždy přes find_user nebo se zeptá
