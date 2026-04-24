"""
Memory service — ukládání a načítání pamětí.
Automatická extrakce: AI rozhoduje co uložit po každé odpovědi.
Ruční uložení: přímý zápis přes endpoint.
"""
import json
import anthropic

from core.config import settings
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import Memory

logger = get_logger("memory")

MEMORY_EXTRACTION_PROMPT = """
Analyzuj tuto konverzaci a urči, zda obsahuje důležité informace o uživateli, které stojí za zapamatování.

Ukládej pouze:
- preference uživatele (styl komunikace, délka odpovědí, jazyk)
- osobní fakta (jméno, role, vztahy)
- opakující se témata nebo záměry
- důležitá rozhodnutí nebo kontexty

NEPŘIDÁVEJ:
- běžné informace z konverzace
- fakta která jsou zřejmá z kontextu
- duplicity (pokud už bylo uloženo)

Odpověz POUZE jako JSON:
{
  "save": true nebo false,
  "memories": ["fakt 1", "fakt 2"]
}

Pokud není co uložit, vrať: {"save": false, "memories": []}
"""


def extract_and_save(
    conversation_id: int,
    messages: list[dict],
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
    persona_id: int | None = None,
) -> list[str]:
    """
    Automatická extrakce pamětí z konverzace.
    Volá LLM, parsuje výstup, ukládá do DB.
    Vrátí seznam uložených faktů.
    """
    if not messages:
        return []

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Sestavíme konverzaci jako text pro LLM
        conv_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in messages[-10:]  # posledních 10 zpráv
        )

        # Faze 10 Alt A: call_llm_with_trace -> llm_calls (kind='memory_extract').
        # Fallback na primy call pri telemetry failure (neshazuje memory extract).
        try:
            from modules.conversation.application import telemetry_service as _telemetry
            response = _telemetry.call_llm_with_trace(
                client,
                conversation_id=conversation_id,
                kind="memory_extract",
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                system=MEMORY_EXTRACTION_PROMPT,
                messages=[{"role": "user", "content": f"Konverzace:\n\n{conv_text}"}],
                tenant_id=tenant_id,
                user_id=user_id,
                persona_id=persona_id,
            )
        except Exception as _te:
            logger.warning(f"MEMORY | telemetry skip: {_te}")
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                system=MEMORY_EXTRACTION_PROMPT,
                messages=[{"role": "user", "content": f"Konverzace:\n\n{conv_text}"}],
            )

        raw = response.content[0].text.strip()
        # Odstraní markdown obal
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)

        if not data.get("save") or not data.get("memories"):
            return []

        saved = []
        for fact in data["memories"]:
            if fact and len(fact.strip()) > 3:
                save_memory(
                    content=fact.strip(),
                    user_id=user_id,
                    tenant_id=tenant_id,
                    project_id=project_id,
                )
                saved.append(fact.strip())

        if saved:
            logger.info(f"MEMORY | extracted {len(saved)} facts | conversation_id={conversation_id}")

        return saved

    except Exception as e:
        logger.error(f"MEMORY | extraction failed: {e}")
        return []


def save_memory(
    content: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
) -> int:
    """Ruční uložení paměti do DB."""
    session = get_data_session()
    try:
        memory = Memory(
            content=content,
            user_id=user_id,
            tenant_id=tenant_id,
            project_id=project_id,
        )
        session.add(memory)
        session.commit()
        session.refresh(memory)
        logger.info(f"MEMORY | saved | id={memory.id} | user_id={user_id}")
        return memory.id
    finally:
        session.close()


def get_memories(
    user_id: int | None = None,
    tenant_id: int | None = None,
    project_id: int | None = None,
    limit: int = 10,
) -> list[str]:
    """Načte relevantní paměti pro Composer."""
    session = get_data_session()
    try:
        query = session.query(Memory)
        if user_id:
            query = query.filter(Memory.user_id == user_id)
        if project_id:
            query = query.filter(Memory.project_id == project_id)
        memories = query.order_by(Memory.id.desc()).limit(limit).all()
        return [m.content for m in memories]
    finally:
        session.close()
