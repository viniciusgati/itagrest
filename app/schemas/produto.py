from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from enum import Enum

class CategoriaEnum(str, Enum):
    BEBIDA = "BEBIDA"
    REFEICAO = "REFEICAO"
    OUTROS = "OUTROS"

class ProdutoBase(BaseModel):
    descricao: str = Field(..., min_length=3, max_length=255)
    preco_venda: Decimal = Field(..., gt=0)
    unidade: str = Field("UN", max_length=10)
    categoria: CategoriaEnum = Field(CategoriaEnum.OUTROS)
    ncm: str = Field(..., min_length=8, max_length=8)
    cest: Optional[str] = Field(None, min_length=7, max_length=7)
    cfop: str = Field(..., min_length=4, max_length=4)
    origem: str = Field("0", max_length=1)
    cst_icms: str = Field("000", max_length=3)
    cst_pis: str = Field("07", max_length=2)
    cst_cofins: str = Field("07", max_length=2)
    aliquota_pis: Decimal = Field(Decimal("0.00"))
    aliquota_cofins: Decimal = Field(Decimal("0.00"))
    aliquota_icms: Decimal = Field(Decimal("0.00"))
    imagem_url: Optional[str] = None

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(BaseModel):
    descricao: Optional[str] = Field(None, min_length=3, max_length=255)
    preco_venda: Optional[Decimal] = Field(None, gt=0)
    unidade: Optional[str] = Field(None, max_length=10)
    categoria: Optional[CategoriaEnum] = None
    ncm: Optional[str] = Field(None, min_length=8, max_length=8)
    cest: Optional[str] = Field(None, min_length=7, max_length=7)
    cfop: Optional[str] = Field(None, min_length=4, max_length=4)
    origem: Optional[str] = None
    cst_icms: Optional[str] = None
    cst_pis: Optional[str] = None
    cst_cofins: Optional[str] = None
    aliquota_pis: Optional[Decimal] = None
    aliquota_cofins: Optional[Decimal] = None
    aliquota_icms: Optional[Decimal] = None
    imagem_url: Optional[str] = None

class Produto(ProdutoBase):
    id: int

    class Config:
        from_attributes = True
