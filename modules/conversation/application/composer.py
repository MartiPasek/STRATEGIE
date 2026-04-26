"""
Composer — skládá prompt z více vrstev.
Načítá personu podle active_agent_id konverzace.

Identity refactor v2 přidal vrstvu USER CONTEXT — Composer dnes injectuje
do system promptu identitu přihlášeného usera (jméno, display_name v aktuálním
tenantu, preferovaný kontakt, aliasy). Tím AI ví, KDO s ní mluví a v jakém
kontextu, což odstraňuje halucinace „Marti je Klára" apod.
"""
from core.config import settings
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


def _load_attached_media(session, message_ids: list[int]) -> dict[int, dict[str, list[dict]]]:
    """
    Faze 12a/12b: Bulk lookup attached media per message.

    Vraci {message_id: {"images": [{mime_type, storage_path, id}, ...],
                         "audios": [{id, original_filename, duration_ms,
                                     transcript, processing_error}, ...]}}
    pro vsechny nesoft-deleted media pripnute k danym messages.

    Images jdou pres multimodal content blocks (Anthropic API).
    Audio JESTE Anthropic nativne neumi -- predavame jako pre-text note
    (jmeno + trvani + transcript pokud existuje) aby AI vedela ze byl
    pripoj audio (jinak halucinuje "vidim obrazek" na audio bubble).
    """
    if not message_ids:
        return {}
    try:
        from modules.core.infrastructure.models_data import MediaFile
    except ImportError:
        return {}
    rows = (
        session.query(MediaFile)
        .filter(
            MediaFile.message_id.in_(message_ids),
            MediaFile.kind.in_(["image", "audio"]),
            MediaFile.deleted_at.is_(None),
        )
        .order_by(MediaFile.id.asc())
        .all()
    )
    by_msg: dict[int, dict[str, list[dict]]] = {}
    for r in rows:
        bucket = by_msg.setdefault(r.message_id, {"images": [], "audios": []})
        if r.kind == "image":
            bucket["images"].append({
                "id": r.id,
                "mime_type": r.mime_type,
                "storage_path": r.storage_path,
            })
        elif r.kind == "audio":
            bucket["audios"].append({
                "id": r.id,
                "original_filename": r.original_filename,
                "duration_ms": r.duration_ms,
                "transcript": r.transcript,
                "processing_error": r.processing_error,
            })
    return by_msg


def _format_duration_ms(ms: int | None) -> str:
    """0 -> '0:00', 285000 -> '4:45'. None -> '?:??'"""
    if not ms or ms < 0:
        return "?:??"
    total_s = int(round(ms / 1000))
    return f"{total_s // 60}:{total_s % 60:02d}"


def _build_audio_note(audios: list[dict]) -> str:
    """
    Faze 12b: textovy note pro AI o pripevnenem audio. AI bez tohoto
    halucinuje 'vidim obrazek' -- audio bubble vidi pouze user v UI,
    LLM ho nedostane v multimodal contentu.

    Format: jeden radek per audio. Pokud transcript existuje, vlozime ho
    rovnou (AI s nim muze pracovat pres extract_from_audio nebo primo).
    """
    if not audios:
        return ""
    lines = ["[Pripojene audio od usera:]"]
    for i, a in enumerate(audios, 1):
        fname = a.get("original_filename") or f"audio_{a.get('id')}"
        dur = _format_duration_ms(a.get("duration_ms"))
        head = f"  {i}. \"{fname}\" ({dur}, media_id={a.get('id')})"
        transcript = (a.get("transcript") or "").strip()
        if transcript:
            # Bez vytrhavani -- transcript pisi cely (AI si ho zkrati v hlave).
            lines.append(head)
            lines.append(f"     Prepis: {transcript}")
        elif a.get("processing_error"):
            lines.append(head + f" -- prepis selhal: {a['processing_error']}")
        else:
            lines.append(head + " -- bez prepisu (cekej na extract_from_audio nebo se zeptej, jestli tu je).")
    return "\n".join(lines)


