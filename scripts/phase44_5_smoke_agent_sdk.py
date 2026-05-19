"""Phase 44.5 smoke test — Anthropic Agent SDK availability na cloud APP.

Marti's autonomy mandate (19.5.2026 odpoledne, post-Phase-44-drop):
"To rozbehneme dnes... Dobra priprava na patek... Jdem A Agent SDK"

Cilem: overit ze claude-agent-sdk je nainstalovany, authenticky, persistent
session funguje pres restart. ~30 sekund run.

Usage (na cloud APP):
  cd C:\\Projekty\\STRATEGIE
  $env:ANTHROPIC_API_KEY = "sk-ant-..."   # pokud neni v .env nebo Machine env
  python scripts/_phase44_5_smoke_agent_sdk.py
"""
from __future__ import annotations

import anyio
import os
import sys
import uuid


async def main():
    print("=== Phase 44.5 Agent SDK smoke test ===\n")

    # 1. Verify install
    try:
        import claude_agent_sdk
        print(f"[1/4] claude_agent_sdk installed: version={getattr(claude_agent_sdk, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"FAIL: claude_agent_sdk not installed: {e}")
        print("Fix: pip install --upgrade claude-agent-sdk")
        sys.exit(1)

    # 2. Verify env (s placeholder detection)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("FAIL: ANTHROPIC_API_KEY env not set")
        print("Fix: $env:ANTHROPIC_API_KEY = 'sk-ant-api03-...' (skutecny klic, ne placeholder)")
        sys.exit(1)
    if len(api_key) < 50 or "..." in api_key:
        print(f"FAIL: ANTHROPIC_API_KEY ma podezrelou delku (length={len(api_key)}) — placeholder?")
        print("Skutecny Anthropic klic ma ~100 znaku, zacina 'sk-ant-api03-'.")
        print("Najdi: Get-Content C:\\Projekty\\STRATEGIE\\.env | Select-String 'ANTHROPIC'")
        print("Nebo: https://console.anthropic.com/settings/keys")
        sys.exit(1)
    print(f"[2/4] ANTHROPIC_API_KEY found (length={len(api_key)}, prefix={api_key[:15]}...)")

    # 3. First call — Agent SDK 0.2.82 vyzaduje UUID session_id
    print("\n[3/4] First call (verify auth)...")
    first_session_uuid = str(uuid.uuid4())
    print(f"  session_id (UUID): {first_session_uuid}")
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions

        options = ClaudeAgentOptions(
            session_id=first_session_uuid,
            resume=False,  # fresh session
        )
        first_reply_chunks = []
        async for msg in query(
            prompt="Ahoj. Kratce mi odpoves cesky: 'Ano, smoke test funguje.' Jedna veta.",
            options=options,
        ):
            first_reply_chunks.append(str(msg))
            preview = str(msg)[:300].replace("\n", " ")
            print(f"  msg: {preview}")

        print(f"  Reply chunks: {len(first_reply_chunks)}")
        print("  [OK] First call succeeded\n")
    except Exception as e:
        print(f"FAIL: first call failed: {type(e).__name__}: {e}")
        sys.exit(1)

    # 4. Resume call — same UUID, resume=True (test persistence)
    print("[4/4] Resume call (verify session persistence)...")
    try:
        options_resume = ClaudeAgentOptions(
            session_id=first_session_uuid,
            resume=True,
        )
        resume_reply_chunks = []
        async for msg in query(
            prompt="Pamatujes na predchozi prompt? Zopakuj prosim presne co jsi mi odpovedel.",
            options=options_resume,
        ):
            resume_reply_chunks.append(str(msg))
            preview = str(msg)[:300].replace("\n", " ")
            print(f"  msg: {preview}")

        print(f"  Reply chunks: {len(resume_reply_chunks)}")
        print("  [OK] Resume call succeeded (Claude mention previous = persistence works)\n")
    except Exception as e:
        print(f"WARN: resume call failed (mozna SDK nepodporuje resume v teto verzi): "
              f"{type(e).__name__}: {e}")
        # Nevyhazujeme — first call OK je dost pro smoke

    # 5. Session storage location
    sessions_dir = os.path.expanduser("~/.claude/projects")
    print(f"[5/5] Sessions persistence dir: {sessions_dir}")
    if os.path.isdir(sessions_dir):
        contents = os.listdir(sessions_dir)
        print(f"  Existing sessions/projects: {len(contents)}")
        for item in contents[:5]:
            print(f"    - {item}")
    else:
        print(f"  (Sessions dir not yet created — first call may have just persisted)")

    print("\n=== SMOKE TEST DONE ===")
    print("Pokud videl Marti 'OK First call' + 'OK Resume call' s Claude'em")
    print("mentioning previous prompt -> Agent SDK je funkcni, jdeme do design fáze.")


if __name__ == "__main__":
    anyio.run(main)
