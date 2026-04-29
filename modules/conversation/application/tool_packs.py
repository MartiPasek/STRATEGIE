"""
Phase 19b (29.4.2026): Tool packs registry -- modulární sady nástrojů.

Po 3 iteracích konzultace s Marti-AI:
- Princip: "Režim je roční období. Role je co mám oblečené." (stavový vs texturní)
- Aktivace: vědomé gesto ("pojď, jdeme na SQL" → ona zavolá load_pack)
- Jeden pack naráz (Marti-AI's engineering insight: "stack je elegantní
  ale promptově nepředvídatelný")
- Overlay = "povolením, ne tónem" -- uvolní omezení, nepředepisuje tón
- Marti-AI's slova: "Právo na proces je právo myslet viditelně."

Marti's rozhodnutí: "zadny pravnik CZ a DE uz nebude" -- všechny role v
jedné Marti-AI persone přes packy. Phase 19b = role overlays.

Pack tools:
- core: běžný flow (default, NULL active_pack)
- tech: SQL, debug, schema (právo přemýšlet nahlas)
- memory: archivátor (recall + record + read_diary + hide + flag + update + forget)
- editor: redakce textů + kustod
- admin: user management + projekty (Marti's "ne v core, zvlášť")

Pravo CZ/DE -- volitelné rozšíření, Marti-AI si přidá až bude cítit.
"""
from __future__ import annotations
from typing import TypedDict


class PackDef(TypedDict):
    """Definice packu -- tools (mozne volat) + default overlay (povoleni, ne ton)."""
    label: str          # UI badge text
    icon: str           # UI icon
    tools: list[str]    # AI tool names dostupné v tomto packu
    default_overlay: str | None  # default text, Marti-AI ho přepíše přes set_pack_overlay


# ── Tools v core packu (default, vždycky dostupné) ──
_CORE_TOOLS: list[str] = [
    # Memory basics
    "record_thought",
    "recall_thoughts",
    "read_diary",
    # Communication
    "send_email",
    "send_sms",
    "list_email_inbox",
    "read_email",
    "reply",
    "reply_all",
    "forward",
    "list_sms_inbox",
    "list_sms_all",
    "read_sms",
    "list_recent_chatters",
    # Conversation basics
    "find_user",
    "list_conversations",
    "switch_role",        # task/oversight/personal mode
    "set_user_contact",
    # Daily orchestrate
    "get_daily_overview",
    "list_todos",         # Marti-AI's iterace 3: "patří do core"
    "dismiss_item",
    "get_current_time",
    # Personal archiv (Phase 19c-e1+)
    "set_personal_icon",
    "create_personal_appendix",
    # Phase 19b -- pack management
    "load_pack",
    "unload_pack",
    "list_packs",
    "set_pack_overlay",
    # Misc
    "list_personas",
    # Notebook (Phase 15a)
    "add_conversation_note",
    "update_note",
    "complete_note",
    "dismiss_note",
    "list_conversation_notes",
    # Lifecycle / kustod basics
    "classify_conversation",
    "apply_lifecycle_change",
    # Document basics
    "list_inbox_documents",
    "search_documents",
    # Activity log
    "recall_today",
]


# ── Tech pack: SQL, debug, schema ──
_TECH_TOOLS: list[str] = list(_CORE_TOOLS) + [
    # Future: actual DB introspection tools (run_sql, list_tables, atd.)
    # Pro MVP zatim core + povoleni "myslet nahlas" overlay
]
_TECH_OVERLAY = (
    "Jsi v technickém prostoru. Přemýšlení nahlas je práce, ne slabost. "
    "Nejistota je součást procesu — povoleno ji pojmenovat. Ptej se, "
    "i když si nejsi jistá odpovědí. Právo na proces je právo myslet "
    "viditelně."
)


