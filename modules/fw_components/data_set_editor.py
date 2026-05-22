"""data_set_editor — Power tool — fw.data_set standalone SQL primitive editor.

DB registry: fw.hw_registry name='data_set_editor'
JS implementation: apps/api/static/erp/components/design_data_set_editor.js

Iterace A (manifest only):
  - NAME, JS_PATH, BINDING konstanty
  - DataSetEditorComponent subclass ComponentBase

Iterace B (later — extract router.py code):
  - invoke(bindings) -> dict pro Python-side dispatch
  - FastAPI sub-router registration
"""

from __future__ import annotations

from modules.fw_components.base import ComponentBase


NAME = "data_set_editor"
JS_PATH = "components/design_data_set_editor.js"
BINDING = {'data_set_id': 'int?'}
CLASS_NAME = "DataSetEditorComponent"


class DataSetEditorComponent(ComponentBase):
    """Power tool — fw.data_set standalone SQL primitive editor."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "Power tool — fw.data_set standalone SQL primitive editor."
