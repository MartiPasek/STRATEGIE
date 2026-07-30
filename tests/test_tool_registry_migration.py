# -*- coding: utf-8 -*-
"""Testy migračního modulu (tool_registry/migration.py) — samoobslužná migrace
JIŽ ŽIVÉHO nástroje z tools.py/_handle_tool do vlastního run(). Běží bez DB
(čistá logika + souborová mechanika); DB-větve (propose/approve/reject/rollback/
dispatch_migrated) volají core.database až uvnitř funkcí, takže samotný import
a specy jsou testovatelné i v sandboxu bez živé appky (stejný vzor jako
test_tool_registry.py u zbytku Tool Factory)."""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(HERE)
_CANDS = [_ROOT, os.path.join(_ROOT, "modules", "conversation", "application")]
for _c in _CANDS:
    if os.path.isdir(os.path.join(_c, "tool_registry")):
        if _c not in sys.path:
            sys.path.insert(0, _c)
        break

import tool_registry as reg
from tool_registry import migration as MIG
from tool_registry import runtime as RT
from tool_registry._common import ToolContext


# ── import bezpečnost (DORMANT) ──────────────────────────────────────────────────
def test_migration_module_imports_without_db():
    # Import samotný nesmí sáhnout na DB / core.database — jen lazy uvnitř funkcí.
    assert callable(MIG.propose)
    assert callable(MIG.approve)
    assert callable(MIG.reject)
    assert callable(MIG.dispatch_migrated)


def test_handlers_module_imports_without_db():
    from tool_registry import handlers as H
    assert callable(H.handle)


# ── _load_defs_spec (čistá souborová operace, žádná DB) ──────────────────────────
def test_load_defs_spec_existing():
    spec = MIG._load_defs_spec("example_echo")
    assert spec is not None
    assert spec["name"] == "example_echo"
    assert set(("name", "description", "input_schema")).issubset(spec.keys())
    assert "_order" not in spec  # interní klíč se nesmí prosakovat


def test_load_defs_spec_missing():
    assert MIG._load_defs_spec("neexistujici_nastroj_xyz_123") is None


# ── _is_migration_payload ─────────────────────────────────────────────────────────
def test_is_migration_payload():
    assert MIG._is_migration_payload({"kind": "migrace", "spec": {}}) is True
    assert MIG._is_migration_payload({"spec": {}, "code": "x"}) is False   # create_tool payload (bez kind)
    assert MIG._is_migration_payload({"kind": "jine"}) is False
    assert MIG._is_migration_payload(None) is False
    assert MIG._is_migration_payload("neni dict") is False


# ── meta-specy shape ────────────────────────────────────────────────────────────
def test_migration_meta_specs_shape():
    names = {s["name"] for s in MIG.MIGRATION_META_SPECS}
    for must in ("navrhni_migraci_nastroje", "schval_migraci_nastroje",
                 "zamitni_migraci_nastroje", "seznam_migraci_nastroju", "vrat_na_legacy"):
        assert must in names
    for s in MIG.MIGRATION_META_SPECS:
        assert set(("name", "description", "input_schema")).issubset(s.keys())
        assert s["input_schema"]["type"] == "object"
    assert MIG.MIGRATION_META_NAMES == names


# ── souborová mechanika v MIGRATIONS_DIR (write/load/execute round-trip) ─────────
def test_write_load_execute_roundtrip_in_migrations_dir():
    tmp = tempfile.mkdtemp(prefix="migtest_")
    try:
        spec = {"name": "mig_test_pozdrav", "description": "Test migrace.", "input_schema": {
            "type": "object", "properties": {"kdo": {"type": "string"}}, "required": ["kdo"]}}
        code = "who = need(args, 'kdo')\nreturn ok(f'Ahoj {who} (migrovano)')"
        path = RT.write_generated("mig_test_pozdrav", spec, code, directory=tmp)
        assert os.path.exists(path)
        loaded_spec, run = RT.load_generated("mig_test_pozdrav", directory=tmp)
        assert loaded_spec["name"] == "mig_test_pozdrav"
        out = run({"kdo": "Marti"}, ToolContext(entita_id=2))
        assert out == "Ahoj Marti (migrovano)"
        out2 = RT.execute("mig_test_pozdrav", {"kdo": "Kristy"}, ToolContext(entita_id=2), directory=tmp)
        assert out2 == "Ahoj Kristy (migrovano)"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_migrations_dir_constant_separate_from_generated():
    # MIGRATIONS_DIR musí být VLASTNÍ adresář — nikdy stejný jako GENERATED_DIR
    # (migrace existujícího nástroje se nesmí splést s nástrojem zbrusu novým).
    assert reg.MIGRATIONS_DIR != reg.GENERATED_DIR
    assert reg.MIGRATIONS_DIR.endswith("generated_migrations")


def test_load_all_does_not_pick_up_migrations_dir():
    # load_all() (živý seznam speců) skenuje jen defs/ (+ generated/), NIKDY
    # generated_migrations/ — migrace mění handler, ne veřejný seznam nástrojů.
    mods = reg.load_all()
    names = [m.name for m in mods]
    assert "mig_test_pozdrav" not in names   # náhodou by nemělo uniknout z předchozího testu
