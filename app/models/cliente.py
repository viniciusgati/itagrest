from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    documento = Column(String(20), unique=True, index=True, nullable=False) # CPF ou CNPJ
    email = Column(String(100))
    telefone = Column(String(20))
    
    # Endereço (Simplificado para NFC-e)
    logradouro = Column(String(100))
    numero = Column(String(10))
    bairro = Column(String(50))
    municipio_nome = Column(String(50))
    uf = Column(String(2))
    cep = Column(String(8))

    data_cadastro = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    vendas = relationship("Venda", back_populates="cliente")
