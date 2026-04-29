from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from enum import Enum
from app.schemas.produto import Produto

class StatusVenda(str, Enum):
    ABERTA = "ABERTA"
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    PAGA = "PAGA"
    CANCELADA = "CANCELADA"

class FormaPagamento(str, Enum):
    DINHEIRO = "DINHEIRO"

# --- Schemas para Itens ---

class VendaItemBase(BaseModel):
    produto_id: int
    quantidade: int

class VendaItemCreate(VendaItemBase):
    preco_customizado: Optional[Decimal] = None

class VendaItemUpdate(BaseModel):
    quantidade: Optional[int] = None
    preco_unitario: Optional[Decimal] = None

class VendaItem(VendaItemBase):
    id: int
    venda_id: int
    preco_unitario: Decimal
    subtotal: Decimal
    descricao: Optional[str] = None
    unidade: Optional[str] = None
    produto: Optional[Produto] = None

    class Config:
        from_attributes = True

# --- Schemas para Venda (Cabeçalho) ---

from app.schemas.cliente import Cliente

class VendaBase(BaseModel):
    mesa: int
    cliente_id: Optional[int] = None

class VendaCreate(VendaBase):
    pass

class VendaUpdate(BaseModel):
    status: Optional[StatusVenda] = None
    forma_pagamento: Optional[FormaPagamento] = None
    cliente_id: Optional[int] = None

class Venda(VendaBase):
    id: int
    status: StatusVenda
    total: Decimal
    data_abertura: datetime
    data_fechamento: Optional[datetime] = None
    forma_pagamento: Optional[FormaPagamento] = None
    pix_payload: Optional[str] = None
    pix_expiracao: Optional[datetime] = None
    itens: List[VendaItem] = []
    cliente: Optional[Cliente] = None

    class Config:
        from_attributes = True

        from_attributes = True

# Schema para status simplificado de mesa
class MesaStatus(BaseModel):
    mesa: int
    venda_id: Optional[int] = None
    status: str # 'LIVRE', 'EM_ATENDIMENTO', 'AGUARDANDO_PAGAMENTO'
    total: Decimal = Decimal("0.00")
