"""entity_picker — FW entity picker s bidirectional binding (form save flow, field_extern column).

DB registry: fw.hw_registry name='entity_picker'
JS implementation: apps/api/static/erp/components/entity_picker.js

Iterace A (manifest only):
  - NAME, JS_PATH, BINDING konstanty
  - EntityPickerComponent subclass ComponentBase

Iterace B (later — extract router.py code):
  - invoke(bindings) -> dict pro Python-side dispatch
  - FastAPI sub-router registration
"""

from __future__ import annotations

from modules.fw_components.base import ComponentBase


NAME = "entity_picker"
JS_PATH = "components/entity_picker.js"
BINDING = {'data_source_id': 'int', 'field_extern': 'str?', 'display_mode': 'str'}
CLASS_NAME = "EntityPickerComponent"


class EntityPickerComponent(ComponentBase):
    """FW entity picker s bidirectional binding (form save flow, field_extern column)."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "FW entity picker s bidirectional binding (form save flow, field_extern column)."
