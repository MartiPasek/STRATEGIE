"""soudecek_core_form — Form 1+2 — menu_node design (Soudecek + Prehled + DataSource pickery).

DB registry: fw.hw_registry name='soudecek_core_form'
JS implementation: apps/api/static/erp/components/design_soudecek_core_form.js

Iterace A (manifest only):
  - NAME, JS_PATH, BINDING konstanty
  - SoudecekCoreFormComponent subclass ComponentBase

Iterace B (later — extract router.py code):
  - invoke(bindings) -> dict pro Python-side dispatch
  - FastAPI sub-router registration
"""

from __future__ import annotations

from modules.fw_components.base import ComponentBase


NAME = "soudecek_core_form"
JS_PATH = "components/design_soudecek_core_form.js"
BINDING = {'menu_node_id': 'int'}
CLASS_NAME = "SoudecekCoreFormComponent"


class SoudecekCoreFormComponent(ComponentBase):
    """Form 1+2 — menu_node design (Soudecek + Prehled + DataSource pickery)."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "Form 1+2 — menu_node design (Soudecek + Prehled + DataSource pickery)."
