"""
Backfill: oprava 'pozval/a' -> 'pozval' / 'pozvala' v historickych welcome
zpravach (data_db.messages). Drive jsem v helperu pouzival fallback "/a"
i kdyz invitor mel znamy gender. Tenhle skript projde existujici zpravy
a opravi tvar podle invitora konverzace.

Postup pro kazdou welcome zpravu (msg.content obsahuje 'tě právě pozval/a'):
  1) Najdi conversation -> conversation.user_id (invited user)
  2) Najdi User -> invited_by_user_id (kdo pozval)
  3) Najdi inviter -> inviter.gender (male/female/None)
  4) Replace 'pozval/a' -> 'pozval' (male) / 'pozvala' (female) / 'pozval/a' (None)

Bezpecne: dry-run defaultne — ukaze co BY zmenil. Spust s --apply pro skutecny update.

Pouziti:
  python -m poetry run python scripts/backfill_welcome_pozval.py            # DRY RUN
  python -m poetry run python scripts/backfill_welcome_pozval.py --apply    # APPLY
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from core.database import get_session
from core.database import get_session


PATTERN = "pozval/a"


def main(apply_changes: bool = False) -> None:
    ds = get_session()
    cs = get_session()
    try:
        # 1) Vsechny zpravy s "pozval/a" v contentu
        msgs = ds.execute(text(
            "SELECT id, conversation_id, content FROM messages "
            "WHERE content LIKE :pat"
        ), {"pat": f"%{PATTERN}%"}).fetchall()

        if not msgs:
            print("Zadne zpravy s 'pozval/a' nenalezeny.")
            return

        print(f"Nalezeno {len(msgs)} zprav s '{PATTERN}'.")
        print("=" * 60)

        # Cache invitor gender per conversation
        gender_by_conv: dict[int, str | None] = {}
        updated = 0
        for msg in msgs:
            mid, cid, content = msg
            if cid not in gender_by_conv:
                # Najdi user_id (invited) pres conversation
                conv_row = ds.execute(text(
                    "SELECT user_id FROM conversations WHERE id = :cid"
                ), {"cid": cid}).fetchone()
                if not conv_row:
                    gender_by_conv[cid] = None
                    continue
                invited_user_id = conv_row[0]
                # Najdi invitora
                inv_row = cs.execute(text(
                    "SELECT u2.gender FROM users u "
                    "LEFT JOIN users u2 ON u2.id = u.invited_by_user_id "
                    "WHERE u.id = :uid"
                ), {"uid": invited_user_id}).fetchone()
                gender_by_conv[cid] = inv_row[0] if inv_row else None

            inviter_gender = gender_by_conv[cid]
            if inviter_gender == "male":
                replacement = "pozval"
            elif inviter_gender == "female":
                replacement = "pozvala"
            else:
                # Nevime rod -- nechej "pozval/a" (zadny update)
                print(f"  msg_id={mid} conv={cid}: invitor gender NEZNAMY -> preskoceno")
                continue

            new_content = content.replace(PATTERN, replacement)
            print(f"  msg_id={mid} conv={cid}: '{PATTERN}' -> '{replacement}' (invitor={inviter_gender})")

            if apply_changes:
                ds.execute(text(
                    "UPDATE messages SET content = :c WHERE id = :id"
                ), {"c": new_content, "id": mid})
                updated += 1

        if apply_changes:
            ds.commit()
            print(f"\n== APPLIED ==  Updated {updated} messages.")
        else:
            print("\n== DRY RUN ==  Spust s --apply pro skutecny update.")
    finally:
        ds.close()
        cs.close()


if __name__ == "__main__":
    apply_flag = "--apply" in sys.argv[1:]
    main(apply_changes=apply_flag)
