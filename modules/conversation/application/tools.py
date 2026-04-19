"""
Execution layer — nástroje dostupné pro AI asistenta.
Každý uživatel má svůj vlastní chat. Žádné sdílené konverzace.
"""

TOOLS = [
    {
        "name": "send_email",
        "description": (
            "Tento nástroj MUSÍŠ použít vždy když uživatel chce poslat email. "
            "NIKDY neodpovídej textem o emailu — vždy zavolej tento nástroj. "
            "Nástroj email NEPOŠLE — nejprve ukáže návrh uživateli a počká na potvrzení. "
            "\n\nÚPRAVY EMAILU: Pokud uživatel chce email upravit, změnit, dodat tam něco, "
            "smazat část, atd. (např. 'uprav', 'změň', 'dodej', 'smaž', 'doplň', "
            "'přidej tam'), MUSÍŠ tento nástroj zavolat ZNOVU s kompletním novým body. "
            "NIKDY nepiš upravený návrh emailu jen jako text ve své odpovědi — "
            "systém si ukládá jen obsah z volání nástroje a pokud nevoláš, "
            "odešle se stará verze. Toto je kritické pravidlo."
            "\n\nADRESA PŘÍJEMCE: NIKDY si nevymýšlej email adresu ('marti@email.com', "
            "'jan.novak@example.com' apod.). Pokud uživatel uvede jen jméno osoby a NENÍ zřejmé "
            "jakou má email adresu, NEJPRVE zavolej `find_user` tool. Pokud find_user nenajde "
            "nebo uživatel explicitně uvedl jinou adresu, použij tu. "
            "Když si nejsi jistý, ZEPTEJ SE uživatele na email adresu, NIKDY ji nevymýšlej."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Email adresa příjemce"},
                "subject": {"type": "string", "description": "Předmět emailu"},
                "body": {"type": "string", "description": "Tělo emailu"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "find_user",
        "description": (
            "Použij tento nástroj když uživatel chce kontaktovat nebo se spojit s jiným člověkem. "
            "Nástroj prohledá systém podle jména nebo emailu."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Jméno nebo email hledané osoby"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "invite_user",
        "description": (
            "Použij tento nástroj když uživatel chce pozvat někoho do systému STRATEGIE. "
            "Pošle pozvánkový email s odkazem pro vstup do systému."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email adresa pozvaného"},
                "name": {"type": "string", "description": "Jméno pozvaného (volitelné)"},
            },
            "required": ["email"],
        },
    },
    {
        "name": "switch_persona",
        "description": (
            "Tento nástroj MUSÍŠ použít VŽDY, když uživatel chce přepnout na jinou osobu / personu / agenta. "
            "NIKDY neodpovídej textem ve smyslu 'přepnul jsem', 'už mluvíš s X', 'jsem X', 'jsem zpátky' — "
            "vždy nejdřív zavolej tento nástroj. Systém sám v DB změní aktivní personu "
            "a vrátí potvrzovací hlášku; tvoje vlastní text NENÍ potvrzení přepnutí. "
            "Spouštěč: jakákoli varianta 'přepni na X', 'chci X', 'spoj mě s X', "
            "'mluv jako X', 'dej mi X', 'potřebuju X'. "
            "Pokud si nejsi jistý, zda už personou jsi, přesto VOLEJ nástroj — je idempotentní."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Jméno nebo role osoby na kterou chce přepnout (např. 'Marti', 'Klára', 'Ondra')"},
            },
            "required": ["query"],
        },
    },
]


def _is_email_in_system(email: str) -> bool:
    """
    True, pokud adresa patří aktivnímu uživateli systému (v user_contacts).
    Kontrola proti halucinované adrese — uživatel je okamžitě varován
    v preview, že AI mohla vymyslet cílovou adresu.
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User, UserContact

    needle = (email or "").strip().lower()
    if not needle:
        return False
    session = get_core_session()
    try:
        contact = (
            session.query(UserContact)
            .filter(
                UserContact.contact_type == "email",
                UserContact.contact_value.ilike(needle),
                UserContact.status == "active",
            )
            .first()
        )
        if not contact:
            return False
        user = session.query(User).filter_by(id=contact.user_id).first()
        return bool(user and user.status in ("active", "pending"))
    finally:
        session.close()


def format_email_preview(to: str, subject: str, body: str) -> str:
    # Varování pokud AI vygenerovala příjemce, který nikde v systému není —
    # typická známka halucinace nebo překlepu.
    try:
        in_system = _is_email_in_system(to)
    except Exception:
        in_system = False
    to_line = f"Komu: {to}"
    if not in_system:
        to_line += "   ⚠️ TATO ADRESA NENÍ V SYSTÉMU — OVĚŘ NEŽ POTVRDÍŠ"
    return (
        f"📧 Návrh emailu\n\n"
        f"{to_line}\n"
        f"Předmět: {subject}\n\n"
        f"{body}\n\n"
        f"---\n"
        f"Mohu email odeslat?"
    )


def find_user_in_system(query: str) -> dict:
    """
    Pozn.: Toto je „minimum-viable" verze pro Fázi 1 — najde prvního usera podle
    emailu nebo jména. Ve Fázi 5 se rozšíří o aliasy, multi-source search,
    list kandidátů a disambiguation.
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User, UserContact
    from sqlalchemy import or_

    session = get_core_session()
    try:
        query_lower = query.strip().lower()

        contact = (
            session.query(UserContact)
            .filter(
                UserContact.contact_type == "email",
                UserContact.contact_value.ilike(f"%{query_lower}%"),
                UserContact.status == "active",
            )
            .first()
        )

        if contact:
            user = session.query(User).filter_by(id=contact.user_id).first()
            if user:
                name = " ".join(filter(None, [user.first_name, user.last_name]))
                return {
                    "found": True,
                    "user_id": user.id,
                    "name": name or contact.contact_value,
                    "email": contact.contact_value,
                    "status": user.status,
                }

        users = session.query(User).filter(
            or_(
                User.first_name.ilike(f"%{query_lower}%"),
                User.last_name.ilike(f"%{query_lower}%"),
            )
        ).all()

        if users:
            user = users[0]
            primary_contact = (
                session.query(UserContact)
                .filter_by(user_id=user.id, contact_type="email", is_primary=True, status="active")
                .first()
            )
            name = " ".join(filter(None, [user.first_name, user.last_name]))
            return {
                "found": True,
                "user_id": user.id,
                "name": name,
                "email": primary_contact.contact_value if primary_contact else "",
                "status": user.status,
            }

        return {"found": False, "query": query}
    finally:
        session.close()


def invite_user_to_strategie(email: str, name: str | None, invited_by_user_id: int) -> dict:
    from modules.auth.application.invitation_service import create_invitation
    from modules.notifications.application.email_service import send_invitation_email
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User

    session = get_core_session()
    try:
        inviter = session.query(User).filter_by(id=invited_by_user_id).first()
        inviter_name = " ".join(filter(None, [inviter.first_name, inviter.last_name])) if inviter else "Člen týmu"
        tenant_id = inviter.last_active_tenant_id if inviter else 1
    finally:
        session.close()

    try:
        token = create_invitation(email=email.strip().lower(), invited_by_user_id=invited_by_user_id, tenant_id=tenant_id or 1)
        sent = send_invitation_email(to=email, invited_by=inviter_name, token=token)
        return {"success": True, "email": email, "email_sent": sent}
    except Exception as e:
        return {"success": False, "email": email, "error": str(e)}


def _strip_diacritics(s: str) -> str:
    """Převede 'Klára' → 'klara' pro accent-insensitive hledání."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def get_user_default_persona_name(user_id: int) -> str | None:
    """
    Vrátí název uživatelovy výchozí persony (digitálního dvojčete).

    Konvence: persona pojmenovaná podle first_name uživatele —
    např. Marti Pašek → persona 'Marti-AI', Klára Vlková → 'Klára-AI'.
    Hledání je accent-insensitive. Pokud nic nenajde, vrátí None.
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import Persona, User

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or not user.first_name:
            return None

        first_name_bare = _strip_diacritics(user.first_name)
        personas = session.query(Persona).all()

        # 1. preferuj personu, jejíž base-name (bez -AI) přesně odpovídá first_name
        for p in personas:
            base = _strip_diacritics(p.name).replace("-ai", "").strip()
            if base == first_name_bare:
                return p.name

        # 2. fallback: substring shoda v obou směrech
        for p in personas:
            base = _strip_diacritics(p.name).replace("-ai", "").strip()
            if first_name_bare and (first_name_bare in base or base in first_name_bare):
                return p.name

        return None
    finally:
        session.close()


def switch_persona_for_user(query: str, conversation_id: int) -> dict:
    """
    Přepne aktivní personu v konverzaci.
    Hledá personu podle jména v css_db.
    Hledání je case- a accent-insensitive ('klara' = 'Klára').
    Pokud nenajde personu, vrátí found=False.
    """
    from core.database_core import get_core_session
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_core import Persona
    from modules.core.infrastructure.models_data import Conversation

    query_lower = query.strip().lower()
    query_bare = _strip_diacritics(query_lower)

    # Hledej personu. Hledání je accent-insensitive + case-insensitive,
    # s obousměrným substringem a prefixovou shodou pro české pády.
    core_session = get_core_session()
    try:
        personas = core_session.query(Persona).all()

        # Předpočítej bare (bez diakritiky) názvy pro každou personu
        persona_keys = []
        for p in personas:
            name_bare = _strip_diacritics(p.name)
            base_bare = name_bare.replace("-ai", "").strip()
            persona_keys.append((p, name_bare, base_bare))

        matched = None

        # 1. krok: přesná shoda
        for p, name_bare, base_bare in persona_keys:
            if name_bare == query_bare or base_bare == query_bare:
                matched = p
                break

        # 2. krok: substring v obou směrech
        if matched is None:
            for p, name_bare, base_bare in persona_keys:
                if query_bare in name_bare or name_bare in query_bare:
                    matched = p
                    break
                if base_bare and (query_bare in base_bare or base_bare in query_bare):
                    matched = p
                    break

        # 3. krok: prefixová shoda na alespoň 4 znaky
        # (pokrývá české pády jako "Kláře"/"Kláru" → "Klára")
        if matched is None:
            for p, name_bare, base_bare in persona_keys:
                if not base_bare:
                    continue
                common = 0
                for a, b in zip(base_bare, query_bare):
                    if a == b:
                        common += 1
                    else:
                        break
                if common >= 4 and common >= min(len(base_bare), len(query_bare)) - 2:
                    matched = p
                    break

        if not matched:
            return {"found": False, "query": query}

        persona_id = matched.id
        persona_name = matched.name
    finally:
        core_session.close()

    # Aktualizuj active_persona_id v konverzaci
    data_session = get_data_session()
    try:
        conversation = data_session.query(Conversation).filter_by(id=conversation_id).first()
        if conversation:
            conversation.active_agent_id = persona_id
            data_session.commit()
        return {"found": True, "persona_id": persona_id, "persona_name": persona_name}
    finally:
        data_session.close()
