from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class ClienteBase(BaseModel):
    nome: str
    documento: str
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    municipio_nome: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(ClienteBase):
    nome: Optional[str] = None
    documento: Optional[str] = None

class Cliente(ClienteBase):
    id: int
    data_cadastro: datetime

    class Config:
        from_attributes = True
