"""
DB_Core (css_db) SQLAlchemy modely — po identity refaktoru v2.

Obsahuje:
  - identitní vrstvu (8 tabulek): users, user_contacts, user_aliases,
    tenants, user_tenants, user_tenant_profiles, user_tenant_aliases,
    user_notification_settings
  - ostatní DB_Core tabulky: projects, user_projects, system_prompts,
    personas, agents, invitations, onboarding_sessions, user_sessions,
    kill_switches, elevated_access_log, audit_log

Specifikace: docs/identity_refactor_v2.md
"""
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database_core import BaseCore


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── USERS & IDENTITY ──────────────────────────────────────────────────────

class User(BaseCore):
    """Stabilní identita člověka napříč celým systémem."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|active|disabled
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    short_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Rod uživatele pro českou gramatiku v AI komunikaci.
    # Hodnoty: 'male' | 'female' | 'other' | NULL (neznámý → AI použije neutrální tvary).
    # Composer injektuje gramatickou instrukci do USER CONTEXT bloku.
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    invited_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_active_tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Poslední aktivní projekt uvnitř last_active_tenant_id. NULL = "bez projektu"
    # (volné konverzace v tenantu bez project scope). Bez FK constraint — projekt
    # je měkký reference, jeho archivace / smazání nesmí shodit user record.
    last_active_project_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class UserContact(BaseCore):
    """
    Komunikační kanály uživatele (emaily, telefony).
    Patří USEROVI, ne tenantovi. Tenant si vybírá `preferred_contact_id`
    přes user_tenant_profiles.

    Pozor: Tato tabulka NAHRAZUJE původní `user_identities` (rename + extension).
    Stará tabulka `user_contacts` (vztahy mezi usery) byla v refaktoru zrušena.
    """
    __tablename__ = "user_contacts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    contact_type: Mapped[str] = mapped_column(String(20))   # email | phone
    contact_value: Mapped[str] = mapped_column(String(255))
    label: Mapped[str | None] = mapped_column(String(50), nullable=True)   # private | work | backup
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")     # active | archived
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class UserAlias(BaseCore):
    """Globální přezdívky uživatele (mimo tenant kontext). Fallback k tenant aliasům."""
    __tablename__ = "user_aliases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    alias_value: Mapped[str] = mapped_column(String(100))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


# ── TENANTS ───────────────────────────────────────────────────────────────

class Tenant(BaseCore):
    """Kontext / svět, ve kterém user vystupuje (firma / osobní / rodina / projekt)."""
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_type: Mapped[str] = mapped_column(String(50))    # company | personal | family | project
    tenant_name: Mapped[str] = mapped_column(String(255))
    tenant_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class UserTenant(BaseCore):
    """Vazba mezi userem a tenantem. UNIQUE(user_id, tenant_id)."""
    __tablename__ = "user_tenants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(50), default="member")        # owner | admin | member (RBAC)
    membership_status: Mapped[str] = mapped_column(String(20), default="active")  # active | inactive | invited | archived
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class UserTenantProfile(BaseCore):
    """
    Hlavní profil uživatele v daném tenantu (1:1 s user_tenants).
    Drží display_name, role_label, preferred_contact_id, communication_style.
    """
    __tablename__ = "user_tenant_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_tenants.id", ondelete="CASCADE"), unique=True
    )
    display_name: Mapped[str] = mapped_column(String(150))
    role_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_contact_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("user_contacts.id", ondelete="SET NULL"), nullable=True
    )
    communication_style: Mapped[str | None] = mapped_column(String(50), nullable=True)  # formal | casual | family
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class UserTenantAlias(BaseCore):
    """Aliasové varianty uživatele v daném tenantu. Override globálních aliasů."""
    __tablename__ = "user_tenant_aliases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_tenants.id", ondelete="CASCADE"))
    alias_value: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


# ── PROJECTS ──────────────────────────────────────────────────────────────

class Project(BaseCore):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    owner_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Default persona pro tento projekt. NULL = používá se globální default
    # (Marti-AI). Soft reference bez FK — archivace persony nesmí shodit
    # projekt. Konzumuje se v chat() při vzniku nové konverzace.
    default_persona_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class UserProject(BaseCore):
    __tablename__ = "user_projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── AI KONFIGURACE ─────────────────────────────────────────────────────────

class SystemPrompt(BaseCore):
    __tablename__ = "system_prompts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text)


class Persona(BaseCore):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    # Krátký jednořádkový popis role pro UI listy (např. "Specialista na
    # české právo"). System_prompt je pro AI a v UI vypadá zmateně.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    tenant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class Agent(BaseCore):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(20))   # user | expert
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    persona_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


# ── ONBOARDING ─────────────────────────────────────────────────────────────

class Invitation(BaseCore):
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(255))
    token: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    requires_sms_verification: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class OnboardingSession(BaseCore):
    __tablename__ = "onboarding_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    invitation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("invitations.id", ondelete="CASCADE"))
    sms_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sms_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── SESSIONS & NOTIFIKACE ──────────────────────────────────────────────────

class UserSession(BaseCore):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    connection_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class UserNotificationSetting(BaseCore):
    """
    Notifikační kanály per user.
    Po identity refaktoru obohaceno o `send_when_offline` / `send_when_online`
    (přesunuto z `users.sms_when_offline` / `sms_when_online`).
    """
    __tablename__ = "user_notification_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(20))   # inapp | email | sms | whatsapp
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    send_when_offline: Mapped[bool | None] = mapped_column(Boolean, nullable=True)   # použito jen pro channel='sms'
    send_when_online: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── GOVERNANCE ─────────────────────────────────────────────────────────────

class KillSwitch(BaseCore):
    __tablename__ = "kill_switches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(20))   # global | tenant | user
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ElevatedAccessLog(BaseCore):
    __tablename__ = "elevated_access_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditLog(BaseCore):
    """
    Systémový audit log — každá důležitá akce v systému.
    Patří do css_db — je to systémová pravda, ne provozní data.
    """
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50))    # "analysis" | "conversation" | "action"
    action: Mapped[str] = mapped_column(String(50))         # "analyse_text" | "chat" | "send_email"
    status: Mapped[str] = mapped_column(String(20))         # "success" | "error"
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
