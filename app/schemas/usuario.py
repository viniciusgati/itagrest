from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.usuario import PapelUsuario

class UsuarioBase(BaseModel):
    full_name: str
    username: str
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class Usuario(UsuarioBase):
    id: int
    created_at: datetime
    is_active: int
    papel: PapelUsuario

    class Config:
        from_attributes = True

class SetupBootstrap(BaseModel):
    admin: UsuarioCreate
