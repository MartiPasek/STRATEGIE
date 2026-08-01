# -*- coding: utf-8 -*-
"""Vzorový nástroj — ukazuje kontrakt „jeden soubor = jeden nástroj".

Toto je jediný živý příklad v registru (dormant). Skutečné nástroje sem přijdou
migrací z tools.py přes scripts/migrate_tools_to_registry.py; při go-live se tento
příklad odstraní. Kontrakt: modul vyexportuje SPEC (+ volitelně run()).
"""
from tool_registry._common import ToolContext, need, ok

SPEC = {
    "name": "example_echo",
    "description": "Ukázkový nástroj: vrátí zpět předaný text. Šablona kontraktu SPEC+run pro registr.",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text k zopakování."},
        },
        "required": ["text"],
    },
    "_order": 999_000,  # interní klíč (s '_') — do API se neposílá
}


def run(args: dict, ctx: ToolContext) -> str:
    text = need(args, "text")
    return ok(f"echo: {text}")
