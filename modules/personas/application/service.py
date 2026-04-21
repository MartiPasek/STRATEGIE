"""
Personas application service -- UI listing + direct switch by id.

Lisi se od switch_persona_for_user (query-based pro chat tool) tim, ze:
  - list vraci VSECHNY dostupne personas pro current tenant usera
    (tenant_id IS NULL = globalni; tenant_id = current = tenantove)
  - switch prijima primo persona_id (ne query), takze vede k presnemu
    prepnuti bez fuzzy matchingu (UI uz ma ID)
"""
from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import (
    Persona, User,
)
from modules.core.infrastructure.models_data import Conversation

logger = get_logger("personas.service")


class PersonaError(Exception):
    pass


def _is_superadmin(user_id: int | None) -> bool:
    """
    Superadmin check. MVP: user_id == 1 (seeded Marti). Do budoucna lze
    rozsirit napr. o flag v User table nebo seznam v configu. Centralizovano
    tady, aby zmeny mechanismu meli jedno misto.
    """
    return user_id == 1


def list_personas_for_user(user_id: int) -> list[dict]:
    """
    Vrati personas dostupne pro current user:
      - globalni (tenant_id IS NULL)
      - tenant-specificke pro current user.last_active_tenant_id

    Pole per item: id, name, is_default, tenant_id, is_global (bool),
    system_prompt_preview (prvnich 120 znaku).
    """
    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=user_id).first()
        current_tenant_id = user.last_active_tenant_id if user else None

        # Vsechny personas — bez rozdilu, pak filter v Pythonu (pro cistotu);
        # tabulka je mala.
        all_personas = cs.query(Persona).order_by(Persona.is_default.desc(), Persona.id.asc()).all()

        out: list[dict] = []
        for p in all_personas:
            # Global persona (tenant_id NULL) nebo persona current tenantu
            if p.tenant_id is None or p.tenant_id == current_tenant_id:
                out.append({
                    "id": p.id,
                    "name": p.name,
                    "description": (p.description or "").strip() or None,
                    "is_default": p.is_default,
                    "tenant_id": p.tenant_id,
                    "is_global": p.tenant_id is None,
                    "has_avatar": bool(p.avatar_path),
                })
        return out
    finally:
        cs.close()


def create_persona(
    *, user_id: int, name: str, system_prompt: str, description: str | None = None,
) -> dict:
    """
    Vytvori novou personu v tenantu aktualniho usera. Tenant owner muze
    (MVP -- jeste neni role-based, prosty owner check). Vraci dict s id +
    name pro UI.
    """
    name = (name or "").strip()
    if not name:
        raise PersonaError("Jmeno persony nesmi byt prazdne.")
    if len(name) > 255:
        raise PersonaError("Jmeno persony je prilis dlouhe.")
    system_prompt = (system_prompt or "").strip()
    if not system_prompt:
        raise PersonaError("System prompt persony nesmi byt prazdny.")
    description = (description or "").strip() or None

    # MVP zabezpeceni: persony smi vytvaret JEN superadmin (centralne).
    if not _is_superadmin(user_id):
        raise PersonaError(
            "Persony smi vytvaret jen superadmin. Pokud chces novou personu, "
            "napis Martimu."
        )

    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=user_id).first()
        if user is None:
            raise PersonaError("User neexistuje.")
        tenant_id = user.last_active_tenant_id
        if tenant_id is None:
            raise PersonaError("Nemas aktivni tenant, do ktereho personu pridat.")

        persona = Persona(
            name=name,
            description=description,
            system_prompt=system_prompt,
            tenant_id=tenant_id,
            is_default=False,
        )
        cs.add(persona)
        cs.commit()
        cs.refresh(persona)
        logger.info(
            f"PERSONA | created | user={user_id} | tenant={tenant_id} | "
            f"persona_id={persona.id} | name={name!r}"
        )
        return {"id": persona.id, "name": persona.name}
    finally:
        cs.close()


