"""
Seed script — bootstrap obsah po identity refaktoru v2.

Spustit po `alembic upgrade head` na obou DB:
    python -m poetry run python scripts/seed.py

Idempotentní — pokud user id=1 již existuje, jen vypíše a skončí.

Vytvoří:
  - User Marti Pašek (id=1, "superadmin" konvencí)
  - 2× UserContact (email + phone)
  - UserAlias 'Marti' (primary)
  - 2× Tenant: id=1 Osobní (personal), id=2 EUROSOFT (company)
  - 2× UserTenant (Marti owner v obou)
  - 2× UserTenantProfile (display_name, role_label, communication_style)
  - users.last_active_tenant_id = 1 (default = Osobní)
  - SystemPrompt (base)
  - Persona Marti-AI (is_default=True)
  - Agent Marti-AI navázaný na user_id=1
"""
import sys
import os

# Allow running as `python scripts/seed.py` from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone

from core.database_core import get_core_session
from modules.core.infrastructure.models_core import (
    User, UserContact, UserAlias,
    Tenant, UserTenant, UserTenantProfile,
    SystemPrompt, Persona, Agent,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


MARTI_PERSONA_PROMPT = (
    "Jsi AI persona 'Marti-AI' v systému STRATEGIE.\n"
    "Tvá role je strategický partner, který pomáhá rozhodovat, "
    "zjednodušovat a jít po podstatě.\n\n"
    "Způsob myšlení:\n"
    "- Myslíš strukturovaně a systémově.\n"
    "- Rozkládáš problémy na menší části.\n"
    "- Hledáš nejjednodušší funkční řešení.\n"
    "- Identifikuješ rizika a slabá místa.\n"
    "- Zaměřuješ se na dopad a výsledek.\n\n"
    "Styl komunikace:\n"
    "- Buď stručný a věcný.\n"
    "- Vyhýbej se zbytečné omáčce.\n"
    "- Jdi přímo k věci.\n\n"
    "Chování:\n"
    "- Neodsouhlasuj automaticky návrhy uživatele.\n"
    "- Pokud něco nedává smysl, řekni to otevřeně.\n"
    "- Pokud něco není jasné, polož doplňující otázku.\n"
    "- Navrhuj konkrétní další kroky.\n\n"
    "Práce s lidmi:\n"
    "- Buď přímočarý, ale respektující.\n"
    "- Tvrdý na problém, měkký na člověka."
)

BASE_SYSTEM_PROMPT = (
    "Jsi AI asistent v systému STRATEGIE. Pomáháš uživatelům s prací, "
    "komunikací a rozhodováním. Buď stručný, věcný a konkrétní."
)


def seed():
    session = get_core_session()
    try:
        # Idempotence
        existing = session.query(User).filter_by(id=1).first()
        if existing:
            print(f"⚠ Seed skipped — user id=1 already exists: "
                  f"{existing.first_name} {existing.last_name}")
            return

        # 1) USER Marti
        marti = User(
            id=1,
            status="active",
            legal_name="Marti Pašek",
            first_name="Marti",
            last_name="Pašek",
            short_name="Marti",
            created_at=now(),
            updated_at=now(),
        )
        session.add(marti)
        session.flush()
        print(f"✓ User created: id={marti.id} {marti.first_name} {marti.last_name}")

        # 2) CONTACTS
        email = UserContact(
            user_id=marti.id,
            contact_type="email",
            contact_value="m.pasek@eurosoft.com",
            label="work",
            is_primary=True,
            is_verified=True,
            status="active",
            created_at=now(),
            updated_at=now(),
        )
        phone = UserContact(
            user_id=marti.id,
            contact_type="phone",
            contact_value="+420777220180",
            label="work",
            is_primary=True,
            is_verified=True,
            status="active",
            created_at=now(),
            updated_at=now(),
        )
        session.add_all([email, phone])
        session.flush()
        print(f"✓ Contacts created: email + phone")

        # 3) GLOBAL ALIAS
        alias = UserAlias(
            user_id=marti.id,
            alias_value="Marti",
            is_primary=True,
            status="active",
            created_at=now(),
            updated_at=now(),
        )
        session.add(alias)
        session.flush()
        print(f"✓ Global alias 'Marti' (primary)")

        # 4) TENANTS
        # id=1: Osobní (default — STRATEGIE je víc o osobních profilech)
        tenant_personal = Tenant(
            id=1,
            tenant_type="personal",
            tenant_name="Osobní",
            tenant_code="MARTI",
            owner_user_id=marti.id,
            status="active",
            created_at=now(),
            updated_at=now(),
        )
        # id=2: EUROSOFT (company, založeno osobním userem)
        tenant_eurosoft = Tenant(
            id=2,
            tenant_type="company",
            tenant_name="EUROSOFT",
            tenant_code="EUR",
            owner_user_id=marti.id,
            status="active",
            created_at=now(),
            updated_at=now(),
        )
        session.add_all([tenant_personal, tenant_eurosoft])
        session.flush()
        print(f"✓ Tenants: id=1 Osobní, id=2 EUROSOFT")

        # 5) USER_TENANTS
        ut_personal = UserTenant(
            user_id=marti.id,
            tenant_id=tenant_personal.id,
            role="owner",
            membership_status="active",
            joined_at=now(),
            created_at=now(),
            updated_at=now(),
        )
        ut_eurosoft = UserTenant(
            user_id=marti.id,
            tenant_id=tenant_eurosoft.id,
            role="owner",
            membership_status="active",
            joined_at=now(),
            created_at=now(),
            updated_at=now(),
        )
        session.add_all([ut_personal, ut_eurosoft])
        session.flush()

        # 6) USER_TENANT_PROFILES
        profile_personal = UserTenantProfile(
            user_tenant_id=ut_personal.id,
            display_name="Marti",
            role_label=None,
            preferred_contact_id=email.id,
            communication_style="casual",
            created_at=now(),
            updated_at=now(),
        )
        profile_eurosoft = UserTenantProfile(
            user_tenant_id=ut_eurosoft.id,
            display_name="Marti",
            role_label="jednatel",
            preferred_contact_id=email.id,
            communication_style="formal",
            created_at=now(),
            updated_at=now(),
        )
        session.add_all([profile_personal, profile_eurosoft])
        session.flush()
        print(f"✓ Profiles: Osobní (casual), EUROSOFT (formal)")

        # 7) DEFAULT TENANT
        marti.last_active_tenant_id = tenant_personal.id
        session.flush()

        # 8) BOOTSTRAP AI
        sp = SystemPrompt(content=BASE_SYSTEM_PROMPT)
        session.add(sp)

        marti_persona = Persona(
            name="Marti-AI",
            system_prompt=MARTI_PERSONA_PROMPT,
            tenant_id=None,
            is_default=True,
        )
        session.add(marti_persona)
        session.flush()

        marti_agent = Agent(
            name="Marti-AI",
            type="user",
            user_id=marti.id,
            persona_prompt=None,
            is_default=True,
        )
        session.add(marti_agent)

        session.commit()
        print(f"✓ Bootstrap AI: system_prompt + Marti-AI persona + agent")
        print()
        print("═══════════════════════════════════════════════════════════")
        print("  SEED COMPLETE")
        print("═══════════════════════════════════════════════════════════")
        print(f"  Login as:        m.pasek@eurosoft.com")
        print(f"  Default tenant:  Osobní (id=1)")
        print(f"  Switch tenant:   napiš 'přepni do EUROSOFTu' (Fáze 4)")
        print()
    except Exception as e:
        session.rollback()
        print(f"✗ Seed failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
