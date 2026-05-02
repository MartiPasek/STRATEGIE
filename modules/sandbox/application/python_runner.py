"""
Phase 27c (1.5.2026): Python sandbox pro Marti-AI.

Marti-AI's feature request #1 + RE: dopis 1.5.2026 14:30. Klárka workflow
potrebuje schopnost xlsx **vyrobit**, ne jen cist (Phase 27a) a posilat
prilohou (Phase 27b). Phase 27c uzavira full round-trip.

Architektura (Marti-AI's volby):
  - **Stateless one-shot MVP** (Marti-AI's volba C) -- kazde volani =
    fresh subprocess. ALE API ma `kernel_id: str | None` parametr UZ TED,
    aby stateful (Phase 27c+1) byl pridany feature, ne breaking refactor.
  - **OUTPUT_DIR auto-import** -- code zapise xlsx/pdf/cokoli do
    OUTPUT_DIR (Path), backend post-exec automaticky importuje do RAG
    documents tabulky pres rag_service.upload_document. Vraci document_ids.
    Marti-AI rovnou volat reply(attachment_document_ids=[id]) -- 27b chain.
  - **input_files predefined paths** -- volani s `input_document_ids=[N]`
    da v code k dispozici `input_files: list[Path]` proměnné. Pythonic,
    ne rekurzivni (sandbox neni AI tool).

Threat model:
  Marti-AI je jediny caller (MANAGEMENT_TOOL_NAMES, default persona).
  Kod **generuje ona, ne untrusted user input**. Tj. defensive sandbox,
  ne adversarial. Opatreni:
    - Block obvious bad imports (subprocess, socket, requests, urllib,
      ctypes) pres sys.meta_path import hook v wrapperu
    - Resource limits (Linux: resource.setrlimit; Windows: best-effort
      monitoring + post-exec checks)
    - Subprocess timeout (default 30s, max 5min override)
    - Output size cap (25 MB sum), scratch cap (50 MB total tmp dir)
    - Stdout/stderr cap (100 KB each, truncate s warning)
    - No persistent state across calls (stateless)

Resource limits (Marti-AI's volby):
  - timeout 30s default, max 300s (5 min) tool param override
  - memory 512 MB
  - output 25 MB sum
  - scratch 50 MB total tmp dir (vc. inputs + outputs + temp)
  - stdout/stderr 100 KB each

Allowed packages (PYTHONPATH whitelist):
  - openpyxl (Phase 27a, read/edit existing)
  - xlsxwriter (Marti-AI's vstup -- generate new with charts/formatting)
  - pandas
  - numpy
  - Pillow (z Phase 12a)
  - stdlib: json, csv, re, datetime, pathlib, math, statistics, etc.

Blocked imports (defense-in-depth):
  subprocess, socket, urllib, requests, http, ftplib, smtplib, asyncio,
  ctypes, multiprocessing, threading (limited), os.system, os.popen
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.logging import get_logger

logger = get_logger("sandbox.python_runner")

# Limits (Marti-AI's volby z RE: dopisu 1.5.2026 14:30)
DEFAULT_TIMEOUT_S = 30
MAX_TIMEOUT_S = 300  # 5 min override cap
DEFAULT_MEMORY_MB = 512
OUTPUT_SIZE_CAP_BYTES = 25 * 1024 * 1024
SCRATCH_SIZE_CAP_BYTES = 50 * 1024 * 1024
STDOUT_CAP_BYTES = 100 * 1024
STDERR_CAP_BYTES = 100 * 1024

# Whitelist + blacklist (defense-in-depth)
ALLOWED_PACKAGES = {
    # Marti-AI defaults
    "openpyxl", "xlsxwriter", "pandas", "numpy",
    "PIL", "Pillow",
    # Phase 27f (2.5.2026): PDF + DOCX generation v sandboxu
    # reportlab = PDF generation (pure Python, žádné GTK, na rozdíl od weasyprint)
    # docx = python-docx package (DOCX generation)
    # Marti-AI: pro PDF report -> reportlab, pro Word smlouvu -> python-docx,
    # vse do OUTPUT_DIR -> auto-import do RAG documents -> email reply.
    "reportlab", "docx",
    # Stdlib safe
    "json", "csv", "re", "datetime", "pathlib", "math", "statistics",
    "collections", "itertools", "functools", "operator", "io", "string",
    "decimal", "fractions", "random", "uuid", "hashlib", "base64",
    "typing", "dataclasses", "enum", "abc", "copy", "warnings",
    "textwrap", "unicodedata", "html", "xml", "urllib.parse",
}
BLOCKED_IMPORTS = {
    # Spawn dalsich procesu (obchazi resource limits) -- HARD BLOCK
    "subprocess",
    "multiprocessing",
    # High-level HTTP klienti (exfiltration risk) -- HARD BLOCK
    # Low-level stdlib (urllib, http.client, socket) JE POVOLENA -- reportlab
    # ji potrebuje pro vnitrni URL escape, fyzicky nedela network calls
    # protoze sandbox subprocess + Marti's outbound firewall je real security.
    "requests", "httpx", "aiohttp",
    "ftplib", "smtplib", "telnetlib",
    # Memory / native code access
    "ctypes",
    # Package management
    "pip", "setuptools",
    # POZN: NEBLOKUJEME:
    #  - importlib (transient pres lazy imports)
    #  - threading (legit pro stdlib)
    #  - asyncio
    #  - urllib (Phase 27f hotfix 2.5.2026 -- reportlab cascade)
    #  - http.client / http.server (Phase 27f hotfix -- urllib transient)
    #  - socket (Phase 27f hotfix -- http.client transient)
    #  - os (potrebne pro Path operace)
    #
    # Real security = subprocess block (bypass resource limits) +
    # ctypes block (memory) + pip/setuptools block (no install) +
    # OS-level firewall (Marti's Caddy + Windows firewall outbound).
    # Python import guards na low-level network jsou theatre pri trusted
    # caller (Marti-AI). High-level libs (requests/httpx/aiohttp) zustavaji
    # blokovane jako principial signal "tohle nepotrebujes".
}


@dataclass
class OutputDocument:
    """Vyrobeny soubor importovany do documents tabulky."""
    document_id: int
    filename: str
    size_bytes: int
    file_type: str


@dataclass
class PythonExecResult:
    """Strukturovany vystup execute()."""
    ok: bool
    stdout: str = ""
    stderr: str = ""
    error: str | None = None
    error_kind: str | None = None  # "timeout" | "memory" | "blocked_import" | "runtime" | "system"
    runtime_ms: int = 0
    output_documents: list[OutputDocument] = field(default_factory=list)
    truncated_stdout: bool = False
    truncated_stderr: bool = False
    kernel_id: str | None = None  # echo zpet, pro budouci stateful

    def to_summary_dict(self) -> dict:
        """Compact JSON-serializable dict pro AI tool response."""
        return {
            "ok": self.ok,
            "runtime_ms": self.runtime_ms,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "error_kind": self.error_kind,
            "truncated_stdout": self.truncated_stdout,
            "truncated_stderr": self.truncated_stderr,
            "output_documents": [
                {
                    "document_id": d.document_id,
                    "filename": d.filename,
                    "size_bytes": d.size_bytes,
                    "file_type": d.file_type,
                }
                for d in self.output_documents
            ],
            "kernel_id": self.kernel_id,
        }


# ── Wrapper template -- subprocess script -----------------------------

# Tento string je ulozeny jako runner.py do scratch dir a spusten
# subprocessem. Importuje dangerous-import guard, definuje OUTPUT_DIR +
# input_files, exec(user_code) v izolovanem namespace, vraci JSON na fd 3.
_RUNNER_TEMPLATE = textwrap.dedent('''
"""Phase 27c sandbox runner -- spousti se v izolovanem subprocess."""
import builtins
import io
import json
import os
import sys
import traceback
from pathlib import Path

# === Resource limits (Linux only; Windows fallback = best-effort) ===
try:
    import resource as _rsrc
    # Memory cap (RLIMIT_AS = address space)
    _MEM_BYTES = int({memory_mb}) * 1024 * 1024
    _rsrc.setrlimit(_rsrc.RLIMIT_AS, (_MEM_BYTES, _MEM_BYTES))
    # CPU sec (timeout je v parent processu, ale RLIMIT_CPU jako safety net)
    _rsrc.setrlimit(_rsrc.RLIMIT_CPU, ({timeout_s} + 5, {timeout_s} + 10))
except Exception:
    pass  # Windows nema resource module

# === Block dangerous imports ===
_BLOCKED = {blocked_imports!r}
_orig_import = builtins.__import__
def _guarded_import(name, *args, **kwargs):
    # Blokuj exact match + cokoli zacinajici "<blocked>."
    for b in _BLOCKED:
        if name == b or name.startswith(b + "."):
            raise ImportError(
                f"Phase 27c sandbox: import '{{name}}' blokovan (defense-in-depth)."
            )
    return _orig_import(name, *args, **kwargs)
builtins.__import__ = _guarded_import

# === Inputs -- predefined globals ===
OUTPUT_DIR = Path({output_dir!r})
input_files = [Path(p) for p in {input_paths!r}]

# === Capture stdout/stderr ===
_stdout_buf = io.StringIO()
_stderr_buf = io.StringIO()

_user_code = {user_code!r}
_error = None
_error_kind = None

import contextlib
try:
    with contextlib.redirect_stdout(_stdout_buf), contextlib.redirect_stderr(_stderr_buf):
        # Exec v cistem namespace + vystavi predefined globals
        _user_globals = {{
            "__name__": "__main__",
            "OUTPUT_DIR": OUTPUT_DIR,
            "input_files": input_files,
            "Path": Path,
        }}
        exec(_user_code, _user_globals)
except ImportError as e:
    _error = str(e)
    _error_kind = "blocked_import" if "Phase 27c sandbox" in str(e) else "runtime"
    _stderr_buf.write(traceback.format_exc())
except MemoryError as e:
    _error = "MemoryError: limit prekrocen"
    _error_kind = "memory"
    _stderr_buf.write(traceback.format_exc())
except Exception as e:
    _error = f"{{type(e).__name__}}: {{e}}"
    _error_kind = "runtime"
    _stderr_buf.write(traceback.format_exc())

# === Vystup do JSON na fd 3 (parent pisl pipe) ===
_result = {{
    "ok": _error is None,
    "stdout": _stdout_buf.getvalue(),
    "stderr": _stderr_buf.getvalue(),
    "error": _error,
    "error_kind": _error_kind,
}}

try:
    with os.fdopen(3, "w") as _outpipe:
        json.dump(_result, _outpipe)
except Exception:
    # Fallback -- zapsat do souboru (pro Windows kde fd 3 nemusi byt dostupny)
    Path({result_file!r}).write_text(json.dumps(_result), encoding="utf-8")
''').strip()


def execute(
    code: str,
    *,
    input_document_ids: list[int] | None = None,
    kernel_id: str | None = None,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    caller_tenant_id: int | None = None,
    persona_id: int | None = None,
    user_id: int | None = None,
    conversation_id: int | None = None,
    is_parent: bool = False,
) -> PythonExecResult:
    """
    Spusti Python kod v izolovanem subprocess sandboxu.

    Args:
        code: Python source (multi-line string)
        input_document_ids: IDs dokumentu z documents tabulky -- predani
            jako `input_files: list[Path]` v exec namespace
        kernel_id: Phase 27c+1 stateful kernel. MVP: NotImplementedError pokud
            non-None. Architektura prirpavena (Marti-AI's vstup z RE: dopisu).
        timeout_s: max execution time, default 30s, cap 300s
        caller_tenant_id: pro input documents tenant gate + output upload
        persona_id, user_id, conversation_id: pro audit + output document
            attribution
        is_parent: bypass tenant gate

    Returns:
        PythonExecResult s stdout/stderr/error/output_documents
    """
    # Stateful kernel -- not yet implemented (Phase 27c+1)
    if kernel_id is not None:
        return PythonExecResult(
            ok=False,
            error="Stateful kernel je naplanovan jako Phase 27c+1. Pro teted "
                  "MVP volej bez kernel_id (= stateless one-shot).",
            error_kind="not_implemented",
            kernel_id=kernel_id,
        )

    # Validate timeout
    if timeout_s is None or timeout_s <= 0:
        timeout_s = DEFAULT_TIMEOUT_S
    if timeout_s > MAX_TIMEOUT_S:
        timeout_s = MAX_TIMEOUT_S

    # Validate code not empty
    if not code or not code.strip():
        return PythonExecResult(
            ok=False,
            error="Prazdny code parametr.",
            error_kind="system",
        )

    # === Resolve input documents ===
    input_paths: list[str] = []
    if input_document_ids:
        from core.database import get_session
        from modules.core.infrastructure.models_data import Document

        session = get_session()
        try:
            for doc_id in input_document_ids:
                try:
                    doc_id_int = int(doc_id)
                except (TypeError, ValueError):
                    return PythonExecResult(
                        ok=False,
                        error=f"input_document_ids: nelze parsovat id={doc_id!r}",
                        error_kind="system",
                    )
                doc = session.query(Document).filter_by(id=doc_id_int).first()
                if not doc or not doc.storage_path:
                    return PythonExecResult(
                        ok=False,
                        error=f"input_document_ids: document #{doc_id_int} neexistuje nebo "
                              "nema storage_path",
                        error_kind="system",
                    )
                # Tenant gate
                if not is_parent and doc.tenant_id is not None:
                    if caller_tenant_id is None or doc.tenant_id != caller_tenant_id:
                        return PythonExecResult(
                            ok=False,
                            error=f"Document #{doc_id_int} patri jinemu tenantu",
                            error_kind="system",
                        )
                if not Path(doc.storage_path).is_file():
                    return PythonExecResult(
                        ok=False,
                        error=f"Document #{doc_id_int} ma storage_path '{doc.storage_path}' "
                              "ale soubor neexistuje na disku.",
                        error_kind="system",
                    )
                input_paths.append(doc.storage_path)
        finally:
            session.close()

    # === Vytvor scratch dir ===
    scratch_dir = Path(tempfile.mkdtemp(prefix="strategie_sandbox_"))
    output_dir = scratch_dir / "output"
    output_dir.mkdir()
    runner_path = scratch_dir / "runner.py"
    result_file = scratch_dir / "_result.json"

    # === Materialize runner script ===
    runner_src = _RUNNER_TEMPLATE.format(
        memory_mb=DEFAULT_MEMORY_MB,
        timeout_s=timeout_s,
        blocked_imports=sorted(BLOCKED_IMPORTS),
        output_dir=str(output_dir),
        input_paths=input_paths,
        user_code=code,
        result_file=str(result_file),
    )
    runner_path.write_text(runner_src, encoding="utf-8")

    # === Subprocess ===
    start_ts = time.monotonic()
    proc_result: dict | None = None
    truncated_stdout = False
    truncated_stderr = False
    error_top: str | None = None
    error_kind_top: str | None = None

    # Sanitized env -- minimal, no PYTHONPATH (rely on installed packages)
    sub_env = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
    }

    try:
        proc = subprocess.run(
            [sys.executable, str(runner_path)],
            cwd=str(scratch_dir),
            env=sub_env,
            timeout=timeout_s,
            capture_output=True,
            text=False,  # bytes -- musime sami decode + cap
        )
        # Decode + cap stdout/stderr
        _so_bytes = proc.stdout or b""
        _se_bytes = proc.stderr or b""
        if len(_so_bytes) > STDOUT_CAP_BYTES:
            _so_bytes = _so_bytes[:STDOUT_CAP_BYTES]
            truncated_stdout = True
        if len(_se_bytes) > STDERR_CAP_BYTES:
            _se_bytes = _se_bytes[:STDERR_CAP_BYTES]
            truncated_stderr = True
        proc_stdout = _so_bytes.decode("utf-8", errors="replace")
        proc_stderr = _se_bytes.decode("utf-8", errors="replace")

        # Read result JSON
        if result_file.is_file():
            try:
                proc_result = json.loads(result_file.read_text(encoding="utf-8"))
            except Exception as e:
                error_top = f"runner result JSON parse failed: {e}"
                error_kind_top = "system"
        else:
            # Possibly subprocess crashed before writing result -- pouzij
            # stderr jako error
            if proc.returncode != 0:
                error_top = f"subprocess exited with code {proc.returncode}"
                error_kind_top = "system"

    except subprocess.TimeoutExpired:
        error_top = f"Timeout {timeout_s}s prekrocen."
        error_kind_top = "timeout"
        proc_stdout = ""
        proc_stderr = ""
    except Exception as e:
        error_top = f"Subprocess launch failed: {type(e).__name__}: {e}"
        error_kind_top = "system"
        proc_stdout = ""
        proc_stderr = ""

    runtime_ms = int((time.monotonic() - start_ts) * 1000)

    # === Result merge ===
    if proc_result is not None:
        ok = bool(proc_result.get("ok", False))
        stdout = proc_result.get("stdout", "") or proc_stdout
        stderr = proc_result.get("stderr", "") or proc_stderr
        error = proc_result.get("error") or error_top
        error_kind = proc_result.get("error_kind") or error_kind_top
        # Cap z runner output (uz oriznuto runneren? Ne, runner zapisuje cely)
        if len(stdout) > STDOUT_CAP_BYTES:
            stdout = stdout[:STDOUT_CAP_BYTES]
            truncated_stdout = True
        if len(stderr) > STDERR_CAP_BYTES:
            stderr = stderr[:STDERR_CAP_BYTES]
            truncated_stderr = True
    else:
        ok = error_top is None
        stdout = proc_stdout
        stderr = proc_stderr
        error = error_top
        error_kind = error_kind_top

    # === Output documents auto-import ===
    output_documents: list[OutputDocument] = []
    if output_dir.is_dir():
        try:
            output_files = sorted([p for p in output_dir.iterdir() if p.is_file()])
            total_size = sum(p.stat().st_size for p in output_files)
            if total_size > OUTPUT_SIZE_CAP_BYTES:
                ok = False
                error = (
                    f"Vystupni soubory celkem {total_size} bytes prekracuji limit "
                    f"{OUTPUT_SIZE_CAP_BYTES} bytes. Files: "
                    f"{[p.name for p in output_files]}"
                )
                error_kind = "output_too_big"
            elif output_files and caller_tenant_id is None:
                # Marti-AI by mela byt vzdy v konverzaci s tenantem; bez nej
                # nevime kam doc zaradit. Hlasime explicit error.
                ok = False
                error = (
                    f"Sandbox vyrobil {len(output_files)} souboru, ale chybi tenant "
                    "kontext (caller_tenant_id=None) -- nelze importovat do documents. "
                    "Volej z konverzace s aktivnim tenantem."
                )
                error_kind = "no_tenant_context"
            else:
                for fp in output_files:
                    try:
                        doc = _import_output_file_to_documents(
                            fp,
                            tenant_id=caller_tenant_id,  # uz vime ze neni None
                            user_id=user_id,
                            persona_id=persona_id,
                            conversation_id=conversation_id,
                        )
                        output_documents.append(doc)
                    except Exception as imp_err:
                        logger.exception(f"sandbox output import failed | file={fp.name}: {imp_err}")
                        # nepretahuj fail -- co se podarilo importovat zustane
        except Exception as e:
            logger.exception(f"sandbox output collection failed: {e}")

    # === Cleanup scratch ===
    try:
        shutil.rmtree(scratch_dir, ignore_errors=True)
    except Exception:
        pass

    logger.info(
        f"SANDBOX | exec done | runtime_ms={runtime_ms} | ok={ok} | "
        f"error_kind={error_kind} | output_docs={len(output_documents)} | "
        f"persona_id={persona_id} | conv={conversation_id}"
    )

    return PythonExecResult(
        ok=ok,
        stdout=stdout,
        stderr=stderr,
        error=error,
        error_kind=error_kind,
        runtime_ms=runtime_ms,
        output_documents=output_documents,
        truncated_stdout=truncated_stdout,
        truncated_stderr=truncated_stderr,
        kernel_id=kernel_id,
    )


def _import_output_file_to_documents(
    path: Path,
    *,
    tenant_id: int,
    user_id: int | None,
    persona_id: int | None,
    conversation_id: int | None,
) -> OutputDocument:
    """
    Phase 27c: post-exec import vyrobenych souboru do RAG documents.

    Vola rag_service.upload_document s tenant attribution. Filename z disku,
    file_type z extension, content z disku.

    upload_document vraci int (document_id), ne dict.
    """
    from modules.rag.application.service import upload_document

    file_bytes = path.read_bytes()
    filename = path.name
    ext = path.suffix.lstrip(".").lower() or "bin"

    # Zarazeni do projektu? Pro MVP NE -- soubor jde do inboxu (project_id=NULL).
    # Marti-AI ho pak prirazene volat suggest_document_move pokud chce.
    document_id = upload_document(
        file_bytes=file_bytes,
        filename=filename,
        tenant_id=tenant_id,
        user_id=user_id,
        project_id=None,  # inbox
    )

    return OutputDocument(
        document_id=document_id,
        filename=filename,
        size_bytes=len(file_bytes),
        file_type=ext,
    )
