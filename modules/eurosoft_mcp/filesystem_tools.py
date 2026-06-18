"""EUROSOFT MCP filesystem tools — sdilena pracovni slozka pres MCP server.

Phase 38.4 (11.5.2026 vecer): puvodni per-user namespaces na C:\STRATEGIE-Share.

Marti's redesign (12.5.2026 vecer doma): 2 oficialni sdilene slozky na
EC-SERVER2 misto per-user folders:

  D:\Data\ZZ_Marti-AI RO  — RO zone (Marti-AI publishes, users read-only)
    Drzi doktrinu "Personal je knizka — uzavrena, nedotknutelna"
    (Phase 19c-e1, 27.4.) rozsirenou na filesystem.

  D:\Data\ZZ_Marti-AI RW  — RW zone (bidirectional)
    Lide davaji vstupy/podklady, Marti-AI cte + reaguje. EC_Vedeni ma
    Modify pres NTFS, Marti-AI MCP service ma full RW pres SYSTEM grant.

Architektura:
  - EUROSOFT MCP server (EC-SERVER2) ma RW na obou pres LocalSystem
    (NTFS grant SYSTEM:(OI)(CI)M na obe slozky, 12.5.2026 vecer)
  - Users pristupuji pres UNC \\192.168.30.11\Data\ZZ_Marti-AI RO/RW
  - Marti-AI vola eurosoft_file_* s user_namespace="ro" nebo "rw"

Tooly:
  1. eurosoft_file_list(user_namespace, subpath?) — vypise obsah slozky
  2. eurosoft_file_read(user_namespace, path) — precte soubor (text / base64 binary)
  3. eurosoft_file_write(user_namespace, path, content, encoding?, mode?) — zapise soubor
  4. eurosoft_file_delete(user_namespace, path) — smaze soubor

Security:
  - user_namespace whitelist: {"ro", "rw"} (case-insensitive)
  - Path traversal guard: resolved abs path MUSI startsWith(base)
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


def _namespace_bases() -> dict[str, str]:
    """Return mapping namespace → base path (from env-driven settings).

    Marti's redesign 12.5.2026: 2 zones (ro/rw), 2 separate env vars.
    Empty string = feature disabled for that zone.
    """
    return {
        "ro": settings.filesystem_ro_base,
        "rw": settings.filesystem_rw_base,
    }


def _resolve_namespace(user_namespace: str) -> str | None:
    """Validate user_namespace proti whitelistu {ro, rw}. Case-insensitive.

    Marti-AI typicky vola s "ro" nebo "rw" (matches ZZ_Marti-AI RO/RW
    share names). Tolerujeme uppercase taky pro friendliness.
    """
    if not user_namespace or not isinstance(user_namespace, str):
        return None
    ns = user_namespace.strip().lower()
    if not ns:
        return None
    if ns in ("ro", "rw"):
        return ns
    return None


def _resolve_path(user_namespace: str, subpath: str = "") -> tuple[Path | None, str | None]:
    """Resolve absolute path uvnitr ro/rw base.

    Returns (Path, None) at success, (None, error_message) at failure.
    Path traversal guard: resolved path MUSI startsWith(base).
    """
    ns = _resolve_namespace(user_namespace)
    if not ns:
        return None, (
            f"Neznamy user_namespace '{user_namespace}'. "
            f"Povolene: 'ro' (output zone, Marti-AI publikuje, users RO) nebo "
            f"'rw' (bidirectional zone, kazdy pise/cte)."
        )
    bases = _namespace_bases()
    base_str = bases.get(ns)
    if not base_str:
        return None, (
            f"Namespace '{ns}' je disabled (MCP_FILESYSTEM_{ns.upper()}_BASE "
            f"env nenastaveno)."
        )
    base = Path(base_str).resolve()
    # Path traversal — strip leading / and \, then resolve
    cleaned = (subpath or "").replace("\\", "/").lstrip("/").strip()
    if cleaned in ("", "."):
        target = base
    else:
        target = (base / cleaned).resolve()
    # Guard — target MUSI byt uvnitr base (po normalizaci .. ven)
    try:
        target.relative_to(base)
    except ValueError:
        return None, f"Path traversal blokovan: '{subpath}' resolved mimo namespace '{ns}'"
    return target, None


# ─────────────────────────────────────────────────────────────────────
# Fáze C (18.6.2026): base_override — přístup k pravým složkám Centrály
# (lokální D:\data\... na EC-SERVER2). Hrubá pojistka = povolené kořeny.
# ─────────────────────────────────────────────────────────────────────

def _parse_roots(raw: str) -> list[Path]:
    out = []
    for part in (raw or "").replace("\n", ";").split(";"):
        p = part.strip().strip('"')
        if not p:
            continue
        try:
            out.append(Path(p).resolve())
        except Exception:
            pass
    return out


def _allow_roots() -> tuple[list[Path], list[Path]]:
    """(rw_roots, ro_roots) z env (MCP_FS_RW_ROOTS / MCP_FS_RO_ROOTS)."""
    return _parse_roots(settings.fs_rw_roots), _parse_roots(settings.fs_ro_roots)


def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_path_override(base_override: str, subpath: str, require_write: bool) -> tuple[Path | None, str | None]:
    """Resolve cesty pod base_override s vynucením povolených kořenů.

    - base_override MUSÍ ležet pod některým RW nebo RO kořenem.
    - require_write → base NESMÍ být pod RO kořenem a MUSÍ být pod RW kořenem.
    - subpath traversal guard relativně k base.
    """
    rw_roots, ro_roots = _allow_roots()
    if not rw_roots and not ro_roots:
        return None, ("Přímé cesty (base_override) jsou vypnuté — na MCP nejsou "
                      "nastavené MCP_FS_RW_ROOTS / MCP_FS_RO_ROOTS.")
    try:
        base = Path(base_override).resolve()
    except Exception as exc:
        return None, f"Neplatná cesta base_override: {exc}"
    in_ro = any(_under(base, r) or base == r for r in ro_roots)
    in_rw = any(_under(base, r) or base == r for r in rw_roots)
    if not (in_ro or in_rw):
        return None, (f"Cesta '{base_override}' není pod žádným povoleným kořenem "
                      f"(RW: {[str(r) for r in rw_roots]}, RO: {[str(r) for r in ro_roots]}).")
    if require_write:
        # RO má přednost: cokoli pod RO kořenem je read-only, i kdyby leželo
        # i pod (širším) RW kořenem.
        if in_ro:
            return None, f"Cesta '{base_override}' je jen pro čtení (pod RO kořenem)."
        if not in_rw:
            return None, f"Cesta '{base_override}' není pod RW kořenem (zápis zakázán)."
    cleaned = (subpath or "").replace("\\", "/").lstrip("/").strip()
    target = base if cleaned in ("", ".") else (base / cleaned).resolve()
    if not (_under(target, base) or target == base):
        return None, f"Path traversal blokován: '{subpath}' mimo base."
    return target, None


def _resolve(user_namespace: str, subpath: str, base_override: str = "", require_write: bool = False):
    """Jednotný resolver: base_override (Fáze C) má přednost, jinak ns ro/rw."""
    if base_override:
        return _resolve_path_override(base_override, subpath, require_write)
    return _resolve_path(user_namespace, subpath)


# ─────────────────────────────────────────────────────────────────────
# Tool 1: list folder contents
# ─────────────────────────────────────────────────────────────────────

async def eurosoft_file_list(
    user_namespace: str = "",
    subpath: str = "",
    base_override: str = "",
    **_extra: Any,
) -> dict[str, Any]:
    target, err = _resolve(user_namespace, subpath, base_override, False)
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

async def eurosoft_file_read(
    user_namespace: str = "",
    path: str = "",
    encoding: str | None = None,
    base_override: str = "",
    **_extra: Any,
) -> dict[str, Any]:
    encoding = (encoding or "utf-8").lower()
    if not path:
        return {"ok": False, "error": "Parametr 'path' chybi."}
    target, err = _resolve(user_namespace, path, base_override, False)
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

async def eurosoft_file_write(
    user_namespace: str = "",
    path: str = "",
    content: str = "",
    encoding: str | None = None,
    mode: str | None = None,
    base_override: str = "",
    **_extra: Any,
) -> dict[str, Any]:
    encoding = (encoding or "utf-8").lower()
    mode = (mode or "overwrite").lower()
    if not path:
        return {"ok": False, "error": "Parametr 'path' chybi."}
    if mode not in ("overwrite", "fail_if_exists", "append"):
        return {
            "ok": False,
            "error": f"Neznamy mode '{mode}'. Povolene: overwrite, fail_if_exists, append.",
        }
    target, err = _resolve(user_namespace, path, base_override, True)
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

async def eurosoft_file_delete(
    user_namespace: str = "",
    path: str = "",
    base_override: str = "",
    **_extra: Any,
) -> dict[str, Any]:
    if not path:
        return {"ok": False, "error": "Parametr 'path' chybi."}
    target, err = _resolve(user_namespace, path, base_override, True)
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
# Tool 5: fs_info — self-report co server reálně povoluje (audit, Fáze C)
# ─────────────────────────────────────────────────────────────────────

async def eurosoft_fs_info(**_extra: Any) -> dict[str, Any]:
    """Vrátí, co MCP filesystem reálně povoluje — pro audit/kontrolu z appky."""
    rw_roots, ro_roots = _allow_roots()
    return {
        "ok": True,
        "ns_ro_base": settings.filesystem_ro_base or None,
        "ns_rw_base": settings.filesystem_rw_base or None,
        "rw_roots": [str(r) for r in rw_roots],
        "ro_roots": [str(r) for r in ro_roots],
        "max_size_bytes": settings.filesystem_max_size,
        "override_enabled": bool(rw_roots or ro_roots),
    }


# ─────────────────────────────────────────────────────────────────────
# Tool specs (Anthropic JSON schema format)
# ─────────────────────────────────────────────────────────────────────

_NAMESPACE_DESC = (
    "Sdilena zona EUROSOFT corporate filesystem (D:\\Data\\ZZ_Marti-AI RO/RW). "
    "Hodnoty:\n"
    "  - 'ro' = output zone. Marti-AI sem publikuje vystupy (sablony, "
    "rozvrhové soubory, dokumenty pro kolegy). Users (vc. EC_Vedeni) maji "
    "read-only — nikdo nemuze prepisovat ani mazat tve vystupy. Pouzij pro "
    "trvale ulozeni veci, ktere maji byt videt a nemenne.\n"
    "  - 'rw' = bidirectional zone. Lide sem davaji vstupy/podklady "
    "(naskenovane PDF, foto, podklady k zakazkam) a Marti-AI sem muze "
    "psat odpovedi nebo extrahovana data. Vsechni s pristupem mohou "
    "psat i mazat."
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


_BASE_OVERRIDE_DESC = (
    "Fáze C (volitelně): absolutní cesta-kořen (např. 'D:\\\\data\\\\podklady vyroba'). "
    "Když je zadán, ignoruje se user_namespace a použije se přímá cesta — MUSÍ ležet "
    "pod povoleným kořenem (MCP_FS_RW_ROOTS / MCP_FS_RO_ROOTS). Pro pravé složky Centrály."
)

# base_override do properties všech file toolů (akceptace + dokumentace)
for _spec in FILESYSTEM_TOOL_SPECS:
    _spec["inputSchema"]["properties"]["base_override"] = {
        "type": "string", "description": _BASE_OVERRIDE_DESC,
    }

FILESYSTEM_TOOL_SPECS.append({
    "name": "eurosoft_fs_info",
    "description": (
        "Self-report MCP filesystem: jaké zóny (ro/rw) a povolené kořeny "
        "(MCP_FS_RW_ROOTS / MCP_FS_RO_ROOTS) server reálně vynucuje. Pro audit "
        "z appky — kontrola 'co je nakonfigurováno vs. co server vidí'."
    ),
    "inputSchema": {"type": "object", "properties": {}},
})


FILESYSTEM_TOOL_HANDLERS = {
    "eurosoft_file_list": eurosoft_file_list,
    "eurosoft_file_read": eurosoft_file_read,
    "eurosoft_file_write": eurosoft_file_write,
    "eurosoft_file_delete": eurosoft_file_delete,
    "eurosoft_fs_info": eurosoft_fs_info,
}
