"""catalog_picker — Generic single-value picker — listing pres data_source + vyber ID.

DB registry: fw.hw_registry name='catalog_picker'
JS implementation: apps/api/static/erp/components/catalog_picker.js

Iterace A (manifest only):
  - NAME, JS_PATH, BINDING konstanty
  - CatalogPickerComponent subclass ComponentBase

Iterace B (later — extract router.py code):
  - invoke(bindings) -> dict pro Python-side dispatch
  - FastAPI sub-router registration
"""

from __future__ import annotations

from modules.fw_components.base import ComponentBase


NAME = "catalog_picker"
JS_PATH = "components/catalog_picker.js"
BINDING = {'data_source_id': 'int', 'initial_selected_id': 'int?'}
CLASS_NAME = "CatalogPickerComponent"


class CatalogPickerComponent(ComponentBase):
    """Generic single-value picker — listing pres data_source + vyber ID."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "Generic single-value picker — listing pres data_source + vyber ID."
