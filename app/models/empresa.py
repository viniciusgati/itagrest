from sqlalchemy import Column, Integer, String, Boolean, Enum
from app.db.session import Base

class Empresa(Base):
    """
    Modelo do Emitente da NF-e / NFC-e.
    Guarda os dados do restaurante e o status da ativação fiscal.
    """
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(14), unique=True, index=True, nullable=False)
    razao_social = Column(String(255), nullable=False)
    inscricao_estadual = Column(String(20), nullable=False)
    
    # Endereço Básico (Exigido pela SEFAZ)
    logradouro = Column(String(255))
    numero = Column(String(20))
    bairro = Column(String(100))
    municipio_ibge = Column(String(7)) # Código IBGE da cidade
    municipio_nome = Column(String(100))
    uf = Column(String(2))
    cep = Column(String(8))
    
    # Configurações de Emissão
    ambiente = Column(Integer, default=2) # 1: Produção, 2: Homologação (Testes)
    
    # Certificado Digital (PFX)
    # Guardamos apenas o caminho do arquivo físico que subirá para storage/certs/
    certificado_path = Column(String(255))
    certificado_senha = Column(String(255)) # Senha do Certificado Digital
    
    # Para NFC-e (Cupom Fiscal de Venda de Balcão)
    csc_token = Column(String(100)) # Token do Código de Segurança do Contribuinte
    csc_id = Column(String(10))     # ID do Token (ex: 000001)
    
    # Recebimentos
    pix_chave = Column(String(100), nullable=True) # Chave PIX para pagamentos
    
    configurado = Column(Boolean, default=False)
