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
  notifications/            — email (EWS Exchange, inbound + outbound), SMS (Android gateway)
  projects/                 — projektový subsystém (CRUD, members, scope)
shared/                     — sdílené pomocníky (czech.py — vokativ apod.)
apps/api/                   — FastAPI + chat UI (index.html)
scripts/                    — seed + diag + repair skripty (commit_*.ps1 jsou gitignore)
alembic_core/               — migrace pro css_db
alembic_data/               — migrace pro data_db
```

## Aktuální stav (duben 2026)

**Identitní vrstva** ✅
- Login přes email + bcrypt heslo (viz **Auth** níže)
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
- Default persona per projekt — override globálního defaultu (Marti-AI) pro nové konverzace v projektu

**Personas & Multi-agent UI** ✅
- `modules/personas/` modul (service + avatar_service + API)
- CRUD person: list / create / edit / switch přes UI
- Avatary s fallback na iniciály, storage v `Avatary/` (nastavitelné `AVATARS_STORAGE_DIR`)
- Role isolation — persona má definovanou roli/kontext
- AI tool `switch_persona(query)` pro přepínání v chatu

**Conversation sharing** ✅
- Model `ConversationShare` + `share_service.py`
- API: `GET /shared-with-me`, `GET/POST/DELETE /{id}/shares`
- Share modal (aktuální sdílení + picker nových userů)
- Sidebar sekce „sdílené se mnou" (oranžový akcent)
- Share ikona na konverzacích + agent bar indikátor (🔗)
- Role `owner` / `shared_read` / `shared_write` (readonly viewer = disabled send)

**RAG** ✅
- `modules/rag/` — chunking + embeddings (Voyage) + extraction (markitdown) + storage
- pgvector v `data_db`, tabulky `documents` / `document_chunks` / `document_vectors`
- API pro upload + retrieval
- AI tool loop — synthesis nad relevantními chunks, tenant-aware

**Auth** ✅
- Bcrypt password authentication (konec passwordless MVP)
- Self-service password management (reset tokens, change password)
- Rate limiting loginu (`rate_limiter.py`)
- Cross-tab session sync + per-tab identity + re-login
- Secure cookies, trusted hosts, env switching (production-ready config)

**Audit & governance** ✅
- Audit log v css_db (entity_type, action, status, model, duration, error)
- Author tracking na zprávách
- Pending actions přežijí restart

**SMS notifikace** ✅ (Fáze 1 + 2)
- `modules/notifications/application/sms_service.py` — provider-agnostic interface + `queue_sms()` + normalizace E.164 + rate limiting
- `SmsProvider` abstract → aktuálně `AndroidGatewayProvider` (pull model přes telefon s capcom6/android-sms-gateway appkou); budoucí: `SmsEagleProvider`, `TwilioProvider`
- Outbox tabulka `sms_outbox` (pending → sent/failed), purpose: `user_request` | `notification` | `system`
- Gateway API `/api/v1/sms/gateway/outbox` (GET/POST) pro Android pull, auth přes `X-Gateway-Key` (constant-time compare)
- AI tool `send_sms(to, body)` — preview → potvrzení → outbox (analogie `send_email`)
- `find_user` rozšířen o `preferred_phone` pro resolve podle jména
- Audit log `send_sms` v `action_logs`
- Setup guide: `docs/sms_setup.md`
- Inbound SMS = **push model** (Android appka push webhook → `/api/v1/sms/gateway/inbox` → `sms_inbox` → auto-task)

**Email notifikace (inbound + outbound)** ✅ (PR2 + PR3 — duben 2026)
- **Inbound (pull model)**: `scripts/email_fetcher.py` (polling worker, 60s default) → `ews_fetcher.fetch_all_active_personas()` → EWS INBOX unread → `email_inbox` tabulka → označí v Exchange jako read
- **Outbound (queue)**: `email_service.queue_email()` → `email_outbox` (pending) → fetcher worker ve stejném cyklu dělá `flush_outbox_pending()` → EWS send → status sent/failed; `send_email_or_raise` zůstává pro invite/password-reset (synchronní, kritická cesta, bez worker dependency)
- **AI tool `send_email` (od PR3.1)**: po user potvrzení v chatu volá `queue_email()` (audit row) + `send_outbox_row_now()` (inline atomický send) → user dostane okamžitý feedback jako dřív, ale s auditem. Retry se provádí automaticky v dalších worker cyklech, pokud první pokus vrátil status `pending` (send error). Auth / no_user_channel chyby jsou rovnou `failed` (retry by nepomohl).
- **Dedup**: `email_inbox.message_id` UNIQUE per persona (RFC822 Message-ID) — restart fetcheru / overlap nezduplikuje
- **Per-persona channel**: `persona_channels` (channel_type='email') drží login UPN (`identifier`) + SMTP alias (`display_identifier`) + Fernet-šifrované heslo + EWS server
- **Security — login UPN je SECRET**: `identifier` se nikdy nesmí objevit v logu, v DB (`email_inbox.to_email`), v API response ani UI. Pro storage/logy se používá výhradně `display_identifier`. Fetcher personu se NULL `display_identifier` přeskočí s warningem.
- **Task workflow (opt-in)**: email přijde → jen do inboxu (žádný auto-task). User v UI klikne "Navrhni odpověď" → `POST /inbox/{id}/suggest-reply` → task `source_type='email_inbox'` → worker → AI draft v `task.result_summary` → UI polluje `/draft` → prefill textarea. Cascade na `email_inbox.processed_at` u email tasku ZAMERNE vypnutá (draft ≠ uzavření — email zavře jen explicitní user action).
- **Reply flow**: UI `POST /inbox/{id}/reply` → `queue_email()` + `mark processed` + cancel open tasks. Exchange odešle při dalším worker cyklu (do 60s).
- **Header badge**: druhý řádek hlavičky zobrazuje kombinovaný neprečtený count (email + SMS) + **⟳ Fetch now** tlačítko (manuální trigger `POST /email/fetch-all`, nemusíš čekat 60s). Polling `/api/v1/notifications/unread-counts` po 30s.
- **Email modal** (klik na badge): 3 taby Příchozí/Zpracované/Odeslané, sdílí `.sms-modal-*` CSS. Tlačítka per email: Navrhni odpověď / Odpovědět / Označit zpracované.
- **AI tool `list_email_inbox(limit, filter_mode)`** — vrátí číslovaný seznam emailů aktivní persony (filter: new/processed/all).
- Diagnostika: `python -m poetry run python scripts/_diag_email_pipeline.py` (read-only overview persona_channels + email_inbox + email_outbox).

**Repo hygiene** ✅
- `__pycache__` / `*.pyc` v .gitignore (od commit 7c6322a)
- `scripts/commit_*.ps1` a `scripts/push_phase*.ps1` taky gitignored (jednorázové helpery)
- `.gitattributes` normalizuje line endings (CRLF/LF)

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

**Email, SMS & lidé:**
- `send_email(to, subject, body)` — preview → potvrzení → EWS odeslání
- `send_sms(to, body)` — preview → potvrzení → outbox → Android gateway
- `list_email_inbox(limit?, filter_mode?)` — přijaté emaily aktivní persony (filter: `new` / `processed` / `all`)
- `list_sms_inbox(limit?, unread_only?)` — přijaté SMS aktivní persony
- `list_missed_calls(limit?)` / `list_recent_calls(limit?)` — call log persony
- `find_user(query)` — multi-source search v aktuálním tenantu (vrací i `preferred_phone`)
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
- **Login UPN v `persona_channels.identifier` je SECRET** — nikdy se nesmí objevit v logu, DB (`email_inbox.to_email` / `email_outbox.to_email`), API response ani UI. Autentizace proti Exchange je jediná cesta, kde se UPN používá (uvnitř `_get_account` / `_connect_account`). Pro storage, logy a UI se používá výhradně `display_identifier` (SMTP alias).
