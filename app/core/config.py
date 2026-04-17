import os
from dotenv import load_dotenv

# Carregar arquivo .env manualmente
load_dotenv()

class Settings:
    APP_NAME: str = "iTagREST"
    VERSION: str = "1.0.0"
    
    # AMBIENTE: test, homolog, production (Default: homolog para sua máquina)
    ENV: str = os.getenv("APP_ENV", "homolog").lower()
    
    # LÓGICA DE BANCO DE DADOS (Regra de Ouro)
    @property
    def DATABASE_URL(self) -> str:
        # 1. Se for ambiente de TEST, forçar SQLite
        if self.ENV == "test":
            return "sqlite:///./test.db"
        
        # 2. Para Homolog ou Produção, DEVE ser Postgres
        db_url = os.getenv("DATABASE_URL")
        
        # Se houver uma URL no .env e for Postgres, usamos ela
        if db_url and db_url.startswith("postgresql"):
            return db_url
            
        # 3. Fallback: Montar nome baseado no ambiente (itagrest_homolog ou itagrest_production)
        db_user = os.getenv("DB_USER", "root")
        db_pass = os.getenv("DB_PASS", "root")
        db_host = os.getenv("DB_HOST", "localhost")
        db_name = f"itagrest_{self.ENV}"
        
        return f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}"

    # Fiscal
    CERT_DIR: str = os.getenv("CERT_DIR", "storage/certs")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "SUA_CHAVE_SECRETA_SUPER_SEGURA")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

# Singleton
settings = Settings()
