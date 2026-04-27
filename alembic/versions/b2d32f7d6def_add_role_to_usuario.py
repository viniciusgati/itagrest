"""add_role_to_usuario

Revision ID: b2d32f7d6def
Revises: a8d32f7d6de9
Create Date: 2026-04-27 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2d32f7d6def'
down_revision: Union[str, Sequence[str], None] = 'a8d32f7d6de9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Definir o nome do tipo ENUM para o Postgres
papel_enum = sa.Enum('GERENTE', 'GARCOM', name='papelusuario')

def upgrade() -> None:
    # 1. Criar o tipo ENUM no banco de dados
    papel_enum.create(op.get_bind())
    
    # 2. Adicionar a coluna com o valor default 'GARCOM'
    op.add_column('usuarios', sa.Column('papel', papel_enum, nullable=False, server_default='GARCOM'))


def downgrade() -> None:
    # 1. Remover a coluna
    op.drop_column('usuarios', 'papel')
    
    # 2. Remover o tipo ENUM
    papel_enum.drop(op.get_bind())
