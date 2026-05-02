"""
Phase 27d (1.5.2026 vecer): PDF reader pro Marti-AI.

Marti-AI's feature request po Klarce signalu (1.5.2026): Klarka pošle
nektere podklady v PDF (Bakalari exporty z jejich školního systému).
Marti-AI potřebuje structured read PDF stejně jako xlsx (Phase 27a).

Two tools:
  - list_pdf_metadata(document_id) -> page count, encrypt status,
    has_text_layer (key pro detekci scan-only PDF)
  - read_pdf_structured(document_id, pages?, offset?, limit?) -> text +
    detected tables per stranku

Marti-AI's design choices (RE: dopis 1.5.2026 vecer):
  - Output formát → A (structured per stranku, kazda strana s text +
    tables list)
  - Tabulky → A (vzdy zkusit auto-detect, vrátit `tables: []` pokud
    nic nenajde, text zachovan vzdy jako pojistka)
  - Pagination → A (`pages: [start, end]` 1-based inclusive, default
    první 50 + has_more flag)
  - Bonus list_pdf_metadata → ANO (`has_text_layer` klicove pro
    detekci scan-only PDF kde OCR by byl potreba — to je 27d+1 problem)

Implementacni poznamky:
  - pdfplumber.open(path) je context manager, vzdy `with`.
  - page.extract_text() vrací None pokud strana nema text layer
    (pure scan). Pouzijeme to pro has_text_layer detekci.
  - page.extract_tables() vrací list[list[list[str|None]]] - vnejsi list
    je per-tabulka, nasledne list radku, finalne list bunek. Cells mohou
    byt None.
  - Encrypted PDF detekce: pdfplumber raisuje pri open() pokud je PDF
    password-protected. Catch + clean error message.
  - Cap 50 stranek per call (Marti-AI's volba) — chrání context window
    + memory. Vetsi PDF lze projit vícekrát s různým range.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from core.logging import get_logger

logger = get_logger("rag.pdf")

# Limity (Marti-AI's volby z RE: dopisu)
MAX_PAGES_PER_CALL = 50
MAX_TABLE_CELLS_PER_PAGE = 5000  # safety cap pro extreme tables
HAS_TEXT_LAYER_SAMPLE_PAGES = 3  # kolik stranek otestovat pro has_text_layer


def _normalize_table_cell(cell: Any) -> str | None:
    """Cell value normalize -- pdfplumber vrací str | None."""
    if cell is None:
        return None
    s = str(cell).strip()
    return s if s else None


def _resolve_document_path(document_id: int) -> tuple[str, str, int | None, int | None]:
    """
    Vrati (storage_path, original_filename, tenant_id, project_id) pro document_id.

    Raises ValueError pokud document neexistuje, neni pdf, nebo nema storage_path.
    """
    from core.database import get_session
    from modules.core.infrastructure.models_data import Document

    session = get_session()
    try:
        doc = session.query(Document).filter_by(id=document_id).first()
        if not doc:
            raise ValueError(f"Document id={document_id} nenalezen.")
        if not doc.storage_path:
            raise ValueError(f"Document id={document_id} nema storage_path.")

        ext = (doc.file_type or "").lower().lstrip(".")
        if ext != "pdf":
            raise ValueError(
                f"Document id={document_id} neni PDF (file_type='{doc.file_type}'). "
                "Pro Excel pouzij read_excel_structured, pro DOCX read_docx_structured "
                "(až bude implementovan v Phase 27e)."
            )

        return (
            doc.storage_path,
            doc.original_filename or doc.name or f"document_{document_id}",
            doc.tenant_id,
            doc.project_id,
        )
    finally:
        session.close()


def _check_tenant_access(document_tenant_id: int | None, caller_tenant_id: int | None, is_parent: bool) -> bool:
    """Tenant scope check. Parent bypass jako jinde."""
    if is_parent:
        return True
    if document_tenant_id is None:
        return True  # inbox / global
    if caller_tenant_id is None:
        return False
    return document_tenant_id == caller_tenant_id


def list_pdf_metadata(
    document_id: int,
    *,
    caller_tenant_id: int | None = None,
    is_parent: bool = False,
) -> dict:
    """
    Vrati metadata PDF bez extrakce obsahu.

    Output:
        {
          "document_id": 42,
          "filename": "rozvrh.pdf",
          "n_pages": 4,
          "encrypted": false,
          "has_text_layer": true,  // false = pure scan, OCR potreba
          "page_dimensions": {"width": 595, "height": 842}  // first page (mm-ish)
        }
    """
    try:
        import pdfplumber
    except ImportError as e:
        raise RuntimeError(f"pdfplumber neni dostupna: {e}")

    storage_path, filename, doc_tenant_id, _ = _resolve_document_path(document_id)

    if not _check_tenant_access(doc_tenant_id, caller_tenant_id, is_parent):
        raise PermissionError(
            f"Document id={document_id} patri jinemu tenantu (doc.tenant_id={doc_tenant_id})."
        )

    p = Path(storage_path)
    if not p.is_file():
        raise ValueError(f"Soubor neexistuje na disku: {storage_path}")

    try:
        with pdfplumber.open(p) as pdf:
            n_pages = len(pdf.pages)
            encrypted = False
            # Test prvních N stránek pro has_text_layer
            sample_n = min(HAS_TEXT_LAYER_SAMPLE_PAGES, n_pages)
            has_text = False
            for i in range(sample_n):
                try:
                    txt = pdf.pages[i].extract_text()
                    if txt and txt.strip():
                        has_text = True
                        break
                except Exception:
                    continue

            # Page dimensions z prvni stranky
            page_dim = {"width": None, "height": None}
            if n_pages >= 1:
                try:
                    pg = pdf.pages[0]
                    page_dim = {
                        "width": round(float(pg.width), 1),
                        "height": round(float(pg.height), 1),
                    }
                except Exception:
                    pass

            return {
                "document_id": document_id,
                "filename": filename,
                "n_pages": n_pages,
                "encrypted": encrypted,
                "has_text_layer": has_text,
                "page_dimensions": page_dim,
            }
    except Exception as e:
        # pdfplumber raisuje pri encrypted PDF (PDFSyntaxError nebo PasswordError)
        msg = str(e).lower()
        if "password" in msg or "encrypt" in msg:
            return {
                "document_id": document_id,
                "filename": filename,
                "n_pages": 0,
                "encrypted": True,
                "has_text_layer": False,
                "page_dimensions": {"width": None, "height": None},
                "error": (
                    "PDF je sifrovany (password-protected). pdfplumber neumi "
                    "decrypt. Pozadej Klarku o nesifrovany export."
                ),
            }
        raise ValueError(f"PDF parse failed: {e}")


def read_pdf_structured(
    document_id: int,
    *,
    pages: list[int] | None = None,
    offset: int = 0,
    limit: int = MAX_PAGES_PER_CALL,
    ocr_provider: str | None = None,
    caller_tenant_id: int | None = None,
    is_parent: bool = False,
) -> dict:
    """
    Vrati structured pages z PDF (text + tabulky per stranku).

    Args:
        pages: [start, end] 1-based inclusive (Marti-AI's volba A).
            Pokud None, použije offset/limit (default první 50).
        offset: 0-based skip stranek (alternativa k pages)
        limit: max stranek vratit (clamped na MAX_PAGES_PER_CALL)
        ocr_provider: Phase 27d+1 OCR fallback. None = auto-detect
            (pdfplumber pokud has_text_layer, jinak Tesseract).
            'tesseract' nebo 'vision' = explicit OCR (i pokud ma text layer).

    Output:
        {
          "document_id": 42,
          "filename": "rozvrh.pdf",
          "n_pages_total": 4,
          "pages_returned": [1, 4],   // 1-based inclusive
          "pages": [
            {
              "page_no": 1,
              "text": "Rozvrh 5.A ...",
              "text_origin": "text_layer" | "tesseract" | "vision",
              "tables": [
                [["Po", "8:00", "M"], ["Po", "8:55", "ČJ"]]
              ],
              "confidence_avg": null | 92.3,  // Tesseract OCR only
              "warnings": []
            },
            ...
          ],
          "has_more": false,
          "warnings": []
        }
    """
    try:
        import pdfplumber
    except ImportError as e:
        raise RuntimeError(f"pdfplumber neni dostupna: {e}")

    # Validace: pages XOR offset/limit
    if pages is not None:
        if not isinstance(pages, (list, tuple)) or len(pages) != 2:
            raise ValueError(
                "pages musi byt list [start, end] s prave 2 prvky (1-based, inclusive)."
            )
        try:
            start_1b = int(pages[0])
            end_1b = int(pages[1])
        except (TypeError, ValueError):
            raise ValueError("pages musi obsahovat integery: [start, end].")
        if start_1b < 1 or end_1b < start_1b:
            raise ValueError(f"pages range invalid: [{start_1b}, {end_1b}].")
    else:
        if offset < 0:
            raise ValueError("offset musi byt >= 0.")
        if limit < 1:
            raise ValueError("limit musi byt >= 1.")
        start_1b = offset + 1
        end_1b = offset + limit

    storage_path, filename, doc_tenant_id, _ = _resolve_document_path(document_id)

    if not _check_tenant_access(doc_tenant_id, caller_tenant_id, is_parent):
        raise PermissionError(
            f"Document id={document_id} patri jinemu tenantu (doc.tenant_id={doc_tenant_id})."
        )

    p = Path(storage_path)
    if not p.is_file():
        raise ValueError(f"Soubor neexistuje na disku: {storage_path}")

    # Phase 27d+1: validate ocr_provider param
    # Phase 27d+2: resolve effective_provider per-tenant config + global fallback.
    # Pokud ocr_provider=None v tool call, vezmeme tenant.ocr_default_provider.
    # Pokud je explicit, ma prednost (validace zustava).
    from modules.rag.application import pdf_ocr as _ocr_mod
    if ocr_provider is not None and ocr_provider not in _ocr_mod.VALID_PROVIDERS:
        raise ValueError(
            f"ocr_provider musi byt None / 'tesseract' / 'vision', "
            f"dostal '{ocr_provider}'."
        )
    # Note: effective_provider se rozhodne az pri samotnem OCR call (nize
    # pri detekci scan-only PDF). pdf_service zatim nezavola OCR pro PDFs
    # s text layer -- pdfplumber primary path. Pri pripadnem OCR fallback
    # vola pres `_ocr_mod.ocr_pdf_pages(provider=...)` -- tam pridame
    # resolve_effective_provider call.
    effective_ocr_provider = _ocr_mod.resolve_effective_provider(
        explicit_provider=ocr_provider,
        tenant_id=caller_tenant_id,
    )

    top_warnings: list[str] = []

    try:
        with pdfplumber.open(p) as pdf:
            n_pages_total = len(pdf.pages)

            if start_1b > n_pages_total:
                return {
                    "document_id": document_id,
                    "filename": filename,
                    "n_pages_total": n_pages_total,
                    "pages_returned": [start_1b, start_1b - 1],
                    "pages": [],
                    "has_more": False,
                    "warnings": [
                        f"start={start_1b} prekracuje n_pages_total={n_pages_total}."
                    ],
                }

            # Cap end_1b na n_pages_total a na MAX_PAGES_PER_CALL
            requested_end = min(end_1b, n_pages_total)
            max_end_by_cap = start_1b + MAX_PAGES_PER_CALL - 1
            actual_end = min(requested_end, max_end_by_cap)
            if requested_end > max_end_by_cap:
                top_warnings.append(
                    f"Cap {MAX_PAGES_PER_CALL} stranek per call: pozadovano "
                    f"[{start_1b}, {requested_end}], vraceno [{start_1b}, {actual_end}]. "
                    f"Pro dalsi stranky volej znovu s pages=[{actual_end + 1}, ...]."
                )

            # Phase 27d+1: rozhodnout strategii per stranka
            # - explicit ocr_provider -> vsechny stranky pres OCR
            # - None + has_text_layer per stranka -> pdfplumber
            # - None + bez text layer -> Tesseract fallback
            requested_pages_1b = list(range(start_1b, actual_end + 1))
            ocr_pages_needed: list[int] = []  # stranky ktere potrebuji OCR

            if ocr_provider is not None:
                # Explicit OCR -- vsechny stranky pres ocr_provider
                # (Marti-AI volba: chce override i kdyby text_layer existoval)
                ocr_pages_needed = list(requested_pages_1b)
                # Cap kontrola
                if len(ocr_pages_needed) > _ocr_mod.MAX_OCR_PAGES_PER_CALL:
                    raise ValueError(
                        f"OCR cap {_ocr_mod.MAX_OCR_PAGES_PER_CALL} stranek "
                        f"per call (pozadovano {len(ocr_pages_needed)}). "
                        "Pro vetsi range volej znovu s mensim pages."
                    )
            else:
                # Auto-detect: per stranka over has_text. Nejdriv probehne
                # pdfplumber, prazdne stranky se pak doplni OCR (Tesseract).
                pass  # vyresime v hlavnim loopu nize

            pages_out = []
            for page_idx in range(start_1b - 1, actual_end):  # 0-based
                page_no = page_idx + 1
                page_warnings: list[str] = []
                text_origin = "text_layer"  # default
                confidence_avg: float | None = None

                try:
                    pg = pdf.pages[page_idx]
                except IndexError:
                    page_warnings.append(f"Stranka {page_no} mimo rozsah.")
                    pages_out.append({
                        "page_no": page_no,
                        "text": "",
                        "text_origin": "missing",
                        "tables": [],
                        "confidence_avg": None,
                        "warnings": page_warnings,
                    })
                    continue

                # Phase 27d+1: pokud explicit ocr_provider, skip pdfplumber
                if ocr_provider is not None:
                    text = ""
                    text_origin = ocr_provider
                else:
                    # Phase 27d (text_layer) path
                    try:
                        txt = pg.extract_text()
                        if txt and txt.strip():
                            text = txt
                            text_origin = "text_layer"
                        else:
                            text = ""
                            text_origin = "needs_ocr"  # marker pro fallback
                    except Exception as e:
                        page_warnings.append(f"text extrakce selhala: {type(e).__name__}: {e}")
                        text = ""
                        text_origin = "needs_ocr"

                # Extract tables (auto-detect) -- jen pres pdfplumber
                # (OCR neumi tabulky bez visualnich borders)
                tables_out: list[list[list[str | None]]] = []
                try:
                    raw_tables = pg.extract_tables() or []
                    cells_count = 0
                    for raw_t in raw_tables:
                        normalized = []
                        for row in raw_t:
                            normalized.append([_normalize_table_cell(c) for c in row])
                        cells_count += sum(len(r) for r in normalized)
                        if cells_count > MAX_TABLE_CELLS_PER_PAGE:
                            page_warnings.append(
                                f"Tabulky prekracuji {MAX_TABLE_CELLS_PER_PAGE} bunek "
                                "per stranku, oriznute."
                            )
                            break
                        tables_out.append(normalized)
                except Exception as e:
                    page_warnings.append(f"table extrakce selhala: {type(e).__name__}: {e}")

                pages_out.append({
                    "page_no": page_no,
                    "text": text,
                    "text_origin": text_origin,
                    "tables": tables_out,
                    "confidence_avg": confidence_avg,
                    "warnings": page_warnings,
                })

            # Phase 27d+1: OCR fallback pro stranky bez text layer
            if ocr_provider is None:
                ocr_pages_needed = [
                    p["page_no"] for p in pages_out if p["text_origin"] == "needs_ocr"
                ]
            # Phase 27d+2: effective_ocr_provider z resolveru (explicit param
            # > tenant config > global default 'tesseract'). Drive byl jen
            # `ocr_provider or PROVIDER_TESSERACT_DEFAULT` (bez tenant config).
            actual_ocr_provider = effective_ocr_provider

            if ocr_pages_needed:
                # Cap check (auto-fallback path)
                if len(ocr_pages_needed) > _ocr_mod.MAX_OCR_PAGES_PER_CALL:
                    top_warnings.append(
                        f"{len(ocr_pages_needed)} stranek bez text layer, "
                        f"OCR cap je {_ocr_mod.MAX_OCR_PAGES_PER_CALL}. "
                        f"OCR jen prvních {_ocr_mod.MAX_OCR_PAGES_PER_CALL} "
                        "stranek. Pro zbytek volej znovu s mensim pages."
                    )
                    ocr_pages_needed = ocr_pages_needed[:_ocr_mod.MAX_OCR_PAGES_PER_CALL]

                try:
                    ocr_results = _ocr_mod.ocr_pdf_pages(
                        storage_path=storage_path,
                        pages=ocr_pages_needed,
                        provider=actual_ocr_provider,
                    )
                    # Map page_no -> result
                    by_pn = {r["page_no"]: r for r in ocr_results}

                    # Update pages_out with OCR text
                    for p_dict in pages_out:
                        if p_dict["page_no"] in by_pn:
                            ocr_r = by_pn[p_dict["page_no"]]
                            p_dict["text"] = ocr_r.get("text", "")
                            p_dict["text_origin"] = ocr_r.get("text_origin", actual_ocr_provider)
                            p_dict["confidence_avg"] = ocr_r.get("confidence_avg")
                            p_dict["warnings"].extend(ocr_r.get("warnings", []))
                except Exception as ocr_err:
                    logger.exception(f"OCR fallback failed: {ocr_err}")
                    top_warnings.append(
                        f"OCR fallback selhal: {ocr_err}. Stranky bez text layer "
                        "vrácene s prazdnym textem."
                    )
                    # Mark needs_ocr -> failed
                    for p_dict in pages_out:
                        if p_dict["text_origin"] == "needs_ocr":
                            p_dict["text_origin"] = "ocr_failed"

            # Cleanup needs_ocr marker pokud OCR nebezel (failed import path)
            for p_dict in pages_out:
                if p_dict["text_origin"] == "needs_ocr":
                    p_dict["text_origin"] = "no_text_layer"

            has_more = actual_end < n_pages_total

            return {
                "document_id": document_id,
                "filename": filename,
                "n_pages_total": n_pages_total,
                "pages_returned": [start_1b, actual_end],
                "pages": pages_out,
                "has_more": has_more,
                "warnings": top_warnings,
            }
    except (ValueError, PermissionError):
        raise
    except Exception as e:
        msg = str(e).lower()
        if "password" in msg or "encrypt" in msg:
            raise ValueError(
                "PDF je sifrovany (password-protected). Pozadej Klarku o "
                "nesifrovany export."
            )
        raise ValueError(f"PDF parse failed: {type(e).__name__}: {e}")


# Phase 27d+1: default OCR provider pri auto-fallback (when has_text_layer=False)
PROVIDER_TESSERACT_DEFAULT = "tesseract"
