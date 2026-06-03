"""act_registry — katalog handlerů akcí (FW Action Pipelines).

Autoritativní zdroj FE/BE kontextu (Marti 3.6.): handler sám deklaruje, kde
běží. `act_def.action_type` v DB je jen kategorie/label — runtime pravda je
tady.

BE handler = Python modul s kontraktem:
    validate(ctx) -> None              # volitelné; raise ValueError = nespustí run
    run(ctx) -> {"result_code", "output"}   # povinné; logika, smí mít side effects
    finalize(ctx, result) -> None      # volitelné; cleanup, nesmí hodit výjimku

FE handler = běží v prohlížeči (orchestrátor). Tady jen deklarace kontextu —
executor při něm pipeline PAUSNE a vrátí klientu „spusť handler X", po dokončení
klient zavolá resume.

ctx (předaný handleru): {
    "params":   dict,   # statická konfigurace tasku (act_task_def.params_schema)
    "inputs":   dict,   # rozmapované vstupy (act_task_def.input_mapping)
    "run_id":   int, "task_id": int, "step_no": int,
    "dry_run":  bool,   # True = simuluj, NEdělej reálný side effect
    "started_by_user_id": int|None, "started_by_persona_id": int|None,
}
"""
from __future__ import annotations

from typing import Callable, Optional

# code -> Python modul (BE handler)
_BE_HANDLERS: dict[str, object] = {}
# code -> True (FE handler — běží v prohlížeči, executor pausne)
_FE_HANDLERS: dict[str, bool] = {}


def register_be(code: str, module: object) -> None:
    """Zaregistruj backend handler (modul s run()/validate()/finalize())."""
    if not hasattr(module, "run"):
        raise ValueError(f"act handler '{code}' nemá povinný run(ctx)")
    _BE_HANDLERS[code] = module


def register_fe(code: str) -> None:
    """Zaregistruj frontend handler (jen deklarace — exekuce je v prohlížeči)."""
    _FE_HANDLERS[code] = True


def context_of(code: str) -> Optional[str]:
    """'backend' | 'frontend' | None (neznámý handler)."""
    if code in _BE_HANDLERS:
        return "backend"
    if code in _FE_HANDLERS:
        return "frontend"
    return None


def be_module(code: str) -> Optional[object]:
    return _BE_HANDLERS.get(code)


def all_handlers() -> dict[str, str]:
    """Přehled pro katalog/diagnostiku: code -> context."""
    out = {c: "backend" for c in _BE_HANDLERS}
    out.update({c: "frontend" for c in _FE_HANDLERS})
    return out


def bootstrap() -> None:
    """Načti a zaregistruj všechny zabudované handlery. Voláno jednou při startu
    (act_router import). FE handlery deklarujeme zde, BE se registrují importem."""
    # BE handlery (každý vlastní soubor)
    from modules.act_pipeline.act_handlers import act_db_insert as _h_ins
    from modules.act_pipeline.act_handlers import act_push_notification as _h_push
    from modules.act_pipeline.act_handlers import act_note_writeback as _h_note
    register_be("db_insert", _h_ins)
    register_be("push_notification", _h_push)
    register_be("note_writeback", _h_note)
    # FE handlery (exekuce v prohlížeči — orchestrátor)
    register_fe("cell_trigger")
    register_fe("open_core")
    register_fe("grid_refresh")
