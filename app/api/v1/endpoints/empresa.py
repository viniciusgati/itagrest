from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.empresa import Empresa as EmpresaModel
from app.schemas.empresa import EmpresaCreate, Empresa as EmpresaSchema
from app.services.certificado import CertificadoService

router = APIRouter()

@router.get("/status", response_model=dict)
def get_empresa_status(db: Session = Depends(get_db)):
    """Verifica se a empresa já está configurada."""
    empresa = db.query(EmpresaModel).first()
    return {
        "configurado": empresa.configurado if empresa else False,
        "empresa": EmpresaSchema.model_validate(empresa) if empresa else None
    }

@router.post("/configurar", response_model=EmpresaSchema)
def configurar_empresa(empresa_in: EmpresaCreate, db: Session = Depends(get_db)):
    """Salva os dados iniciais da empresa (CNPJ, IE, Endereço, etc.)."""
    empresa = db.query(EmpresaModel).first()
    
    if not empresa:
        empresa = EmpresaModel(**empresa_in.model_dump())
        db.add(empresa)
    else:
        # Atualiza dados se já existir
        for field, value in empresa_in.model_dump().items():
            # SEGURANÇA: Não sobrescreve a senha do certificado se vier vazia
            if field == 'certificado_senha' and not value:
                continue
            setattr(empresa, field, value)
            
    db.commit()
    db.refresh(empresa)
    return empresa

@router.post("/upload-certificado", response_model=dict)
async def upload_certificado(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    senha: str = Form(...)
):
    """Realiza o upload do certificado PFX e valida a senha."""
    # 1. Validar se o arquivo é .pfx
    if not file.filename.endswith(".pfx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos .pfx são permitidos."
        )
    
    # 2. Ler conteúdo para validação
    content = await file.read()
    
    # 3. Validar Certificado PFX
    if not CertificadoService.validar_pfx(content, senha):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha do certificado inválida ou arquivo corrompido."
        )
        
    # 4. Salvar Certificado
    path = CertificadoService.salvar_pfx(content, file.filename)
    
    # 5. Atualizar Empresa no Banco
    empresa = db.query(EmpresaModel).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configure os dados da empresa (Passo 1) antes de enviar o certificado."
        )
        
    empresa.certificado_path = path
    empresa.certificado_senha = senha
    empresa.configurado = True # Marca como concluído o wizard fiscal
    
    db.commit()
    
    return {"message": "Certificado configurado com sucesso!", "path": path}
