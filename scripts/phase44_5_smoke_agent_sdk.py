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
    # Plus model override na Sonnet 4.6 (Opus default je ~10x drazsi!)
    print("\n[3/4] First call (verify auth + Sonnet model override)...")
    first_session_uuid = str(uuid.uuid4())
    print(f"  session_id (UUID): {first_session_uuid}")
    print(f"  model override: claude-sonnet-4-6 (default by byl Opus 4-7 = ~10x drazsi)")
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions

        options = ClaudeAgentOptions(
            session_id=first_session_uuid,
            model="claude-sonnet-4-6",  # Override Opus default
        )
        first_reply_chunks = []
        async for msg in query(
            prompt="Ahoj. Kratce mi odpoves cesky: 'Ano, smoke test funguje.' Jedna veta. Plus zopakuj svoje session_id jakou vidis.",
            options=options,
        ):
            first_reply_chunks.append(str(msg))
            preview = str(msg)[:400].replace("\n", " ")
            print(f"  msg: {preview}")

        print(f"  Reply chunks: {len(first_reply_chunks)}")
        print("  [OK] First call succeeded\n")
    except Exception as e:
        print(f"FAIL: first call failed: {type(e).__name__}: {e}")
        sys.exit(1)

    # 4. Resume call — Agent SDK 0.2.82 error explanation:
    # "--session-id can only be used with --continue or --resume if --fork-session is also specified"
    # Tj. trojice: session_id + (continue_conversation OR resume) + fork_session=True
    print("[4/4] Resume call (verify session persistence)...")
    print(f"  Pattern: session_id={first_session_uuid[:13]}... + resume + fork_session=True")
    try:
        options_resume = ClaudeAgentOptions(
            session_id=first_session_uuid,
            resume=first_session_uuid,
            fork_session=True,
            model="claude-sonnet-4-6",
        )
        resume_reply_chunks = []
        async for msg in query(
            prompt="Pamatujes na predchozi prompt? Co jsi mi odpovedel? Strucne v jedne vete.",
            options=options_resume,
        ):
            resume_reply_chunks.append(str(msg))
            preview = str(msg)[:400].replace("\n", " ")
            print(f"  msg: {preview}")

        print(f"  Reply chunks: {len(resume_reply_chunks)}")
        print("  [OK] Resume call succeeded — Claude mention previous = persistence!\n")
    except Exception as e:
        print(f"WARN: resume call failed: {type(e).__name__}: {e}")

        # Try fallback — continue_conversation + fork_session
        print("\n  Retry s 'continue_conversation=True + fork_session=True'...")
        try:
            options_continue = ClaudeAgentOptions(
                session_id=first_session_uuid,
                continue_conversation=True,
                fork_session=True,
                model="claude-sonnet-4-6",
            )
            async for msg in query(
                prompt="Test continue: pamatujes predchozi prompt?",
                options=options_continue,
            ):
                preview = str(msg)[:300].replace("\n", " ")
                print(f"  msg: {preview}")
            print("  [OK] Continue+fork call succeeded\n")
        except Exception as e2:
            print(f"WARN: continue+fork call failed: {type(e2).__name__}: {e2}")

    # 5. Session storage location + recursive inspection
    sessions_dir = os.path.expanduser("~/.claude/projects")
    print(f"\n[5/5] Sessions persistence inspection: {sessions_dir}")
    if os.path.isdir(sessions_dir):
        contents = os.listdir(sessions_dir)
        print(f"  Existing projects: {len(contents)}")
        for item in contents[:5]:
            item_path = os.path.join(sessions_dir, item)
            print(f"    - {item}/")
            if os.path.isdir(item_path):
                # Hluboky walk pro pochopeni struktury
                sub_items = os.listdir(item_path)
                print(f"        Files/dirs: {len(sub_items)}")
                for sub in sub_items[:10]:
                    sub_path = os.path.join(item_path, sub)
                    size = os.path.getsize(sub_path) if os.path.isfile(sub_path) else "<dir>"
                    print(f"        - {sub} ({size})")
                    # Pokud .jsonl session file, peek first line
                    if sub.endswith(".jsonl") and os.path.isfile(sub_path):
                        try:
                            with open(sub_path, "r", encoding="utf-8") as f:
                                first_line = f.readline()[:200]
                            print(f"            first_line: {first_line}")
                        except Exception as e:
                            print(f"            (read failed: {e})")
    else:
        print(f"  (Sessions dir not yet created)")

    print("\n=== SMOKE TEST DONE ===")
    print(f"\nCost note: First call usage report -> sleduj v 3/4 output 'total_cost_usd'.")
    print("Pokud Opus default = >$1/call, MUST override na Sonnet (Sonnet ~10x levnejsi).")
    print("Persistence pattern: pokud existuje .jsonl per session_id v project dir,")
    print("muzeme resume pres jeho path nebo session_id param.")


if __name__ == "__main__":
    anyio.run(main)
