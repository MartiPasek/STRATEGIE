"""field_picker_modal — Helper modal — vyber fields z entity columns (FW form +Pole button).

DB registry: fw.hw_registry name='field_picker_modal'
JS implementation: apps/api/static/erp/components/field_picker_modal.js

Iterace A (manifest only):
  - NAME, JS_PATH, BINDING konstanty
  - FieldPickerModalComponent subclass ComponentBase

Iterace B (later — extract router.py code):
  - invoke(bindings) -> dict pro Python-side dispatch
  - FastAPI sub-router registration
"""

from __future__ import annotations

from modules.fw_components.base import ComponentBase


NAME = "field_picker_modal"
JS_PATH = "components/field_picker_modal.js"
BINDING = {'entity_type': 'str', 'current_fields': 'str[]'}
CLASS_NAME = "FieldPickerModalComponent"


class FieldPickerModalComponent(ComponentBase):
    """Helper modal — vyber fields z entity columns (FW form +Pole button)."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "Helper modal — vyber fields z entity columns (FW form +Pole button)."