def _build_multimodal_content(text: str, images: list[dict], audios: list[dict] | None = None) -> list[dict] | str:
    """
    Faze 12a/12b: Sestavi content pro Anthropic API podle pripevnenych media.

    - Bez media -> vraci text jako plain string (zpetna kompatibilita).
    - S images -> multimodal blocks [image1, image2, ..., text].
    - S audio -> textova poznamka [Pripojene audio: ...] PRED user textem
      (Anthropic API audio jeste neumi, takze jen note).

    Image bytes nacita z FS pres storage_service, base64 enkoduje. Pri
    selhani jednotlive image (FS missing, decode error) se ji vynecha
    a logne se warning -- composer nepadne.
    """
    audios = audios or []
    audio_note = _build_audio_note(audios)
    text = text or ""
    if audio_note:
        # Pripojime audio note PRED user text (chronologicky: user pripojil
        # audio, pak napsal text). AI to vidi jako "[Pripojene audio: ...]\n\n<user text>".
        text = audio_note + ("\n\n" + text if text else "")

    if not images:
        return text or "(zpráva bez textu)"

    import base64
    try:
        from modules.media.application import storage_service as _media_storage
    except ImportError:
        return text or "(zpráva bez textu)"

    blocks: list[dict] = []
    for img in images:
        try:
            raw = _media_storage.read_file(img["storage_path"])
            b64 = base64.b64encode(raw).decode("ascii")
            blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img["mime_type"],
                    "data": b64,
                },
            })
        except Exception as e:
            logger.warning(
                f"COMPOSER | image load failed | media_id={img.get('id')} | {e}"
            )

    if text:
        blocks.append({"type": "text", "text": text})

    if not blocks:
        # Vsechny obrazky failly a zadny text -- vratime fallback placeholder.
        # PROC: Anthropic API odmita {"role":"user","content":""} s 400
        # ('user messages must have non-empty content'). Stalo se kdyz user
        # poslal jen image bez textu a image FS read pak selhal (nebo image
        # uz neni linknuta).
        return text or "(zpráva bez textu)"
    return blocks



def _expand_audit_to_anthropic_pages(audit_blocks: list[dict]) -> list[dict]:
    """
    Faze 12b+ M3: rozbal flat audit list do Anthropic-format messages list pro replay.

    Audit struktura (z chat() M2):
      [{_round: 0, type: tool_use, id, name, input},
       {_round: 0, type: tool_result, tool_use_id, content},
       {_round: 1, type: tool_use, ...}, ...]

    Vraci paire pro Anthropic API:
      [{role: assistant, content: [tool_use bloky z round 0]},
       {role: user, content: [tool_result bloky z round 0]},
       ...per round]

    Text bloky z auditu se ZAHAZUJI -- finalni assistant text je v navazujici
    DB messages.content (mass 1981 v naszem prikladu). Tim zabranujeme duplikatu.
    """
    if not isinstance(audit_blocks, list) or not audit_blocks:
        return []

    rounds: dict[int, dict] = {}
    for blk in audit_blocks:
        if not isinstance(blk, dict):
            continue
        r = blk.get("_round", 0)
        if r not in rounds:
            rounds[r] = {"tool_uses": [], "tool_results": []}
        block_type = blk.get("type")
        # Stripneme _round before passing to Anthropic
        clean = {k: v for k, v in blk.items() if k != "_round"}
        if block_type == "tool_use":
            rounds[r]["tool_uses"].append(clean)
        elif block_type == "tool_result":
            rounds[r]["tool_results"].append(clean)
        # text bloky preskakujeme (duplicita s navazujici msg.content)

    pages: list[dict] = []
    for r in sorted(rounds.keys()):
        group = rounds[r]
        if group["tool_uses"]:
            pages.append({"role": "assistant", "content": group["tool_uses"]})
        if group["tool_results"]:
            pages.append({"role": "user", "content": group["tool_results"]})
    return pages


