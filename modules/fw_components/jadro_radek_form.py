"""jadro_radek_form — Form 3 — sub-row detail (1:N joined tables, napr. emails/phones na user).

DB registry: fw.hw_registry name='jadro_radek_form'
JS implementation: apps/api/static/erp/components/design_jadro_radek_form.js

Iterace A (manifest only):
  - NAME, JS_PATH, BINDING konstanty
  - JadroRadekFormComponent subclass ComponentBase

Iterace B (later — extract router.py code):
  - invoke(bindings) -> dict pro Python-side dispatch
  - FastAPI sub-router registration
"""

from __future__ import annotations

from modules.fw_components.base import ComponentBase


NAME = "jadro_radek_form"
JS_PATH = "components/design_jadro_radek_form.js"
BINDING = {'parent_id': 'int', 'child_key': 'str', 'row_id': 'int?'}
CLASS_NAME = "JadroRadekFormComponent"


class JadroRadekFormComponent(ComponentBase):
    """Form 3 — sub-row detail (1:N joined tables, napr. emails/phones na user)."""
    name = NAME
    binding_schema = BINDING
    js_path = JS_PATH
    description = "Form 3 — sub-row detail (1:N joined tables, napr. emails/phones na user)."
