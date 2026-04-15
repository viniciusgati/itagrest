from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Engine do SQLAlchemy (Conexão direta com o Postgres)
engine = create_engine(settings.DATABASE_URL)

# Fábrica de sessões (Cada request da API terá a sua)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para herança das tabelas do banco
Base = declarative_base()

# Dependência do FastAPI para obter a sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
