"""
Voyage AI embedding wrapper.

API:
    embed_documents(texts) -> list[list[float]]      # batch chunky pri ingestu
    embed_query(query) -> list[float]                # single query pri search

Voyage rozlisuje input_type ('document' vs 'query') -- pro asymmetrickou
similarity (query muze byt mnohem kratsi nez document a presto se mu uspesne
matchovat). Asymmetrie zlepsuje retrieval kvalitu o ~5-10%.

Batch limit: Voyage API berze az 128 textu / request, kazdy max 32k tokens.
Pri vetsim chunkingu rozdelujeme na batches.

Cost: voyage-3 = $0.06 / 1M tokens. Pro 100 PDF * 50 stran ~ 2.5M tokens
= ~$0.15 jednorazoveho indexovani. Search query embedding ~100 tokens =
zanedbatelne.
"""
from __future__ import annotations

from core.config import settings
from core.logging import get_logger

logger = get_logger("rag.embeddings")

VOYAGE_MODEL = "voyage-3"
EMBEDDING_DIM = 1024
BATCH_SIZE = 128


def _client():
    """Lazy-load Voyage client. Raises if VOYAGE_API_KEY chybi."""
    if not settings.voyage_api_key:
        raise RuntimeError(
            "VOYAGE_API_KEY není nastaven v .env. RAG nemůže běžet bez embedding providera."
        )
    import voyageai
    return voyageai.Client(api_key=settings.voyage_api_key)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    Embeddne batch dokumentovych textu (input_type='document').
    Vraci list embeddings ve stejnem poradi jako vstup.

    Pri vice nez BATCH_SIZE chunkach posti vice requestu a sloucim.
    """
    if not texts:
        return []

    client = _client()
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        logger.info(f"VOYAGE | embed_documents batch | size={len(batch)} | offset={i}")
        result = client.embed(
            texts=batch,
            model=VOYAGE_MODEL,
            input_type="document",
        )
        all_embeddings.extend(result.embeddings)
    return all_embeddings


def embed_query(query: str) -> list[float]:
    """
    Embeddne search query (input_type='query'). Vraci 1024-dim vektor.
    Voyage doporucuje rozlisovat document/query input_type pro lepsi recall.
    """
    if not query or not query.strip():
        raise ValueError("Query nesmi byt prazdny")
    client = _client()
    logger.info(f"VOYAGE | embed_query | len={len(query)}")
    result = client.embed(
        texts=[query],
        model=VOYAGE_MODEL,
        input_type="query",
    )
    return result.embeddings[0]
