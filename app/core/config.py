import os
from dotenv import load_dotenv

# Carregar arquivo .env manualmente
load_dotenv()

class Settings:
    """Configurações manuais para evitar problemas de validação do Pydantic no ambiente OS."""
    APP_NAME: str = os.getenv("APP_NAME", "iTagRest")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    VERSION: str = os.getenv("VERSION", "0.1.0")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://root:root@localhost:5432/itagrest_db")
    
    # Fiscal
    CERT_DIR: str = os.getenv("CERT_DIR", "storage/certs")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "SUA_CHAVE_SECRETA_SUPER_SEGURA")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

# Singleton
settings = Settings()
