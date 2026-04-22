from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class NotaFiscal(Base):
    """
    Registro de notas fiscais emitidas (NFC-e modelo 65).
    Vinculado a uma venda fechada.
    """
    __tablename__ = "notas_fiscais"

    id = Column(Integer, primary_key=True, index=True)
    venda_id = Column(Integer, ForeignKey("vendas.id"), nullable=False, unique=True)
    
    # Dados da Transmissão
    chave_acesso = Column(String(44), nullable=True, unique=True) # 44 dígitos da NFe
    numero_nota = Column(Integer, nullable=True)
    serie_nota = Column(Integer, nullable=True)
    protocolo = Column(String(50), nullable=True)
    status_sefaz = Column(String(10), nullable=True) # 100=Autorizado, etc.
    motivo_sefaz = Column(String(255), nullable=True)
    
    # Conteúdo XML (Autorizado)
    xml_autorizado = Column(Text, nullable=True)
    
    # Auditoria e Logs
    logs_transmissao = Column(Text, nullable=True)
    data_emissao = Column(DateTime, default=datetime.utcnow)

    # Cancelamento
    protocolo_cancelamento = Column(String(50), nullable=True)
    motivo_cancelamento = Column(String(255), nullable=True)
    data_cancelamento = Column(DateTime, nullable=True)

    # Relacionamento
    venda = relationship("app.models.venda.Venda")
