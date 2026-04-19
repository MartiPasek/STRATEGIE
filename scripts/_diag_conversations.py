"""Diagnostika: kdo vlastni konverzace a kdo pise zpravy."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from core.database_core import get_core_session
from core.database_data import get_data_session


def main() -> None:
    # 1) users + memberships
    cs = get_core_session()
    try:
        print("== USERS (css_db) ==")
        rows = cs.execute(text(
            "SELECT id, first_name, last_name, status, last_active_tenant_id, "
            "last_active_project_id FROM users ORDER BY id"
        )).fetchall()
        for r in rows:
            print(f"  user_id={r[0]:<3} first={r[1]!s:<12} last={r[2]!s:<15} "
                  f"status={r[3]!s:<10} last_active_tenant={r[4]!s:<5} "
                  f"last_active_project={r[5]}")

        print("\n== TENANTS (css_db) ==")
        rows = cs.execute(text(
            "SELECT id, tenant_type, tenant_name, tenant_code, owner_user_id, status "
            "FROM tenants ORDER BY id"
        )).fetchall()
        for r in rows:
            print(f"  tenant_id={r[0]:<3} type={r[1]!s:<10} name={r[2]!s:<15} "
                  f"code={r[3]!s:<10} owner={r[4]!s:<5} status={r[5]}")

        print("\n== USER_TENANTS (css_db) ==")
        rows = cs.execute(text(
            "SELECT ut.user_id, ut.tenant_id, t.tenant_name, t.tenant_type, ut.role, ut.membership_status "
            "FROM user_tenants ut "
            "JOIN tenants t ON t.id = ut.tenant_id "
            "ORDER BY ut.user_id, ut.tenant_id"
        )).fetchall()
        if not rows:
            print("  (zadne)")
        for r in rows:
            print(f"  user_id={r[0]:<3} tenant_id={r[1]:<3} tenant={r[2]!s:<15} "
                  f"type={r[3]!s:<10} role={r[4]!s:<8} membership={r[5]}")

        print("\n== PROJECTS (css_db) ==")
        rows = cs.execute(text(
            "SELECT p.id, p.tenant_id, t.tenant_name, p.name, p.owner_user_id, "
            "p.is_active, p.created_at "
            "FROM projects p "
            "LEFT JOIN tenants t ON t.id = p.tenant_id "
            "ORDER BY p.tenant_id, p.id"
        )).fetchall()
        if not rows:
            print("  (zadne)")
        for r in rows:
            print(f"  proj_id={r[0]:<3} tenant_id={r[1]!s:<3} tenant={r[2]!s:<15} "
                  f"name={r[3]!s:<25} owner={r[4]!s:<5} active={r[5]!s:<5} "
                  f"created={r[6]}")

        print("\n== USER_PROJECTS (css_db) ==")
        rows = cs.execute(text(
            "SELECT up.user_id, up.project_id, p.name, up.role "
            "FROM user_projects up "
            "LEFT JOIN projects p ON p.id = up.project_id "
            "ORDER BY up.user_id, up.project_id"
        )).fetchall()
        if not rows:
            print("  (zadne)")
        for r in rows:
            print(f"  user_id={r[0]:<3} proj_id={r[1]:<3} name={r[2]!s:<25} role={r[3]}")
    finally:
        cs.close()

    # 2) conversations
    ds = get_data_session()
    try:
        print("\n== CONVERSATIONS (data_db, posledních 10) ==")
        rows = ds.execute(text(
            "SELECT id, user_id, tenant_id, active_agent_id, title, is_deleted, created_at "
            "FROM conversations ORDER BY id DESC LIMIT 10"
        )).fetchall()
        for r in rows:
            print(f"  conv_id={r[0]:<3} user_id={r[1]!s:<4} tenant_id={r[2]!s:<5} "
                  f"agent={r[3]!s:<4} del={r[5]!s:<5} title={r[4]!s:<40} created={r[6]}")

        print("\n== MESSAGES (data_db, posledních 15) ==")
        rows = ds.execute(text(
            "SELECT id, conversation_id, role, author_type, author_user_id, "
            "agent_id, message_type, LEFT(content, 50) AS preview "
            "FROM messages ORDER BY id DESC LIMIT 15"
        )).fetchall()
        for r in rows:
            print(f"  msg_id={r[0]:<4} conv={r[1]:<4} role={r[2]:<10} "
                  f"auth_type={r[3]!s:<6} auth_uid={r[4]!s:<5} "
                  f"agent={r[5]!s:<5} msg_type={r[6]!s:<7} | {r[7]}")
    finally:
        ds.close()


if __name__ == "__main__":
    main()