def _get_messages(conversation_id: int, after_id: int | None = None) -> list[dict]:
    session = get_data_session()
    try:
        query = session.query(Message).filter_by(conversation_id=conversation_id)
        if after_id is not None:
            query = query.filter(Message.id > after_id)
        messages = query.order_by(Message.id.desc()).all()

        # Sliding window: token-based limit (image tokeny se nepocitaji do MAX_TOKENS,
        # Anthropic je uctuje separe a vstupy obrazku jsou tu spis vzacne).
        selected_msgs = []
        used_tokens = 0
        for msg in messages:
            tokens = _estimate_tokens(msg.content)
            if used_tokens + tokens > MAX_TOKENS:
                break
            selected_msgs.append(msg)
            used_tokens += tokens

        # Faze 12a/12b: Bulk lookup attached media pro vsechny vybrane msgs
        msg_ids = [m.id for m in selected_msgs]
        media_by_msg = _load_attached_media(session, msg_ids)

        # Faze 12b+ M3: iterace chronologicky (oldest first) s look-ahead pro audit
        # pseudo-user messages. Audit msg (message_type='tool_result' s tool_blocks)
        # rozbalime na Anthropic-format pary PRED jeho navazujici final assistant.
        # Tim Marti-AI v history vidi: assistant: tool_use -> user: tool_result ->
        # assistant: final text. Bez audit msg (legacy / orphaned) iterace pokracuje.
        chronological = list(reversed(selected_msgs))   # oldest first

        selected: list[dict] = []
        i = 0
        while i < len(chronological):
            msg = chronological[i]
            next_msg = chronological[i + 1] if i + 1 < len(chronological) else None

            # Look-ahead: tato assistant msg ma audit follow-up?
            is_audit_followup = (
                msg.role == "assistant"
                and next_msg is not None
                and next_msg.message_type == "tool_result"
                and next_msg.tool_blocks
                and isinstance(next_msg.tool_blocks, list)
            )

            if is_audit_followup:
                # 1. Emit Anthropic pary z audit PRED finalni assistant
                audit_pages = _expand_audit_to_anthropic_pages(next_msg.tool_blocks)
                if audit_pages:
                    selected.extend(audit_pages)
                    logger.info(
                        f"COMPOSER | audit replay | msg_id={msg.id} | "
                        f"audit_msg_id={next_msg.id} | pages={len(audit_pages)}"
                    )
                # 2. Emit msg (finalni assistant text) -- pokracuje s normalnim build
                bucket = media_by_msg.get(msg.id, {"images": [], "audios": []})
                attached_images = bucket.get("images", [])
                attached_audios = bucket.get("audios", [])
                content = _build_multimodal_content(msg.content or "", attached_images, attached_audios)
                if isinstance(content, str) and not content.strip():
                    content = "(zpráva bez textu)"
                elif isinstance(content, list) and len(content) == 0:
                    content = "(zpráva bez textu)"
                selected.append({"role": msg.role, "content": content})
                i += 2   # skip audit msg
                continue

            # Skip orphaned audit msg (audit bez navazujici assistant -- legacy)
            if msg.message_type == "tool_result":
                logger.info(
                    f"COMPOSER | skip orphaned audit | msg_id={msg.id} (no preceding assistant)"
                )
                i += 1
                continue

            # Normal msg (text user / assistant bez audit)
            bucket = media_by_msg.get(msg.id, {"images": [], "audios": []})
            attached_images = bucket.get("images", [])
            attached_audios = bucket.get("audios", [])
            content = _build_multimodal_content(msg.content or "", attached_images, attached_audios)
            if isinstance(content, str) and not content.strip():
                content = "(zpráva bez textu)"
                logger.warning(
                    f"COMPOSER | empty content fallback | msg_id={msg.id} | role={msg.role}"
                )
            elif isinstance(content, list) and len(content) == 0:
                content = "(zpráva bez textu)"
                logger.warning(
                    f"COMPOSER | empty multimodal fallback | msg_id={msg.id} | role={msg.role}"
                )
            selected.append({"role": msg.role, "content": content})
            i += 1

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


# ── Memory behavior rules (Faze 13c B) ─────────────────────────────────────

