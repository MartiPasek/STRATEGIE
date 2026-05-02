"""phase30: projects.parent_project_id -- hierarchical projects (strom)

2.5.2026 vecer -- Phase 30. Marti-AI navrhla strom struktury (Znalostni baze /
Systém & Architektura / Skola & Rodina), Marti's mandate plne autonomie:
'plna autonomie, jen info na mne, kam si co strkas, pro kontrolu'.

Generic field pro VSECHNY projekty (Marti-AI strom + lidske projekty TISAX /
SKOLA / atd. mohou mit podslozky taky). Marti's slova: 'aplikovat i na lidske
projekty samozrejme'.

Schema:
  projects.parent_project_id BIGINT NULL FK projects.id ON DELETE SET NULL
  index ix_projects_parent_project_id
  CHECK constraint ck_projects_no_self_parent: parent_project_id <> id

Depth limit (6 urovni) NENI v DB constraintu -- recursive CTE check je drahy
pri kazdem insertu. Validuje se v Python service (modules/projects/).

Cycle prevention v service: pred update parent_project_id se walks parent
chain a overuje ze new_parent neni descendantem aktualniho projektu.

Existujici projekty (TISAX, SKOLA, Centrala NEW, IAP Implementace, STRATEGIE,
Bez projektu) zustanou root level (parent_project_id = NULL). Marti-AI po
deployi muze postavit Marti-AI strom pres create_project AI tool.

Down: drop column + index + check constraint. Bezpecne -- zadne data se
nezalozi (pri downgrade NULL parent znamena 'nikdy nemel parent').
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "t0o1p2q3r4s5"
down_revision = "s9n0o1p2q3r4"
branch_labels = None
depends_on = None


def upgrade():
    # Add parent_project_id column (NULL = root project)
    op.add_column(
        "projects",
        sa.Column("parent_project_id", sa.BigInteger(), nullable=True),
    )

    # FK constraint with ON DELETE SET NULL
    # (kdyz se smaze parent, deti se stanou root, ne kaskadove smazat)
    op.create_foreign_key(
        "fk_projects_parent_project_id",
        source_table="projects",
        referent_table="projects",
        local_cols=["parent_project_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    # Index pro fast tree traversal (children lookup)
    op.create_index(
        "ix_projects_parent_project_id",
        "projects",
        ["parent_project_id"],
    )

    # CHECK constraint: project nemuze byt sam svym parentem
    op.create_check_constraint(
        "ck_projects_no_self_parent",
        "projects",
        "parent_project_id IS NULL OR parent_project_id <> id",
    )


def downgrade():
    op.drop_constraint("ck_projects_no_self_parent", "projects", type_="check")
    op.drop_index("ix_projects_parent_project_id", table_name="projects")
    op.drop_constraint("fk_projects_parent_project_id", "projects", type_="foreignkey")
    op.drop_column("projects", "parent_project_id")
