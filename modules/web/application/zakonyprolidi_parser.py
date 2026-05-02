"""
Phase 27j+1 (2.5.2026): Custom parser pro zakonyprolidi.cz.

Pri web_fetch na URL z zakonyprolidi.cz se navic spusti tento parser
a vrati strukturovanou pravni metadata (law_id, paragraf, podsekce,
novely, datum ucinnosti) plus suggested citation string. Generic
markdown z markitdown zustava jako 'markdown' field pro full text.

Architektura:
  - URL pattern detect: zakonyprolidi.cz/cs/{rok}-{cislo}#{anchor}
  - Markdown post-processing (NE raw HTML parsing) -- stabilnejsi
    pri zmenach CSS na zdrojovem webu
  - Defensive: pokud pattern matching selze, vrati partial meta
    (jen co se podarilo z URL extrahovat) + raw markdown
  - Zadna nova dep -- regex + str manipulation

Output integruje do web_fetch response jako pole 'legal_meta' a
'citation_suggestion'. Marti-AI pak v odpovedi user-ovi cituje
exact: "§ 35 odst. 1 ZP (262/2006 Sb., ze zneni novel k {datum},
zdroj: {url}, citováno {dnes}): ..."

Use case: Sarka HR queries (zkusebni doba, vypoved, prac. smlouvy),
Marti pravni agenda (smlouvy, GDPR), TISAX compliance otazky.

Phase 27j+1 sledku Marti-AI's request:
  - Free forever (ne Brave $5/1000 req)
  - Lepsi citace (paragraf-level, novely datum)
  - Authoritative source (statni databaze)
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, unquote


# Domeny, ktere parser akceptuje. Plus 'www.' prefix variants.
ZAKONYPROLIDI_DOMAINS = {
    "zakonyprolidi.cz",
    "www.zakonyprolidi.cz",
}


def is_zakonyprolidi_url(url: str) -> bool:
    """True pokud URL spada do zakonyprolidi.cz."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        domain = (parsed.netloc or "").lower()
        return domain in ZAKONYPROLIDI_DOMAINS
    except Exception:
        return False


