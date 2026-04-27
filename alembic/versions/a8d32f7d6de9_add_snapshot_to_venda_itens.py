"""add_snapshot_to_venda_itens

Revision ID: a8d32f7d6de9
Revises: 80d32f7d6dc8
Create Date: 2026-04-27 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8d32f7d6de9'
down_revision: Union[str, Sequence[str], None] = '80d32f7d6dc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Adicionar novas colunas como nullable primeiro
    op.add_column('venda_itens', sa.Column('descricao', sa.String(length=255), nullable=True))
    op.add_column('venda_itens', sa.Column('unidade', sa.String(length=10), nullable=True, server_default='UN'))
    
    # 2. Alterar produto_id para ser nullable (para suportar deleção com SET NULL)
    op.alter_column('venda_itens', 'produto_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # 3. Remover a FK antiga e adicionar a nova com ondelete='SET NULL'
    # Nota: Tentamos dropar a constraint padrão. Se o nome for diferente, o erro aparecerá no log.
    try:
        op.drop_constraint('venda_itens_produto_id_fkey', 'venda_itens', type_='foreignkey')
    except Exception:
        pass
        
    op.create_foreign_key(
        'venda_itens_produto_id_fkey',
        'venda_itens', 'produtos',
        ['produto_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('venda_itens_produto_id_fkey', 'venda_itens', type_='foreignkey')
    op.create_foreign_key(
        'venda_itens_produto_id_fkey',
        'venda_itens', 'produtos',
        ['produto_id'], ['id']
    )
    op.alter_column('venda_itens', 'produto_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('venda_itens', 'unidade')
    op.drop_column('venda_itens', 'descricao')
