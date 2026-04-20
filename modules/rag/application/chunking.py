"""
Text chunking pro RAG.

Algoritmus: char-based sliding window s overlap, ale **respektuje hranice
odstavcu a vet** -- nikdy neresuje uprostred slova ani uprostred vety
pokud to jde.

Default parametry:
    chunk_size_chars  = 2000  (~500 tokenu pro cesky text, ~400 pro anglicky)
    overlap_chars     = 200   (10% overlap, drzí kontext mezi chunky)

Vraci list of dict:
    {"index": 0, "content": "...", "char_start": 0, "char_end": 1987,
     "approx_tokens": 480}

approx_tokens: hruba aproximace 1 token = 4 char (anglicky) / 3 char (cesky).
Pro presnou hodnotu by bylo treba tiktoken/anthropic tokenizer, ale pro
debug/cost tracking staci aproximace.
"""
from __future__ import annotations

import re
from typing import Iterable

# Heuristika: Voyage embedding API ma limit 32_000 tokens per chunk,
# ale my jdeme mensimi okny pro lepsi retrieval precision.
DEFAULT_CHUNK_SIZE_CHARS = 2000
DEFAULT_OVERLAP_CHARS = 200


def chunk_text(
    text: str,
    chunk_size_chars: int = DEFAULT_CHUNK_SIZE_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[dict]:
    """Rozdeli text na chunky. Vraci list of dict s metadata."""
    if not text or not text.strip():
        return []

    # Ochrana pred patalogickymi vstupy
    chunk_size_chars = max(500, chunk_size_chars)
    overlap_chars = max(0, min(overlap_chars, chunk_size_chars // 2))

    chunks: list[dict] = []
    text_len = len(text)
    pos = 0
    index = 0

    while pos < text_len:
        end = min(pos + chunk_size_chars, text_len)

        # Pokud nejsme na konci a nemame stesti narazit na hranici,
        # zkus posunout end zpet na konec vety/odstavce v ramci poslednich
        # 200 znaku. Jinak rezeme na hard limitu.
        if end < text_len:
            window = text[max(end - 200, pos): end]
            best = _find_natural_boundary(window)
            if best is not None:
                end = max(end - 200, pos) + best

        chunk_text_value = text[pos:end].strip()
        if chunk_text_value:
            chunks.append({
                "index": index,
                "content": chunk_text_value,
                "char_start": pos,
                "char_end": end,
                "approx_tokens": _approx_token_count(chunk_text_value),
            })
            index += 1

        if end >= text_len:
            break

        # Posun s overlapem
        pos = end - overlap_chars

    return chunks


def _find_natural_boundary(window: str) -> int | None:
    """V okne hleda preferovany cut bod -- konec odstavce > konec vety > newline.
    Vraci offset v okne, nebo None pokud nic nenajde."""
    # Konec odstavce (dvojity newline)
    m = list(re.finditer(r"\n\s*\n", window))
    if m:
        return m[-1].end()
    # Konec vety (. ? ! nasledovany whitespace)
    m = list(re.finditer(r"[.!?]\s+", window))
    if m:
        return m[-1].end()
    # Konec radky
    m = list(re.finditer(r"\n", window))
    if m:
        return m[-1].end()
    return None


def _approx_token_count(text: str) -> int:
    """Hruba aproximace -- pocet tokenu = pocet slov * 1.3 (cesky / anglicky mix).
    Pro presny pocet pri cost tracking by se hodil tiktoken, ale pro nase
    debug a Voyage limity (max 32k per chunk) staci."""
    word_count = len(text.split())
    return int(word_count * 1.3)
