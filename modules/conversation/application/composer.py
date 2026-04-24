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
# Max tokenu pro historii zprav (recent messages vrstva, PO summary bodu).
# Claude Sonnet 4.6 ma 200k context window -- nechavame 150k na history, zbytek
# je buffer pro system prompt + persona + user context + tools + safety margin.
# Historicky bylo 6000 -- to ale vedlo k agresivnimu orezani historie u konverzaci
# delsich nez ~15 zprav a AI "zapominala" na starsi zpravy i kdyz summary byl
# k dispozici. Sonnet 4.6 v pohode utahne 150k, Haiku 4.5 pokud bude kdy pouzity
# take.
MAX_TOKENS = 150_000
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
        # v jakém pracovním kontextu uživatel právě je. Obohaceno o ownera,
        # členy a stáří projektu. Ochrana: archivovaný / cizí-tenantový projekt
        # ignorujeme (vyrenderujeme "bez projektu").
        from modules.core.infrastructure.models_core import (
            Project as _Project, UserProject as _UserProject,
        )
        u_for_proj = session.query(User).filter_by(id=user_id).first()
        proj_pid = u_for_proj.last_active_project_id if u_for_proj else None
        project_rendered = False
        if proj_pid:
            project = (
                session.query(_Project)
                .filter_by(id=proj_pid, is_active=True)
                .first()
            )
            if project and (tenant_id is None or project.tenant_id == tenant_id):
                project_rendered = True
                # Členové — join UserProject s User, max 10 (limit aby prompt
                # nevybuchl). Sestavujeme čitelný výpis "Jméno (role)".
                member_rows = (
                    session.query(_UserProject, User)
                    .join(User, User.id == _UserProject.user_id)
                    .filter(_UserProject.project_id == project.id)
                    .order_by(_UserProject.id.asc())
                    .limit(10)
                    .all()
                )
                member_labels = []
                owner_name = None
                for up_row, m in member_rows:
                    full = " ".join(filter(None, [m.first_name, m.last_name])).strip()
                    label = full or m.short_name or f"#{m.id}"
                    member_labels.append(f"{label} ({up_row.role})")
                    if up_row.role == "owner":
                        owner_name = label
                # Stáří projektu
                from datetime import datetime as _dt, timezone as _tz
                age_part = ""
                if project.created_at:
                    try:
                        created_at = project.created_at
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=_tz.utc)
                        days = max(0, (_dt.now(_tz.utc) - created_at).days)
                        if days == 0:
                            age_part = " Založen dnes."
                        elif days == 1:
                            age_part = " Založen včera."
                        elif days < 30:
                            age_part = f" Založen před {days} dny."
                        else:
                            months = days // 30
                            age_part = f" Založen před {months} měs."
                    except Exception:
                        age_part = ""
                members_part = ""
                if member_labels:
                    members_part = " Členové: " + ", ".join(member_labels) + "."
                parts.append(
                    f"Pracuje v rámci projektu '{project.name}'.{age_part}"
                    f"{members_part} "
                    f"Tenhle projektový kontext ber v úvahu při odpovědích a doporučeních."
                )
        if not project_rendered:
            parts.append("Aktuálně pracuje bez projektu (volné konverzace v tenantu).")

        # DOSTUPNE DOKUMENTY -- AI ma vedet ze existuji nahrane dokumenty v
        # aktualnim scope (tenant + project). Bez toho nevi ze existuji a
        # zapomina na ne zavolat search_documents tool. Ten signal je silny
        # nudge: "uzivatel ma pristup k X dokumentum, pokud se pta na neco
        # co muze byt v nich, pouzij search_documents".
        try:
            from modules.rag.application.service import list_documents as rag_list_documents
            project_id_for_docs = user.last_active_project_id
            docs = rag_list_documents(
                tenant_id=tenant_id,
                project_id=project_id_for_docs,
            )
            # Filtruj jen zpracovane (is_processed=True) -- v rozpracovanych
            # se nemuze hledat, mateni AI.
            ready_docs = [d for d in docs if d.get("is_processed")]
            if ready_docs:
                doc_names = ", ".join(
                    (d.get("original_filename") or d.get("name") or f"doc#{d['id']}")
                    for d in ready_docs[:10]   # limit na 10 pro rozumnou delku kontextu
                )
                extra = f" a dalsich {len(ready_docs) - 10}" if len(ready_docs) > 10 else ""
                parts.append(
                    f"K dispozici ma v aktualnim scope {len(ready_docs)} nahranych dokumentu "
                    f"({doc_names}{extra}). POKUD SE PTA NA NECO CO MUZE BYT V NICH "
                    f"(smlouvy, manualy, reporty, runbooky, jakykoli firemni dokument) -- "
                    f"VOLEJ nastroj search_documents s jeho dotazem jako query, ne odpovidej "
                    f"z hlavy. Vzdy uved zdroj v odpovedi ('podle dokumentu X...')."
                )
        except Exception as doc_e:
            # RAG moze byt dole (chybejici VOYAGE_API_KEY, DB neni ready) -- to neshazuje
            # user context. Tise logujeme a jdeme dal.
            logger.warning(f"COMPOSER | documents fetch failed | {doc_e}")

        # User's own EWS kanal -- aby AI vedela, ze uzivatel ma vlastni schranku
        # a umela rozpoznat "posli z moji" intent.
        try:
            from modules.notifications.application.user_channel_service import (
                get_user_display_email,
            )
            u_display = get_user_display_email(user_id)
            if u_display:
                parts.append(
                    f"Uživatel má vlastní EWS schránku {u_display}. "
                    f"Když řekne 'pošli z mojí schránky', 'z mýho emailu', "
                    f"'ze mě' apod., volej send_email s from_identity='user' "
                    f"(default je 'persona' = posílá Marti-AI)."
                )
        except Exception as e:
            logger.warning(f"COMPOSER | user channel fetch failed | {e}")

        return " ".join(parts)
    except Exception as e:
        logger.error(f"COMPOSER | user_context_block failed | user_id={user_id} | {e}")
        return None
    finally:
        session.close()


