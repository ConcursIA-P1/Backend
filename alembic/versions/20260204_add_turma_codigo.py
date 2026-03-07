"""add turma codigo

Revision ID: add_turma_codigo
Revises: 196f3771af66
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_turma_codigo'
down_revision: Union[str, None] = '196f3771af66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'turmas')"
    ))
    if result.scalar():
        op.add_column('turmas', sa.Column('codigo', sa.String(10), nullable=True))
        op.create_index('ix_turmas_codigo', 'turmas', ['codigo'], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'turmas')"
    ))
    if result.scalar():
        op.drop_index('ix_turmas_codigo', table_name='turmas')
        op.drop_column('turmas', 'codigo')
