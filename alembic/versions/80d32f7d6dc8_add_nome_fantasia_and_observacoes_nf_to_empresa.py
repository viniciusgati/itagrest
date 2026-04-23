"""add_nome_fantasia_and_observacoes_nf_to_empresa

Revision ID: 80d32f7d6dc8
Revises: e110634bbad6
Create Date: 2026-04-23 08:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80d32f7d6dc8'
down_revision: Union[str, Sequence[str], None] = 'e110634bbad6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Como as colunas já foram criadas via exec manual ou migração anterior perdida,
    # usamos o op.add_column com segurança ou apenas deixamos o alembic feliz.
    # Para garantir coesão, vamos verificar se existem antes.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('empresas')]
    
    if 'nome_fantasia' not in columns:
        op.add_column('empresas', sa.Column('nome_fantasia', sa.String(length=255), nullable=True))
    if 'observacoes_nf' not in columns:
        op.add_column('empresas', sa.Column('observacoes_nf', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('empresas', 'observacoes_nf')
    op.drop_column('empresas', 'nome_fantasia')