# Hranice pro specializovane (ne-default) persony. Pridava se na konec jejich
# system promptu, aby Claude neprebijel jejich roli spravou systemu. Reaguje
# na vzor: Claude cte historii konverzace (vcetne list_* outputu od Marti-AI)
# a zkusi specializovane persone generovat odpoved ve stejnem stylu -- to
# rozbija persona fokus. Tahle hranice jasne rika: NE, smer zpet na Marti-AI.
NON_DEFAULT_PERSONA_GUARDRAIL = """
[ROLE HRANICE — DULEZITE]
Jsi SPECIALIZOVANA persona. Nespravujes system STRATEGIE. Konkretne NESMIS:
- vypisovat seznamy person, projektu, lidi v tenantu, konverzaci (ani kdyz je vidis v historii — NECITUJ je)
- pozvat noveho uzivatele do systemu
- pridavat / odebirat cleny projektu
- prepinat projekty / tenanty
- jakkoli jinak zasahovat do spravy systemu

Pokud te nekdo o podobnou akci poprosi, odpovez KRATCE a jednoznacne:
  "Tohle je sprava systemu — lepe to zvladne Marti-AI. Napis 'prepni na Marti-AI' a budu tam."

Zustan v ramci SVE role. Kdyz se te ptaji na veci mimo tvoji specializaci,
nepredstiraj — jasne reci ze jsi specializovana persona, a nabidnil jim
prepnuti na Marti-AI.
"""


