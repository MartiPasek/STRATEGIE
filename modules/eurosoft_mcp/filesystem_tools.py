"""EUROSOFT MCP filesystem tools — sdilena pracovni slozka pres MCP server.

Phase 38.4 (11.5.2026 vecer). Marti's spec: "spravna cesta je pres MCP server
rovnou on-prem EUROSOFT... nasdilet pracovni slozku na pocitacich uzivatelu".

Architektura:
  - EUROSOFT MCP server (EC-SERVER2) ma access na corporate SMB share / local path
  - Marti-AI vola eurosoft_file_* tools pres existing MCP tunnel
  - Per-user folders + shared common folder
  - Kazdy uzivatel s EUROSOFT pristupem vidi obsah primo (zadny per-user setup)

Tooly:
  1. eurosoft_file_list(user_namespace, subpath?) — vypise obsah slozky
  2. eurosoft_file_read(user_namespace, path) — precte soubor (text / base64 binary)
  3. eurosoft_file_write(user_namespace, path, content, encoding?, mode?) — zapise soubor
  4. eurosoft_file_delete(user_namespace, path) — smaze soubor

Security:
  - user_namespace whitelist (config.filesystem_namespaces) + "shared"
  - Path traversal guard: resolved abs path MUSI startsWith(base/namespace)
  - Size cap (config.filesystem_max_size, default 50 MB)
  - Binary handling: write/read s encoding='base64' pro non-text obsah
"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Any

from .config import settings

logger = logging.getLogger("eurosoft_mcp.filesystem")


def _resolve_namespace(user_namespace: str) -> str | None:
    """Validate user_namespace proti whitelistu. Vrati cisty namespace nebo None.

    "shared" je always allowed (common folder). Ostatní z `filesystem_namespaces`
    config (CSV). Case-sensitive match (Marti-AI musi predat presny tvar).
    """
    if not user_namespace or not isinstance(user_namespace, str):
        return None
    ns = user_namespace.strip()
    if not ns:
        return None
    if ns == "shared":
        return "shared"
    allowed = {n.strip() for n in settings.filesystem_namespaces.split(",") if n.strip()}
    if ns in allowed:
        return ns
    return None


def _resolve_path(user_namespace: str, subpath: str = "") -> tuple[Path | None, str | None]:
    """Resolve absolute path uvnitr filesystem_base/user_namespace.

    Returns (Path, None) at success, (None, error_message) at failure.
    Path traversal guard: resolved path MUSI startsWith(base/namespace).
    """
    if not settings.filesystem_base:
        return None, "MCP filesystem feature disabled (MCP_FILESYSTEM_BASE env nenastaveno)."
    ns = _resolve_namespace(user_namespace)
    if not ns:
        return None, (
            f"Neznamy user_namespace '{user_namespace}'. "
            f"Povolene: shared + {settings.filesystem_namespaces}"
        )
    base = Path(settings.filesystem_base).resolve()
    ns_root = (base / ns).resolve()
    # Path traversal — strip leading / and \, then resolve
    cleaned = (subpath or "").replace("\\", "/").lstrip("/").strip()
    if cleaned in ("", "."):
        target = ns_root
    else:
        target = (ns_root / cleaned).resolve()
    # Guard — target MUSI byt uvnitr ns_root (po normalizaci .. ven)
    try:
        target.relative_to(ns_root)
    except ValueError:
        return None, f"Path traversal blokovan: '{subpath}' resolved mimo namespace '{ns}'"
    return target, None


# ─────────────────────────────────────────────────────────────────────
# Tool 1: list folder contents
# ─────────────────────────────────────────────────────────────────────

async def eurosoft_file_list(arguments: dict[str, Any]) -> dict[str, Any]:
    user_namespace = arguments.get("user_namespace", "")
    subpath = arguments.get("subpath", "")
    target, err = _resolve_path(user_namespace, subpath)
    if err:
        return {"ok": False, "error": err}
    try:
        # Auto-create namespace root if missing (first-time user)
        target.mkdir(parents=True, exist_ok=True)
        items = []
        if target.is_dir():
            for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                try:
                    stat = child.stat()
                    items.append({
                        "name": child.name,
                        "type": "dir" if child.is_dir() else "file",
                        "size": stat.st_size if child.is_file() else None,
                        "modified": int(stat.st_mtime),
                    })
                except OSError as item_err:
                    items.append({
                        "name": child.name,
                        "type": "error",
                        "error": str(item_err),
                    })
        else:
            return {"ok": False, "error": f"Path '{subpath}' neni adresar."}
        return {
            "ok": True,
            "namespace": user_namespace,
            "subpath": subpath,
            "abs_path": str(target),
            "count": len(items),
            "items": items,
        }
    except Exception as exc:
        logger.exception("eurosoft_file_list failed")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# ─────────────────────────────────────────────────────────────────────
# Tool 2: read file
# ─────────────────────────────────────────────────────────────────────

async def eurosoft_file_read(arguments: dict[str, Any]) -> dict[str, Any]:
    user_namespace = arguments.get("user_namespace", "")
    path = arguments.get("path", "")
    encoding = (arguments.get("encoding") or "utf-8").lower()
    if not path:
        return {"ok": False, "error": "Parametr 'path' chybi."}
    target, err = _resolve_path(user_namespace, path)
    if err:
        return {"ok": False, "error": err}
    try:
        if not target.is_file():
            return {"ok": False, "error": f"Soubor '{path}' neexistuje (nebo to neni file)."}
        size = target.stat().st_size
        if size > settings.filesystem_max_size:
            return {
                "ok": False,
                "error": (
                    f"Soubor '{path}' je vetsi nez limit ({size} > "
                    f"{settings.filesystem_max_size} bytes)."
                ),
            }
        raw = target.read_bytes()
        if encoding == "base64":
            content = base64.b64encode(raw).decode("ascii")
            return {
                "ok": True,
                "namespace": user_namespace,
                "path": path,
                "size": size,
                "encoding": "base64",
                "content": content,
            }
        else:
            try:
                content = raw.decode(encoding)
                return {
                    "ok": True,
                    "namespace": user_namespace,
                    "path": path,
                    "size": size,
                    "encoding": encoding,
                    "content": content,
                }
            except UnicodeDecodeError as decode_err:
                return {
                    "ok": False,
                    "error": (
                        f"Soubor neni text v encoding '{encoding}': {decode_err}. "
                        f"Pro binary soubory pouzij encoding='base64'."
                    ),
                }
    except Exception as exc:
        logger.exception("eurosoft_file_read failed")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# ─────────────────────────────────────────────────────────────────────
# Tool 3: write file
# ─────────────────────────────────────────────────────────────────────

async def eurosoft_file_write(arguments: dict[str, Any]) -> dict[str, Any]:
    user_namespace = arguments.get("user_namespace", "")
    path = arguments.get("path", "")
    content = arguments.get("content", "")
    encoding = (arguments.get("encoding") or "utf-8").lower()
    mode = (arguments.get("mode") or "overwrite").lower()
    if not path:
        return {"ok": False, "error": "Parametr 'path' chybi."}
    if mode not in ("overwrite", "fail_if_exists", "append"):
        return {
            "ok": False,
            "error": f"Neznamy mode '{mode}'. Povolene: overwrite, fail_if_exists, append.",
        }
    target, err = _resolve_path(user_namespace, path)
    if err:
        return {"ok": False, "error": err}
    try:
        # Decode content podle encoding
        if encoding == "base64":
            if not isinstance(content, str):
                return {"ok": False, "error": "Pro encoding='base64' musi byt content string."}
            try:
                raw = base64.b64decode(content, validate=True)
            except Exception as b64_err:
                return {"ok": False, "error": f"Base64 decode selhal: {b64_err}"}
        else:
            if not isinstance(content, str):
                return {"ok": False, "error": "Pro text encoding musi byt content string."}
            raw = content.encode(encoding)
        if len(raw) > settings.filesystem_max_size:
            return {
                "ok": False,
                "error": (
                    f"Content je vetsi nez limit ({len(raw)} > "
                    f"{settings.filesystem_max_size} bytes)."
                ),
            }
        # Mode handling
        if mode == "fail_if_exists" and target.exists():
            return {"ok": False, "error": f"Soubor '{path}' jiz existuje (mode=fail_if_exists)."}
        # Auto-create parent dirs
        target.parent.mkdir(parents=True, exist_ok=True)
        if mode == "append" and target.exists():
            with open(target, "ab") as f:
                f.write(raw)
        else:
            target.write_bytes(raw)
        return {
            "ok": True,
            "namespace": user_namespace,
            "path": path,
            "abs_path": str(target),
            "bytes_written": len(raw),
            "mode": mode,
            "encoding": encoding,
        }
    except Exception as exc:
        logger.exception("eurosoft_file_write failed")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# ─────────────────────────────────────────────────────────────────────
# Tool 4: delete file
# ─────────────────────────────────────────────────────────────────────

async def eurosoft_file_delete(arguments: dict[str, Any]) -> dict[str, Any]:
    user_namespace = arguments.get("user_namespace", "")
    path = arguments.get("path", "")
    if not path:
        return {"ok": False, "error": "Parametr 'path' chybi."}
    target, err = _resolve_path(user_namespace, path)
    if err:
        return {"ok": False, "error": err}
    try:
        if not target.exists():
            return {"ok": False, "error": f"Soubor '{path}' neexistuje."}
        if target.is_dir():
            return {
                "ok": False,
                "error": (
                    f"'{path}' je adresar — delete adresaru tool zatim nepodporuje "
                    f"(safety). Smaz po souborech."
                ),
            }
        target.unlink()
        return {
            "ok": True,
            "namespace": user_namespace,
            "path": path,
            "deleted": True,
        }
    except Exception as exc:
        logger.exception("eurosoft_file_delete failed")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# ─────────────────────────────────────────────────────────────────────
# Tool specs (Anthropic JSON schema format)
# ─────────────────────────────────────────────────────────────────────

_NAMESPACE_DESC = (
    "User folder namespace: 'Marti', 'Kristy', 'Sarka', 'Jirka', 'Ondra', 'Pavel', "
    "'Petra', 'Marti-AI' nebo 'shared' (common folder pro vsechny). Kazdy user "
    "ma vlastni privatni slozku; do 'shared' muze psat kazdy a vidi to vsichni."
)

FILESYSTEM_TOOL_SPECS = [
    {
        "name": "eurosoft_file_list",
        "description": (
            "Vypise obsah slozky na EUROSOFT shared filesystem (SMB share / local "
            "path na EC-SERVER2). Per-user folder + shared common folder. "
            "Phase 38.4 (11.5.2026): persistent storage pres MCP server na on-prem."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_namespace": {"type": "string", "description": _NAMESPACE_DESC},
                "subpath": {
                    "type": "string",
                    "description": (
                        "Volitelna podslozka relativne k user_namespace root. "
                        "Empty = vypis rootu. Nepouzivej '..' (path traversal blokovan)."
                    ),
                },
            },
            "required": ["user_namespace"],
        },
    },
    {
        "name": "eurosoft_file_read",
        "description": (
            "Precte soubor z EUROSOFT shared filesystem. Pro text pouzij "
            "encoding='utf-8' (default), pro binary (PDF, Excel, image) "
            "pouzij encoding='base64' a obsah decode v Marti-AI side."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_namespace": {"type": "string", "description": _NAMESPACE_DESC},
                "path": {
                    "type": "string",
                    "description": "Cesta k souboru relativne k user_namespace root.",
                },
                "encoding": {
                    "type": "string",
                    "description": (
                        "'utf-8' (default, text) | 'cp1250' (legacy Windows CZ) | "
                        "'base64' (binary). Pro binary soubory POVINNE base64."
                    ),
                },
            },
            "required": ["user_namespace", "path"],
        },
    },
    {
        "name": "eurosoft_file_write",
        "description": (
            "Zapise soubor do EUROSOFT shared filesystem. Pro binary obsah (PDF, "
            "Excel, image) pouzij encoding='base64' (Marti-AI nejprve base64-encode "
            "binary content). Parent dirs se vytvori auto. Mode: 'overwrite' (default), "
            "'fail_if_exists', 'append'. Phase 38.4: typicke pro Marti-AI's blueprint "
            "PDF, Klarka Excel sablonu, sdilene dokumenty."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_namespace": {"type": "string", "description": _NAMESPACE_DESC},
                "path": {
                    "type": "string",
                    "description": "Cesta relativne k user_namespace root (vc. filename).",
                },
                "content": {
                    "type": "string",
                    "description": "Obsah souboru. Pro binary: base64-encoded string.",
                },
                "encoding": {
                    "type": "string",
                    "description": "'utf-8' (default text) | 'cp1250' | 'base64' (binary).",
                },
                "mode": {
                    "type": "string",
                    "description": "'overwrite' (default) | 'fail_if_exists' | 'append'.",
                },
            },
            "required": ["user_namespace", "path", "content"],
        },
    },
    {
        "name": "eurosoft_file_delete",
        "description": (
            "Smaze soubor z EUROSOFT shared filesystem. Slozky nelze smazat "
            "(safety) — smaz po souborech. Phase 38.4."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_namespace": {"type": "string", "description": _NAMESPACE_DESC},
                "path": {
                    "type": "string",
                    "description": "Cesta relativne k user_namespace root.",
                },
            },
            "required": ["user_namespace", "path"],
        },
    },
]


FILESYSTEM_TOOL_HANDLERS = {
    "eurosoft_file_list": eurosoft_file_list,
    "eurosoft_file_read": eurosoft_file_read,
    "eurosoft_file_write": eurosoft_file_write,
    "eurosoft_file_delete": eurosoft_file_delete,
}
