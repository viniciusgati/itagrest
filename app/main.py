from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.endpoints import setup, auth, empresa, produtos, vendas, notas, clientes
from app.db.session import engine, Base
import os

# Criar diretórios de storage se não existirem
os.makedirs("storage/certs", exist_ok=True)
os.makedirs("storage/produtos", exist_ok=True)

app = FastAPI(title="iTagREST - Sistema Fiscal para Restaurantes", version="0.1.0")

# Servir arquivos estáticos (Imagens de Produtos)
app.mount("/static/produtos", StaticFiles(directory="storage/produtos"), name="produtos")

# Configuração de CORS Dinâmica e Segura
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "").split(",")
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

# Sanitização e adição de origens da variável de ambiente
for origin in allowed_origins_raw:
    clean_origin = origin.strip().strip("\"'").rstrip("/")
    if clean_origin:
        origins.append(clean_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"], # Fallback para * se nada for definido (evita quebrar)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Bem-vindo ao iTagREST API"}

# Registro dos roteadores
app.include_router(setup.router, prefix="/api/v1/setup", tags=["Setup Inicial"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(empresa.router, prefix="/api/v1/empresa", tags=["Configuração Fiscal"])
app.include_router(produtos.router, prefix="/api/v1/produtos", tags=["Cardápio"])
app.include_router(clientes.router, prefix="/api/v1/clientes", tags=["Clientes"])
app.include_router(vendas.router, prefix="/api/v1/vendas", tags=["Operação de Venda"])
app.include_router(notas.router, prefix="/api/v1/notas", tags=["NFC-e"])