def update_persona(
    *,
    user_id: int,
    persona_id: int,
    name: str | None = None,
    description: str | None = None,
    system_prompt: str | None = None,
) -> dict:
    """
    Update existujici persony. JEN superadmin. Vsechna pole PATCH semantika
    -- pokud None, hodnota se nemeni. description '' znamena vycisti (NULL).
    Globalni persony (tenant_id IS NULL) nelze editovat pres tuto cestu
    (ochrana pred zmenou zakladni persony jako default Marti-AI).
    """
    if not _is_superadmin(user_id):
        raise PersonaError(
            "Persony smi editovat jen superadmin. Pokud potrebujes zmenit "
            "personu, napis Martimu."
        )

    cs = get_core_session()
    try:
        persona = cs.query(Persona).filter_by(id=persona_id).first()
        if persona is None:
            raise PersonaError("Persona neexistuje.")
        # Pozn.: drivejsi verze zakazala edit globalnich person (tenant_id IS NULL)
        # plosne. Ted povolujeme superadminovi -- je to jeho plnohodnotna akce
        # (vcetne zmeny default Marti-AI, pripadne avatar fotky).

        changed = []
        if name is not None:
            name = name.strip()
            if not name:
                raise PersonaError("Jmeno persony nesmi byt prazdne.")
            if len(name) > 255:
                raise PersonaError("Jmeno persony je prilis dlouhe.")
            if persona.name != name:
                persona.name = name
                changed.append("name")
        if system_prompt is not None:
            sp = system_prompt.strip()
            if not sp:
                raise PersonaError("System prompt persony nesmi byt prazdny.")
            if persona.system_prompt != sp:
                persona.system_prompt = sp
                changed.append("system_prompt")
        if description is not None:
            d = description.strip() or None  # prazdny string -> NULL (vyczisteno)
            if persona.description != d:
                persona.description = d
                changed.append("description")

        if changed:
            cs.commit()
            logger.info(
                f"PERSONA | updated | user={user_id} | persona_id={persona_id} | "
                f"changed={changed}"
            )
        return {"id": persona.id, "name": persona.name, "changed": changed}
    finally:
        cs.close()


def get_persona_detail(user_id: int, persona_id: int) -> dict:
    """
    Vrati plny obsah persony (vcetne system_prompt) pro edit modal.
    Scope check: jen persony v user scope (global nebo current tenant).
    """
    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=user_id).first()
        current_tenant_id = user.last_active_tenant_id if user else None
        persona = cs.query(Persona).filter_by(id=persona_id).first()
        if persona is None:
            raise PersonaError("Persona neexistuje.")
        if persona.tenant_id is not None and persona.tenant_id != current_tenant_id:
            raise PersonaError("Persona neni v tvem tenantu.")
        return {
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "system_prompt": persona.system_prompt,
            "tenant_id": persona.tenant_id,
            "is_global": persona.tenant_id is None,
            "is_default": persona.is_default,
        }
    finally:
        cs.close()


def switch_persona_direct(user_id: int, conversation_id: int, persona_id: int) -> dict:
    """
    Prepne personu konverzace na konkretni persona_id (UI primarne).
    Validuje:
      - konverzace patri userovi (ochrana pred cizim conversation_id)
      - persona existuje a je v scope usera (global nebo tenant)

    Vraci: {"persona_id": int, "persona_name": str, "already_active": bool}
    """
    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            raise PersonaError("Konverzace neexistuje.")
        if conv.user_id != user_id:
            raise PersonaError("Konverzace neni tvoje.")
        already = (conv.active_agent_id == persona_id)
    finally:
        ds.close()

    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=user_id).first()
        current_tenant_id = user.last_active_tenant_id if user else None
        persona = cs.query(Persona).filter_by(id=persona_id).first()
        if persona is None:
            raise PersonaError("Persona neexistuje.")
        if persona.tenant_id is not None and persona.tenant_id != current_tenant_id:
            raise PersonaError("Persona neni v tvem tenantu.")
        persona_name = persona.name
    finally:
        cs.close()

    if already:
        return {"persona_id": persona_id, "persona_name": persona_name, "already_active": True}

    # Update
    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        conv.active_agent_id = persona_id
        ds.commit()
    finally:
        ds.close()
    logger.info(
        f"PERSONA | direct switch | user={user_id} | conv={conversation_id} | "
        f"persona_id={persona_id} ({persona_name})"
    )
    return {"persona_id": persona_id, "persona_name": persona_name, "already_active": False}
