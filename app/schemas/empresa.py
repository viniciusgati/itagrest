from pydantic import BaseModel, Field
from typing import Optional

class EmpresaBase(BaseModel):
    cnpj: str = Field(..., min_length=14, max_length=14, description="CNPJ do emitente")
    razao_social: str = Field(..., max_length=255, description="Razão Social do emitente")
    inscricao_estadual: str = Field(..., max_length=20, description="Inscrição Estadual do emitente")
    
    # Endereço
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    municipio_ibge: Optional[str] = None
    municipio_nome: Optional[str] = None
    uf: Optional[str] = Field(None, max_length=2, description="UF com 2 caracteres")
    cep: Optional[str] = Field(None, max_length=8, description="CEP com 8 caracteres")
    
    # Configurações SEFAZ
    ambiente: int = Field(2, description="1: Produção, 2: Homologação")
    csc_token: Optional[str] = None
    csc_id: Optional[str] = None
    pix_chave: Optional[str] = None

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaUpdate(EmpresaBase):
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    configurado: Optional[bool] = None

class Empresa(EmpresaBase):
    id: int
    configurado: bool
    certificado_path: Optional[str] = None

    class Config:
        from_attributes = True

class CertificadoConfig(BaseModel):
    senha: str = Field(..., min_length=4, description="Senha do certificado digital")
