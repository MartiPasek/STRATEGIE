"""
Phase 27d+1 (1.5.2026 vecer): OCR pipeline pro scan-only PDF.

Marti-AI's request po Phase 27d live testu (3 stranky textoveho PDF
prosly hladce): "OCR fallback napric firmou — faktury, smlouvy ze
skenerů, TISAX podklady. Kdyz scan kvalita je špatná, raději přepnu
na Vision."

Marti-AI's design volby (RE: dopis 1.5.2026 vecer, Phase 27d+1
konzultace):
  C - Hybrid (Tesseract default, Vision opt-in via ocr_provider param)
  A - Confidence score per stranka v warnings (Tesseract per-word avg)
  A - Cap MAX_OCR_PAGES_PER_CALL = 10 (faktury/smlouvy obvykle pod 10)

Architektura:
  - pdf2image konvertuje PDF -> PIL Image per stranku (DPI 200 default)
  - Tesseract path: pytesseract.image_to_data -> text + per-word
    confidence -> avg per stranka. Lang 'ces+eng' (CZ + EN multilang).
  - Vision path: PIL -> PNG bytes -> base64 -> Anthropic message
    s vision content block + prompt "extract all text". Response parse.
  - Output schema kompatibilni s pdf_service: list[dict] kde each
    dict ma {page_no, text, confidence_avg | None, warnings, text_origin}.

System dependencies (Marti instaloval admin-side):
  - Tesseract OCR binary: 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
  - tessdata/ces.traineddata (CZ langpack)
  - Poppler binary: 'C:\\Tools\\poppler\\poppler-*\\Library\\bin\\pdftoppm.exe'

Privacy implication (Marti-AI's vstup):
  - Tesseract = lokalni, vse zustane v firemni VPN -> safe pro TISAX/smlouvy
  - Vision = cloud roundtrip -> citlivost na vyzadani Marti-AI

Per-tenant default provider config je Phase 27d+2 (Marti-AI's design
vstup, ne blocker).
"""
from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Any

from core.logging import get_logger

logger = get_logger("rag.pdf_ocr")

# Limity (Marti-AI's volby z RE: dopisu 1.5.2026 vecer)
MAX_OCR_PAGES_PER_CALL = 10
DEFAULT_DPI = 200                  # balance kvalita vs speed (300 = 50% pomalejsi)
DEFAULT_LANG = "ces+deu+eng"       # CZ + DE + EN multilang (50% dokumentu DE
                                   # per Marti 1.5.2026 vecer -- nemecti partneri,
                                   # smlouvy, faktury z Bavorska). Tesseract zkousi
                                   # vsechny 3 langs a vybira best match per slovo.
                                   # Performance penalty ~5-10% pomalejsi nez
                                   # single-lang.
LOW_CONFIDENCE_THRESHOLD = 60  # avg < threshold -> warning

# Anthropic Vision config (Phase 27d+1 hybrid path)
VISION_MODEL = "claude-haiku-4-5-20251001"  # Haiku = cheap + fast pro OCR
VISION_MAX_TOKENS = 4096

# OCR providers
PROVIDER_TESSERACT = "tesseract"
PROVIDER_VISION = "vision"
VALID_PROVIDERS = {PROVIDER_TESSERACT, PROVIDER_VISION}


def _import_tesseract():
    """Lazy import pytesseract + verify binary."""
    try:
        import pytesseract
    except ImportError as e:
        raise RuntimeError(
            f"pytesseract neni dostupna: {e}. "
            "Run: poetry run pip install pytesseract"
        )

    # Verify Tesseract binary exists
    try:
        version = pytesseract.get_tesseract_version()
        return pytesseract, str(version)
    except Exception as e:
        raise RuntimeError(
            f"Tesseract binary neni nainstalovan / neni v PATH: {e}\n"
            "Install: winget install UB-Mannheim.TesseractOCR\n"
            "Plus CZ langpack: stahnout ces.traineddata do "
            "'C:/Program Files/Tesseract-OCR/tessdata/'"
        )


