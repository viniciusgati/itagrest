FROM python:3.10-slim

# Dependências de sistema (Agrupadas e otimizadas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    libxml2-dev \
    libxslt1-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    zlib1g-dev \
    libjpeg-dev \
    libffi-dev \
    libssl-dev \
    swig \
    python3-dev \
    pkg-config \
    git \
    xmlsec1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade ferramentas de build
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 1. Copiar apenas o arquivo de dependências primeiro (Otimização de Cache)
COPY requirements.txt .

# 2. Instalar todas as dependências em uma única camada
# Incluímos as dependências críticas do ERPBrasil na mesma leva
RUN pip install --no-cache-dir uvicorn[standard] gunicorn reportlab pillow alembic email-validator && \
    pip install --no-cache-dir "erpbrasil.assinatura" "nfelib<1.0.0" "erpbrasil.edoc" "erpbrasil.edoc.pdf" && \
    pip install --no-cache-dir -r requirements.txt

# 3. Copiar o restante do código (Apenas arquivos permitidos pelo .dockerignore)
COPY . .

RUN chmod +x entrypoint.sh
EXPOSE 8001
ENTRYPOINT ["./entrypoint.sh"]
