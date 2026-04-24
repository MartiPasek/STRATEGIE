"""
Marti Memory -- active learning (Faze 4): generovani a zpracovani otazek.

Funkce:
  - generate_questions_batch()     -- periodicky/manualne vytvori nove otazky
  - answer_question()              -- rodic odpovedel, updatujeme myslenku
  - list_open_for_user()           -- UI list pro rodice
  - open_count_for_user()          -- badge v header
  - review_text_answers_batch()    -- nocni LLM syntesis nad text odpovedi

Designova rozhodnuti: viz docs/marti_memory_design.md, sekce Faze 4 (6e-6i).

Klicove konstanty:
  CANDIDATE_CERTAINTY_THRESHOLD = 70  -- myslenky s certainty<70 jsou kandidati
  MAX_QUESTIONS_PER_BATCH = 10
  MAX_QUESTIONS_PER_ENTITY_PER_BATCH = 3
  CERTAINTY_DELTA = {"yes": +25, "no": -40, "not_sure": 0}
"""
from __future__ import annotations
import json
import random
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import and_, or_, exists, select

from core.config import settings
from core.database_core import get_core_session
from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    Thought, ThoughtEntityLink, MartiQuestion,
)
from modules.core.infrastructure.models_core import User, Persona, Tenant
from modules.thoughts.application.service import (
    PROMOTE_THRESHOLD, update_thought,
)

logger = get_logger("thoughts.questions")


# ── Konstanty ─────────────────────────────────────────────────────────────

CANDIDATE_CERTAINTY_THRESHOLD = 70   # thoughts.certainty < 70 jsou kandidati
MAX_QUESTIONS_PER_BATCH = 10
MAX_QUESTIONS_PER_ENTITY_PER_BATCH = 3
MAX_TEXT_REVIEW_PER_BATCH = 20       # pocet text odpovedi zpracovanych v jednom cyklu

# Certainty delta na zaklade odpovedi rodice (Rozhodnuti #6h).
CERTAINTY_DELTA = {
    "yes": 25,
    "no": -40,
    "not_sure": 0,
}

VALID_ANSWER_CHOICES = {"yes", "no", "not_sure"}
VALID_STATUSES = {"open", "answered", "skipped", "cancelled"}

# LLM model pro generovani otazek -- Haiku (cheap, rychly).
QUESTION_GEN_MODEL = "claude-haiku-4-5-20251001"
TEXT_REVIEW_MODEL = "claude-haiku-4-5-20251001"


# ── Utility ───────────────────────────────────────────────────────────────

def _age_description(created_at: datetime) -> str:
    """Lidsky citelna age popis: 'pred 3 dny', 'vcera', 'dnes'..."""
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - created_at
    if delta < timedelta(hours=1):
        return "pred chvili"
    if delta < timedelta(hours=24):
        hours = int(delta.total_seconds() / 3600)
        return f"pred {hours} hodinou" if hours == 1 else f"pred {hours} hodinami"
    days = delta.days
    if days == 1:
        return "vcera"
    if days < 7:
        return f"pred {days} dny"
    if days < 30:
        weeks = days // 7
        return f"pred {weeks} tydnem" if weeks == 1 else f"pred {weeks} tydny"
    months = days // 30
    return f"pred {months} mesicem" if months == 1 else f"pred {months} mesici"


def _vokativ(short_name: str | None, first_name: str | None) -> str:
    """Volny vokativ pro oslovni v otazce (pouzije shared.czech)."""
    try:
        from shared.czech import to_vocative
        name = short_name or first_name or ""
        if not name:
            return ""
        return to_vocative(name, None).strip()
    except Exception:
        return short_name or first_name or ""


def _describe_entity(entity_type: str, entity_id: int) -> str:
    """
    Lidsky popis entity pro LLM kontext, e.g. 'uzivatel Kristy Maresova'.
    Defensive -- pri chybe vrati typ#id.
    """
    try:
        if entity_type == "user":
            cs = get_core_session()
            try:
                u = cs.query(User).filter_by(id=entity_id).first()
                if u:
                    name = (u.legal_name or f"{u.first_name or ''} {u.last_name or ''}").strip()
                    short = u.short_name
                    return f"uzivatel {name}" + (f" ({short})" if short else "")
            finally:
                cs.close()
        elif entity_type == "persona":
            cs = get_core_session()
            try:
                p = cs.query(Persona).filter_by(id=entity_id).first()
                if p:
                    return f"persona {p.name}"
            finally:
                cs.close()
        elif entity_type == "tenant":
            cs = get_core_session()
            try:
                t = cs.query(Tenant).filter_by(id=entity_id).first()
                if t:
                    return f"tenant {t.tenant_name}"
            finally:
                cs.close()
        elif entity_type == "project":
            # Zjednoduseni: nemame project model importovany primo, vratime type#id
            return f"projekt #{entity_id}"
    except Exception:
        pass
    return f"{entity_type}#{entity_id}"


