"""modules/fw_components — Phase 22.5.2026 centralni evidence FW komponent.

Per Marti's vize: kazda komponenta z fw.hw_registry (kind='component') ma
svuj Python manifest soubor v tomto adresari. Manifest drzi NAME + BINDING +
JS_PATH + ComponentBase subclass.

Usage:
    from modules.fw_components import load_component
    cls = load_component("fw_form")    # -> FwFormComponent
    print(cls.binding_schema)            # {"core_id": "int", ...}

Iterace A (scaffold) — manifests only, zadny code extract.
Iterace B (postupne) — extract router.py endpoints do per-komponenta .py.
"""

from __future__ import annotations

import importlib
from typing import Any


def load_component(name: str) -> type[Any]:
    """Dynamic load Component class from manifest module.

    Lookup: modules/fw_components/<name>.py exports <ClassName>Component.
    Manifest module musi mit CLASS_NAME konstantu pro reflection.

    Args:
        name: fw.hw_registry.name (e.g. "fw_form", "data_source_editor")

    Returns:
        Component class (subclass of ComponentBase)

    Raises:
        ImportError: pokud manifest neexistuje
        AttributeError: pokud manifest nema CLASS_NAME export
    """
    module = importlib.import_module(f"modules.fw_components.{name}")
    class_name = getattr(module, "CLASS_NAME")
    return getattr(module, class_name)
