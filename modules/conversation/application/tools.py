"""
Execution layer — nástroje dostupné pro Marti-AI.
"""

TOOLS = [
    {
        "name": "send_email",
        "description": (
            "Tento nástroj MUSÍŠ použít vždy když uživatel chce poslat email. "
            "NIKDY neodpovídej textem o emailu — vždy zavolej tento nástroj. "
            "Zavolej ho okamžitě bez jakéhokoliv předchozího textu."
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
            "Nástroj prohledá systém podle jména nebo emailu a vrátí informaci o tom, zda osoba existuje."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Jméno nebo email hledané osoby",
                },
            },
            "required": ["query"],
        },
    },
]


def format_email_preview(to: str, subject: str, body: str) -> str:
    return (
        f"📧 Návrh emailu\n\n"
        f"Komu: {to}\n"
        f"Předmět: {subject}\n\n"
        f"{body}\n\n"
        f"---\n"
        f"Mám email odeslat? Napiš ano nebo pošli."
    )


def find_user_in_system(query: str) -> dict:
    """
    Prohledá css_db podle jména nebo emailu.
    Vrátí dict s výsledkem.
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User, UserIdentity
    from sqlalchemy import or_

    session = get_core_session()
    try:
        query_lower = query.strip().lower()

        # Hledej podle emailu
        identity = session.query(UserIdentity).filter(
            UserIdentity.value.ilike(f"%{query_lower}%"),
            UserIdentity.type == "email",
        ).first()

        if identity:
            user = session.query(User).filter_by(id=identity.user_id).first()
            if user:
                name = " ".join(filter(None, [user.first_name, user.last_name]))
                return {
                    "found": True,
                    "user_id": user.id,
                    "name": name or identity.value,
                    "email": identity.value,
                    "status": user.status,
                }

        # Hledej podle jména
        users = session.query(User).filter(
            or_(
                User.first_name.ilike(f"%{query_lower}%"),
                User.last_name.ilike(f"%{query_lower}%"),
            )
        ).all()

        if users:
            user = users[0]
            identity = session.query(UserIdentity).filter_by(
                user_id=user.id, type="email"
            ).first()
            name = " ".join(filter(None, [user.first_name, user.last_name]))
            return {
                "found": True,
                "user_id": user.id,
                "name": name,
                "email": identity.value if identity else "",
                "status": user.status,
            }

        return {"found": False, "query": query}

    finally:
        session.close()