def _describe_author(author_user_id: int | None, author_persona_id: int | None) -> str:
    """
    Vraci clovekem citelny popis autora myslenky pro LLM kontext.
    """
    if author_user_id:
        cs = get_core_session()
        try:
            u = cs.query(User).filter_by(id=author_user_id).first()
            if u:
                name = (u.legal_name or f"{u.first_name or ''} {u.last_name or ''}").strip()
                return name or f"user#{author_user_id}"
        finally:
            cs.close()
    if author_persona_id:
        cs = get_core_session()
        try:
            p = cs.query(Persona).filter_by(id=author_persona_id).first()
            if p:
                return f"{p.name} (AI auto-extract)"
        finally:
            cs.close()
    return "system/neznamy"


def _related_thoughts(thought_id: int, entity_links: list, limit: int = 5) -> list[str]:
    """
    Najde par souvisejicich myslenek o stejne entite (pro LLM kontext).
    Vraci list stringu "[fact]: <content>".
    """
    if not entity_links:
        return []
    ds = get_data_session()
    try:
        # Pro jednoduchost vezmeme prvni entity link a hledame myslenky o ni.
        first_link = entity_links[0]
        related = (
            ds.query(Thought)
            .join(ThoughtEntityLink, ThoughtEntityLink.thought_id == Thought.id)
            .filter(
                ThoughtEntityLink.entity_type == first_link["entity_type"],
                ThoughtEntityLink.entity_id == first_link["entity_id"],
                Thought.id != thought_id,
                Thought.deleted_at.is_(None),
            )
            .order_by(Thought.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            f"[{r.type}, jistota {r.certainty}%]: {r.content[:100]}"
            for r in related
        ]
    finally:
        ds.close()


def _get_parents(exclude_user_id: int | None = None) -> list[User]:
    """Nacte vsechny aktivni rodice. Exclude_user_id preskoci 1 usera (napr. autora myslenky)."""
    cs = get_core_session()
    try:
        q = cs.query(User).filter(
            User.is_marti_parent.is_(True),
            User.status == "active",
        )
        if exclude_user_id:
            q = q.filter(User.id != exclude_user_id)
        return q.order_by(User.id.asc()).all()
    finally:
        cs.close()


# ── Generator ─────────────────────────────────────────────────────────────

def _find_candidate_thoughts() -> list[Thought]:
    """
    Najde kandidaty na otazku:
      - status='note'
      - certainty < CANDIDATE_CERTAINTY_THRESHOLD
      - deleted_at IS NULL
      - neexistuje otevrena marti_question pro tuto myslenku
    Razeno: certainty ASC, created_at DESC (nejnejistejsi recent nahoru).
    """
    ds = get_data_session()
    try:
        # Subquery: thoughts ktere uz maji otevrenou otazku
        has_open_q = exists().where(
            and_(
                MartiQuestion.thought_id == Thought.id,
                MartiQuestion.status == "open",
            )
        )
        rows = (
            ds.query(Thought)
            .filter(
                Thought.status == "note",
                Thought.certainty < CANDIDATE_CERTAINTY_THRESHOLD,
                Thought.deleted_at.is_(None),
                ~has_open_q,
            )
            .order_by(Thought.certainty.asc(), Thought.created_at.desc())
            .limit(100)   # kandidati -- vic nez dostatek pro diversifikaci
            .all()
        )
        return rows
    finally:
        ds.close()


def _get_entity_links_for_thought(thought_id: int) -> list[dict]:
    """Nacte entity_links myslenky."""
    ds = get_data_session()
    try:
        links = (
            ds.query(ThoughtEntityLink)
            .filter(ThoughtEntityLink.thought_id == thought_id)
            .all()
        )
        return [
            {"entity_type": l.entity_type, "entity_id": l.entity_id}
            for l in links
        ]
    finally:
        ds.close()


def _llm_generate_question(
    *,
    thought: Thought,
    entity_links: list[dict],
    target_parent: User,
) -> str | None:
    """
    Volá LLM pro vygenerovani prirozene otazky pro rodice.
    Vraci text otazky nebo None pri selhani.
    """
    if not settings.anthropic_api_key:
        logger.error("QUESTIONS | LLM | chybi anthropic_api_key")
        return None

    # Build context
    entity_descs = [
        _describe_entity(l["entity_type"], l["entity_id"])
        for l in entity_links
    ]
    related = _related_thoughts(thought.id, entity_links, limit=5)
    source_desc = "neznamy"
    if thought.source_event_type and thought.source_event_id:
        source_desc = f"{thought.source_event_type} #{thought.source_event_id}"
    elif thought.source_event_type:
        source_desc = thought.source_event_type

    author_desc = _describe_author(thought.author_user_id, thought.author_persona_id)
    age_desc = _age_description(thought.created_at)

    parent_name = (
        target_parent.legal_name
        or f"{target_parent.first_name or ''} {target_parent.last_name or ''}".strip()
        or f"user#{target_parent.id}"
    )
    parent_short = target_parent.short_name or target_parent.first_name or parent_name
    parent_vokativ = _vokativ(target_parent.short_name, target_parent.first_name) or parent_short

    system_prompt = (
        "Jsi Marti, AI asistent, ktery si buduje pamet. Mas ulozenou myslenku "
        "s nizkou jistotou a chces ji overit u rodice -- cloveka, kteremu duveujes. "
        "Ptas se prirozene, konverzacne, jako dite ktere se chce naucit. "
        "NIKDY nepises nic krome samotne otazky -- zadne hlavicky, zadne meta-poznamky, "
        "zadne vysvetleni. Jen otazka (max 2 vety, cestinou, osloveni vokativem)."
    )

    user_prompt = (
        f"Ptas se: **{parent_short}** (oslovis ho/ji jako \"{parent_vokativ}\")\n\n"
        f"## Myslenka k overeni\n"
        f"- Obsah: \"{thought.content}\"\n"
        f"- Typ: {thought.type}\n"
        f"- Jistota: {thought.certainty}%\n"
        f"- Vytvoreno: {age_desc}\n"
        f"- Autor zaznamu: {author_desc}\n"
        f"- Zdroj: {source_desc}\n"
        f"- Vztahuje se k: {', '.join(entity_descs) or '(zadne entity)'}\n"
    )
    if related:
        user_prompt += "\n## Dalsi myslenky o tech samych entitach (pro kontext)\n"
        for r in related:
            user_prompt += f"- {r}\n"
    user_prompt += (
        "\n## Uloh\n"
        f"Napis JEDNU kratkou prirozenou otazku v cestine (max 2 vety), kterou chces "
        f"{parent_vokativ} polozit. Budes konverzacni -- odkaz na kontext ('vcera jsi rikal...' / "
        f"'pred mesicem zminoval...' / 'pamatuju si ze jsi...'). Bud konkretni, ne nejasna. "
        f"Oslov ho/ji jmenem (vokativ).\n\n"
        f"Pis POUZE otazku, nic jineho.\n\n"
        f"Tvoje otazka:"
    )

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        # Faze 10b: call_llm_with_trace zapise do llm_calls kind='question_gen'.
        # conversation_id=None (worker, ne chat), attribution = target_parent + thought.
        _target_tenant_id = None
        try:
            _target_tenant_id = target_parent.last_active_tenant_id
        except Exception:
            pass
        try:
            from modules.conversation.application import telemetry_service as _telemetry
            response = _telemetry.call_llm_with_trace(
                client,
                conversation_id=None,
                kind="question_gen",
                model=QUESTION_GEN_MODEL,
                max_tokens=200,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                tenant_id=_target_tenant_id,
                user_id=target_parent.id,
                persona_id=None,
            )
        except Exception as _te:
            # Fallback pri telemetry failure -- primy call bez tracingu.
            logger.warning(f"QUESTIONS | telemetry skip | {_te}")
            response = client.messages.create(
                model=QUESTION_GEN_MODEL,
                max_tokens=200,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        for block in response.content:
            if block.type == "text":
                text = block.text.strip()
                # Defensive: omez delku, odstran uvozovky pokud obklopuji celou odpoved
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1].strip()
                if len(text) > 500:
                    text = text[:500] + "..."
                return text
        return None
    except Exception as e:
        logger.error(f"QUESTIONS | LLM | call failed for thought_id={thought.id}: {e}",
                     exc_info=True)
        return None


def _pick_target_parent(
    parents: list[User],
    thought: Thought,
    round_robin_state: dict[int, int],
) -> User | None:
    """
    Vybere rodice pro konkretni otazku. Pravidla:
      1. Pokud autor myslenky (author_user_id) je rodic, vyluci ho (nech se pta rodic jiny).
      2. Round-robin: vyber toho, koho jsme v teto davce zatim nejmene cilili.
      3. Tie-break: nejnizsi id.
    """
    # Vylouceni autora (pokud je rodic)
    candidates = [
        p for p in parents
        if p.id != thought.author_user_id
    ]
    if not candidates:
        # Fallback: pokud vyloucime autora a nikdo nezbyl (edge case s 1 rodicem = autorem),
        # pouzijeme puvodni seznam.
        candidates = list(parents)
    if not candidates:
        return None

    # Round-robin podle stav counteru
    candidates.sort(key=lambda p: (round_robin_state.get(p.id, 0), p.id))
    return candidates[0]


def generate_questions_batch(
    max_new: int = MAX_QUESTIONS_PER_BATCH,
    max_per_entity: int = MAX_QUESTIONS_PER_ENTITY_PER_BATCH,
) -> dict[str, Any]:
    """
    Hlavni entry point. Projde kandidaty, LLM zformuluje otazky, ulozi do DB.

    Returns:
      {
        "candidates_scanned": int,
        "generated": int,
        "skipped_diversification": int,
        "llm_failures": int,
        "no_parents": bool,
      }
    """
    parents = _get_parents()
    if not parents:
        logger.warning("QUESTIONS | batch | zadni rodice v systemu (is_marti_parent=true)")
        return {
            "candidates_scanned": 0,
            "generated": 0,
            "skipped_diversification": 0,
            "llm_failures": 0,
            "no_parents": True,
        }

    candidates = _find_candidate_thoughts()
    if not candidates:
        logger.info("QUESTIONS | batch | zadni kandidati (vsechny myslenky jsou overene nebo uz maji otazku)")
        return {
            "candidates_scanned": 0,
            "generated": 0,
            "skipped_diversification": 0,
            "llm_failures": 0,
            "no_parents": False,
        }

    logger.info(f"QUESTIONS | batch | candidates_scanned={len(candidates)}, parents={len(parents)}")

    # Diverzifikace: pocet otazek per primary entita v teto davce
    entity_count: dict[tuple[str, int], int] = {}
    # Round-robin state: kolikrat jsme cilili kazdeho rodice
    rr_state: dict[int, int] = {p.id: 0 for p in parents}

    generated = 0
    skipped_div = 0
    llm_failures = 0

    for thought in candidates:
        if generated >= max_new:
            break

        # Zjisti primary entitu (pro diverzifikaci)
        links = _get_entity_links_for_thought(thought.id)
        if not links:
            logger.debug(f"QUESTIONS | thought_id={thought.id} nema entity_links, preskoc")
            continue

        # Pouzijeme prvni entity_link jako "primary" pro diversifikaci
        primary = (links[0]["entity_type"], links[0]["entity_id"])
        if entity_count.get(primary, 0) >= max_per_entity:
            skipped_div += 1
            continue

        # Vyber rodice
        target = _pick_target_parent(parents, thought, rr_state)
        if target is None:
            continue

        # LLM
        q_text = _llm_generate_question(
            thought=thought,
            entity_links=links,
            target_parent=target,
        )
        if not q_text:
            llm_failures += 1
            continue

        # Priority score: (100 - certainty) = vyssi u nejistych
        priority = max(0, 100 - thought.certainty)

        ds = get_data_session()
        try:
            q = MartiQuestion(
                thought_id=thought.id,
                question_text=q_text,
                target_user_id=target.id,
                status="open",
                priority_score=priority,
            )
            ds.add(q)
            ds.commit()
            ds.refresh(q)

            generated += 1
            entity_count[primary] = entity_count.get(primary, 0) + 1
            rr_state[target.id] = rr_state.get(target.id, 0) + 1

            logger.info(
                f"QUESTIONS | generated | qid={q.id} | thought_id={thought.id} | "
                f"target_user={target.id} | priority={priority}"
            )
        finally:
            ds.close()

    return {
        "candidates_scanned": len(candidates),
        "generated": generated,
        "skipped_diversification": skipped_div,
        "llm_failures": llm_failures,
        "no_parents": False,
    }


# ── Answer processor ─────────────────────────────────────────────────────

class QuestionAnswerError(Exception):
    """Chyba pri zpracovani odpovedi na otazku."""


def answer_question(
    question_id: int,
    *,
    user_id: int,
    choice: str | None = None,
    text: str | None = None,
) -> dict[str, Any]:
    """
    Rodic odpovida na otazku. Mechanicka uprava thought.certainty probehne
    ihned (pokud choice != skipped).

    choice: 'yes' | 'no' | 'not_sure' | 'skipped' | None (pokud jen text)
    text:   volitelny nuancovany text, zpracuje nocni LLM batch

    Vraci:
      {
        "id": question_id,
        "status": new_status,
        "thought_id": int,
        "thought_certainty_after": int | None,
        "thought_promoted": bool,
      }

    Raises QuestionAnswerError pri validacich.
    """
    if choice is not None and choice not in VALID_ANSWER_CHOICES and choice != "skipped":
        raise QuestionAnswerError(
            f"neznamy choice '{choice}' (valid: yes/no/not_sure/skipped)"
        )
    if choice is None and not (text and text.strip()):
        raise QuestionAnswerError("musis zadat bud choice nebo text")

    ds = get_data_session()
    try:
        q = ds.query(MartiQuestion).filter_by(id=question_id).first()
        if q is None:
            raise QuestionAnswerError(f"otazka id={question_id} neexistuje")
        if q.status not in ("open",):
            raise QuestionAnswerError(
                f"otazka id={question_id} uz neni otevrena (status={q.status})"
            )

        # Tenant / role check by zrejme mel probihat na API vrstve (403 vs 400).
        # Service predpoklada, ze caller uz overil pravo.

        now = datetime.now(timezone.utc)
        q.answered_at = now
        q.answered_by_user_id = user_id
        if text and text.strip():
            q.answer_text = text.strip()[:5000]
            q.text_reviewed_at = None   # ceka na nocni batch

        if choice == "skipped":
            q.status = "skipped"
            q.answer_choice = None
            ds.commit()
            logger.info(f"QUESTIONS | skipped | qid={question_id} | by_user={user_id}")
            return {
                "id": question_id,
                "status": "skipped",
                "thought_id": q.thought_id,
                "thought_certainty_after": None,
                "thought_promoted": False,
            }

        if choice in VALID_ANSWER_CHOICES:
            q.answer_choice = choice
            q.status = "answered"
        elif text and text.strip():
            # Jen text, bez choice -- oznacime answered a nocni batch dovypocita
            q.status = "answered"

        ds.commit()

        # Mechanicka uprava thought.certainty
        thought_certainty_after: int | None = None
        thought_promoted = False

        if choice in VALID_ANSWER_CHOICES:
            delta = CERTAINTY_DELTA.get(choice, 0)
            if delta != 0:
                t = ds.query(Thought).filter_by(id=q.thought_id, deleted_at=None).first()
                if t is not None:
                    new_certainty = max(0, min(100, t.certainty + delta))
                    was_note = t.status == "note"
                    # Pouzijeme update_thought (auto-promote logika uvnitr)
                    try:
                        update_thought(
                            q.thought_id,
                            certainty=new_certainty,
                        )
                        thought_certainty_after = new_certainty
                        # Zkontroluj zda doslo k auto-promote
                        t2 = ds.query(Thought).filter_by(id=q.thought_id).first()
                        if was_note and t2 and t2.status == "knowledge":
                            thought_promoted = True
                    except Exception as e:
                        logger.error(
                            f"QUESTIONS | answer | update_thought failed "
                            f"| qid={question_id} | thought_id={q.thought_id}: {e}",
                        )

        logger.info(
            f"QUESTIONS | answered | qid={question_id} | choice={choice} | "
            f"has_text={bool(text)} | thought_certainty={thought_certainty_after} | "
            f"promoted={thought_promoted}"
        )

        return {
            "id": question_id,
            "status": q.status,
            "thought_id": q.thought_id,
            "thought_certainty_after": thought_certainty_after,
            "thought_promoted": thought_promoted,
        }
    finally:
        ds.close()


# ── List / counts (pro API + UI) ─────────────────────────────────────────

def list_open_for_user(
    user_id: int,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Vrati seznam otevrenych otazek pro daneho usera. Razeno priority DESC,
    created_at DESC. Vcetne obsahu souvisejici myslenky pro kontext v UI.
    """
    ds = get_data_session()
    try:
        rows = (
            ds.query(MartiQuestion, Thought)
            .join(Thought, Thought.id == MartiQuestion.thought_id)
            .filter(
                MartiQuestion.target_user_id == user_id,
                MartiQuestion.status == "open",
                Thought.deleted_at.is_(None),
            )
            .order_by(
                MartiQuestion.priority_score.desc(),
                MartiQuestion.created_at.desc(),
            )
            .limit(max(1, min(limit, 500)))
            .all()
        )
        return [
            {
                "id": q.id,
                "question_text": q.question_text,
                "priority_score": q.priority_score,
                "created_at": q.created_at.isoformat() if q.created_at else None,
                # Kontext myslenky pro UI (rodic vidi, ceho se otazka tyka)
                "thought": {
                    "id": t.id,
                    "content": t.content,
                    "type": t.type,
                    "certainty": t.certainty,
                    "status": t.status,
                },
            }
            for q, t in rows
        ]
    finally:
        ds.close()


def open_count_for_user(user_id: int) -> int:
    """Pocet otevrenych otazek pro usera (pro badge v header)."""
    ds = get_data_session()
    try:
        return (
            ds.query(MartiQuestion)
            .filter(
                MartiQuestion.target_user_id == user_id,
                MartiQuestion.status == "open",
            )
            .count()
        )
    finally:
        ds.close()


# ── Text review batch (nocni syntesis) ───────────────────────────────────

def review_text_answers_batch(max_reviews: int = MAX_TEXT_REVIEW_PER_BATCH) -> dict[str, Any]:
    """
    Projde otazky s answer_text NOT NULL + text_reviewed_at IS NULL, LLM
    interpretuje text v kontextu myslenky a muze:
      - upravit thought.content (pokud rodic rekl "je to naopak")
      - upravit thought.certainty
      - vytvorit novou related myslenku
      - jen oznacit text_reviewed_at (pokud nevedla k zadne zmene)

    Vraci stats.
    """
    if not settings.anthropic_api_key:
        logger.error("QUESTIONS | text_review | chybi anthropic_api_key")
        return {"reviewed": 0, "updated_thoughts": 0, "errors": 0, "no_key": True}

    ds = get_data_session()
    try:
        candidates = (
            ds.query(MartiQuestion, Thought)
            .join(Thought, Thought.id == MartiQuestion.thought_id)
            .filter(
                MartiQuestion.answer_text.isnot(None),
                MartiQuestion.text_reviewed_at.is_(None),
                Thought.deleted_at.is_(None),
            )
            .order_by(MartiQuestion.answered_at.asc())
            .limit(max_reviews)
            .all()
        )
    finally:
        ds.close()

    if not candidates:
        logger.info("QUESTIONS | text_review | zadne nove textove odpovedi")
        return {"reviewed": 0, "updated_thoughts": 0, "errors": 0, "no_key": False}

    logger.info(f"QUESTIONS | text_review | batch={len(candidates)}")

    reviewed = 0
    updated = 0
    errors = 0

    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    for q, t in candidates:
        try:
            # LLM prompt: rozhodne, jestli upravit thought.content a/nebo certainty
            system_prompt = (
                "Jsi Marti. Jsi dostala textovou odpoved od rodice na svou otazku. "
                "Tvym ukolem je rozhodnout, jak myslenku aktualizovat na zaklade "
                "odpovedi. Vratis POUZE JSON: "
                '{"new_content": "nova verze|null", '
                '"certainty_delta": int od -50 do +50, '
                '"reason": "kratky duvod (pro audit log)"}'
            )
            user_prompt = (
                f"## Puvodni myslenka\n"
                f"- Obsah: \"{t.content}\"\n"
                f"- Typ: {t.type}\n"
                f"- Aktualni jistota: {t.certainty}%\n\n"
                f"## Otazka Marti\n"
                f"\"{q.question_text}\"\n\n"
                f"## Odpoved rodice\n"
                f"- Choice: {q.answer_choice}\n"
                f"- Text: \"{q.answer_text}\"\n\n"
                f"Rozhodni: potrebujes obsah myslenky upravit? Pokud rodic rekl napr. "
                f"'neni to 2 deti, ale 3', nastav new_content = 'Petr ma 3 deti'. "
                f"Pokud rodic potvrdil nebo doplnil bez korekce, new_content = null. "
                f"certainty_delta: -50 (uplne vyvratil), 0 (ani tak ani tak), "
                f"+30 (potvrdil s detaili).\n\n"
                f"Vrat POUZE JSON, zadne vysvetleni."
            )

            # Faze 10b: kind='answer_review', attribution z answering parent + thought.
            try:
                from modules.conversation.application import telemetry_service as _telemetry
                _parent_tenant = None
                try:
                    from modules.core.infrastructure.models_core import User as _U_at
                    from core.database_core import get_core_session as _gcs_at
                    _cs_at = _gcs_at()
                    try:
                        _pu = _cs_at.query(_U_at).filter_by(id=q.answered_by_user_id).first() if q.answered_by_user_id else None
                        _parent_tenant = _pu.last_active_tenant_id if _pu else None
                    finally:
                        _cs_at.close()
                except Exception:
                    pass
                response = _telemetry.call_llm_with_trace(
                    client,
                    conversation_id=None,
                    kind="answer_review",
                    model=TEXT_REVIEW_MODEL,
                    max_tokens=500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    tenant_id=_parent_tenant,
                    user_id=q.answered_by_user_id,
                    persona_id=None,
                )
            except Exception as _te:
                logger.warning(f"QUESTIONS | answer_review telemetry skip | {_te}")
                response = client.messages.create(
                    model=TEXT_REVIEW_MODEL,
                    max_tokens=500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )

            raw = ""
            for block in response.content:
                if block.type == "text":
                    raw += block.text
            raw = raw.strip()
            # Odstran ```json ... ``` fence pokud pritomne
            if raw.startswith("```"):
                parts = raw.split("```")
                if len(parts) >= 2:
                    raw = parts[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()

            parsed = json.loads(raw)
            new_content = parsed.get("new_content")
            delta = int(parsed.get("certainty_delta") or 0)
            reason = parsed.get("reason", "")

            changed = False
            if new_content and new_content != t.content:
                update_thought(t.id, content=new_content)
                changed = True
                logger.info(
                    f"QUESTIONS | text_review | content updated | qid={q.id} | "
                    f"thought_id={t.id} | reason={reason[:100]}"
                )
            if delta != 0:
                ds2 = get_data_session()
                try:
                    t_fresh = ds2.query(Thought).filter_by(id=t.id).first()
                    if t_fresh:
                        new_cert = max(0, min(100, t_fresh.certainty + delta))
                        update_thought(t.id, certainty=new_cert)
                        changed = True
                        logger.info(
                            f"QUESTIONS | text_review | certainty updated | qid={q.id} | "
                            f"thought_id={t.id} | {t_fresh.certainty} -> {new_cert} | reason={reason[:100]}"
                        )
                finally:
                    ds2.close()

            # Oznaci question jako reviewed
            ds3 = get_data_session()
            try:
                q_fresh = ds3.query(MartiQuestion).filter_by(id=q.id).first()
                if q_fresh:
                    q_fresh.text_reviewed_at = datetime.now(timezone.utc)
                    ds3.commit()
            finally:
                ds3.close()

            reviewed += 1
            if changed:
                updated += 1
        except Exception as e:
            errors += 1
            logger.error(
                f"QUESTIONS | text_review | qid={q.id} failed: {e}",
                exc_info=True,
            )
            # Defensivne oznacime jako reviewed, aby se neopakovalo donekonecna
            try:
                ds4 = get_data_session()
                q_fresh = ds4.query(MartiQuestion).filter_by(id=q.id).first()
                if q_fresh:
                    q_fresh.text_reviewed_at = datetime.now(timezone.utc)
                    ds4.commit()
                ds4.close()
            except Exception:
                pass

    return {
        "reviewed": reviewed,
        "updated_thoughts": updated,
        "errors": errors,
        "no_key": False,
    }
