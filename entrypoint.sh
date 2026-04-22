#!/bin/bash
set -e

echo "--- Iniciando iTagREST Backend ---"

# Aguarda o DB estar pronto
echo "Aguardando banco de dados (db:5432)..."
until pg_isready -h "db" -p 5432 -U "root" > /dev/null 2>&1; do
  sleep 2
done
echo "Banco de dados pronto!"

# Executa as migrações do Alembic
echo "Executando migrações..."
alembic upgrade head

# Inicia o servidor FastAPI
echo "Iniciando Uvicorn na porta 8001..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
