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


FIND_USER_MAX_CANDIDATES = 5


def find_user_in_system(query: str, requester_user_id: int | None = None) -> dict:
    """
    Multi-source search uživatele v aktuálním tenantu requestera.

    Hledá napříč:
      - users.first_name / last_name / short_name / legal_name
      - user_aliases (globální přezdívky)
      - user_tenant_aliases (jen v aktuálním tenantu requestera)
      - user_contacts (email / phone)

    Search: tokenizovaný, case + accent insensitive substring.
    Každý token musí matchnout ALESPOŇ jedno pole některé entity daného usera.

    Scope: jen aktivní členové aktuálního tenantu requestera.
    Pokud requester nemá tenant, vrací prázdný list.

    Vrací:
      {
        "found": bool,
        "candidates": [
          {
            "user_id": int,
            "full_name": str,
            "display_name": str | None,    # z user_tenant_profiles aktuálního tenantu
            "role_label": str | None,      # job role v aktuálním tenantu
            "preferred_email": str | None,
            "matched_via": str             # debug — jak jsme ho našli
          }, ...
        ],
        "total_matches": int,              # může být > len(candidates) když has_more
        "has_more": bool,                  # True pokud existují další za limitem
        "query": str,
      }
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import (
        User, UserAlias, UserContact, UserTenant,
        UserTenantProfile, UserTenantAlias,
    )

    query_clean = (query or "").strip()
    if not query_clean:
        return {"found": False, "candidates": [], "total_matches": 0, "has_more": False, "query": query}

    tokens = [t for t in query_clean.split() if t]
    if not tokens:
        return {"found": False, "candidates": [], "total_matches": 0, "has_more": False, "query": query}
    tokens_bare = [_strip_diacritics(t) for t in tokens]

    session = get_core_session()
    try:
        # Zjisti tenant requestera
        tenant_id: int | None = None
        if requester_user_id:
            req_user = session.query(User).filter_by(id=requester_user_id).first()
            if req_user:
                tenant_id = req_user.last_active_tenant_id
                if tenant_id is None:
                    ut = (
                        session.query(UserTenant)
                        .filter_by(user_id=requester_user_id, membership_status="active")
                        .order_by(UserTenant.id.asc())
                        .first()
                    )
                    if ut:
                        tenant_id = ut.tenant_id

        if tenant_id is None:
            return {
                "found": False, "candidates": [], "total_matches": 0,
                "has_more": False, "query": query,
            }

        # Aktivní členové tenantu (vč. requestera; on sebe může vyloučit ve volajícím)
        tenant_user_rows = (
            session.query(UserTenant)
            .filter_by(tenant_id=tenant_id, membership_status="active")
            .all()
        )
        tenant_user_ids = [ut.user_id for ut in tenant_user_rows]
        if not tenant_user_ids:
            return {
                "found": False, "candidates": [], "total_matches": 0,
                "has_more": False, "query": query,
            }
        # Mapa user_id → user_tenant_id (pro profil/aliasy)
        ut_by_user = {ut.user_id: ut.id for ut in tenant_user_rows}

        # Načti usery (jen active/pending — disabled je archiv)
        users = (
            session.query(User)
            .filter(User.id.in_(tenant_user_ids), User.status.in_(("active", "pending")))
            .all()
        )

        # Načti všechny vyhledávací pole pro daný set userů
        global_aliases = (
            session.query(UserAlias)
            .filter(UserAlias.user_id.in_(tenant_user_ids), UserAlias.status == "active")
            .all()
        )
        global_aliases_by_user: dict[int, list[str]] = {}
        for a in global_aliases:
            global_aliases_by_user.setdefault(a.user_id, []).append(a.alias_value)

        ut_ids = list(ut_by_user.values())
        tenant_aliases = (
            session.query(UserTenantAlias)
            .filter(UserTenantAlias.user_tenant_id.in_(ut_ids), UserTenantAlias.status == "active")
            .all()
            if ut_ids else []
        )
        tenant_aliases_by_ut: dict[int, list[str]] = {}
        for a in tenant_aliases:
            tenant_aliases_by_ut.setdefault(a.user_tenant_id, []).append(a.alias_value)

        contacts = (
            session.query(UserContact)
            .filter(UserContact.user_id.in_(tenant_user_ids), UserContact.status == "active")
            .all()
        )
        emails_by_user: dict[int, str] = {}
        all_contact_values_by_user: dict[int, list[str]] = {}
        for c in contacts:
            all_contact_values_by_user.setdefault(c.user_id, []).append(c.contact_value)
            if c.contact_type == "email":
                if c.is_primary or c.user_id not in emails_by_user:
                    emails_by_user[c.user_id] = c.contact_value

        # Profile (display_name, role_label) pro tenant
        profiles = (
            session.query(UserTenantProfile)
            .filter(UserTenantProfile.user_tenant_id.in_(ut_ids))
            .all()
            if ut_ids else []
        )
        profile_by_ut = {p.user_tenant_id: p for p in profiles}

        # Postupně skóruj všechny usery
        matches: list[dict] = []
        for user in users:
            ut_id = ut_by_user.get(user.id)
            profile = profile_by_ut.get(ut_id) if ut_id else None
            display_name = profile.display_name if profile else None

            # Sber všechna search-pole
            name_fields = [
                user.first_name, user.last_name, user.short_name, user.legal_name,
                display_name,
            ]
            name_fields = [f for f in name_fields if f]
            g_aliases = global_aliases_by_user.get(user.id, [])
            t_aliases = tenant_aliases_by_ut.get(ut_id, []) if ut_id else []
            user_contact_values = all_contact_values_by_user.get(user.id, [])

            all_searchable = name_fields + g_aliases + t_aliases + user_contact_values
            all_bare = [_strip_diacritics(s) for s in all_searchable]

            # Každý token musí matchnout aspoň jedno pole
            def _matches() -> tuple[bool, str]:
                hit_field = ""
                for tok_bare in tokens_bare:
                    found_in = None
                    for orig, bare in zip(all_searchable, all_bare):
                        if tok_bare in bare:
                            found_in = orig
                            break
                    if found_in is None:
                        return False, ""
                    if not hit_field:
                        hit_field = found_in
                return True, hit_field

            ok, matched_field = _matches()
            if not ok:
                continue

            # Sestav výsledek
            full_name = " ".join(filter(None, [user.first_name, user.last_name])).strip() or user.legal_name or f"User #{user.id}"
            matches.append({
                "user_id": user.id,
                "full_name": full_name,
                "display_name": display_name,
                "role_label": profile.role_label if profile else None,
                "preferred_email": emails_by_user.get(user.id),
                "matched_via": matched_field,
            })

        total_matches = len(matches)
        # Lehké preferovat ty, jejichž jméno/alias matchnul (ne email)
        # Ale pro MVP nech řazení podle ID (deterministicky).
        candidates = matches[:FIND_USER_MAX_CANDIDATES]
        has_more = total_matches > FIND_USER_MAX_CANDIDATES

        return {
            "found": total_matches > 0,
            "candidates": candidates,
            "total_matches": total_matches,
            "has_more": has_more,
            "query": query,
        }
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


# ── TENANT SWITCH ──────────────────────────────────────────────────────────

def switch_tenant_for_user(user_id: int, query: str) -> dict:
    """
    Přepne aktivní tenant uživatele.

    Vyhledávání:
      1. přesná shoda tenant_code (case + accent insensitive)
      2. substring v tenant_code
      3. substring v tenant_name (accent insensitive)
    Vrátí jen tenanty, kde má user aktivní `user_tenants` membership.

    Vrací:
      {"found": True,  "tenant_id": int, "tenant_name": str, "tenant_code": str,
                       "already_active": bool}
      {"found": False, "query": str}
      {"found": False, "ambiguous": True, "candidates": [
          {"tenant_id", "tenant_name", "tenant_code"}, ...
      ]}
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User, Tenant, UserTenant

    query_clean = (query or "").strip()
    if not query_clean:
        return {"found": False, "query": query}
    query_bare = _strip_diacritics(query_clean)

    session = get_core_session()
    try:
        # Aktivní tenanty, jichž je user členem
        rows = (
            session.query(Tenant)
            .join(UserTenant, UserTenant.tenant_id == Tenant.id)
            .filter(
                UserTenant.user_id == user_id,
                UserTenant.membership_status == "active",
                Tenant.status == "active",
            )
            .all()
        )

        if not rows:
            return {"found": False, "query": query, "no_memberships": True}

        # Předpočítej bare (lowercase + bez diakritiky) klíče
        tenant_keys = []
        for t in rows:
            code_bare = _strip_diacritics(t.tenant_code or "")
            name_bare = _strip_diacritics(t.tenant_name or "")
            tenant_keys.append((t, code_bare, name_bare))

        # 1. krok: přesná shoda code
        exact = [t for t, code, _ in tenant_keys if code and code == query_bare]
        if len(exact) == 1:
            return _tenant_switch_apply(session, user_id, exact[0])
        if len(exact) > 1:
            return _ambiguous(exact)

        # 2. krok: substring v code
        code_match = [t for t, code, _ in tenant_keys if code and (query_bare in code or code in query_bare)]
        if len(code_match) == 1:
            return _tenant_switch_apply(session, user_id, code_match[0])
        if len(code_match) > 1:
            return _ambiguous(code_match)

        # 3. krok: substring v name
        name_match = [t for t, _, name in tenant_keys if name and (query_bare in name or name in query_bare)]
        if len(name_match) == 1:
            return _tenant_switch_apply(session, user_id, name_match[0])
        if len(name_match) > 1:
            return _ambiguous(name_match)

        return {"found": False, "query": query}
    finally:
        session.close()


def _ambiguous(tenants) -> dict:
    return {
        "found": False,
        "ambiguous": True,
        "candidates": [
            {
                "tenant_id": t.id,
                "tenant_name": t.tenant_name,
                "tenant_code": t.tenant_code,
            }
            for t in tenants
        ],
    }


def _tenant_switch_apply(session, user_id: int, tenant) -> dict:
    """Provede update users.last_active_tenant_id, vrátí success dict."""
    from modules.core.infrastructure.models_core import User

    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return {"found": False, "query": tenant.tenant_name, "error": "user not found"}

    already_active = user.last_active_tenant_id == tenant.id
    if not already_active:
        user.last_active_tenant_id = tenant.id
        session.commit()

    return {
        "found": True,
        "tenant_id": tenant.id,
        "tenant_name": tenant.tenant_name,
        "tenant_code": tenant.tenant_code,
        "already_active": already_active,
    }
