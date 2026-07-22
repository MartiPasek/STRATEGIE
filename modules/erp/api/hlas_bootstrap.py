"""Hlas engine — FAZE 1 bootstrap (schema hlas + tabulky + granty).
Marti / Cowork 22.7.2026. Idempotentni (IF NOT EXISTS). Vola se pres @@HLASINIT
z /diag-sql mostu. PG DDL je transakcni -> vse nebo nic (rollback pri chybe).
Odkazy na g2007.entita / g2007.graf jsou MEKKE (bigint bez FK) — engine je
domenove odpojeny a nevyzaduje REFERENCES na cizi schema (viz i domain_key)."""
from sqlalchemy import text as _t

_DDL = [
    "CREATE SCHEMA IF NOT EXISTS hlas",
    """CREATE TABLE IF NOT EXISTS hlas.kanal (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id bigint NOT NULL,
    firma varchar(8),
    kod varchar(64) NOT NULL,
    nazev text,
    typ varchar(16) NOT NULL DEFAULT 'text',
    entita_id bigint,
    domain_key varchar(64),
    graf_id bigint,
    config jsonb NOT NULL DEFAULT '{}'::jsonb,
    stav varchar(16) NOT NULL DEFAULT 'navrh',
    poradi integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, kod)
)""",
    """CREATE TABLE IF NOT EXISTS hlas.relace (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id bigint NOT NULL,
    kanal_id bigint NOT NULL REFERENCES hlas.kanal(id),
    smer varchar(12) NOT NULL DEFAULT 'prichozi',
    protistrana varchar(128),
    stav varchar(20) NOT NULL DEFAULT 'probiha',
    vysledek text,
    kontext jsonb NOT NULL DEFAULT '{}'::jsonb,
    zahajeno_at timestamptz NOT NULL DEFAULT now(),
    ukonceno_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
)""",
    "CREATE INDEX IF NOT EXISTS ix_hlas_relace_kanal ON hlas.relace(kanal_id)",
    "CREATE INDEX IF NOT EXISTS ix_hlas_relace_stav ON hlas.relace(stav)",
    """CREATE TABLE IF NOT EXISTS hlas.vyslovnost (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id bigint,
    scope varchar(12) NOT NULL DEFAULT 'global',
    scope_ref varchar(64),
    typ varchar(16) NOT NULL,
    rezim varchar(12) NOT NULL DEFAULT 'alias',
    vzor text NOT NULL,
    nahrada text NOT NULL,
    priorita integer NOT NULL DEFAULT 100,
    poznamka text,
    stav varchar(12) NOT NULL DEFAULT 'aktivni',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
)""",
    "CREATE INDEX IF NOT EXISTS ix_hlas_vyslovnost_scope ON hlas.vyslovnost(scope, typ, priorita)",
    'GRANT USAGE ON SCHEMA hlas TO strategie, "Marti-AI"',
    'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA hlas TO strategie, "Marti-AI"',
    'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA hlas TO strategie, "Marti-AI"',
    'ALTER DEFAULT PRIVILEGES IN SCHEMA hlas GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO strategie, "Marti-AI"',
]


def hlas_init():
    """Zaloz schema hlas + tabulky + granty. Idempotentni, transakcni."""
    from core.database import get_session
    sg = get_session()
    done = []
    try:
        for stmt in _DDL:
            sg.execute(_t(stmt))
            done.append(stmt.strip().split("\n", 1)[0][:70])
        sg.commit()
    except Exception as e:
        try:
            sg.rollback()
        except Exception:
            pass
        sg.close()
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:400]),
                "provedeno_pred_chybou": done}
    sg.close()
    return {"ok": True, "prikazu": len(done), "provedeno": done}