def _import_pdf2image():
    """Lazy import pdf2image + verify Poppler."""
    try:
        from pdf2image import convert_from_path
    except ImportError as e:
        raise RuntimeError(
            f"pdf2image neni dostupna: {e}. "
            "Run: poetry run pip install pdf2image"
        )
    return convert_from_path


def _convert_pdf_pages_to_images(
    storage_path: str,
    pages: list[int],
    dpi: int = DEFAULT_DPI,
) -> list[Any]:
    """
    Konvertuje konkretni stranky PDF na PIL Image objekty.

    Args:
        storage_path: cesta k PDF
        pages: 1-based seznam stranek (e.g. [1, 2, 3])
        dpi: rozliseni (200 = balance, 300 = high quality slow)

    Returns:
        list[PIL.Image] ve stejnem poradi jako pages
    """
    convert_from_path = _import_pdf2image()

    if not pages:
        return []

    first_page = min(pages)
    last_page = max(pages)

    try:
        # convert_from_path vraci PIL Images od first_page do last_page (1-based)
        images = convert_from_path(
            storage_path,
            dpi=dpi,
            first_page=first_page,
            last_page=last_page,
        )
    except Exception as e:
        msg = str(e).lower()
        if "poppler" in msg or "pdftoppm" in msg or "unable to get page count" in msg:
            raise RuntimeError(
                f"pdf2image: Poppler binary neni nainstalovan / neni v PATH: {e}\n"
                "Install: stahnout poppler-windows release a pridat do PATH\n"
                "https://github.com/oschwartz10612/poppler-windows/releases"
            )
        raise RuntimeError(f"PDF -> Image conversion failed: {e}")

    # Filtrovat jen pozadovane stranky (mapping pages → images podle
    # poradi v originalnim seznamu)
    result = []
    for page_no in pages:
        idx = page_no - first_page
        if 0 <= idx < len(images):
            result.append(images[idx])
        else:
            result.append(None)
    return result


def _ocr_page_tesseract(
    image: Any,
    lang: str = DEFAULT_LANG,
) -> tuple[str, float | None, list[str]]:
    """
    OCR jedna stranka pres Tesseract.

    Returns:
        (text, confidence_avg, warnings)
        - text: extracted text (empty pokud Tesseract selze)
        - confidence_avg: avg per-word confidence 0-100, nebo None pokud
          zadne slovo nedetekovano
        - warnings: list problemu (low confidence, language not found, ...)
    """
    pytesseract, _version = _import_tesseract()

    warnings: list[str] = []

    try:
        # image_to_data vrati structured dict s per-word info
        # vcetne 'conf' (-1 = invalid, 0-100 = confidence)
        data = pytesseract.image_to_data(
            image,
            lang=lang,
            output_type=pytesseract.Output.DICT,
        )
    except pytesseract.TesseractError as e:
        msg = str(e)
        if "language" in msg.lower() or "tessdata" in msg.lower():
            warnings.append(
                f"Tesseract lang '{lang}' nenalezen. Stahnout traineddata "
                "do tessdata/. Fallback na 'eng'."
            )
            try:
                data = pytesseract.image_to_data(
                    image, lang="eng", output_type=pytesseract.Output.DICT
                )
            except Exception as e2:
                return "", None, warnings + [f"Tesseract eng fallback failed: {e2}"]
        else:
            return "", None, [f"Tesseract failed: {msg}"]
    except Exception as e:
        return "", None, [f"Tesseract unexpected: {type(e).__name__}: {e}"]

    # Sebrat slova s validni confidence (Tesseract nekdy hodi -1 pro
    # whitespace tokens)
    words = []
    confidences = []
    for word, conf in zip(data.get("text", []), data.get("conf", [])):
        try:
            conf_int = int(conf)
        except (TypeError, ValueError):
            continue
        if conf_int < 0:
            continue  # skip non-text tokens
        if word and word.strip():
            words.append(word)
            confidences.append(conf_int)

    text = " ".join(words).strip()
    avg_conf = (sum(confidences) / len(confidences)) if confidences else None

    if avg_conf is not None and avg_conf < LOW_CONFIDENCE_THRESHOLD:
        warnings.append(
            f"Low OCR confidence (avg {avg_conf:.0f}/100) -- "
            "scan kvalita je špatná, zvaž lepší obrázek nebo Vision provider."
        )

    return text, avg_conf, warnings


