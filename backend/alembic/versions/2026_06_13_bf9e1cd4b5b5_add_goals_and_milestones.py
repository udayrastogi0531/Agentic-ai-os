"""add goals and milestones tables

Revision ID: bf9e1cd4b5b5
Revises: 7e4f1cd4b5b4
Create Date: 2026-06-13 21:05:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'bf9e1cd4b5b5'
down_revision: Union[str, None] = '7e4f1cd4b5b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create goals table
    op.create_table('goals',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.String(length=1000), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=False),
    sa.Column('progress', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('target_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goals_user_id'), 'goals', ['user_id'], unique=False)

    # Create milestones table
    op.create_table('milestones',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('goal_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('is_completed', sa.Boolean(), nullable=False),
    sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_milestones_goal_id'), 'milestones', ['goal_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_milestones_goal_id'), table_name='milestones')
    op.drop_table('milestones')
    op.drop_index(op.f('ix_goals_user_id'), table_name='goals')
    op.drop_table('goals')
