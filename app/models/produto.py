from sqlalchemy import Column, Integer, String, Numeric, Enum, Boolean
from app.db.session import Base
import enum

class CategoriaEnum(str, enum.Enum):
    BEBIDA = "BEBIDA"
    REFEICAO = "REFEICAO"
    OUTROS = "OUTROS"

class Produto(Base):
    """
    Cadastro de produtos do cardápio com tributação detalhada para NFC-e.
    """
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    codigo_barras = Column(String(13), nullable=True)
    plu = Column(Integer, nullable=True)
    descricao = Column(String(255), nullable=False)
    preco_venda = Column(Numeric(10, 2), nullable=False)
    unidade = Column(String(10), default="UN")
    categoria = Column(Enum(CategoriaEnum), default=CategoriaEnum.OUTROS)
    imagem_url = Column(String(255))
    ativo = Column(Boolean, default=True)
    
    # --- Campos Fiscais ---
    ncm = Column(String(8), nullable=False)
    cest = Column(String(7), nullable=True)
    cfop = Column(String(4), nullable=False)
    origem = Column(String(1), default="0") # 0=Nacional, 1=Importado
    
    # Tributação ICMS/PIS/COFINS (Conforme XML de referência)
    cst_icms = Column(String(3), default="000") # Ou CSOSN
    cst_pis = Column(String(2), default="07")
    cst_cofins = Column(String(2), default="07")
    
    # Alíquotas
    aliquota_pis = Column(Numeric(5, 2), default=0.00)
    aliquota_cofins = Column(Numeric(5, 2), default=0.00)
    aliquota_icms = Column(Numeric(5, 2), default=0.00)