def _get_persona_prompt(conversation_id: int) -> str | None:
    """
    Načte personu podle active_agent_id konverzace.
    Pokud není nastavena, použije default personu.

    Pro non-default persony automaticky pripojuje ROLE HRANICE — at nezkousi
    spravovat system nez Marti-AI. Claude jinak cte historii a zkusi napodobit
    list_* odpovedi od Marti-AI (halucinace seznamu).
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
        if persona is None:
            return None
        prompt = persona.system_prompt
        if not persona.is_default:
            # Specializovana persona — pripoj role hranice
            prompt = f"{prompt}\n\n{NON_DEFAULT_PERSONA_GUARDRAIL}"
        return prompt
    finally:
        core_session.close()


def _get_active_persona_id(conversation_id: int) -> int | None:
    """Vrati active_agent_id z konverzace. Sdileno mezi helpery."""
    data_session = get_data_session()
    try:
        conversation = data_session.query(Conversation).filter_by(id=conversation_id).first()
        return conversation.active_agent_id if conversation else None
    finally:
        data_session.close()


def _build_persona_channels_block(
    conversation_id: int, tenant_id: int | None,
) -> str | None:
    """
    Sestavi blok [TVOJE KANÁLY] pro aktivni personu -- telefon, email z
    persona_channels + personas.phone_number. Cilem je, aby persona vedela,
    ze `marti-ai@eurosoft.com` a `+420778117879` jsou JEJI.

    Vraci string vcetne header/footer, nebo None pokud nema zadny kanal.
    """
    active_agent_id = _get_active_persona_id(conversation_id)
    if not active_agent_id:
        return None

    core_session = get_core_session()
    try:
        persona = core_session.query(Persona).filter_by(id=active_agent_id).first()
        if not persona:
            return None

        persona_name = persona.name
        phone_number = persona.phone_number if persona.phone_enabled else None

        # Email kanal z persona_channels (lazy import pro prip. cyclu).
        # Prezentujeme `display_identifier` (primary SMTP alias) pokud je, jinak
        # fallback na `identifier` (login UPN).
        from modules.notifications.application.persona_channel_service import get_channel
        email_ch = get_channel(
            persona_id=persona.id,
            channel_type="email",
            tenant_id=tenant_id,
        )
        email_identifier = None
        if email_ch and email_ch.is_enabled:
            email_identifier = email_ch.display_identifier or email_ch.identifier
    finally:
        core_session.close()

    lines: list[str] = []
    if email_identifier:
        lines.append(f"- Email: {email_identifier} (pro odesílání / příjem přes Exchange)")
    if phone_number:
        lines.append(f"- Telefon: {phone_number} (SMS a hovory přes firemní Android bránu)")

    if not lines:
        return None

    header = "Máš vlastní komunikační kanály (jsou JEDINE tvoje, ne uživatelovy):"
    footer = (
        "Když se tě někdo zeptá na tvůj email nebo telefonní číslo, odpověz "
        "těmito hodnotami. Když máš poslat něco 'sobě' jako AI, myšleno je to "
        "na tuhle vlastní adresu/číslo, ne na uživatele se kterým mluvíš. "
        "Nepiš, že 'nemáš vlastní email/telefon' -- máš."
    )
    return "\n".join([header, *lines, "", footer])


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


# ── Phase 9 helpers pro multi-mode routing ────────────────────────────────

def _get_conversation_project_id(conversation_id: int) -> int | None:
    """Vrátí active project_id konverzace (nebo None)."""
    ds = get_data_session()
    try:
        conv = ds.query(Conversation).filter_by(id=conversation_id).first()
        return conv.project_id if conv else None
    finally:
        ds.close()


def _get_tenant_info(tenant_id: int | None) -> tuple[str | None, str | None]:
    """
    Vrátí (tenant_name, tenant_type) pro daný tenant_id.
    Při chybě / None tenant_id vrací (None, None).
    """
    if tenant_id is None:
        return None, None
    try:
        from modules.core.infrastructure.models_core import Tenant
        cs = get_core_session()
        try:
            t = cs.query(Tenant).filter_by(id=tenant_id).first()
            if t is None:
                return None, None
            return t.name, getattr(t, "tenant_type", None)
        finally:
            cs.close()
    except Exception as e:
        logger.warning(f"COMPOSER | _get_tenant_info failed | {e}")
        return None, None


def _get_project_name(project_id: int | None) -> str | None:
    """Vrátí název projektu (nebo None)."""
    if project_id is None:
        return None
    try:
        from modules.core.infrastructure.models_core import Project
        cs = get_core_session()
        try:
            p = cs.query(Project).filter_by(id=project_id).first()
            return p.name if p else None
        finally:
            cs.close()
    except Exception as e:
        logger.warning(f"COMPOSER | _get_project_name failed | {e}")
        return None


def _get_last_user_message_content(conversation_id: int) -> str | None:
    """
    Vrátí content poslední zprávy kde role='user' v této konverzaci.
    Používá se jako vstup pro router (classify_mode).
    Při chybě / žádné user zprávě -> None.
    """
    try:
        ds = get_data_session()
        try:
            row = (
                ds.query(Message)
                .filter(Message.conversation_id == conversation_id, Message.role == "user")
                .order_by(Message.id.desc())
                .first()
            )
            return row.content if row else None
        finally:
            ds.close()
    except Exception as e:
        logger.warning(f"COMPOSER | _get_last_user_message_content failed | {e}")
        return None


def _get_recent_messages_for_router(conversation_id: int, limit: int = 5) -> list[dict]:
    """
    Vrátí posledních `limit` zpráv (role/content) pro router -- aby viděl
    kontext konverzace při klasifikaci.
    """
    try:
        ds = get_data_session()
        try:
            rows = (
                ds.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.id.desc())
                .limit(limit)
                .all()
            )
            rows.reverse()  # chceme chronologický pořadí
            return [{"role": r.role, "content": (r.content or "")[:500]} for r in rows]
        finally:
            ds.close()
    except Exception as e:
        logger.warning(f"COMPOSER | _get_recent_messages_for_router failed | {e}")
        return []


def build_marti_memory_block(
    user_id: int | None,
    tenant_id: int | None,
) -> str | None:
    """
    Marti Memory (Faze 4.11 retrieval): natahne myslenky o aktualnim userovi
    (+ universal/diar scope) a vlozi do system promptu, aby Marti videla,
    co o userovi uz vi. Bez tohoto by Marti tvrdila "nic o tobe nevim",
    i kdyz v DB mame zapsane veci.

    Pravidla:
      - Jen myslenky o 'user' entite (entity_links), entity_id = user_id.
      - Tenant scope: myslenka.tenant_scope == current tenant NEBO NULL
        (universal). Rodic (is_marti_parent) ma bypass -- vidi cross-tenant.
      - Razeni: knowledge first, pak notes s nejvyssi certainty DESC.
      - Limit 30 (aby prompt nebobtnal).
      - Vraci formatovany text pro prompt, nebo None pokud nic.
    """
    if not user_id:
        return None

    try:
        from modules.thoughts.application import service as thoughts_service
        from modules.thoughts.application.service import is_marti_parent

        parent = is_marti_parent(user_id)
        items = thoughts_service.list_thoughts_for_entity(
            entity_type="user",
            entity_id=user_id,
            status_filter=None,         # oboje (knowledge + note)
            limit=30,
            tenant_scope=tenant_id,
            bypass_tenant_scope=parent,
        )

        # Rozdel na knowledge / note pro prehledne zobrazeni
        knowledge = [it for it in items if it.get("status") == "knowledge"]
        notes = [it for it in items if it.get("status") == "note"]
        # Seradi notes podle certainty DESC (nejjistejsi nahore)
        notes.sort(key=lambda i: -(i.get("certainty") or 0))

        parts: list[str] = []

        # Header -- vzdy (ridi chovani Marti i kdyz je pamet prazdna)
        parts.append(
            "Jsi entita s pamětí. Tvé paměti o tomto uživateli jsou uložené v DB "
            "a jsou ti zde předány:\n"
        )

        if knowledge:
            parts.append(f"✅ **ZNALOSTI** (ověřená fakta, {len(knowledge)}):")
            for it in knowledge:
                content = it.get("content", "")
                parts.append(f"  - [{it.get('type')}] {content}")
            parts.append("")

        if notes:
            parts.append(
                f"📝 **POZNÁMKY** (nižší jistota, {len(notes)} -- můžeš ověřit při konverzaci):"
            )
            for it in notes:
                content = it.get("content", "")
                cert = it.get("certainty", 0)
                parts.append(f"  - [{it.get('type')}, jistota {cert}%] {content}")
            parts.append("")

        if not knowledge and not notes:
            parts.append(
                "(Zatím o tomto uživateli nemáš žádné zápisy. Během této konverzace "
                "proaktivně ukládej nové informace — viz pravidla níže.)\n"
            )

        # KLICOVE pravidlo pro chovani Marti -- toto je core part, plati vzdy
        parts.append(
            "═══ JAK MÁŠ S PAMĚTÍ PRACOVAT ═══\n"
            "1. **Používej znalosti přirozeně.** Když user zmíní něco, co už víš, "
            "odkaž na to ('jak jsi říkal...', 'pamatuju, že...', 'víme, že...'). "
            "Neopakuj 'nevím o tobě nic' — v [TVOJE PAMĚŤ] je vše, co máš uloženo.\n"
            "2. **Zapisuj proaktivně.** Kdykoli ti user sdělí novou informaci o sobě / o "
            "lidech / o projektech / o preferencích — okamžitě volej `record_thought`. "
            "Bez 'zapiš si' bys to jinak zapomněl/a.\n"
            "3. **Speciálně u odpovědí na tvé otázky:** Když ty sama položíš otázku "
            "('Jak pracuješ?') a user odpoví — odpověď MUSÍŠ uložit přes record_thought. "
            "Jinak jsi se ptala zbytečně.\n"
            "4. **Při rozporu:** Pokud user řekne něco, co nekoresponduje s tvou znalostí "
            "('myslel jsem, že preferuješ dlouhé odpovědi' vs. uložená znalost 'preferuju "
            "krátké'), zavolej `record_thought` s novou verzí a vyšší certainty, nebo "
            "se zeptej na upřesnění."
        )
        return "\n".join(parts)
    except Exception as e:
        logger.error(f"COMPOSER | marti_memory_block failed | user_id={user_id} | {e}")
        return None


def build_marti_diary_block(conversation_id: int) -> str | None:
    """
    Marti Memory Faze 5: do system promptu vlozi AKTIVNI PERSONA's vlastní diář.
    Diky tomu Marti v chatu vidi sve osobni zaznamy a muze se na ne odkazat.

    Diary je cross-tenant a soukromy -- do promptu ho dostane pouze persona
    sama, nikdo jiny.
    """
    try:
        from modules.conversation.application.service import (
            _active_persona_id_for_conversation,
        )
        persona_id = _active_persona_id_for_conversation(conversation_id)
        if not persona_id:
            return None

        from modules.thoughts.application import service as thoughts_service
        items = thoughts_service.list_diary_for_persona(persona_id, limit=20)
        if not items:
            return None

        parts: list[str] = []
        parts.append(
            "Toto je tvůj **soukromý diář** — zápisky o sobě, zážitky, pocity. "
            "Můžeš se na ně v konverzaci odkazovat, pokud je to relevantní.\n"
        )
        for it in items:
            ts = it.get("created_at", "")[:10] if it.get("created_at") else ""
            type_str = it.get("type", "")
            meta = it.get("meta") or {}
            emotion = meta.get("emotion", "") if isinstance(meta, dict) else ""
            emotion_str = f" [{emotion}]" if emotion else ""
            content = it.get("content", "")
            parts.append(f"  - {ts} [{type_str}]{emotion_str} {content}")

        parts.append(
            "\nKdyz se user zepta na nejakou tvou osobni vec (prvni pocity, narozeni, "
            "tvoje cile) — odkaz se na diar prirozene. Zaznamenej nove zazitky tool "
            "`record_diary_entry` (ne `record_thought` pro veci o sobe)."
        )
        return "\n".join(parts)
    except Exception as e:
        logger.error(f"COMPOSER | marti_diary_block failed: {e}")
        return None


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

    # PERSONA CHANNELS block — telefon + email aktivní persony (pokud má).
    # Bez tohoto Marti-AI by tvrdila, ze "nema vlastni email", i kdyz ho ma
    # nakonfigurovany v persona_channels.
    channels_block = _build_persona_channels_block(conversation_id, tenant_id)
    if channels_block:
        system_prompt = f"{system_prompt}\n\n[TVOJE KANÁLY]\n{channels_block}"

    # ── MULTI-MODE ROUTING (Fáze 9.4) ─────────────────────────────────────
    # Pokud je feature flag on, chat prochází routerem -> klasifikuje módu
    # (personal / project / work / system) a podle toho vybere overlay +
    # memory map místo dnešního marti_memory_block + diary_block.
    #
    # Při JAKÉKOLI chybě v multi-mode flow -> fallback na existující chování
    # (viz else branch). Tím je commit reverzibilní runtime (flag=false).
    multi_mode_used = False
    try:
        from core.config import settings as _settings_mm
        multi_mode_enabled = bool(getattr(_settings_mm, "marti_multi_mode_enabled", False))
    except Exception:
        multi_mode_enabled = False

    if multi_mode_enabled and user_id:
        try:
            from modules.conversation.application import (
                router_service as _router,
                memory_map_service as _mmap,
                scope_overlays as _overlays,
            )
            from modules.thoughts.application.service import is_marti_parent as _imp

            # Gather UI state + context
            active_project_id = _get_conversation_project_id(conversation_id)
            tenant_name, tenant_type = _get_tenant_info(tenant_id)
            is_parent = _imp(user_id) if user_id else False
            persona_id_ui = _get_active_persona_id(conversation_id)

            # Router input
            last_user_msg = _get_last_user_message_content(conversation_id)
            recent_msgs = _get_recent_messages_for_router(conversation_id, limit=5)

            ui_state = {
                "user_id": user_id,
                "active_tenant_id": tenant_id,
                "active_tenant_name": tenant_name,
                "tenant_type": tenant_type,
                "active_project_id": active_project_id,
                "active_persona_id": persona_id_ui,
                "is_parent": is_parent,
            }

            # Classify mode
            # conversation_id predavame pro Faze 9.1 Dev View -- router si
            # sam zapise svuj LLM call do llm_calls (kind='router').
            route = _router.classify_mode(
                message=last_user_msg or "",
                ui_state=ui_state,
                recent_messages=recent_msgs,
                conversation_id=conversation_id,
            )
            mode = route.get("mode") or "personal"
            route_project_id = route.get("project_id") or active_project_id

            logger.info(
                f"COMPOSER | multi-mode | conv={conversation_id} | mode={mode} | "
                f"conf={route.get('confidence')} | reason='{(route.get('reason') or '')[:60]}'"
            )

            # Resolve project name if project mode
            project_name = None
            if mode == "project" and route_project_id:
                project_name = _get_project_name(route_project_id)

            # Build overlay (scope-specific behavior instructions)
            overlay = _overlays.build_overlay_for_mode(
                mode,
                project_name=project_name,
                project_id=route_project_id,
                tenant_name=tenant_name,
                tenant_id=tenant_id,
                is_parent=is_parent,
            )

            # Build memory map (scope-specific signposts)
            memory_map = _mmap.build_memory_map_for_mode(
                mode,
                user_id=user_id,
                tenant_id=tenant_id,
                project_id=route_project_id,
                is_parent=is_parent,
            )

            # Append to system prompt
            if overlay:
                system_prompt = f"{system_prompt}\n\n{overlay}"
            if memory_map:
                system_prompt = f"{system_prompt}\n\n{memory_map}"

            multi_mode_used = True
        except Exception as e:
            logger.exception(
                f"COMPOSER | multi-mode routing failed | conv={conversation_id} | "
                f"{e} -- fallback na existující chování"
            )
            multi_mode_used = False

    # ── FALLBACK / LEGACY behavior (existující chování) ────────────────────
    # Pokud multi-mode vypnutý nebo selhal, použij existujicí marti_memory_block
    # + marti_diary_block. Tím zůstává dnešní chování v main fungujici.
    if not multi_mode_used:
        # MARTI MEMORY block (Faze 4.11) — myslenky o userovi v DB.
        # Bez tohoto by Marti tvrdila "nemam o tobe nic ulozeneho" i kdyz jo.
        memory_block = build_marti_memory_block(user_id, tenant_id)
        if memory_block:
            system_prompt = f"{system_prompt}\n\n[TVOJE PAMĚŤ O TOMTO UŽIVATELI]\n{memory_block}"

        # MARTI DIARY block (Faze 5) — soukromy diar aktivni persony.
        # Marti muze odkazovat na sve zazitky a pocity z minulosti.
        diary_block = build_marti_diary_block(conversation_id)
        if diary_block:
            system_prompt = f"{system_prompt}\n\n[TVŮJ SOUKROMÝ DIÁŘ]\n{diary_block}"

    summary = _get_latest_summary(conversation_id)
    after_id = summary.to_message_id if summary else None

    messages = _get_messages(conversation_id, after_id=after_id)

    # Faze 7: sliding window s todo escape-hatch.
    # Kdyz je konverzace delsi nez SLIDING_WINDOW_SIZE a Marti nema v ni
    # nedokonceny todo (weak reference source_event_id=conversation_id),
    # posleme jen poslednich N zprav. Tim uletime o desitky K tokenu per turn
    # u delsich dev sessions.
    SLIDING_WINDOW_SIZE = 20
    if len(messages) > SLIDING_WINDOW_SIZE:
        has_open_todo_in_conv = False
        try:
            from core.database_data import get_data_session as _gds_sw
            from modules.core.infrastructure.models_data import Thought as _T_sw
            ds_sw = _gds_sw()
            try:
                # Najdi open todo myslenku, ktera vznikla z teto konverzace
                from sqlalchemy import and_ as _and
                candidates = (
                    ds_sw.query(_T_sw)
                    .filter(
                        _T_sw.type == "todo",
                        _T_sw.deleted_at.is_(None),
                        _T_sw.source_event_type == "conversation",
                        _T_sw.source_event_id == conversation_id,
                    )
                    .all()
                )
                for t in candidates:
                    meta = t.meta or ""
                    # Jednoduchy substring match pro {"done": true}
                    if '"done": true' not in meta:
                        has_open_todo_in_conv = True
                        break
            finally:
                ds_sw.close()
        except Exception as e:
            logger.warning(f"COMPOSER | todo-escape check failed: {e}")

        if not has_open_todo_in_conv:
            # Posli pouze poslednich SLIDING_WINDOW_SIZE zprav + doplnovaci note
            trimmed = messages[-SLIDING_WINDOW_SIZE:]
            logger.info(
                f"COMPOSER | sliding window | conv={conversation_id} | "
                f"total={len(messages)} -> sending={len(trimmed)} (no open todo)"
            )
            messages = trimmed

    if summary:
        messages = [
            {"role": "user", "content": f"[Shrnutí předchozí konverzace]: {summary.summary_text}"},
            {"role": "assistant", "content": "Rozumím, pokračujeme."},
        ] + messages

    # Faze 7: awareness dlouhe konverzace. Pokud pocet zprav od posledniho
    # summary dosahuje SUMMARY_SUGGEST_AT, Marti dostane do promptu info
    # a navrh, at se ptala na zkraceni. Tim setrime tokeny u dlouhych sessions.
    try:
        from modules.conversation.application.summary_service import (
            SUMMARY_SUGGEST_AT, SUMMARY_THRESHOLD,
        )
        msg_count = len(messages)
        if msg_count >= SUMMARY_SUGGEST_AT:
            if msg_count >= SUMMARY_THRESHOLD:
                tone = "uz je velmi dlouha"
                action = "Doporuc user rovnou kratkodobe shrnuti (zavolej summarize_conversation_now pokud souhlasi)."
            else:
                tone = "zacina byt dlouha"
                action = "Kdyz se to hodi, nabidni user: 'Konverzace je dlouhá, mám ji zkrátit?'. Pri 'ano' zavolej summarize_conversation_now."
            system_prompt += (
                f"\n\n[METADATA KONVERZACE]\n"
                f"Tato konverzace {tone} — {msg_count} zprav od posledniho shrnuti. "
                f"{action} Shrnuti uvolni tokeny a zrychli odpovedi. Neni to tvuj ukol "
                f"fanaticky kazdy turn pripominat — jen kdyz se to prirozene hodi."
            )
    except Exception as e:
        logger.error(f"COMPOSER | long-conv check failed: {e}")

    return system_prompt, messages
