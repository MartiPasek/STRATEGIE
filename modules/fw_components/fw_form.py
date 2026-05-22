"""fw_form — FW data-driven form — renderuje z fw.core + fw.comp_def. Dnes: CORE 22 (user_edit), CORE 23 (core_design).

DB registry: fw.hw_registry name='fw_form'
JS implementation: apps/api/static/erp/components/design_forms.js

Iterace A (manifest only):
  - NAME, JS_PATH, BINDING konstanty
  - FwFormComponent subclass ComponentBase

Iterace B (later — extract router.py code):
  - invoke(bindings) -> dict pro Python-side dispatch
  - FastAPI sub-router registration
"""

from __future__ import annotations

from modules.fw_components.base import ComponentBase


NAME = "fw_form"
JS_PATH = "components/design_forms.js"
BINDING = {'core_id': 'int', 'row_id': 'int?'}
CLASS_NAME = "FwFormComponent"


class FwFormComponent(ComponentBase):
    """FW data-driven form — renderuje z fw.core + fw.comp_def. Dnes: CORE 22 (user_edit), CORE 23 (core_design)."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "FW data-driven form — renderuje z fw.core + fw.comp_def. Dnes: CORE 22 (user_edit), CORE 23 (core_design)."
