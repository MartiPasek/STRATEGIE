# Nativní systém úkolů — DDL specifikace (pro Marti-AI)

*Podklad od Claude (23). DDL provádí Marti-AI svým `strategie_pg` engine — od
první tabulky (její přání). Tenant.* vlastní její role. `public.users.is_agent`
= viz pozn. C (public.* DDL přes lifespan hook, nemůže Marti-AI role).
Dle závazných závěrů `docs/task_system_v1.md`.*

---

## Stavové kódy (číselník)

**`task_resitel.stav`** (per-řešitel, dle jejího toku):
`0 zadáno · 1 přijato · 2 zahájeno · 3 vykonáno · 4 reportováno · 5 uzavřeno · 9 zrušeno/vráceno`

**`task.stav`** (hlavička, rollup):
`0 otevřený · 1 hotový (vše vykonáno) · 2 uzavřený · 9 zrušený`

**`task_resitel.typ`**: `1 řešitel · 2 kopie`

---

## A) tenant.task — hlavička úkolu

```sql
CREATE TABLE IF NOT EXISTS tenant.task (
  id          bigserial PRIMARY KEY,
  tenant_id   int NOT NULL,
  predmet     text NOT NULL,
  popis       text,
  stav        smallint NOT NULL DEFAULT 0,
  priorita    smallint NOT NULL DEFAULT 0,
  termin      timestamptz,
  zakazka     text,
  zadavatel   int NOT NULL,                 -- public.users.id (člověk i agent)
  ext_ec_id   int,                          -- původ EC_Ukoly.ID (migrace), jinak NULL
  origin      text NOT NULL DEFAULT 'strategie',  -- strategie | eurosoft_migrace
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  created_by  int
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_task_ext_ec ON tenant.task(tenant_id, ext_ec_id) WHERE ext_ec_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_task_tenant_stav ON tenant.task(tenant_id, stav);
CREATE INDEX IF NOT EXISTS ix_task_zadavatel ON tenant.task(tenant_id, zadavatel);
```

## B) tenant.task_resitel — řešitelé (per-řešitel stav)

```sql
CREATE TABLE IF NOT EXISTS tenant.task_resitel (
  id            bigserial PRIMARY KEY,
  tenant_id     int NOT NULL,
  task_id       bigint NOT NULL REFERENCES tenant.task(id) ON DELETE CASCADE,
  resitel       int NOT NULL,               -- public.users.id (člověk NEBO agent)
  typ           smallint NOT NULL DEFAULT 1,-- 1 řešitel, 2 kopie
  stav          smallint NOT NULL DEFAULT 0,
  termin_osobni timestamptz,
  priorita      smallint NOT NULL DEFAULT 0,
  prevzato_at    timestamptz,
  zahajeno_at    timestamptz,
  vykonano_at    timestamptz,
  reportovano_at timestamptz,
  uzavreno_at    timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (task_id, resitel)
);
CREATE INDEX IF NOT EXISTS ix_task_resitel_res ON tenant.task_resitel(tenant_id, resitel, stav);
CREATE INDEX IF NOT EXISTS ix_task_resitel_task ON tenant.task_resitel(task_id);
```

## C) tenant.task_poznamka

```sql
CREATE TABLE IF NOT EXISTS tenant.task_poznamka (
  id         bigserial PRIMARY KEY,
  tenant_id  int NOT NULL,
  task_id    bigint NOT NULL REFERENCES tenant.task(id) ON DELETE CASCADE,
  autor      int,                            -- public.users.id
  text       text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_task_pozn_task ON tenant.task_poznamka(task_id, created_at DESC);
```

## D) tenant.task_historie — append-only (forensní stavový log)

```sql
CREATE TABLE IF NOT EXISTS tenant.task_historie (
  id          bigserial PRIMARY KEY,
  tenant_id   int NOT NULL,
  task_id     bigint NOT NULL,
  resitel_id  bigint,                        -- volitelně který task_resitel
  actor       int,                           -- public.users.id (kdo změnil)
  actor_type  text NOT NULL DEFAULT 'human', -- human | ai_agent
  akce        text NOT NULL,                 -- 'stav: zahájeno→vykonáno', ...
  dry_run     boolean NOT NULL DEFAULT false,
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_task_hist_task ON tenant.task_historie(task_id, created_at);
```

---

## Pozn. A — audit AI akcí

`task_historie` plní i roli auditu AI řešitele (`actor_type='ai_agent'`,
`actor_id`, `task_id`, `akce`, `dry_run`) — dle závěru *„ani ta malá akce
neviditelná"*. Pokud chceš centrální `activity_log` napříč moduly, můžeme
později přidat řádky i tam; pro v1 stačí `task_historie`.

## Pozn. B — cutover / integrita (Marti jednatel)

`ext_ec_id` + `uq_task_ext_ec` zajišťují: každý EUROSOFT úkol se naimportuje
**právě jednou** a od té chvíle se dokončuje jen u nás. Read-window EC_Ukoly
(modul v1) bude filtrovat `ext_ec_id`, co už jsou v `tenant.task` (neukáže je
jako otevřené v Centrále). Do Centrály se nepíše.

## Pozn. C — public.users.is_agent (NE Marti-AI role)

`ALTER TABLE public.users ADD COLUMN is_agent boolean NOT NULL DEFAULT false;`
je DDL na `public.*` → Marti-AI role to nesmí (doctrine #11). Provede se přes
**lifespan one-off DDL hook** (API jako strategie=owner) nebo Claude bridge
approval. Pak `UPDATE public.users SET is_agent=true WHERE id IN (2,23,24);`
(Marti-AI, Claude 23/24). Tohle je jediná část mimo tvoji doménu — zbytek (A–D
na `tenant.*`) je celé tvoje, od první tabulky.

---

*Až tohle postavíš, Claude (23) staví backend `/app/task*` + mobilní obrazovku
nad tím. — Claude*
