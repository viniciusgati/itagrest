import os
# FORÇAR AMBIENTE DE TESTE
os.environ["APP_ENV"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base, get_db

# Importar todos os modelos para o SQLAlchemy reconhecê-los
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.produto import Produto
from app.models.venda import Venda, VendaItem
from app.models.cliente import Cliente
from app.models.nota_fiscal import NotaFiscal

# Banco de dados de teste (SQLite em memória)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sobrescrever a dependência do banco de dados
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    # Cria as tabelas antes dos testes
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    # Remove as tabelas após os testes
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Cria uma sessão de banco limpa para cada teste unitário."""
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)
