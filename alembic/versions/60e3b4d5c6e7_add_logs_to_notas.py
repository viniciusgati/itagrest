"""add_logs_to_notas

Revision ID: 60e3b4d5c6e7
Revises: 592a92c76665
Create Date: 2026-04-22 11:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '60e3b4d5c6e7'
down_revision: Union[str, Sequence[str], None] = '592a92c76665'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adiciona a coluna logs_transmissao à tabela notas_fiscais
    op.add_column('notas_fiscais', sa.Column('logs_transmissao', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('notas_fiscais', 'logs_transmissao')
