from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import setup, auth
from app.db.session import engine, Base

# Criação das tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="iTagREST - Sistema Fiscal para Restaurantes", version="0.1.0")

# Configurar CORS para o Frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
