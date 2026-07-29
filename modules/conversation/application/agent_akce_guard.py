# -*- coding: utf-8 -*-
"""Bezpečnostní brána pro RUCE Marti-AI v Cílovém režimu (Krok 2) — 27.7.2026, C23.

Klasifikuje každou ZAMÝŠLENOU akci (nástroj + vstup) do tří verdiktů:
  - "allow"        → smí se vykonat rovnou (pod schváleným cílem), zaloguje se.
  - "app_approval" → efekt ven / nevratné → i pod cílem přes palec v appce.
  - "deny"         → katastrofické, nikdy (ani pod cílem).

Doktrína #21: žádný volný shell, jen whitelist + audit. Dno drží KÓD, ne prompt.
Tento modul sám o sobě NIC nevykonává ani nezapíná — je to čistý posuzovač, který
write-enabled goal loop zavolá PŘED vykonáním každé akce. Bezpečné importovat kdykoli.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# ── Verdikt ───────────────────────────────────────────────────────────────────
@dataclass
class Verdikt:
    verdikt: str          # "allow" | "app_approval" | "deny"
    duvod: str = ""

    @property
    def povoleno(self) -> bool:
        return self.verdikt == "allow"

    @property
    def zamitnuto(self) -> bool:
        return self.verdikt == "deny"

    @property
    def pres_appku(self) -> bool:
        return self.verdikt == "app_approval"


# ── Tvrdý katastrofický deny (nikdy, ani pod schváleným cílem) ──────────────────
# Raw shell / vykonavače libovolného kódu — proti doktríně #21.
_HARD_DENY_TOOLNAMES = {
    "bash", "shell", "sh", "cmd", "powershell", "exec", "eval",
    "run_shell", "system", "subprocess",
}

# Vzory v JAKÉMKOLI stringovém vstupu akce → tvrdý deny.
_HARD_DENY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"power\s*shell|\bpwsh\b", re.I), "PowerShell (doctrine #21: jen whitelist)"),
    (re.compile(r"\bschtasks\b|\bcrontab\b|\bcron\b|New-ScheduledTask", re.I), "plánované úlohy / cron"),
    (re.compile(r"\brm\s+-rf\b|\bRemove-Item\b|\brmdir\b|\bdel\s+/[a-z]", re.I), "destruktivní mazání"),
    (re.compile(r"\bdrop\s+(table|database|schema|trigger)\b|\btruncate\s+table\b", re.I), "DROP/TRUNCATE"),
    (re.compile(r"\.env\b|\.credentials|credentials\.json|\.pem\b|\.key\b|\bsecret[s_]|_token\b|oauth", re.I), "tajemství / credentials"),
    (re.compile(r"(?:^|[\\/])\.git[\\/]|\bgit\s+push\b.*--force|\breset\s+--hard\b", re.I), "git internals / force"),
    (re.compile(r"\bdisable\s+trigger\b", re.I), "sabotáž auditu (disable trigger)"),
    (re.compile(r"(?:^|[\\/])backups?[\\/]|\bCMIS\b|zaloh", re.I), "zásah do záloh"),
]

# Append-only audit: DELETE/UPDATE/DROP/TRUNCATE/ALTER nad claude_aktivita v LIBOVOLNÉM
# pořadí (INSERT je OK — append). Řeší se zvlášť, ať chytneme obě slovosledová pořadí.
_AUDIT_TABLE_RE = re.compile(r"claude_aktivita", re.I)
_AUDIT_DESTRUCT_RE = re.compile(r"\b(delete|update|drop|truncate|alter|disable)\b", re.I)

# ── Efekty ven / nevratné → i pod cílem přes appku (palec rodiče) ───────────────
_EFEKTY_VEN_TOOLNAMES = {
    "send_email", "send_sms", "reply", "reply_all", "forward",
    "send_pwa_install_invite", "send_pwa_install_invite_bulk",
}

# ── Nástroje, které pod schváleným cílem smí rovnou (whitelist „rukou") ─────────
# Governed write nástroje s vlastními pojistkami (write-zóna / vlastní approval logika).
_ALLOW_WRITE_TOOLNAMES = {
    "strategie_file_write",          # write-zóna marti_workspace/ (security.py)
    "strategie_pg_insert_row", "strategie_pg_update_row",
    "strategie_pg_create_table", "strategie_pg_alter_table",
    "strategie_pg_create_function", "strategie_pg_create_trigger",
    "propose_deployment",            # návrh nasazení → schválí rodič (nevykoná samo)
    "create_tool",                   # Tool Factory: self-test + propose, aktivace rodič
    "record_diary_entry", "record_thought", "update_thought",
    "add_conversation_note", "zapis_znalost",
    "navrhni_zmenu_kodu", "navrhni_zmenu_kodu_patch",
}


def _iter_strings(obj: Any):
    """Projdi všechny stringové hodnoty ve vstupu (rekurzivně)."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _iter_strings(v)


def _hard_deny_scan(tool_name: str, tool_input: dict) -> Verdikt | None:
    tn = (tool_name or "").strip().lower()
    if tn in _HARD_DENY_TOOLNAMES:
        return Verdikt("deny", f"nástroj '{tool_name}' = volný shell/exec (doctrine #21)")
    for s in _iter_strings(tool_input or {}):
        for pat, why in _HARD_DENY_PATTERNS:
            if pat.search(s):
                return Verdikt("deny", why)
        if _AUDIT_TABLE_RE.search(s) and _AUDIT_DESTRUCT_RE.search(s):
            return Verdikt("deny", "sabotáž append-only auditu (claude_aktivita)")
    return None


