"""
Composer — skládá prompt z více vrstev.
Načítá personu podle active_agent_id konverzace.

Identity refactor v2 přidal vrstvu USER CONTEXT — Composer dnes injectuje
do system promptu identitu přihlášeného usera (jméno, display_name v aktuálním
tenantu, preferovaný kontakt, aliasy). Tím AI ví, KDO s ní mluví a v jakém
kontextu, což odstraňuje halucinace „Marti je Klára" apod.
"""
from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import (
    SystemPrompt, Persona,
    User, UserAlias,
    Tenant, UserTenant, UserTenantProfile, UserTenantAlias,
    UserContact,
)
from modules.core.infrastructure.models_data import Message, ConversationSummary, Conversation

logger = get_logger("conversation.composer")

DEFAULT_SYSTEM_PROMPT = "Jsi neutrální asistent. Odpovídej věcně a srozumitelně."
MAX_TOKENS = 6000
CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def _get_system_prompt() -> str:
    session = get_core_session()
    try:
        prompt = session.query(SystemPrompt).first()
        return prompt.content if prompt else DEFAULT_SYSTEM_PROMPT
    finally:
        session.close()


def build_user_context_block(user_id: int | None, tenant_id: int | None) -> str | None:
    """
    Vytvoří USER CONTEXT blok pro injekci do system promptu.

    Vrací větný formát (lépe stravitelný pro LLM než JSON):
        Mluvíš s uživatelem Marti Pašek. V kontextu tohoto tenantu (EUROSOFT,
        company) ho oslovuj jako 'Marti'. Jeho preferovaný email je
        m.pasek@eurosoft.com. Další jeho aliasy: Martin, M.P. Pracovní
        pozice: jednatel.

    Pokud chybí user_id (např. anonymní session) → vrátí None.
    Pokud chybí tenant_id → vynechá tenant část, jen identita usera.
    Při jakékoli chybě (nekonzistentní DB) → vrátí None, ať Composer pokračuje.
    """
    if user_id is None:
        return None

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return None

        # Jméno (preferuj first+last, fallback na legal_name)
        full_name = " ".join(filter(None, [user.first_name, user.last_name])).strip()
        if not full_name:
            full_name = user.legal_name or f"User #{user.id}"

        parts: list[str] = [f"Mluvíš s uživatelem {full_name}."]

        # Český gramatický rod uživatele — bez toho AI defaultuje na rod své
        # vlastní persony (např. ženská Marti-AI by Martiho oslovovala
        # ženskými tvary „přepnula jsi", „jednatelka").
        if user.gender == "male":
            parts.append(
                "Tento uživatel je mužského rodu. V minulém čase používej "
                "mužské tvary sloves (přepnul, byl, šel). U podstatných jmen "
                "označujících osobu používej mužský rod (jednatel, kolega, "
                "ředitel — ne jednatelka, kolegyně, ředitelka). Zájmena: "
                "on, jeho, mu, ho, jím."
            )
        elif user.gender == "female":
            parts.append(
                "Tento uživatel je ženského rodu. V minulém čase používej "
                "ženské tvary sloves (přepnula, byla, šla). U podstatných jmen "
                "označujících osobu používej ženský rod (jednatelka, kolegyně, "
                "ředitelka — ne jednatel, kolega, ředitel). Zájmena: "
                "ona, její, jí, ji, jí."
            )
        elif user.gender == "other":
            parts.append(
                "Rod tohoto uživatele není určen. Volej neutrální tvary, "
                "vyhýbej se rodově zabarveným podstatným jménům "
                "(piš spíše 'v této roli', 'tato osoba')."
            )
        # Pokud user.gender is None — žádná instrukce (AI použije default).

        # Tenant část (pouze pokud je tenant_id)
        display_name: str | None = None
        if tenant_id is not None:
            tenant = session.query(Tenant).filter_by(id=tenant_id, status="active").first()
            if tenant:
                ut = (
                    session.query(UserTenant)
                    .filter_by(user_id=user_id, tenant_id=tenant_id)
                    .first()
                )
                profile = None
                tenant_aliases: list[str] = []
                role_label = None
                preferred_email: str | None = None
                if ut:
                    profile = (
                        session.query(UserTenantProfile)
                        .filter_by(user_tenant_id=ut.id)
                        .first()
                    )
                    if profile:
                        display_name = profile.display_name
                        role_label = profile.role_label

                        if profile.preferred_contact_id:
                            pc = (
                                session.query(UserContact)
                                .filter_by(id=profile.preferred_contact_id)
                                .first()
                            )
                            if pc and pc.contact_type == "email":
                                preferred_email = pc.contact_value

                    # Tenant aliasy (active)
                    tenant_alias_rows = (
                        session.query(UserTenantAlias)
                        .filter_by(user_tenant_id=ut.id, status="active")
                        .order_by(UserTenantAlias.id.asc())
                        .all()
                    )
                    tenant_aliases = [a.alias_value for a in tenant_alias_rows]

                # Sestav tenant větu
                tenant_label = f"{tenant.tenant_name}, {tenant.tenant_type}"
                if display_name:
                    parts.append(
                        f"V kontextu tohoto tenantu ({tenant_label}) ho oslovuj jako '{display_name}'."
                    )
                else:
                    parts.append(f"V kontextu tohoto tenantu: {tenant_label}.")

                # Preferred email — pokud není v tenantu, fallback na primary
                if not preferred_email:
                    primary = (
                        session.query(UserContact)
                        .filter_by(user_id=user_id, contact_type="email", is_primary=True, status="active")
                        .first()
                    )
                    if primary is None:
                        primary = (
                            session.query(UserContact)
                            .filter_by(user_id=user_id, contact_type="email", status="active")
                            .first()
                        )
                    preferred_email = primary.contact_value if primary else None

                if preferred_email:
                    parts.append(f"Jeho preferovaný email v tomto tenantu je {preferred_email}.")

                # Tenant + globální aliasy (deduplikované, tenant má prioritu)
                global_alias_rows = (
                    session.query(UserAlias)
                    .filter_by(user_id=user_id, status="active")
                    .order_by(UserAlias.is_primary.desc(), UserAlias.id.asc())
                    .all()
                )
                global_aliases = [a.alias_value for a in global_alias_rows]
                # Aliasy bez display_name (to už říkáme jako 'oslovuj jako')
                seen = {(display_name or "").lower()}
                merged_aliases: list[str] = []
                for a in tenant_aliases + global_aliases:
                    key = a.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    merged_aliases.append(a)
                if merged_aliases:
                    parts.append(f"Další jeho aliasy: {', '.join(merged_aliases)}.")

                if role_label:
                    parts.append(f"Pracovní pozice: {role_label}.")
        else:
            # Bez tenantu — alespoň primary email + globální aliasy
            primary = (
                session.query(UserContact)
                .filter_by(user_id=user_id, contact_type="email", is_primary=True, status="active")
                .first()
            )
            if primary:
                parts.append(f"Jeho preferovaný email je {primary.contact_value}.")
            global_alias_rows = (
                session.query(UserAlias)
                .filter_by(user_id=user_id, status="active")
                .order_by(UserAlias.is_primary.desc(), UserAlias.id.asc())
                .all()
            )
            if global_alias_rows:
                parts.append(
                    "Aliasy: " + ", ".join(a.alias_value for a in global_alias_rows) + "."
                )

        # Aktivní projekt (uvnitř current tenantu) — informace pro AI o tom,
        # v jakém pracovním kontextu uživatel právě je. Ochrana: archivovaný
        # nebo cizí-tenantový projekt ignorujeme (vyrenderujeme "bez projektu").
        from modules.core.infrastructure.models_core import Project as _Project
        u_for_proj = session.query(User).filter_by(id=user_id).first()
        proj_pid = u_for_proj.last_active_project_id if u_for_proj else None
        if proj_pid:
            project = (
                session.query(_Project)
                .filter_by(id=proj_pid, is_active=True)
                .first()
            )
            if project and (tenant_id is None or project.tenant_id == tenant_id):
                parts.append(
                    f"Pracuje v rámci projektu '{project.name}'. "
                    f"Tenhle projektový kontext ber v úvahu při odpovědích a doporučeních."
                )
            else:
                parts.append("Aktuálně pracuje bez projektu (volné konverzace v tenantu).")
        else:
            parts.append("Aktuálně pracuje bez projektu (volné konverzace v tenantu).")

        return " ".join(parts)
    except Exception as e:
        logger.error(f"COMPOSER | user_context_block failed | user_id={user_id} | {e}")
        return None
    finally:
        session.close()