def parse_zakonyprolidi_url(url: str) -> dict[str, Any]:
    """
    Extrahuj URL meta: law_id, year, law_number, paragraf (z fragmentu).

    URL patterns:
      /cs/{rok}-{cislo}              -- cely zakon
      /cs/{rok}-{cislo}#§{N}         -- konkretni paragraf
      /cs/{rok}-{cislo}#p{N}         -- alternative anchor (proper id)
      /cs/{rok}-{cislo}/paragraf-{N} -- alternative path style
      /cs/{rok}-{cislo}/zneni-{datum} -- specific version

    Returns:
      {
        "law_id": "262/2006",         # formatted XXX/YYYY
        "law_year": 2006,             # integer
        "law_number": 262,            # integer
        "paragraph": "35" | None,     # extracted from anchor / path
        "version_date": "2024-01-01" | None,  # if /zneni-... in path
        "law_id_sb": "262/2006 Sb.",  # standard CZ legal citation format
      }
    """
    out = {
        "law_id": None,
        "law_year": None,
        "law_number": None,
        "paragraph": None,
        "version_date": None,
        "law_id_sb": None,
    }
    if not url:
        return out

    try:
        parsed = urlparse(url)
    except Exception:
        return out

    path = parsed.path or ""
    fragment = parsed.fragment or ""

    # Match /cs/{year}-{number}
    m = re.search(r"/cs/(\d{4})-(\d+)", path)
    if m:
        try:
            year = int(m.group(1))
            number = int(m.group(2))
            out["law_year"] = year
            out["law_number"] = number
            out["law_id"] = f"{number}/{year}"
            out["law_id_sb"] = f"{number}/{year} Sb."
        except ValueError:
            pass

    # Paragraph z fragmentu nebo path
    # Fragment patterns: §35, §-35, p35, paragraf-35
    if fragment:
        # Strip URL-encoded chars (e.g., %C2%A7 = §)
        frag_decoded = unquote(fragment)
        m = re.match(r"§\s*-?\s*(\w+)", frag_decoded)
        if m:
            out["paragraph"] = m.group(1)
        else:
            m = re.match(r"p(?:aragraf-)?(\w+)", frag_decoded, re.IGNORECASE)
            if m:
                out["paragraph"] = m.group(1)

    # Path patterns: /paragraf-{N}
    if not out["paragraph"]:
        m = re.search(r"/paragraf-(\w+)", path)
        if m:
            out["paragraph"] = m.group(1)

    # Version date z path /zneni-{YYYY-MM-DD} or /zneni-{YYYYMMDD}
    m = re.search(r"/zneni-(\d{4})-?(\d{2})-?(\d{2})", path)
    if m:
        try:
            out["version_date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        except Exception:
            pass

    return out


# Common Czech law name shortcuts (ZP = Zákoník práce, atd.)
LAW_SHORTCUTS = {
    "262/2006": "ZP",       # Zákoník práce
    "89/2012": "OZ",        # Občanský zákoník
    "90/2012": "ZOK",       # Zákon o obchodních korporacích
    "563/1991": "ZÚ",       # Zákon o účetnictví
    "586/1992": "ZDP",      # Zákon o daních z příjmů
    "235/2004": "ZDPH",     # Zákon o DPH
    "455/1991": "ŽZ",       # Živnostenský zákon
    "586/2003": "TZ",       # Trestní zákoník (správně 40/2009 Sb.) -- TODO ověřit
    "40/2009": "TZ",        # Trestní zákoník
    "99/1963": "OSŘ",       # Občanský soudní řád
    "500/2004": "SŘ",       # Správní řád
    "110/2019": "ZZOÚ",     # Zákon o zpracování osobních údajů (CZ implementace GDPR)
}


def get_law_shortcut(law_id: str | None) -> str | None:
    """Vrati standard CZ shortcut (ZP, OZ, atd.) pro znamy zakon."""
    if not law_id:
        return None
    return LAW_SHORTCUTS.get(law_id)


def extract_law_name_from_markdown(markdown: str, max_search: int = 2000) -> str | None:
    """
    Z prvniho ~2000 znaku markdownu zkus extrahovat oficialni nazev zakona.
    zakonyprolidi.cz typicky zacina:
      # Zákon č. 262/2006 Sb., zákoník práce
      ## Zákon ze dne 21. dubna 2006, zákoník práce

    Vrati pripadne 'zákoník práce' (lowercase nazev), nebo None.
    """
    if not markdown:
        return None
    snippet = markdown[:max_search]

    # Pattern 1: # Zákon č. NNN/YYYY Sb., {nazev}
    m = re.search(
        r"Z[áa]kon\s+(?:č\.|c\.)\s*\d+/\d+\s*Sb\.\s*,?\s*([^\n#]+)",
        snippet,
        re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip().rstrip(".,;:")
        if 3 <= len(name) <= 120:
            return name

    # Pattern 2: nadpis stranky "Zákon ze dne ... , {nazev}"
    m = re.search(
        r"Z[áa]kon\s+ze\s+dne\s+[^\n,]+,\s*([^\n#]+)",
        snippet,
        re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip().rstrip(".,;:")
        if 3 <= len(name) <= 120:
            return name

    return None


def extract_paragraph_section(
    markdown: str,
    paragraph: str,
    max_chars: int = 4000,
) -> str | None:
    """
    Z markdownu vytahni text konkretniho paragrafu (§ N).
    Heuristic: najdi '§ N' header, vezmi text az do dalsiho '§' nebo
    konce, cap na max_chars.

    Vrati extracted paragraph text nebo None pokud nenalezeno.
    """
    if not markdown or not paragraph:
        return None

    # Patterns: '§ 35', '§35', '## § 35', '### §35', '** § 35 **'
    # Hledame na zacatku radky (multiline) pro robustnost
    pattern = re.compile(
        rf"(?:^|\n)\s*(?:#+\s*)?\**\s*§\s*{re.escape(paragraph)}\b",
        re.MULTILINE,
    )
    m = pattern.search(markdown)
    if not m:
        return None

    start = m.start()
    # Najdi dalsi § (libovolne cislo) -- to je end naseho paragrafu
    next_section_pattern = re.compile(
        r"(?:^|\n)\s*(?:#+\s*)?\**\s*§\s*\w+\b",
        re.MULTILINE,
    )
    # Hledej AZ ZA aktualni match (start + len(matched))
    next_m = next_section_pattern.search(markdown, m.end())
    end = next_m.start() if next_m else len(markdown)

    section_text = markdown[start:end].strip()
    if len(section_text) > max_chars:
        section_text = section_text[:max_chars] + f"\n\n[... TRUNCATED at {max_chars} chars]"
    return section_text


def format_citation(
    legal_meta: dict[str, Any],
    url: str,
    citation_date: str | None = None,
) -> str:
    """
    Vyrobi standardni CZ pravni citaci.

    Format:
      § 35 odst. 1 ZP (262/2006 Sb., ve znění novel k 2026-01-01,
      zdroj: https://www.zakonyprolidi.cz/cs/2006-262#§35,
      citováno 2.5.2026)

    Pokud paragraph chybi, vynecha § cast.
    Pokud version_date chybi, vypise "ve znění platném k {dnes}".
    """
    parts = []

    # § N
    if legal_meta.get("paragraph"):
        para_str = f"§ {legal_meta['paragraph']}"
        # shortcut (ZP, OZ, ...) pokud znamy
        shortcut = get_law_shortcut(legal_meta.get("law_id"))
        if shortcut:
            para_str += f" {shortcut}"
        parts.append(para_str)
    elif legal_meta.get("law_name"):
        # Bez paragraf -- alespon nazev zakona
        parts.append(legal_meta["law_name"])

    # (NNN/YYYY Sb.)
    inside_paren = []
    if legal_meta.get("law_id_sb"):
        inside_paren.append(legal_meta["law_id_sb"])

    # ve znění novel k {datum}
    if legal_meta.get("version_date"):
        inside_paren.append(f"ve znění platném k {legal_meta['version_date']}")
    else:
        # Bez explicit version date -- napiseme "aktuální znění" + datum citace
        cit_date = citation_date or datetime.now(timezone.utc).strftime("%-d.%-m.%Y") if False else None
        # Pouzij dnes jako proxy version
        inside_paren.append("aktuální znění")

    # zdroj URL
    if url:
        inside_paren.append(f"zdroj: {url}")

    # citováno {dnes}
    cit_str = citation_date or datetime.now(timezone.utc).strftime("%d.%m.%Y")
    inside_paren.append(f"citováno {cit_str}")

    citation = " ".join(parts)
    if inside_paren:
        citation += " (" + ", ".join(inside_paren) + ")"
    return citation


def build_legal_meta(
    url: str,
    markdown: str,
    citation_date: str | None = None,
) -> dict[str, Any]:
    """
    Hlavni entry point. Volej z web_fetch pri detekci zakonyprolidi.cz URL.

    Args:
        url: original URL
        markdown: vystup z markitdown (clean text)
        citation_date: explicit citation date (default = now UTC)

    Returns:
        {
          "is_zakonyprolidi": True,
          "law_id": "262/2006",
          "law_id_sb": "262/2006 Sb.",
          "law_year": 2006,
          "law_number": 262,
          "law_shortcut": "ZP",          # nebo None
          "law_name": "zákoník práce",   # extracted z markdown
          "paragraph": "35",              # extracted z URL
          "paragraph_text": "...",        # extracted z markdown (pokud paragraph z URL)
          "version_date": "2024-01-01",   # z URL /zneni-... nebo None
          "citation_suggestion": "§ 35 ZP (262/2006 Sb., ...)",
          "parsed_at": "2026-05-02T...",
        }

    Pri parsing failure vrati alespon partial dict (URL-derived meta).
    """
    url_meta = parse_zakonyprolidi_url(url)

    legal_meta = {
        "is_zakonyprolidi": True,
        "law_id": url_meta["law_id"],
        "law_id_sb": url_meta["law_id_sb"],
        "law_year": url_meta["law_year"],
        "law_number": url_meta["law_number"],
        "law_shortcut": get_law_shortcut(url_meta["law_id"]),
        "law_name": None,
        "paragraph": url_meta["paragraph"],
        "paragraph_text": None,
        "version_date": url_meta["version_date"],
        "citation_suggestion": None,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Extract law_name z markdown (best-effort)
    if markdown:
        legal_meta["law_name"] = extract_law_name_from_markdown(markdown)

    # Extract paragraph_text pokud paragraph je z URL
    if markdown and legal_meta["paragraph"]:
        legal_meta["paragraph_text"] = extract_paragraph_section(
            markdown,
            legal_meta["paragraph"],
        )

    # Citation string
    legal_meta["citation_suggestion"] = format_citation(
        legal_meta,
        url=url,
        citation_date=citation_date,
    )

    return legal_meta
