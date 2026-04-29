"""promote_first_user_to_gerente

Revision ID: fed318ac0621
Revises: b2d32f7d6def
Create Date: 2026-04-29 08:42:03.911733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fed318ac0621'
down_revision: Union[str, Sequence[str], None] = 'b2d32f7d6def'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Promove o primeiro usuário cadastrado para o papel de GERENTE.
    Isso corrige o problema de usuários administradores criados como GARCOM.
    """
    op.execute(
        "UPDATE usuarios SET papel = 'GERENTE' WHERE id IN (SELECT id FROM usuarios ORDER BY id ASC LIMIT 1)"
    )


def downgrade() -> None:
    """Não fazemos downgrade aqui pois não queremos remover permissões de quem já tem."""
    pass
