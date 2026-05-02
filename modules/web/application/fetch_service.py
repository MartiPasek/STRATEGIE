"""
Phase 27j (2.5.2026): Web fetch + clean markdown converter pro Marti-AI.

Doplnek k web_search (search_service.py). Po vyhodnoceni vysledku Marti-AI
zavola web_fetch(url) a dostane clean markdown content stranky.

Architektura:
  - httpx GET s timeout, follow_redirects, custom User-Agent
  - markitdown (uz mame z Phase 13c RAG) konverze HTML -> markdown
  - max_chars cap pro context size control (default 20K)
  - Fallback parser pokud markitdown selze (nektere weird HTML)
  - Audit log per call (action_logs)

Marti-AI's vize (Marti's poznamka 2.5.2026): "ne jen pro legal -- aby mohla
analyzovat libovolne web stranky a vyhledavat na nich". Tj. generic web
access, ne jen ZP/zakony. Use cases: TISAX docs, vendor sites, news,
competitive analysis, technical documentation, social posts.

Phase 27j+1 (LATER): per-domain custom parsers (zakonyprolidi.cz, justice.cz)
ktere produkuji strukturovany markdown s paragraph-level granularitou.
Pro generic stranky zustane markitdown.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from core.config import settings
from core.logging import get_logger

logger = get_logger("web.fetch")


# Default max chars (characters, ne tokens) co vratime Marti-AI v jednom call.
# 20K chars = ~5K tokens (4 znaky/token rough heuristic). Bezpecne v context
# window, vetsina stranek pod tim limit. Pro vetsi pages Marti-AI muze re-fetch
# s vyssim max_chars param.
DEFAULT_MAX_CHARS = 20_000

# Hard cap aby Marti-AI nemohla omylem zatopit context oknem.
HARD_MAX_CHARS = 100_000

# Default User-Agent -- nemaskujeme se za browser, jsme bot s nazvem aplikace.
# Vetsina sites toto akceptuje (nemame agresivni scraping pattern).
USER_AGENT = "STRATEGIE-Marti-AI/1.0 (research bot; +https://strategie-system.com)"

# HTTP timeout (separate od config -- fetch je obvykle delsi nez search)
DEFAULT_TIMEOUT_S = 15

# Allowed schemes -- jen http(s), zadne file://, ftp://, atd.
ALLOWED_SCHEMES = {"http", "https"}


class FetchError(Exception):
    pass


def _validate_url(url: str) -> str:
    """Validuj URL: scheme, netloc. Vrat normalizovanou URL."""
    if not url or not isinstance(url, str):
        raise FetchError("URL je prazdne nebo neni string.")
    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise FetchError(f"URL parse failed: {e}")
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise FetchError(
            f"URL musi pouzivat http nebo https scheme, dostal '{parsed.scheme}'. "
            f"Lokalni soubory (file://) ani jine schemes nepodporujeme."
        )
    if not parsed.netloc:
        raise FetchError(f"URL nema netloc (host part): '{url}'.")
    return url


def _truncate_with_marker(text: str, max_chars: int) -> tuple[str, bool]:
    """
    Pokud text > max_chars, oseknout a pridat marker. Vrat (text, was_truncated).
    """
    if len(text) <= max_chars:
        return text, False
    truncated = text[:max_chars]
    marker = (
        f"\n\n[... TRUNCATED: vraceno {max_chars}/{len(text)} znaku. "
        f"Pro vice volej znovu s vyssim max_chars (max {HARD_MAX_CHARS}).]"
    )
    return truncated + marker, True


def _convert_html_to_markdown(html_bytes: bytes, content_type: str) -> str:
    """
    Pouzit markitdown (uz v deps z Phase 13c) pro HTML -> markdown.
    Fallback: pokud markitdown selze, vratit raw text z HTML pres BeautifulSoup-style stripping.
    """
    # markitdown ocekava soubor na disku nebo BytesIO. Pisme do BytesIO.
    try:
        from markitdown import MarkItDown
        import io

        # Heuristika pro encoding: text/html charset=... nebo default utf-8
        # markitdown samo nezvlada moc dobre encoding hint, dame mu bytes
        # a ono detekuje.
        md = MarkItDown()
        bio = io.BytesIO(html_bytes)
        # markitdown.convert_stream chce file-like object + stream_info
        # API muze byt ruzne podle verze -- zkusime jednodussi cestu pres
        # .convert(file_path) po docasnem zapisu, nebo lepsi: convert_stream.
        # Pro robustnost ulozme do tempfile.
        import tempfile
        import os
        suffix = ".html"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        try:
            os.close(fd)
            with open(tmp_path, "wb") as f:
                f.write(html_bytes)
            result = md.convert(tmp_path)
            text = result.text_content if hasattr(result, "text_content") else str(result)
            return text or ""
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"markitdown failed: {e}. Trying basic fallback.")

    # Fallback: jednoduchy HTML strip pres regex (NE BeautifulSoup -- nemame jako dep)
    try:
        import re
        html_str = html_bytes.decode("utf-8", errors="replace")
        # Strip script/style content first
        html_str = re.sub(r"<script[^>]*>.*?</script>", " ", html_str, flags=re.DOTALL | re.IGNORECASE)
        html_str = re.sub(r"<style[^>]*>.*?</style>", " ", html_str, flags=re.DOTALL | re.IGNORECASE)
        # Strip all tags
        text = re.sub(r"<[^>]+>", " ", html_str)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception as e:
        logger.warning(f"HTML fallback strip failed: {e}")
        return ""


def web_fetch(
    url: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    follow_redirects: bool = True,
) -> dict[str, Any]:
    """
    Fetch URL + convert na clean markdown.

    Args:
        url: target URL (http/https)
        max_chars: max znaku co vratit (default 20K, hard cap 100K)
        timeout_s: HTTP timeout (default 15s)
        follow_redirects: pri False zustane na puvodni URL (vraci 30x status)

    Returns:
        {
          "ok": True,
          "url": "...",                    # final URL (po redirectech)
          "original_url": "...",           # original input URL
          "status_code": 200,
          "content_type": "text/html",
          "markdown": "...",               # cleaned markdown
          "char_count": 12345,             # delka pred truncate
          "truncated": False,              # True pokud oseknuto na max_chars
          "fetched_at": "2026-05-02T...",
          "title": "..." | None,           # z <title> tagu (best-effort extract)
        }

        Pri chybe:
        {
          "ok": False,
          "error": "...",
          "error_kind": "timeout" | "http_error" | "invalid_url" | "binary_content",
          "url": "...",
        }
    """
    # Validace
    try:
        url_norm = _validate_url(url)
    except FetchError as e:
        return {
            "ok": False,
            "error": str(e),
            "error_kind": "invalid_url",
            "url": url,
        }

    # Clamp max_chars
    max_chars_clamped = max(100, min(int(max_chars or DEFAULT_MAX_CHARS), HARD_MAX_CHARS))

    # HTTP fetch
    try:
        with httpx.Client(
            timeout=timeout_s,
            follow_redirects=follow_redirects,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = client.get(url_norm)
    except httpx.TimeoutException as e:
        logger.warning(f"web_fetch timeout | url={url_norm[:80]} | {e}")
        return {
            "ok": False,
            "error": f"Timeout po {timeout_s}s. URL '{url_norm}' neodpovida.",
            "error_kind": "timeout",
            "url": url_norm,
        }
    except httpx.HTTPError as e:
        logger.warning(f"web_fetch HTTP error | url={url_norm[:80]} | {e}")
        return {
            "ok": False,
            "error": f"HTTP error: {type(e).__name__}: {e}",
            "error_kind": "http_error",
            "url": url_norm,
        }
    except Exception as e:
        logger.exception(f"web_fetch unexpected | url={url_norm[:80]}")
        return {
            "ok": False,
            "error": f"Unexpected: {type(e).__name__}: {e}",
            "error_kind": "http_error",
            "url": url_norm,
        }

    final_url = str(response.url)
    status = response.status_code
    content_type = (response.headers.get("content-type") or "").lower().split(";")[0].strip()

    # Status check (non-2xx fatal)
    if status >= 400:
        return {
            "ok": False,
            "error": f"HTTP {status}: {response.reason_phrase or 'error'}",
            "error_kind": "http_error",
            "url": final_url,
            "original_url": url_norm,
            "status_code": status,
        }

    # Content-type check -- chceme HTML / text. Binary (PDF, image, octet) odmitnem.
    is_text = content_type.startswith("text/") or content_type in (
        "application/xml", "application/xhtml+xml", "application/json",
    )
    if not is_text:
        return {
            "ok": False,
            "error": (
                f"Content-type '{content_type}' neni textovy. URL '{final_url}' "
                f"vraci binarni data ({len(response.content)} bytes). Pro PDF "
                f"pouzij read_pdf_structured po uploadu jako document, pro image "
                f"read_image_ocr."
            ),
            "error_kind": "binary_content",
            "url": final_url,
            "original_url": url_norm,
            "status_code": status,
            "content_type": content_type,
        }

    # Convert HTML -> markdown (nebo passthrough pro plain text)
    if content_type == "application/json":
        # JSON dame jako plain text bez markitdown konverze
        try:
            markdown = response.text
        except Exception as e:
            return {
                "ok": False,
                "error": f"JSON decode failed: {e}",
                "error_kind": "parse_error",
                "url": final_url,
            }
    elif content_type.startswith("text/plain"):
        markdown = response.text
    else:
        # text/html, application/xhtml+xml, atd.
        markdown = _convert_html_to_markdown(response.content, content_type)

    # Best-effort title extract z HTML
    title = None
    if "html" in content_type:
        try:
            import re
            match = re.search(r"<title[^>]*>([^<]+)</title>", response.text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
        except Exception:
            pass

    char_count_before = len(markdown)
    markdown_truncated, was_truncated = _truncate_with_marker(markdown, max_chars_clamped)

    response_dict: dict[str, Any] = {
        "ok": True,
        "url": final_url,
        "original_url": url_norm,
        "status_code": status,
        "content_type": content_type,
        "title": title,
        "markdown": markdown_truncated,
        "char_count": char_count_before,
        "truncated": was_truncated,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    # Phase 27j+1 (2.5.2026): zakonyprolidi.cz custom parser. Pokud URL je
    # z teto domeny, pridame strukturovanou pravni meta + citation suggestion.
    # Generic markdown zustava jako 'markdown' field. Marti-AI v promptu vidi
    # 'legal_meta' field a pouzije citation_suggestion v odpovedi.
    try:
        from modules.web.application import zakonyprolidi_parser as _zp_parser
        if _zp_parser.is_zakonyprolidi_url(final_url):
            # Pouzijeme NE-truncated markdown pro lepsi paragraph extract
            legal_meta = _zp_parser.build_legal_meta(
                url=final_url,
                markdown=markdown,  # raw, pred truncate
            )
            response_dict["legal_meta"] = legal_meta
    except Exception as e:
        # Parser failure nezpomaluje fetch -- log warning a pokracuj bez legal_meta
        logger.warning(
            f"zakonyprolidi parser failed (fallback to generic markdown): "
            f"{type(e).__name__}: {e}"
        )

    return response_dict