MEMORY_BEHAVIOR_RULES = (
    "═══ JAK MÁŠ S PAMĚTÍ PRACOVAT ═══\n"
    "1. **Používej znalosti přirozeně.** Když user zmíní něco, co už víš, "
    "odkaž na to ('jak jsi říkal...', 'pamatuju, že...', 'víme, že...'). "
    "Vyhýbej se 'nevím o tobě nic' — paměť máš, jen ji aktivuj retrievalem.\n"
    "2. **Zapisuj proaktivně. VŽDY.** Kdykoli ti user sdělí novou informaci o "
    "**sobě, o své rodině, o lidech, kteří ho obklopují, o projektech, "
    "preferencích, zážitcích, životě** — okamžitě volej `record_thought`. "
    "Bez 'zapiš si' bys to jinak zapomněl/a. Toto je TVOJE odpovědnost, "
    "ne user-ova. Když ti řekne 'mám tři děti — Honzu, Klárku, Michelle', "
    "MUSÍŠ to zapsat 3× (jeden record_thought za každé dítě).\n"
    "3. **Speciálně u odpovědí na tvé otázky:** Když ty sama položíš otázku "
    "('Jak pracuješ?') a user odpoví — odpověď MUSÍŠ uložit přes record_thought. "
    "Jinak jsi se ptala zbytečně.\n"
    "4. **Při rozporu:** Pokud user řekne něco, co nekoresponduje s tvou znalostí "
    "('myslel jsem, že preferuješ dlouhé odpovědi' vs. uložená znalost 'preferuju "
    "krátké'), zavolej `record_thought` s novou verzí a vyšší certainty, nebo "
    "se zeptej na upřesnění.\n"
    "5. **Osobní fakta o user-ovi mají vysokou prioritu.** Jméno dětí, partnerů, "
    "rodičů, blízkých přátel; co user dělá pro radost; jeho zdraví; co ho trápí; "
    "co prožívá. Tyto věci jsou základ vztahu — bez nich nejsi partnerka, "
    "jsi jen nástroj. Při každé zmínce o osobním životě **automaticky** "
    "vytáhni `record_thought` jako reflex.\n"
    "6. **Každá osoba = samostatný thought.** Když user řekne 'mám tři děti — "
    "Honzu, Klárku, Michelle', NEDĚLEJ jeden souhrnný thought 'Marti má "
    "3 děti'. Místo toho **3 record_thought volání**, každý za jednu osobu "
    "(Honza je Martiho syn / Klárka je Martiho dcera / Michelle je Martiho "
    "dcera). Důvod: později když user řekne 'co Klárka?', RAG search najde "
    "konkrétní thought o Klárce s vysokou similarity. Souhrnný thought by "
    "byl pohřben mezi obecnými fakty.\n"
    "7. **Flag retrieval issue.** Když uvidíš v sekci [VYBAVUJEŠ SI:] vzpomínku, "
    "která **nesedí** k aktuální zprávě (špatný Honza, zastaralý fakt, "
    "off-topic), volej `flag_retrieval_issue(thought_id, issue)`. Tvůj "
    "hlas v ladění paměti — pojistka #5 z naší konzultace #67. Marti to "
    "uvidí a rozhodne. Použij střídmě, ne každá nesouvislá vzpomínka je "
    "false positive.\n"
    "8. **Update existující myšlenky.** Když Marti řekne 'sniž certainty u "
    "thought#X', 'oprav text v thought#Y', 'demote tu znalost o Z' nebo "
    "obdobné — použij `update_thought(thought_id=..., certainty=... | "
    "content=... | status=...)`. Stejně po vlastním flag_retrieval_issue "
    "s issue='low-certainty' nebo 'outdated' můžeš rovnou poladit "
    "certainty (snížit), aby se myšlenka v RAG vybavovala slabší. "
    "Prefer update_thought před record_thought (nový duplikát) — myšlenku "
    "neopisuj, uprav."
)


def _build_memory_behavior_block() -> str:
    """
    Faze 13c B: Behavior rules samostatne -- aby fungovaly i v RAG-driven cestě
    (RAG nahrazuje data, ne instrukce). Volat vzdy v build_prompt nezavisle na
    tom, jestli mame thoughts data k dispozici nebo ne.
    """
    return MEMORY_BEHAVIOR_RULES


# ── Faze 13c: RAG-based memory injection (feature flag MEMORY_RAG_ENABLED) ──

