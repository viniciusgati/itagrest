from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.cliente import Cliente as ClienteModel
from app.schemas.cliente import Cliente, ClienteCreate, ClienteUpdate

router = APIRouter()

@router.get("/", response_model=List[Cliente])
def listar_clientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(ClienteModel).offset(skip).limit(limit).all()

@router.post("/", response_model=Cliente, status_code=status.HTTP_201_CREATED)
def criar_cliente(cliente_in: ClienteCreate, db: Session = Depends(get_db)):
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
def buscar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente

@router.get("/buscar-doc/{documento}", response_model=Cliente)
def buscar_por_documento(documento: str, db: Session = Depends(get_db)):
    doc_limpo = "".join(filter(str.isdigit, documento))
    cliente = db.query(ClienteModel).filter(ClienteModel.documento == doc_limpo).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente
