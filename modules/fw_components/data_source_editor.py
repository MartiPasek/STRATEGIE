"""data_source_editor — Power tool — fw.data_source + fw.data_source_op SQL editor (Ace + param extract).

DB registry: fw.hw_registry name='data_source_editor'
JS implementation: apps/api/static/erp/components/design_data_source_editor.js

Iterace A (manifest only):
  - NAME, JS_PATH, BINDING konstanty
  - DataSourceEditorComponent subclass ComponentBase

Iterace B (later — extract router.py code):
  - invoke(bindings) -> dict pro Python-side dispatch
  - FastAPI sub-router registration
"""

from __future__ import annotations

from modules.fw_components.base import ComponentBase


NAME = "data_source_editor"
JS_PATH = "components/design_data_source_editor.js"
BINDING = {'data_source_id': 'int?'}
CLASS_NAME = "DataSourceEditorComponent"


class DataSourceEditorComponent(ComponentBase):
    """Power tool — fw.data_source + fw.data_source_op SQL editor (Ace + param extract)."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "Power tool — fw.data_source + fw.data_source_op SQL editor (Ace + param extract)."
