"""add DM (direct message) chat support

Revision ID: c3d1a82e7f90
Revises: 2474a5913b41
Create Date: 2026-04-18 13:10:00.000000

Adds basic user-to-user chat (DM) on top of existing conversations/messages:
  - conversations: conversation_type, created_by_user_id, dm_user_low_id,
    dm_user_high_id, last_message_id
  - messages: message_type
  - new table: conversation_participants (per-user read state / flags)
  - partial unique index on (dm_user_low_id, dm_user_high_id) WHERE conversation_type='dm'
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c3d1a82e7f90'
down_revision: Union[str, None] = '2474a5913b41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── conversations ─────────────────────────────────────────────────
    op.add_column(
        'conversations',
        sa.Column(
            'conversation_type',
            sa.String(length=20),
            nullable=False,
            server_default='ai',
        ),
    )
    op.add_column('conversations', sa.Column('created_by_user_id', sa.BigInteger(), nullable=True))
    op.add_column('conversations', sa.Column('dm_user_low_id', sa.BigInteger(), nullable=True))
    op.add_column('conversations', sa.Column('dm_user_high_id', sa.BigInteger(), nullable=True))
    op.add_column('conversations', sa.Column('last_message_id', sa.BigInteger(), nullable=True))

    # partial unique index: only one DM per unordered pair of users
    op.execute(
        "CREATE UNIQUE INDEX ix_conversations_dm_pair "
        "ON conversations (dm_user_low_id, dm_user_high_id) "
        "WHERE conversation_type = 'dm'"
    )

    # ── messages ──────────────────────────────────────────────────────
    op.add_column(
        'messages',
        sa.Column(
            'message_type',
            sa.String(length=20),
            nullable=False,
            server_default='text',
        ),
    )

    # ── conversation_participants ─────────────────────────────────────
    op.create_table(
        'conversation_participants',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('participant_role', sa.String(length=20), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_read_message_id', sa.BigInteger(), nullable=True),
        sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_muted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'user_id', name='uq_participant_conv_user'),
    )
    op.create_index(
        'ix_participants_user_id',
        'conversation_participants',
        ['user_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_participants_user_id', table_name='conversation_participants')
    op.drop_table('conversation_participants')

    op.drop_column('messages', 'message_type')

    op.execute('DROP INDEX IF EXISTS ix_conversations_dm_pair')
    op.drop_column('conversations', 'last_message_id')
    op.drop_column('conversations', 'dm_user_high_id')
    op.drop_column('conversations', 'dm_user_low_id')
    op.drop_column('conversations', 'created_by_user_id')
    op.drop_column('conversations', 'conversation_type')