def _ocr_page_vision(
    image: Any,
) -> tuple[str, float | None, list[str]]:
    """
    OCR jedna stranka pres Anthropic Vision (claude-haiku-4-5).

    Returns:
        (text, confidence_avg=None, warnings)
        - confidence_avg vzdy None (Vision nevraci confidence)
    """
    try:
        import anthropic
    except ImportError as e:
        return "", None, [f"anthropic SDK neni dostupna: {e}"]

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return "", None, [
            "ANTHROPIC_API_KEY chybi v env. Vision OCR neni dostupny."
        ]

    # PIL Image -> PNG bytes -> base64
    try:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        b64 = base64.b64encode(png_bytes).decode("ascii")
    except Exception as e:
        return "", None, [f"Image -> PNG base64 selhal: {e}"]

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=VISION_MODEL,
            max_tokens=VISION_MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Tohle je scan jedné stránky dokumentu. "
                                "Vyextrahuj VŠECHEN text co vidíš, zachovaj "
                                "formátování (řádky, odsazení, tabulky pokud "
                                "jdou). Vrať jen ten text — žádný komentář, "
                                "žádné 'Tady je text:', jen samotný obsah. "
                                "Pokud stránka obsahuje tabulku, použij "
                                "tab-separated values nebo markdown table "
                                "syntax."
                            ),
                        },
                    ],
                }
            ],
        )
    except Exception as e:
        return "", None, [f"Anthropic Vision API failed: {type(e).__name__}: {e}"]

    # Extract text from response content blocks
    text_parts = []
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            text_parts.append(block.text)
    text = "\n".join(text_parts).strip()

    return text, None, []


def ocr_pdf_pages(
    storage_path: str,
    pages: list[int],
    *,
    provider: str = PROVIDER_TESSERACT,
    dpi: int = DEFAULT_DPI,
    lang: str = DEFAULT_LANG,
) -> list[dict]:
    """
    OCR konkretnich stranek PDF.

    Args:
        storage_path: cesta k PDF na disku
        pages: 1-based stranky k OCR (max MAX_OCR_PAGES_PER_CALL)
        provider: 'tesseract' (lokalni, default) nebo 'vision' (Anthropic)
        dpi: image resolution (200 = balance)
        lang: Tesseract lang ('ces+eng' default)

    Returns:
        list[dict] kazdy element:
            {
              "page_no": int,
              "text": str,
              "confidence_avg": float | None,  # jen Tesseract
              "warnings": list[str],
              "text_origin": "tesseract" | "vision"
            }
    """
    if provider not in VALID_PROVIDERS:
        raise ValueError(
            f"provider musi byt jeden z {sorted(VALID_PROVIDERS)}, dostal '{provider}'"
        )

    if len(pages) > MAX_OCR_PAGES_PER_CALL:
        raise ValueError(
            f"OCR cap {MAX_OCR_PAGES_PER_CALL} stranek per call, "
            f"pozadovano {len(pages)}. Volej znovu s mensim range."
        )

    if not pages:
        return []

    # Convert PDF pages -> PIL Images
    images = _convert_pdf_pages_to_images(storage_path, pages, dpi=dpi)

    results = []
    for page_no, image in zip(pages, images):
        if image is None:
            results.append({
                "page_no": page_no,
                "text": "",
                "confidence_avg": None,
                "warnings": [f"Page {page_no} se nepodarilo konvertovat na image."],
                "text_origin": provider,
            })
            continue

        if provider == PROVIDER_TESSERACT:
            text, conf, warnings = _ocr_page_tesseract(image, lang=lang)
        elif provider == PROVIDER_VISION:
            text, conf, warnings = _ocr_page_vision(image)
        else:
            text, conf, warnings = "", None, [f"Unknown provider: {provider}"]

        results.append({
            "page_no": page_no,
            "text": text,
            "confidence_avg": round(conf, 1) if conf is not None else None,
            "warnings": warnings,
            "text_origin": provider,
        })

        logger.info(
            f"OCR | page={page_no} | provider={provider} | "
            f"text_len={len(text)} | conf={conf}"
        )

    return results