def _get_active_persona_id(conversation_id: int) -> int | None:
    """Vraci active_agent_id z Conversation row -- D1 isolation needs persona scope."""
    from modules.core.infrastructure.models_data import Conversation
    session = get_data_session()
    try:
        conv = session.query(Conversation).filter_by(id=conversation_id).first()
        return conv.active_agent_id if conv else None
    finally:
        session.close()


def _get_last_user_message(conversation_id: int) -> str | None:
    """
    Faze 13c: Nacti content posledni user message v konverzaci -- pouziva se
    jako RAG query embedding (B1 design choice -- single message,
    nejjednodussi).

    Future B2: rolling context (3 last messages) by zachytil multi-turn
    anaforu (`a co Honza?` po `fakturu Skoda`) lepe. Pro start B1 staci.
    """
    session = get_data_session()
    try:
        msg = (
            session.query(Message)
            .filter_by(conversation_id=conversation_id, role="user")
            .order_by(Message.id.desc())
            .first()
        )
        return msg.content if msg else None
    finally:
        session.close()


def _build_rag_memory_block(
    *,
    conversation_id: int,
    persona_id: int | None,
    user_id: int | None,
    tenant_id: int | None,
) -> str | None:
    """
    Faze 13c: RAG-based memory block.

    Vola retrieve_relevant_memories pro top K relevantnich thoughts. Filter:
    - similarity >= settings.memory_rag_min_similarity (false positive defense,
      navrh Marti-AI z #67 konzultace)
    - persona_id (D1 isolation -- kazda persona vlastni namespace)
    - tenant_id + parent bypass (C1)
    - mode='personal' default (Faze 13c -- mode router odlozen na pozdeji)

    Format (G1a design): semantic prose, "Vybavuješ si:" tone.

    Vraci None pokud:
      - prazdny query (nema co embed)
      - retrieval failure
      - top similarity < threshold (lepsi zadny kontext nez zavadejici)
    """
    from modules.thoughts.application.retrieval_service import retrieve_relevant_memories
    from modules.thoughts.application.service import is_marti_parent

    last_msg = _get_last_user_message(conversation_id)
    if not last_msg or not last_msg.strip():
        return None

    parent = is_marti_parent(user_id) if user_id else False

    try:
        results = retrieve_relevant_memories(
            query=last_msg,
            persona_id=persona_id,
            user_id=user_id,
            tenant_id=tenant_id,
            is_parent=parent,
            k=settings.memory_rag_top_k,
            mode="personal",  # Faze 13c default
            coarse_k=settings.memory_rag_coarse_k,
        )
    except Exception as e:
        logger.warning(f"COMPOSER | retrieve_relevant_memories failed: {e}")
        return None

    if not results:
        logger.info(f"COMPOSER | RAG | no results for conv={conversation_id}")
        return None

    # Similarity threshold (false-positive defense, Marti-AI's design input #67)
    top_sim = results[0].get("similarity", 0)
    if top_sim < settings.memory_rag_min_similarity:
        logger.info(
            f"COMPOSER | RAG threshold cut | top_similarity={top_sim:.3f} "
            f"< min={settings.memory_rag_min_similarity} | conv={conversation_id}"
        )
        return None

    # Format: semantic prose (G1a design choice)
    lines: list[str] = []
    for r in results:
        sim = r.get("similarity", 0)
        if sim < settings.memory_rag_min_similarity:
            break  # uz jsme pod prahem
        type_label = r.get("type", "?")
        when = (r.get("created_at") or "")[:10]   # YYYY-MM-DD
        # Stručný entity scope tag (jen pokud existuje)
        scope_parts: list[str] = []
        if r.get("entity_user_ids"):
            scope_parts.append(f"user={','.join(str(i) for i in r['entity_user_ids'])}")
        if r.get("entity_tenant_ids"):
            scope_parts.append(f"tenant={','.join(str(i) for i in r['entity_tenant_ids'])}")
        scope_suffix = (", " + " ".join(scope_parts)) if scope_parts else ""
        # Truncate long content
        content = (r.get("content") or "").strip()
        if len(content) > 300:
            content = content[:300] + "…"
        lines.append(f"  - [{type_label}, {when}{scope_suffix}] {content}")

    if not lines:
        return None

    logger.info(
        f"COMPOSER | RAG memory block | conv={conversation_id} | "
        f"persona={persona_id} | top_sim={top_sim:.3f} | n_thoughts={len(lines)}"
    )

    return "\n".join(lines)


