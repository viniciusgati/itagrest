from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime
import enum

class StatusVenda(str, enum.Enum):
    ABERTA = "ABERTA"
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    PAGA = "PAGA"
    CANCELADA = "CANCELADA"

class FormaPagamento(str, enum.Enum):
    DINHEIRO = "DINHEIRO"

class Venda(Base):
    """
    Cabeçalho da venda (Comanda/Mesa).
    Controla o estado da mesa e o total acumulado.
    """
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)
    mesa = Column(Integer, nullable=False) # Número da mesa/comanda
    status = Column(Enum(StatusVenda), default=StatusVenda.ABERTA)
    total = Column(Numeric(10, 2), default=0.00)
    data_abertura = Column(DateTime, default=datetime.utcnow)
    data_fechamento = Column(DateTime, nullable=True)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=True)
    
    # Payload PIX gerado para esta venda específica
    pix_payload = Column(String(512), nullable=True)
    pix_expiracao = Column(DateTime, nullable=True)

    # Relacionamentos
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    cliente = relationship("Cliente", back_populates="vendas")
    
    itens = relationship("VendaItem", back_populates="venda", cascade="all, delete-orphan")

    # ÍNDICE DE UNICIDADE PARCIAL: Só permite uma mesa ativa (ABERTA ou AGUARDANDO_PAGAMENTO) por vez.
    # Se status for PAGA ou CANCELADA, a mesa pode ser aberta novamente.
    __table_args__ = (
        Index(
            "idx_venda_ativa_mesa",
            "mesa",
            unique=True,
            postgresql_where=(status.in_([StatusVenda.ABERTA, StatusVenda.AGUARDANDO_PAGAMENTO]))
        ),
    )

class VendaItem(Base):
    """
    Itens vinculados a uma venda.
    Copia todos os dados do produto no momento da venda para garantir histórico imutável.
    """
    __tablename__ = "venda_itens"

    id = Column(Integer, primary_key=True, index=True)
    venda_id = Column(Integer, ForeignKey("vendas.id"), nullable=False)
    # Tornamos produto_id opcional para caso o produto seja deletado do cadastro
    produto_id = Column(Integer, ForeignKey("produtos.id", ondelete="SET NULL"), nullable=True)
    quantidade = Column(Integer, default=1)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    # --- Dados do Snapshot (Cópia fiel do produto no momento do lançamento) ---
    descricao = Column(String(255), nullable=True)
    unidade = Column(String(10), default="UN")
    
    # --- Campos Fiscais ---
    ncm = Column(String(8), nullable=True)
    cest = Column(String(7), nullable=True)
    cfop = Column(String(4), nullable=True)
    origem = Column(String(1), default="0")
    cst_icms = Column(String(3), nullable=True)
    cst_pis = Column(String(2), nullable=True)
    cst_cofins = Column(String(2), nullable=True)
    aliquota_pis = Column(Numeric(5, 2), default=0.00)
    aliquota_cofins = Column(Numeric(5, 2), default=0.00)
    aliquota_icms = Column(Numeric(5, 2), default=0.00)

    # Relacionamentos
    venda = relationship("Venda", back_populates="itens")
    # Usamos o relacionamento mas precisamos estar cientes de que pode ser None se o produto for deletado
    produto = relationship("Produto", lazy="joined")
