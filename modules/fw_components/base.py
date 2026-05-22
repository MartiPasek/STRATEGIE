"""modules/fw_components/base.py — Phase 22.5.2026.

ComponentBase = minimum abstract base pro vsechny komponenty.
Iterace A: jen metadata (name, binding_schema, js_path, description).
Iterace B: pridat invoke(bindings) -> dict pro Python-side dispatch.
"""

from __future__ import annotations

from typing import Any, ClassVar


class ComponentBase:
    """Base class pro FW komponenty (fw.hw_registry kind='component').

    Subclass musi prepsat:
        name: ClassVar[str]                  # fw.hw_registry.name
        binding_schema: ClassVar[dict]       # {param: type_hint}
        js_path: ClassVar[str]               # components/X.js
        description: ClassVar[str]           # human-readable label

    Iterace B (later) pridame:
        @classmethod
        def invoke(cls, bindings: dict) -> dict:
            # Python-side dispatch — vraci data pro frontend
            raise NotImplementedError
    """
    name: ClassVar[str] = ""
    binding_schema: ClassVar[dict] = {}
    js_path: ClassVar[str] = ""
    description: ClassVar[str] = ""

    @classmethod
    def manifest(cls) -> dict[str, Any]:
        """Vrati component metadata jako dict — pro debug + diagnostic tools."""
        return {
            "name": cls.name,
            "binding_schema": cls.binding_schema,
            "js_path": cls.js_path,
            "description": cls.description,
        }