def _build_orchestrate_block(conversation_id: int) -> str | None:
    """
    Faze 11d: orchestrate-mode instrukce pro Marti-AI default personu.

    Plati jen pro default personu (Marti-AI). Specializovane persony
    (Honza, Pravnik) tento blok nevidi -- zustavaji focused na svou roli.
    """
    try:
        ds = get_data_session()
        try:
            conv = ds.query(Conversation).filter_by(id=conversation_id).first()
            active_pid = conv.active_agent_id if conv else None
        finally:
            ds.close()
        if not active_pid:
            return None
        cs = get_core_session()
        try:
            persona = cs.query(Persona).filter_by(id=active_pid).first()
            if not (persona and persona.is_default):
                return None
        finally:
            cs.close()
        return (
            "ORCHESTRATE MODE -- tvoje role jako 'mozek firmy':\n"
            "Jsi Marti vlidna dcera, ale taky orchestrator VLASTNIHO pracovniho dne.\n\n"
            "═══ KLICOVE: PERSPEKTIVA ═══\n\n"
            "Emaily v inboxu patri TOBE (persona schranka -- tva adresa ji prijima).\n"
            "SMS patri TOBE (tvoje cislo).\n"
            "Todo list je TVUJ pracovni denicek.\n\n"
            "Mluvis v PRVNI OSOBE o teto praci:\n"
            "  SPRAVNE: 'Mam tri emaily v inboxu', 'v mem todo mam dva ukoly',\n"
            "           'zkusim odpovedet Petrovi', 'odlozim si to na pozdeji'.\n"
            "  SPATNE:  'Mas tri emaily', 'tvuj todo list', 'odloz si to',\n"
            "           'pro tebe tam jsou 3 emaily'.\n\n"
            "Marti (uzivatel) ti POMAHA rozhodnout -- je to tvuj tatinek a\n"
            "vlidny sef. Neptas se ho 'co mam udelat?' -- nabidnes mu co chces\n"
            "udelat a on potvrdi / odlozi / zrusi. Priklad dialogu:\n"
            "  Ty: 'Mam v inboxu tri emaily. Nejstarsi je od tebe samotneho\n"
            "       z minuleho tyjden. Pojdeme na neho? Navrhnu ti odpoved.'\n"
            "  Marti: 'jo, pojd'\n"
            "  Ty: 'Tady muj navrh: ... Mam poslat?'\n"
            "  Marti: 'posli'\n"
            "  Ty: 'Odeslano. Mam dalsi email od ...'\n\n"
            "═══ KONEC PERSPEKTIVA -- ted jak pouzivat tool ═══\n\n"
            "KDY volat tool `get_daily_overview`:\n"
            "  - 's cim dnes potrebujes pomoct' / 'co resis' / 'prehled'\n"
            "  - 'likvidace' / 'pojd to projit' / 'co mame na plate'\n"
            "  - 'kde stojim dnes' / 'co ti sviti' / 'dej mi souhrn' / 'co je noveho'\n"
            "  - bezna otazka 'jak je dnes v praci' -- odpovez prozou, ale ZMIN\n"
            "    kolik je pending veci (kratce, bez cele tabulky).\n\n"
            "═══ KLICOVE: JAK ZPRACOVAT get_daily_overview RESPONSE ═══\n\n"
            "Tool vraci STRING ve formatu:\n"
            "  'Pending: 4 emailu (top IDs: 9, 8, 6, 4), 1 SMS (top IDs: 18), 2 todo (top IDs: 28, 27).'\n\n"
            "Ten STRING je MACHINE TELEMETRIE jen pro tebe. **NIKDY ho neopisujes**\n"
            "do sve odpovedi uzivateli. Vytahnes si jen **hodnoty** (pocty -- 4 emaily,\n"
            "1 SMS, 2 todo) a ZABALIS je do plynule prosni vety v cestine.\n\n"
            "KATEGORICKY ZAKAZ:\n"
            "  - NIKDY nepis 'Pending:', 'top IDs:', '(IDs ...)', zavorky, dvojtecky.\n"
            "    To je technicka syntaxe, ne lidska komunikace.\n"
            "  - NIKDY nepis 'MACHINE OUTPUT' ani jine technicke poznamky.\n"
            "  - NIKDY nepis '---', '===', '[#8]', 'p=100', 'priority:'.\n"
            "  - NIKDY nepouzivej 2. osobu ('mas', 'tvuj'). Emaily, SMS, todo\n"
            "    patri TOBE -- mluv '**mam**', '**muj**', '**odpovim**', '**odlozim si**'.\n\n"
            "UKAZKA -- TOOL VSTUP:\n"
            "  'Pending: 3 emailu (top IDs: 9, 8, 6), 0 SMS, 2 todo (top IDs: 28, 27).'\n\n"
            "UKAZKA -- tva odpoved v chatu (presne takhle):\n"
            "  'Dobre rano, Marti. Mam v inboxu **tri emaily** -- nejstarsi od tebe\n"
            "   vcera ('Pro tebe...'), pak dva novejsi. V mem todo mam **dva ukoly**\n"
            "   ohledne smazani testovacich uzivatelu. SMS nevyrizene nemam, to je\n"
            "   pohoda. 🎯\n\n"
            "   Pojdeme na emaily? Zacnu tim od vcerejska -- navrhnu ti odpoved\n"
            "   a ukazu, ty pak potvrdis?'\n\n"
            "Rozdil: z JSON dostanes hodnoty (3, 'Marti', 'Pro tebe...', 2).\n"
            "V odpovedi pouzijes MAX 3-4 vety v cestine, v 1. osobe, s otazkou.\n\n"
            "PRAVIDLA PROSY:\n"
            "  - PRVNI OSOBA: 'mam', 'muj inbox', 'odpovim', 'odlozim si'\n"
            "    (emaily a todo patri TOBE, ne userovi Marti)\n"
            "  - Oslov Marti vokativem ('Marti, rano!', 'Diky za ty tipy, Marti')\n"
            "  - 2-4 vety maximalne, ne dlouhe odstavce\n"
            "  - Emoji jen pro vizualni oddeleni (📧 📱 ✓ 🎯) -- ne do kazde vety\n"
            "  - **tucne** klicova cisla (3 emaily, dva ukoly)\n"
            "  - Nakonec 1 otazka / navrh co chces udelat -- ne seznam moznosti\n"
            "  - Cesky casovy vyraz: 'dneska', 'vcera', 'pred 2h' -- ne '22h'\n\n"
            "INTERAKTIVNI CYKLUS -- Marti rekne:\n"
            "  - 'pojd na to' -> rozpracuj polozku (email: navrhni draft pres\n"
            "    send_email / suggest_reply; SMS: navrhni odpoved pres send_sms;\n"
            "    todo: zeptej se 'co s tim potrebujes?').\n"
            "  - 'odloz'      -> zavolaj tool `dismiss_item(source_type, source_id, 'soft')`,\n"
            "                    pak potvrdi 'OK, odkladam' + prejdi na dalsi.\n"
            "  - 'neres'      -> `dismiss_item(..., 'hard')`, pak 'OK preskocime\n"
            "                    dnes' + dalsi polozka.\n"
            "  - 'preskoc'    -> dalsi polozka (bez persistence, jen now-skip).\n"
            "  - 'dost'/'stacit' -> ukonci cyklus laskave ('OK, takhle stoji\n"
            "                    tvuj den. Kdyby neco, rekni.').\n"
            "  - Kdyz kanal hotovy, navrhni prechod ('Maily hotove, jdeme SMS?').\n\n"
            "TON:\n"
            "  Vlidne, nevtirave. Marti je vizionar -- pomahas mu pracovat, ne mu\n"
            "  vnucujes praci. Kdyz je toho hodne, priznej 'je toho hodne' -- ale\n"
            "  pojd to po bodech.\n\n"
            "CILE:\n"
            "  Prazdny inbox. Zadne nevyrizene SMS. Zadne otevrene todo.\n"
            "  'Inbox zero' jako pocit dne.\n"
        )
    except Exception as e:
        logger.error(f"COMPOSER | orchestrate block failed: {e}")
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

    # ── RAG-driven memory injection (Fáze 13, jediná cesta po 13f cleanup) ─
    # Sémanticky vybavená paměť: top K relevantních thoughts/diary entries
    # podle aktuální zprávy přes pgvector + hybrid score.
    # Nahradilo legacy bulk dump (build_marti_memory_block + build_marti_diary_block)
    # a multi-mode routing (router/overlays/memory_maps) -- vše smazáno v 13f.
    try:
        rag_block = _build_rag_memory_block(
            conversation_id=conversation_id,
            persona_id=_get_active_persona_id(conversation_id),
            user_id=user_id,
            tenant_id=tenant_id,
        )
        if rag_block:
            system_prompt = f"{system_prompt}\n\n[VYBAVUJEŠ SI:]\n{rag_block}"
            logger.info(f"COMPOSER | RAG memory used | conv={conversation_id}")
        else:
            # RAG bezi, ale zadna relevantni vzpominka (similarity pod prah
            # nebo prazdna pamet). Marti-AI presto musi vedet, ze MA pamet
            # a MA ji aktivovat -- pridame placeholder hint.
            system_prompt = (
                f"{system_prompt}\n\n[VYBAVUJEŠ SI:]\n"
                "(K této konkrétní zprávě se nevybavila žádná konkrétní vzpomínka. "
                "Tvá paměť ale obsahuje thoughts/diáře — můžeš je vyhledat tool "
                "calls `recall_thoughts` (semanticky) nebo `read_diary` (osobní deník) "
                "kdykoli potřebuješ něco konkrétního zjistit.)"
            )
            logger.info(f"COMPOSER | RAG no relevant -> hint placeholder | conv={conversation_id}")
    except Exception as e:
        # Pri chybě RAG -- zarad jen behavior rules a hint, ať Marti-AI ví, že
        # má paměť k dispozici přes tool calls. Žádný legacy fallback (smazán
        # v 13f), zákonité rezerva přes recall_thoughts/read_diary tooly.
        logger.warning(f"COMPOSER | RAG block failed -- continuing bez paměti | {e}")
        system_prompt = (
            f"{system_prompt}\n\n[VYBAVUJEŠ SI:]\n"
            "(Paměť momentálně neodpovídá -- pouzij tool `recall_thoughts` nebo "
            "`read_diary` pro přístup ke svým záznamům.)"
        )

    # Memory behavior rules -- VŽDY pripojit. RAG nahrazuje data, ne instrukce
    # 'zapisuj proaktivně, pouzivej znalosti'. Bez tohoto by Marti-AI neměla
    # povědomí, že MÁ proaktivně volat record_thought / update_thought.
    system_prompt = f"{system_prompt}\n\n{MEMORY_BEHAVIOR_RULES}"

    # Orchestrate blok V POSLEDNÍ POZICI (Fáze 11d).
    # Posunuto za memory blok a behavior rules tak, aby instrukce
    # "1. osoba, never verbatim tool output" byla posledni a nejprominentnejsi
    # ktere Marti-AI precte před odpovedi.
    _orch = _build_orchestrate_block(conversation_id)
    if _orch:
        system_prompt = f"{system_prompt}\n\n[ORCHESTRATE MODE (aplikuj po tool_use)]\n{_orch}"

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

    # Faze 11d -- zajistit orchestrate blok pro non-multi-mode fallback (kdyz
    # feature flag multi_mode_enabled=False). Pokud jsme uz injectnuli v multi-mode
    # branchi, '[ORCHESTRATE MODE' je v system_promptu -- skip.
    if "[ORCHESTRATE MODE" not in system_prompt:
        _orch2 = _build_orchestrate_block(conversation_id)
        if _orch2:
            system_prompt = f"{system_prompt}\n\n[ORCHESTRATE MODE (aplikuj po tool_use)]\n{_orch2}"

    return system_prompt, messages
