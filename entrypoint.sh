#!/bin/bash
set -e

# Aguarda o DB estar pronto se necessário (opcional com healthcheck no compose)
echo "Aguardando inicialização do banco de dados..."

# Executa as migrações do Alembic
echo "Executando migrações do Alembic..."
alembic upgrade head

# Inicia o servidor FastAPI
echo "Iniciando servidor FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
