#!/bin/bash
set -e

echo "--- Iniciando iTagREST Backend ---"

# Porta dinâmica para o Railway ou fallback para 8000
PORT="${PORT:-8001}"

# Se estivermos no Railway ou Produção, pulamos o wait de host fixo
if [ "$APP_ENV" != "production" ] && [ -n "$DB_HOST" ]; then
    echo "Aguardando banco de dados ($DB_HOST:5432)..."
    until pg_isready -h "$DB_HOST" -p 5432 -U "${DB_USER:-root}" > /dev/null 2>&1; do
      sleep 2
    done
    echo "Banco de dados pronto!"
fi

# Executa as migrações do Alembic
echo "Executando migrações..."
alembic upgrade head

# Inicia o servidor FastAPI usando a porta correta
echo "Iniciando Uvicorn na porta $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