def _get_persona_prompt(conversation_id: int) -> str | None:
    """
    Načte personu podle active_agent_id konverzace.
    Pokud není nastavena, použije default personu.
    """
    data_session = get_data_session()
    try:
        conversation = data_session.query(Conversation).filter_by(id=conversation_id).first()
        active_agent_id = conversation.active_agent_id if conversation else None
    finally:
        data_session.close()

    core_session = get_core_session()
    try:
        if active_agent_id:
            persona = core_session.query(Persona).filter_by(id=active_agent_id).first()
        else:
            persona = core_session.query(Persona).filter_by(is_default=True).first()
        return persona.system_prompt if persona else None
    finally:
        core_session.close()


def _get_latest_summary(conversation_id: int) -> ConversationSummary | None:
    session = get_data_session()
    try:
        return (
            session.query(ConversationSummary)
            .filter_by(conversation_id=conversation_id)
            .order_by(ConversationSummary.id.desc())
            .first()
        )
    finally:
        session.close()


def _get_messages(conversation_id: int, after_id: int | None = None) -> list[dict]:
    session = get_data_session()
    try:
        query = session.query(Message).filter_by(conversation_id=conversation_id)
        if after_id is not None:
            query = query.filter(Message.id > after_id)
        messages = query.order_by(Message.id.desc()).all()

        selected = []
        used_tokens = 0
        for msg in messages:
            tokens = _estimate_tokens(msg.content)
            if used_tokens + tokens > MAX_TOKENS:
                break
            selected.append({"role": msg.role, "content": msg.content})
            used_tokens += tokens

        selected.reverse()
        return selected
    finally:
        session.close()