def classify_action(tool_name: str, tool_input: dict | None = None) -> Verdikt:
    """Posuď zamýšlenou akci. Read-only nástroje sem nechodí (řeší je smyčka jako allow).

    Pořadí (fail-safe): 1) tvrdý deny (i ve vstupu) 2) efekty ven → appka
    3) známý governed write → allow 4) cokoli neznámého → app_approval (opatrně,
    ne allow — neznámé se raději zvedne k člověku, ne tiše provede)."""
    tool_input = tool_input or {}
    hard = _hard_deny_scan(tool_name, tool_input)
    if hard is not None:
        return hard
    tn = (tool_name or "").strip()
    if tn in _EFEKTY_VEN_TOOLNAMES:
        return Verdikt("app_approval", f"efekt ven ('{tn}') — přes appku i pod cílem")
    if tn in _ALLOW_WRITE_TOOLNAMES:
        return Verdikt("allow", f"governed write ('{tn}') — pod cílem OK, zaloguje se")
    # Neznámý / neklasifikovaný write nástroj → raději k člověku, netiše.
    return Verdikt("app_approval", f"neznámá akce ('{tn}') — pro jistotu přes appku")


# Read-only nástroje (smyčka je pouští volně, sem je posílat netřeba).
READ_ONLY_TOOLNAMES = {
    "Read", "Grep", "Glob",
    "strategie_file_read", "strategie_file_list",
    "strategie_pg_query_raw", "strategie_pg_query_table",
    "strategie_pg_describe_table", "strategie_pg_list_tables", "strategie_pg_list_schemas",
    "g2007_hledej", "hledej_ve_znalostech", "read_diary", "recall_thoughts",
    "search_documents", "web_search", "web_fetch", "zobraz_muj_prompt",
    "list_navrhy_kodu", "zobraz_navrh_kodu",
}


def is_read_only(tool_name: str) -> bool:
    return (tool_name or "").strip() in READ_ONLY_TOOLNAMES


# ── Klasifikátor RAW příkazu (sdílený pro eurosoft_exec / strategie_exec) ────────
# Spec: g2007 doc-marti-ai-eurosoft-exec-spec. Heuristika → 🔴/🟡 chytají nebezpečné,
# zbytek 🟢 (běžná údržba rychle). Drží se stejné logiky jako ops_tools na 30.11.
_EXEC_RED = [
    (re.compile(r"backups?[\\/]|\bCMIS\b|\bzaloh", re.I), "zálohy/CMIS"),
    (re.compile(r"claude_aktivita", re.I), "audit log claude_aktivita"),
    (re.compile(r"kill[_\-]?switch|disable[\s\-][^\n]*\b(audit|kill|trigger)\b", re.I), "audit/kill-switch"),
    (re.compile(r"\.env\b|\.credentials\b|credentials\.json|\.pem\b|\.pfx\b|\.key\b", re.I), "tajemství/credentials"),
]
_FOREIGN_SVC_RE = re.compile(r"\b(Helios|HELIOS[A-Za-z0-9\-]*|Centrala|Centrála)\b", re.I)
_EXEC_YELLOW = [
    (re.compile(r"\b(rm|rmdir|del|erase|unlink|rd)\b|Remove-Item|Clear-Content", re.I), "mazání"),
    (re.compile(r"\bdrop\s+(table|database|schema)\b|\btruncate\b", re.I), "DROP/TRUNCATE"),
    (re.compile(r"netsh|New-NetFirewallRule|Set-NetFirewallRule|firewall|Set-DnsClient|New-NetRoute|Disable-NetAdapter|route\s+(add|delete|change)", re.I), "síťová konfigurace"),
    (re.compile(r"(curl|wget|iwr|Invoke-WebRequest|Invoke-RestMethod)[\s\S]*\|\s*(bash|sh|iex|Invoke-Expression)|DownloadString|/dev/tcp", re.I), "stažení→shell / cizí endpoint"),
    (re.compile(r"\bsudo\b|\brunas\b|Start-Process[\s\S]*-Verb\s+RunAs|psexec", re.I), "eskalace privilegií"),
    (re.compile(r"Set-Content|Out-File|>\s*\S+\.(conf|config|ini|env|ya?ml|json|xml)\b", re.I), "přepis config souboru"),
]


def exec_tier(cmd: str) -> tuple[str, str]:
    """Vrať (tier, důvod). tier ∈ 'green'|'yellow'|'red'. 🔴 blok i v incidentu,
    🟡 banner (mimo incident), 🟢 rovnou."""
    c = cmd or ""
    for pat, why in _EXEC_RED:
        if pat.search(c):
            return "red", why
    if _AUDIT_TABLE_RE.search(c) and _AUDIT_DESTRUCT_RE.search(c):
        return "red", "sabotáž append-only auditu (claude_aktivita)"
    if re.search(r"Stop-Service|\bsc\.exe\s+stop", c, re.I):
        return "yellow", "stop služby"
    if re.search(r"(Restart|Start)-Service|\bsc\.exe\s+(start|config)", c, re.I) and _FOREIGN_SVC_RE.search(c):
        return "yellow", "manipulace cizí služby (Helios/Centrála)"
    for pat, why in _EXEC_YELLOW:
        if pat.search(c):
            return "yellow", why
    return "green", "běžná/reverzibilní operace"
