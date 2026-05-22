"""db_connection_editor — Power tool — fw.db_connection config (URL + credentials).

DB registry: fw.hw_registry name='db_connection_editor'
JS implementation: apps/api/static/erp/components/design_db_connection_editor.js

Iterace A (manifest only):
  - NAME, JS_PATH, BINDING konstanty
  - DbConnectionEditorComponent subclass ComponentBase

Iterace B (later — extract router.py code):
  - invoke(bindings) -> dict pro Python-side dispatch
  - FastAPI sub-router registration
"""

from __future__ import annotations

from modules.fw_components.base import ComponentBase


NAME = "db_connection_editor"
JS_PATH = "components/design_db_connection_editor.js"
BINDING = {'db_connection_id': 'int?'}
CLASS_NAME = "DbConnectionEditorComponent"


class DbConnectionEditorComponent(ComponentBase):
    """Power tool — fw.db_connection config (URL + credentials)."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "Power tool — fw.db_connection config (URL + credentials)."