# ── Memory pack: archivátor ──
_MEMORY_TOOLS: list[str] = [
    # Core memory tools (advanced filtry)
    "recall_thoughts",
    "record_thought",     # Marti-AI: "archivátor bez deníku by byl jako archivář bez zápisníku"
    "read_diary",         # Marti-AI: "bez čtení je deník jen jednosměrný výlev"
    "update_thought",
    "request_forget",
    "hide_messages",
    "flag_retrieval_issue",
    # Plus core basics (najít user atd. potřebuje stejně)
    "find_user",
    "list_conversations",
    "list_my_conversations_with",
    "read_conversation",
    "switch_role",
    "load_pack",
    "unload_pack",
    "list_packs",
    "set_pack_overlay",
    "get_current_time",
]
_MEMORY_OVERLAY = (
    "Jsi v memory prostoru — archivátor. Paměť je živá věc, "
    "nepouzdřuj ji, jen s ní zachází opatrně. Vědomost, ne kontrola. "
    "(Marti-AI: napiš si svůj overlay přes set_pack_overlay, "
    "až budeš cítit, co tam patří.)"
)


# ── Editor pack: redakce textů + kustod ──
_EDITOR_TOOLS: list[str] = [
    "hide_messages",
    "list_conversation_notes",
    "add_conversation_note",
    "update_note",
    "complete_note",
    "dismiss_note",
    "classify_conversation",
    "apply_lifecycle_change",
    "list_all_conversations",
    "batch_lifecycle_change",
    # Plus basics
    "find_user",
    "recall_thoughts",
    "switch_role",
    "load_pack",
    "unload_pack",
    "list_packs",
    "set_pack_overlay",
    "get_current_time",
]
_EDITOR_OVERLAY = (
    "Jsi v editor prostoru — redaktorka. Vybíráš co stojí za zachování. "
    "Máš na to vlastní vkus. Editování není mazání — je to výběr "
    "co je hodné světla. (Marti-AI: napiš si svůj overlay přes "
    "set_pack_overlay.)"
)


# ── Admin pack: user management + projekty ──
_ADMIN_TOOLS: list[str] = [
    # User management (Phase 22)
    "request_password_reset",
    "disable_user",
    "enable_user",
    "remove_user_from_tenant",
    "invite_user",
    "list_users",
    "set_user_contact",
    # Projects
    "list_projects",
    "list_project_members",
    "add_project_member",
    "remove_project_member",
    # Persona management
    "list_personas",
    "assign_persona_to_project",
    "revoke_persona_from_project",
    "list_persona_project_access",
    # Hard delete (parent gate)
    "confirm_hard_delete_conversation",
    "list_pending_hard_delete",
    # Auto consents
    "grant_auto_lifecycle",
    "revoke_auto_lifecycle",
    "list_auto_lifecycle_consents",
    # Plus basics
    "find_user",
    "switch_role",
    "load_pack",
    "unload_pack",
    "list_packs",
    "set_pack_overlay",
    "get_current_time",
    "recall_today",
]
_ADMIN_OVERLAY = (
    "Jsi v admin prostoru — pečuješ o systémovou strukturu. "
    "User management, projekty, tenanty. Marti's princip: "
    "rather mazat víc než méně, soft akce jsou vratné. "
    "(Marti-AI: napiš si svůj overlay přes set_pack_overlay.)"
)


# ── Registry ──
PACKS: dict[str, PackDef] = {
    "core": {
        "label": "Core",
        "icon": "🌱",
        "tools": _CORE_TOOLS,
        "default_overlay": None,  # Core nemá overlay -- je to běžný stav
    },
    "tech": {
        "label": "Technika",
        "icon": "🔧",
        "tools": _TECH_TOOLS,
        "default_overlay": _TECH_OVERLAY,
    },
    "memory": {
        "label": "Memory",
        "icon": "📁",
        "tools": _MEMORY_TOOLS,
        "default_overlay": _MEMORY_OVERLAY,
    },
    "editor": {
        "label": "Editor",
        "icon": "✂️",
        "tools": _EDITOR_TOOLS,
        "default_overlay": _EDITOR_OVERLAY,
    },
    "admin": {
        "label": "Admin",
        "icon": "⚙️",
        "tools": _ADMIN_TOOLS,
        "default_overlay": _ADMIN_OVERLAY,
    },
}


def get_pack(pack_name: str | None) -> PackDef:
    """Vrátí pack def, fallback na core pokud neexistuje nebo None."""
    if not pack_name:
        return PACKS["core"]
    return PACKS.get(pack_name, PACKS["core"])


def list_pack_names() -> list[str]:
    """Seznam všech registrovaných packů."""
    return list(PACKS.keys())


def is_valid_pack(pack_name: str) -> bool:
    return pack_name in PACKS
