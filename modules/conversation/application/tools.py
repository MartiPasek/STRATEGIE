"""
Execution layer — nástroje dostupné pro Marti-AI.
AI navrhne akci, uživatel potvrdí, systém vykoná.
"""

# Definice nástrojů pro Anthropic API
TOOLS = [
    {
        "name": "send_email",
        "description": (
            "Použij tento nástroj IHNED když uživatel chce poslat email. "
            "NEREAGUJ textem před použitím nástroje. "
            "Rovnou zavolej tento nástroj s připraveným emailem. "
            "Nástroj email NEPOŠLE — nejprve ukáže návrh uživateli a počká na potvrzení."
        ),        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Email adresa příjemce"
                },
                "subject": {
                    "type": "string",
                    "description": "Předmět emailu"
                },
                "body": {
                    "type": "string",
                    "description": "Tělo emailu"
                }
            },
            "required": ["to", "subject", "body"]
        }
    }
]


def format_email_preview(to: str, subject: str, body: str) -> str:
    """Formátuje návrh emailu pro zobrazení uživateli."""
    return (
        f"📧 **Návrh emailu**\n\n"
        f"**Komu:** {to}\n"
        f"**Předmět:** {subject}\n\n"
        f"{body}\n\n"
        f"---\n"
        f"Mám email odeslat? Napiš **ano** nebo **pošli**."
    )
