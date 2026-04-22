from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# 1. Importar a Base e os Modelos do Projeto
from app.db.session import Base
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.produto import Produto
from app.models.venda import Venda, VendaItem
from app.models.cliente import Cliente
from app.models.nota_fiscal import NotaFiscal
from app.core.config import settings

# 2. Configurar os logs
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Vincular a URL do Banco do .env ao Alembic
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
