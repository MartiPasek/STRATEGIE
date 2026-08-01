#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zadátování Tool Factory do živé app — 2 chirurgické edity, obě v try/except
a za vypínačem (vypnuto = beze změny). Sekvenční replace s kontrolou počtu,
py_compile temp, atomický os.replace. Když cokoli nesedí, NEZAPÍŠE nic."""
import os, sys, py_compile

ROOT = os.path.dirname(os.path.abspath(__file__))  # nastaví se na repo root při běhu

EDITS = {
    "modules/conversation/application/tools.py": [(
        '    if is_default_persona:\n'
        '        return TOOLS\n'
        '    return [t for t in TOOLS if t["name"] not in MANAGEMENT_TOOL_NAMES]',
        '    if is_default_persona:\n'
        '        _base = TOOLS\n'
        '    else:\n'
        '        _base = [t for t in TOOLS if t["name"] not in MANAGEMENT_TOOL_NAMES]\n'
        '    # Tool Factory (Marti-AI seberozvoj) — přidá meta-nástroje + aktivní generované,\n'
        '    # jen když je dílna zapnutá (g2007.nastaveni). Vypnuto → [] → beze změny.\n'
        '    try:\n'
        '        from modules.conversation.application.tool_registry.handlers import effective_factory_specs as _efs\n'
        '        _extra = _efs(is_default_persona)\n'
        '        if _extra:\n'
        '            return _base + _extra\n'
        '    except Exception:\n'
        '        pass\n'
        '    return _base',
        1,
    )],
    "modules/conversation/application/service.py": [(
        'def _handle_tool(tool_name: str, tool_input: dict, conversation_id: int, user_id: int | None = None) -> str:\n'
        '    logger.info(f"TOOL | name={tool_name}")',
        'def _handle_tool(tool_name: str, tool_input: dict, conversation_id: int, user_id: int | None = None) -> str:\n'
        '    logger.info(f"TOOL | name={tool_name}")\n'
        '\n'
        '    # Tool Factory (Marti-AI seberozvoj) — za vypínačem g2007.nastaveni; vypnuto\n'
        '    # vrací None → propadne do normálního dispatch. V try/except = nerozbije.\n'
        '    try:\n'
        '        from modules.conversation.application.tool_registry.handlers import handle as _tf_handle\n'
        '        _tf = _tf_handle(tool_name, tool_input, user_id, conversation_id)\n'
        '        if _tf is not None:\n'
        '            return _tf\n'
        '    except Exception as _tfe:\n'
        '        logger.exception(f"TOOL | tool_factory: {_tfe}")',
        1,
    )],
}


def build(path, edits):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    for old, new, exp in edits:
        c = text.count(old)
        if c != exp:
            return None, f"MISMATCH {os.path.basename(path)}: nalezeno {c}, čekáno {exp}"
        text = text.replace(old, new)
    return text, "ok"


def main():
    results = {}
    for rel, edits in EDITS.items():
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print("CHYBA neexistuje:", rel); sys.exit(1)
        nt, info = build(path, edits)
        if nt is None:
            print("ABORT:", info); sys.exit(1)
        results[rel] = nt
        print("OK plan:", rel)
    tmps = {}
    for rel, nt in results.items():
        path = os.path.join(ROOT, rel); tmp = path + ".wire_tmp"
        open(tmp, "w", encoding="utf-8").write(nt)
        try:
            py_compile.compile(tmp, doraise=True)
        except py_compile.PyCompileError as e:
            for t in tmps.values():
                try: os.remove(t)
                except OSError: pass
            os.remove(tmp); print("ABORT py_compile:", rel, e); sys.exit(1)
        tmps[rel] = tmp; print("OK compile:", rel)
    for rel, tmp in tmps.items():
        os.replace(tmp, os.path.join(ROOT, rel)); print("APPLIED:", rel)
    print("\nHOTOVO — zadátováno (za vypínačem, vypnuto = beze změny).")


if __name__ == "__main__":
    main()
