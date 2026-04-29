from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.cliente import Cliente as ClienteModel
from app.schemas.cliente import Cliente, ClienteCreate, ClienteUpdate
from app.api.v1.deps import get_current_user
from app.models.usuario import Usuario
from app.services.parser_cnpj import extrair_cnpj_do_pdf

router = APIRouter()

@router.get("", response_model=List[Cliente])
def listar_clientes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(ClienteModel).offset(skip).limit(limit).all()

@router.post("/extrair-cnpj-pdf")
async def extrair_cnpj_pdf(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user)
):
    """Extrai dados de cliente de um Cartão CNPJ (PDF da Receita Federal)."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um PDF.")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF muito grande. Máximo 5MB.")

    try:
        dados = extrair_cnpj_do_pdf(content)
        if not dados.cnpj:
            raise HTTPException(status_code=422, detail="Não foi possível encontrar o CNPJ no PDF. Verifique se é um Cartão CNPJ válido.")
        return dados
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("", response_model=Cliente, status_code=status.HTTP_201_CREATED)
def criar_cliente(
    cliente_in: ClienteCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Limpar máscara do documento
    doc_limpo = "".join(filter(str.isdigit, cliente_in.documento))
    
    db_cliente = db.query(ClienteModel).filter(ClienteModel.documento == doc_limpo).first()
    if db_cliente:
        raise HTTPException(status_code=400, detail="Cliente já cadastrado com este documento.")
    
    new_cliente = ClienteModel(**cliente_in.model_dump())
    new_cliente.documento = doc_limpo
    db.add(new_cliente)
    db.commit()
    db.refresh(new_cliente)
    return new_cliente

@router.get("/{cliente_id}", response_model=Cliente)
def buscar_cliente(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente

@router.get("/buscar-doc/{documento}", response_model=Cliente)
def buscar_por_documento(
    documento: str, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    doc_limpo = "".join(filter(str.isdigit, documento))
    cliente = db.query(ClienteModel).filter(ClienteModel.documento == doc_limpo).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente

@router.get("/pesquisar/termo", response_model=List[Cliente])
def pesquisar_clientes(
    q: str, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Busca clientes por nome ou documento (parcial)."""
    return db.query(ClienteModel).filter(
        (ClienteModel.nome.ilike(f"%{q}%")) | 
        (ClienteModel.documento.ilike(f"%{q}%"))
    ).limit(10).all()
