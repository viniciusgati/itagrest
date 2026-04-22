FROM python:3.10-slim

# Dependências de sistema para compilar bibliotecas fiscais (M2Crypto, lxml, etc)
RUN apt-get update && apt-get install -y \
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Setup pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copiar requirements
COPY requirements.txt .

# Instalar dependências principais (Ordem importa para pacotes namespace)
RUN pip install --no-cache-dir uvicorn[standard] gunicorn reportlab pillow alembic email-validator && \
    pip install --no-cache-dir erpbrasil.base nfelib erpbrasil.edoc

# Instalar o resto dos requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

RUN chmod +x entrypoint.sh
EXPOSE 8001
ENTRYPOINT ["./entrypoint.sh"]