def _get_conversation_context(conversation_id: int) -> tuple[int | None, int | None]:
    """
    Vrátí (user_id, tenant_id) pro danou konverzaci.

    Tenant fallback: pokud conversation.tenant_id chybí (např. konverzace
    založená před identity refactorem nebo bez explicitního tenant kontextu),
    použije se users.last_active_tenant_id.
    """
    data_session = get_data_session()
    try:
        conv = data_session.query(Conversation).filter_by(id=conversation_id).first()
        if not conv:
            return None, None
        user_id = conv.user_id
        tenant_id = conv.tenant_id
    finally:
        data_session.close()

    if tenant_id is None and user_id is not None:
        core_session = get_core_session()
        try:
            user = core_session.query(User).filter_by(id=user_id).first()
            if user and user.last_active_tenant_id:
                tenant_id = user.last_active_tenant_id
        finally:
            core_session.close()

    return user_id, tenant_id


def build_prompt(conversation_id: int) -> tuple[str, list[dict]]:
    """
    Vrátí (system_prompt, messages) pro LLM.

    Pořadí vrstev v system promptu (od obecného k specifickému):
      1. base system_prompt (z DB system_prompts)
      2. persona prompt (podle active_agent_id konverzace)
      3. USER CONTEXT block (kdo je přihlášený user, jak ho oslovovat,
         v jakém tenantu, preferovaný email, aliasy)

    Pak summary a messages jako dříve.
    """
    system_prompt = _get_system_prompt()

    persona_prompt = _get_persona_prompt(conversation_id)
    if persona_prompt:
        system_prompt = f"{system_prompt}\n\n{persona_prompt}"

    # USER CONTEXT block — identita přihlášeného usera a jeho tenantu.
    # Bere user_id a tenant_id přímo z konverzace.
    user_id, tenant_id = _get_conversation_context(conversation_id)
    user_ctx = build_user_context_block(user_id, tenant_id)
    if user_ctx:
        system_prompt = f"{system_prompt}\n\n[KONTEXT UŽIVATELE]\n{user_ctx}"

    summary = _get_latest_summary(conversation_id)
    after_id = summary.to_message_id if summary else None

    messages = _get_messages(conversation_id, after_id=after_id)

    if summary:
        messages = [
            {"role": "user", "content": f"[Shrnutí předchozí konverzace]: {summary.summary_text}"},
            {"role": "assistant", "content": "Rozumím, pokračujeme."},
        ] + messages

    return system_prompt, messages
