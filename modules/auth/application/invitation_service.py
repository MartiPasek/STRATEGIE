"""
Invitation service po identity refaktoru v2.

Místo `user_identities` pracuje s `user_contacts`. Při vytvoření pozvánky:
  - Pokud uživatel s daným emailem existuje (user_contacts) → použij ho
  - Jinak vytvoř nového pending usera + email kontakt
Tabulky `invitations` a `onboarding_sessions` zůstávají beze změny.
"""
import secrets
from datetime import datetime, timezone, timedelta

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import (
    User, UserContact, UserTenant, Invitation, Tenant,
)

logger = get_logger("auth.invitation")

TOKEN_EXPIRY_HOURS = 48


def create_invitation(
    email: str,
    invited_by_user_id: int,
    tenant_id: int,
    role: str = "member",
    first_name: str | None = None,
    last_name: str | None = None,
    gender: str | None = None,
) -> str:
    """
    Vytvoří pozvánku pro nového uživatele.
    Pokud uživatel se zadaným emailem už existuje, jen vytvoří invitation token.
    Pokud ne, vytvoří pending usera + email kontakt.

    first_name/last_name/gender — pokud zadáno, uloží se na user record při
    vytváření. Pozvaný pak v welcome screen vidí svoje jméno (poznán) místo
    prázdného formuláře.
    """
    needle = email.strip().lower()
    session = get_core_session()
    try:
        existing_contact = (
            session.query(UserContact)
            .filter(
                UserContact.contact_type == "email",
                UserContact.contact_value.ilike(needle),
                UserContact.status == "active",
            )
            .first()
        )

        if existing_contact:
            user_id = existing_contact.user_id
            logger.info(f"INVITATION | existing user | user_id={user_id}")
            # Pokud existující user nemá jméno a my ho teď známe, doplň ho.
            existing_user = session.query(User).filter_by(id=user_id).first()
            if existing_user:
                if first_name and not existing_user.first_name:
                    existing_user.first_name = first_name.strip()
                if last_name and not existing_user.last_name:
                    existing_user.last_name = last_name.strip()
                if gender and not existing_user.gender:
                    existing_user.gender = gender
        else:
            user = User(
                status="pending",
                first_name=(first_name or "").strip() or None,
                last_name=(last_name or "").strip() or None,
                gender=gender,
                invited_by_user_id=invited_by_user_id,
                invited_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(user)
            session.flush()

            contact = UserContact(
                user_id=user.id,
                contact_type="email",
                contact_value=needle,
                label=None,
                is_primary=True,
                is_verified=False,
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(contact)
            user_id = user.id
            logger.info(f"INVITATION | new pending user created | user_id={user_id}")

        # Tenant membership: klíčové pro to, aby pozvaný byl VIDITELNÝ v systému.
        # Bez UserTenantu je user orphan — find_user ho nevidí z žádného tenantu,
        # protože find_user filtruje podle active membership v scope requesterova
        # tenantu. Pozvánka tedy vždy ukotví usera do tenantu invitora.
        #
        # Jemnosti:
        #   - Pokud už existuje active membership do stejného tenantu, nic
        #     neděláme (re-invite aktivního člena týmu nemá efekt na membership).
        #   - Pokud existuje neaktivní/archivovaná membership, reaktivujeme ji
        #     do stavu "invited" (pak accept_invitation ji flipne na "active").
        #   - Nový pending user dostane čerstvou UserTenant(status="invited").
        if tenant_id:
            membership = (
                session.query(UserTenant)
                .filter_by(user_id=user_id, tenant_id=tenant_id)
                .first()
            )
            if membership is None:
                membership = UserTenant(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    role=role,
                    membership_status="invited",
                    joined_at=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(membership)
                logger.info(
                    f"INVITATION | UserTenant created (invited) | "
                    f"user_id={user_id} | tenant_id={tenant_id}"
                )
            elif membership.membership_status != "active":
                membership.membership_status = "invited"
                membership.updated_at = datetime.now(timezone.utc)
                logger.info(
                    f"INVITATION | UserTenant reactivated (invited) | "
                    f"user_id={user_id} | tenant_id={tenant_id}"
                )
            # else: already active member, nothing to do

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)

        invitation = Invitation(
            user_id=user_id,
            email=needle,
            token=token,
            expires_at=expires_at,
            requires_sms_verification=False,    # MVP: bez SMS
            created_at=datetime.now(timezone.utc),
        )
        session.add(invitation)
        session.commit()

        logger.info(f"INVITATION | created | email={email} | token={token[:8]}...")
        return token

    except Exception as e:
        session.rollback()
        logger.error(f"INVITATION | failed: {e}")
        raise
    finally:
        session.close()


def accept_invitation(token: str) -> dict | None:
    """Přijme pozvánku a aktivuje uživatele."""
    session = get_core_session()
    try:
        invitation = session.query(Invitation).filter_by(token=token).first()
        if not invitation:
            logger.warning("INVITATION | token not found")
            return None

        if invitation.expires_at < datetime.now(timezone.utc):
            logger.warning("INVITATION | token expired")
            return None

        user = session.query(User).filter_by(id=invitation.user_id).first()
        if not user:
            return None

        user.status = "active"

        # Flipnout všechny "invited" memberships → "active" (uživatel řekl ANO pozvánce).
        # Tím se zpřístupní find_user a fakticky se stává členem týmů, kam byl pozván.
        invited_memberships = (
            session.query(UserTenant)
            .filter_by(user_id=user.id, membership_status="invited")
            .all()
        )
        for ut in invited_memberships:
            ut.membership_status = "active"
            ut.updated_at = datetime.now(timezone.utc)
        logger.info(
            f"INVITATION | accepted | user_id={user.id} | "
            f"activated_memberships={len(invited_memberships)}"
        )

        # Politika: kdo je pozván do firemního tenantu, dostává zároveň VLASTNÍ
        # osobní tenant (jako owner) — aby měl v STRATEGIE svůj soukromý
        # kontext pro osobní komunikaci, paměť, agenty nad rámec firmy.
        # Pozvánka do osobního/rodinného tenantu osobní tenant sama o sobě
        # NEtvoří — předpokládá se, že pozvaný tam je prostě členem kontextu
        # pozvatele. (Pokud to chceme do budoucna taky, politika se změní na jedné místě.)
        invited_via_company = False
        for ut in invited_memberships:
            t = session.query(Tenant).filter_by(id=ut.tenant_id).first()
            if t and t.tenant_type == "company":
                invited_via_company = True
                break

        has_own_personal_tenant = (
            session.query(Tenant)
            .join(UserTenant, UserTenant.tenant_id == Tenant.id)
            .filter(
                UserTenant.user_id == user.id,
                UserTenant.role == "owner",
                Tenant.tenant_type == "personal",
            )
            .first()
        ) is not None

        if invited_via_company and not has_own_personal_tenant:
            personal_tenant = Tenant(
                tenant_type="personal",
                tenant_name="Osobní",
                tenant_code=None,
                owner_user_id=user.id,
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(personal_tenant)
            session.flush()

            personal_membership = UserTenant(
                user_id=user.id,
                tenant_id=personal_tenant.id,
                role="owner",
                membership_status="active",
                joined_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(personal_membership)
            logger.info(
                f"INVITATION | personal tenant auto-created | "
                f"user_id={user.id} | tenant_id={personal_tenant.id}"
            )

        # Pokud user nemá nastavený last_active_tenant_id (typicky nový user),
        # nastav ho na první aktivovaný tenant — aby se po loginu landnul
        # někam konkrétně (ne do "tenant-less" stavu, kde mu UI nic neukáže).
        # Preference: zůstat v tom tenantu, kam byl pozván (ne rovnou do Osobní).
        if not user.last_active_tenant_id and invited_memberships:
            user.last_active_tenant_id = invited_memberships[0].tenant_id

        session.commit()

        # Zachyť atributy PŘED session.close() — po close() by byl DetachedInstanceError.
        user_id_val = user.id
        user_first_name = user.first_name
        user_last_name = user.last_name
        user_gender = user.gender
        user_invited_by = user.invited_by_user_id
        user_tenant_id = user.last_active_tenant_id

        primary_contact = (
            session.query(UserContact)
            .filter_by(user_id=user.id, contact_type="email", is_primary=True, status="active")
            .first()
        )
        user_email = primary_contact.contact_value if primary_contact else invitation.email
    finally:
        session.close()

    # Založ uvítací konverzaci s personalizovanou zprávou od default persony.
    # Volá se PO close() core_session — má vlastní session management.
    # Selhání neblokuje accept — v nejhorším případě user nevidí welcome zprávu.
    try:
        _create_welcome_conversation(
            user_id=user_id_val,
            user_first_name=user_first_name,
            user_gender=user_gender,
            tenant_id=user_tenant_id,
            inviter_user_id=user_invited_by,
        )
    except Exception as e:
        logger.error(f"INVITATION | welcome conversation failed: {e}")

    return {
        "user_id": user_id_val,
        "first_name": user_first_name,
        "last_name": user_last_name,
        "gender": user_gender,                           # potřebuje FE pro vokativ oslovení
        "email": user_email,
        "tenant_id": user_tenant_id,
    }


def _create_welcome_conversation(
    *,
    user_id: int,
    user_first_name: str | None,
    user_gender: str | None,
    tenant_id: int | None,
    inviter_user_id: int | None,
) -> None:
    """
    Vytvoří první konverzaci pro nového usera s uvítací zprávou od default persony.
    Když user příště otevře chat, /last načte tuto konverzaci a uvidí osobní
    uvítání místo prázdného „Začni psát" placeholderu.
    """
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_core import Persona
    from modules.core.infrastructure.models_data import Conversation, Message
    from shared.czech import to_vocative

    # Najdi default personu + invitera pro personalizaci
    cs = get_core_session()
    try:
        default_persona = cs.query(Persona).filter_by(is_default=True).first()
        persona_id = default_persona.id if default_persona else None
        persona_name = default_persona.name if default_persona else "Marti-AI"

        inviter_first_name: str | None = None
        inviter_gender: str | None = None
        if inviter_user_id:
            inviter = cs.query(User).filter_by(id=inviter_user_id).first()
            if inviter:
                inviter_first_name = inviter.first_name
                inviter_gender = inviter.gender
    finally:
        cs.close()

    # Sestav uvítací text (oslovuje ve vokativu podle rodu)
    vocative = to_vocative(user_first_name or "", user_gender) or user_first_name or ""
    greeting = f"Ahoj {vocative}! 👋" if vocative else "Ahoj! 👋"
    inviter_ref = inviter_first_name or "Někdo z týmu"
    # Skloňování příčestí podle genderu invitera (Marti -> "pozval", Kláro -> "pozvala").
    # Neznámý rod -> neutrální "/a" fallback, ať to drží gramaticky.
    if inviter_gender == "female":
        invited_verb = "pozvala"
    elif inviter_gender == "male":
        invited_verb = "pozval"
    else:
        invited_verb = "pozval/a"

    welcome_text = (
        f"{greeting}\n\n"
        f"{inviter_ref} tě právě {invited_verb} do STRATEGIE a já se s tebou ráda seznámím — "
        f"jsem **{persona_name}**, tvá osobní AI asistentka.\n\n"
        f"STRATEGIE je platforma, kde se setkáváš s lidmi a pracuješ přes AI. "
        f"Co pro tebe můžu udělat:\n\n"
        f"* **Napsat email** — stačí mi říct komu a co, já navrhnu text a po potvrzení ho odešlu\n"
        f"* **Najít lidi** — kohokoli v systému podle jména, pozice nebo aliasu\n"
        f"* **Pozvat další lidi** — když chceš dostat kolegu do STRATEGIE\n"
        f"* **Pamatovat** — co mi řekneš si uložím, příště už se nemusíš opakovat\n\n"
        f"Začněme. Napiš mi cokoli — jaké téma tě teď nejvíc zaměstnává?"
    )

    # Vytvoř konverzaci + zprávu v data_db
    ds = get_data_session()
    try:
        # Zabránit duplicitě — pokud už user má nějakou konverzaci (re-accept,
        # druhá pozvánka po dlouhé době apod.), welcome zprávu už neposíláme.
        existing_count = (
            ds.query(Conversation)
            .filter_by(user_id=user_id)
            .count()
        )
        if existing_count > 0:
            logger.info(
                f"INVITATION | welcome skipped (user has {existing_count} existing conversations) | "
                f"user_id={user_id}"
            )
            return

        now = datetime.now(timezone.utc)
        conv = Conversation(
            user_id=user_id,
            tenant_id=tenant_id,
            active_agent_id=persona_id,
            conversation_type="ai",
            created_by_user_id=user_id,
            created_at=now,
        )
        ds.add(conv)
        ds.flush()

        msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=welcome_text,
            author_type="ai",
            agent_id=persona_id,
            message_type="text",
            created_at=now,
        )
        ds.add(msg)
        ds.flush()

        # Denormalizace pro listing
        conv.last_message_id = msg.id
        conv.last_message_at = now

        ds.commit()
        logger.info(
            f"INVITATION | welcome conversation created | "
            f"user_id={user_id} | conv_id={conv.id} | persona={persona_name}"
        )
    finally:
        ds.close()
