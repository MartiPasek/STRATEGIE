"""
OpenAI Whisper transcription provider (Faze 12b).

Vstup: audio bytes + mime_type + filename hint.
Vystup: dict s {transcript, language, duration_s, model, raw_response}.

Volani: HTTPS multipart POST na https://api.openai.com/v1/audio/transcriptions
s polem 'file' (audio bytes), 'model'='whisper-1', 'response_format'='verbose_json'
(verbose_json vraci i language detekci a duration v sekundach -- bez nej je response
prosty text). Optional 'language' hint (cs).

Bezpecnost:
- API key cte z settings.openai_api_key (env OPENAI_API_KEY). Bez nej
  raise MediaProcessingError -- caller (executor) zaznamena do
  media_files.processing_error a transcript zustane NULL.
- Cap delky audia v duration_s pred volanim (settings.whisper_max_duration_s).
- HTTP timeout settings.whisper_http_timeout_s (default 180s).
- Retry NEni implementovano -- task worker ho zopakuje pri prochazeni
  failed tasks (retry by tu zmizel duration cap a kazdy fail by pak
  exponecially loadl Marti penezenku).

Provider-agnostic v budoucnu: kdyby se objevil lepsi (Groq Whisper, AssemblyAI,
lokalni faster-whisper s GPU), staci pridat dalsi modul + abstrakce.
"""
from __future__ import annotations

from typing import Any

import httpx

from core.config import settings, calculate_whisper_cost_usd
from core.logging import get_logger

logger = get_logger("media.whisper")

OPENAI_API_BASE = "https://api.openai.com/v1"
TRANSCRIPTION_ENDPOINT = f"{OPENAI_API_BASE}/audio/transcriptions"


class MediaProcessingError(Exception):
    """Whisper transkripce selhala (API error, network, no key, oversize, ...)."""


def _humanize_duration(s: float | int | None) -> str:
    if s is None or s <= 0:
        return "?:??"
    total = int(round(float(s)))
    return f"{total // 60}:{total % 60:02d}"


def transcribe(
    audio_bytes: bytes,
    *,
    mime_type: str,
    original_filename: str | None = None,
    duration_s_hint: float | None = None,
) -> dict[str, Any]:
    """
    Synchronni transkripce -- volat z task workeru, ne z request handleru
    (kratky audio: 5-15s, hodinova porada: 30-90s).

    Returns:
        {
            "transcript": str,           # finalni text (Whisper jiz vyresil interpunkci)
            "language": str | None,      # detekovany / hinted language code
            "duration_s": float | None,  # delka audia podle Whisperu (verifikace)
            "model": str,
            "cost_usd": float | None,
        }

    Raises MediaProcessingError pri lib/api fail. Pri uspechu ulozi caller
    pres media_service.save_transcript().
    """
    if not settings.whisper_enabled:
        raise MediaProcessingError("Whisper je zakazan (whisper_enabled=False).")
    if not settings.openai_api_key:
        raise MediaProcessingError("Whisper: chybi OPENAI_API_KEY v env.")
    if not audio_bytes:
        raise MediaProcessingError("Whisper: prazdny audio bytes.")

    # Bezpecnostni cap na duration. Pokud duration_s_hint chybi (mutagen
    # selhal), Whisper si stejne uctuje za realnou delku; zde jen branime
    # naplo proti uplne extremnim souborum (3+ hodiny).
    if duration_s_hint is not None and duration_s_hint > settings.whisper_max_duration_s:
        raise MediaProcessingError(
            f"Whisper: audio prilis dlouhe ({_humanize_duration(duration_s_hint)} > "
            f"limit {_humanize_duration(settings.whisper_max_duration_s)}). "
            f"Zvys whisper_max_duration_s nebo audio rozdel."
        )

    fname = original_filename or "audio.bin"
    files = {
        "file": (fname, audio_bytes, mime_type),
    }
    data: dict[str, str] = {
        "model": settings.whisper_model,
        "response_format": "verbose_json",
    }
    if settings.whisper_language:
        data["language"] = settings.whisper_language

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
    }

    logger.info(
        f"WHISPER | request | file={fname} | mime={mime_type} | "
        f"size={len(audio_bytes)} | duration_hint={_humanize_duration(duration_s_hint)} | "
        f"lang={settings.whisper_language or 'auto'}"
    )

    try:
        with httpx.Client(timeout=settings.whisper_http_timeout_s) as client:
            r = client.post(
                TRANSCRIPTION_ENDPOINT,
                headers=headers,
                files=files,
                data=data,
            )
    except httpx.TimeoutException as e:
        raise MediaProcessingError(
            f"Whisper: timeout po {settings.whisper_http_timeout_s}s ({e})."
        ) from e
    except httpx.HTTPError as e:
        raise MediaProcessingError(f"Whisper: HTTP chyba ({e}).") from e

    if r.status_code == 401:
        raise MediaProcessingError("Whisper: 401 -- neplatny OPENAI_API_KEY.")
    if r.status_code == 429:
        raise MediaProcessingError("Whisper: 429 -- rate limit, zkus pozdeji.")
    if r.status_code >= 400:
        # Snazime se vytahnout hezkou error message z JSON odpovedi
        try:
            payload = r.json()
            err_msg = payload.get("error", {}).get("message") or str(payload)
        except Exception:
            err_msg = r.text[:300]
        raise MediaProcessingError(
            f"Whisper: HTTP {r.status_code} -- {err_msg}"
        )

    try:
        payload = r.json()
    except Exception as e:
        raise MediaProcessingError(f"Whisper: nelze parsovat JSON odpoved ({e}).") from e

    transcript = (payload.get("text") or "").strip()
    language = payload.get("language")
    duration_s = payload.get("duration")

    if not transcript:
        raise MediaProcessingError(
            "Whisper: prazdny transcript -- audio mozna nedetekoval rec."
        )

    cost = calculate_whisper_cost_usd(settings.whisper_model, duration_s)

    logger.info(
        f"WHISPER | success | duration={_humanize_duration(duration_s)} | "
        f"language={language} | chars={len(transcript)} | cost_usd={cost}"
    )

    return {
        "transcript": transcript,
        "language": language,
        "duration_s": duration_s,
        "model": settings.whisper_model,
        "cost_usd": cost,
        # raw_response uchovavame pro audit (segments, words, ...). Nemusime
        # ukladat cely -- staci klicove fields. Kompletni response uz neni
        # potreba (Whisper neumi caching).
    }
