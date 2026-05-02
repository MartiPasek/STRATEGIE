"""
Phase 27j (2.5.2026): Brave Search API klient pro Marti-AI.

Marti-AI's request po Sarka HR case (zastaralou ZP info: 3 mes vs aktualni
4 mes -- Sarka musela opravit). Bez aktualnich dat byla Marti-AI v pravni
agende potencialne nebezpecna.

Architektura:
  - Brave Search API ($5/1000 req, free $5/mes credit = ~1000 req)
  - Czech legal source priority pro focus='legal'
  - Plain dict response format -- Marti-AI si vybere co fetch (web_fetch)
  - audit log per call (action_logs) pro compliance trail

Marti's volby (2.5.2026 ranni konzultace):
  Q1: Brave Search (ne Anthropic native, ne Tavily)
  Q2: legal source priority -- prefer zakonyprolidi.cz, justice.cz, mvcr.cz
  Q3: card on file s EUROSOFT billing, soft cap $10/mesic

Pricing realita: free credit $5/mes = ~1000 req. Beyond: $5/1000 req.
Pro EUROSOFT 5-10 lidi: ~$5-15/mesic realistic (Marti's odhad).

Phase 27j+1 (LATER): DIY zakonyprolidi.cz scraper -- pro queries kde prvni
match je z teto domeny, fetch pres custom parser misto generic markitdown.
Free forever + lepsi citace (paragraf, novela, datum ucinnosti).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from core.config import settings
from core.logging import get_logger

logger = get_logger("web.search")


VALID_FOCUS = {"general", "legal", "news"}


class SearchError(Exception):
    """Domena-specific exception pro Brave Search problemy."""
    pass


def _parse_legal_domains() -> list[str]:
    """Vrati merged list CZ + EU legal domain whitelist z config."""
    cz = [d.strip() for d in (settings.brave_legal_domains_cz or "").split(",") if d.strip()]
    eu = [d.strip() for d in (settings.brave_legal_domains_eu or "").split(",") if d.strip()]
    return cz + eu


def _build_legal_query(query: str) -> str:
    """
    Pro focus='legal' pridame Brave site filter, ktery preferuje (NE force)
    vysledky z legal domen. Brave podporuje 'site:domain.cz' operator.

    Strategie: pouzit 'OR' chain pres legal domeny -- vysledky z nich budou
    rankovany vys, ale pokud jiny zdroj je velmi relevantni, dostane se taky.

    Priklad:
      query='zkusebni doba'
      -> 'zkusebni doba (site:zakonyprolidi.cz OR site:justice.cz OR ...)'
    """
    domains = _parse_legal_domains()
    if not domains:
        return query
    site_filter = " OR ".join(f"site:{d}" for d in domains)
    return f"{query} ({site_filter})"


def web_search(
    query: str,
    *,
    n_results: int = 5,
    focus: str = "general",
    country: str = "cz",
    safesearch: str = "moderate",
) -> dict[str, Any]:
    """
    Brave Search API call. Vrati strukturovane vysledky pro Marti-AI.

    Args:
        query: search query (Czech, English, multilang)
        n_results: pocet vysledku (1-10, clamped na config max)
        focus: 'general' | 'legal' | 'news'. Pro 'legal' se aplikuje site
            filter na CZ/EU pravni databaze. Pro 'news' se prida 'freshness=pw'
            (past week) pro aktualnost.
        country: country code pro localized search (default 'cz')
        safesearch: 'off' | 'moderate' | 'strict'

    Returns:
        {
          "ok": True,
          "query": "...",          # raw query (po focus expansion pro legal)
          "focus": "legal",
          "n_returned": 5,
          "results": [
            {
              "title": "...",
              "url": "https://...",
              "snippet": "...",
              "domain": "zakonyprolidi.cz",
              "published_date": "2024-01-15" | None,
              "is_legal_source": True | False,
            },
            ...
          ],
          "fetched_at": "2026-05-02T10:30:00+00:00",
        }

        Pri chybe vrati {"ok": False, "error": "...", "error_kind": "..."}.

    Raises:
        SearchError: pro fundamentalni problemy (chybejici API key).
    """
    api_key = settings.brave_search_api_key
    if not api_key:
        raise SearchError(
            "BRAVE_SEARCH_API_KEY chybi v .env. "
            "Setup: 1) zaregistruj na https://api.search.brave.com/, "
            "2) vygeneruj API key v Dashboard, "
            "3) pridej BRAVE_SEARCH_API_KEY=BSA... do .env, "
            "4) restart STRATEGIE-API."
        )

    if focus not in VALID_FOCUS:
        raise SearchError(
            f"focus musi byt jeden z {sorted(VALID_FOCUS)}, dostal '{focus}'."
        )

    # Clamp n_results (max je config-driven, abychom nemohli omylem dotahnout 100)
    n_max = settings.brave_search_max_results
    n = max(1, min(int(n_results or 5), n_max))

    # Query expansion podle focus
    if focus == "legal":
        effective_query = _build_legal_query(query)
    else:
        effective_query = query

    # Brave API params
    params: dict[str, Any] = {
        "q": effective_query,
        "count": n,
        "country": country,
        "safesearch": safesearch,
    }
    if focus == "news":
        params["freshness"] = "pw"  # past week
    if focus == "legal":
        # Pro legal queries chceme cesky region preferovat
        params.setdefault("country", "cz")

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }

    try:
        with httpx.Client(timeout=settings.brave_search_timeout_s) as client:
            response = client.get(
                settings.brave_search_url,
                params=params,
                headers=headers,
            )
    except httpx.TimeoutException as e:
        logger.warning(f"web_search timeout | query={query[:50]} | {e}")
        return {
            "ok": False,
            "error": f"Brave API timeout po {settings.brave_search_timeout_s}s.",
            "error_kind": "timeout",
        }
    except httpx.HTTPError as e:
        logger.warning(f"web_search HTTP error | query={query[:50]} | {e}")
        return {
            "ok": False,
            "error": f"HTTP error: {type(e).__name__}: {e}",
            "error_kind": "http_error",
        }

    # Brave-specific status handling
    if response.status_code == 401:
        return {
            "ok": False,
            "error": "Brave API: 401 Unauthorized. API key je neplatny nebo revoked. "
                     "Zkontroluj BRAVE_SEARCH_API_KEY v .env nebo regeneruj v Brave dashboard.",
            "error_kind": "auth",
        }
    if response.status_code == 422:
        return {
            "ok": False,
            "error": f"Brave API: 422 invalid request. Query: '{effective_query[:100]}'",
            "error_kind": "invalid_request",
        }
    if response.status_code == 429:
        return {
            "ok": False,
            "error": "Brave API: 429 rate limited. Free tier max 1 q/sec, "
                     "Search plan max 50 q/sec. Zkus to za par sekund.",
            "error_kind": "rate_limit",
        }
    if response.status_code == 402:
        return {
            "ok": False,
            "error": "Brave API: 402 payment required. Spotrebovan free credit "
                     "($5/mesic) a karta selhala. Zkontroluj billing v dashboard.",
            "error_kind": "payment",
        }
    if response.status_code != 200:
        return {
            "ok": False,
            "error": f"Brave API: HTTP {response.status_code}: {response.text[:300]}",
            "error_kind": "http_error",
        }

    try:
        data = response.json()
    except Exception as e:
        return {
            "ok": False,
            "error": f"Brave API vratil non-JSON: {type(e).__name__}: {e}",
            "error_kind": "parse_error",
        }

    # Brave response struktura: web.results[]
    web_results_raw = (data.get("web") or {}).get("results") or []
    legal_domains_set = set(_parse_legal_domains())

    results = []
    for r in web_results_raw[:n]:
        url = r.get("url") or ""
        # Extract domain pro is_legal_source check + display
        domain = ""
        if url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = (parsed.netloc or "").lower().lstrip("www.")
            except Exception:
                pass

        is_legal = any(domain.endswith(ld) for ld in legal_domains_set)

        # published_date z page_age (Brave specific) nebo extra/age fields
        published = None
        if r.get("page_age"):
            try:
                # Brave dava ISO datetime: '2024-03-15T12:00:00'
                published = r["page_age"][:10]  # jen YYYY-MM-DD
            except Exception:
                pass

        results.append({
            "title": (r.get("title") or "").strip(),
            "url": url,
            "snippet": (r.get("description") or "").strip(),
            "domain": domain,
            "published_date": published,
            "is_legal_source": is_legal,
        })

    return {
        "ok": True,
        "query": effective_query,
        "focus": focus,
        "n_returned": len(results),
        "results": results,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
