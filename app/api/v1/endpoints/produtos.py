from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.produto import Produto as ProdutoModel, CategoriaEnum
from app.schemas.produto import ProdutoCreate, ProdutoUpdate, Produto as ProdutoSchema
from app.services.imagem import ImagemService
from app.api.v1.deps import get_current_user, get_current_gerente
from app.models.usuario import Usuario

router = APIRouter()

from app.services.migracao import MigracaoService

@router.post("/importar-xml", status_code=status.HTTP_200_OK)
async def importar_xml(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    """Importa produtos de um arquivo XML legado (@PRODUTOS.XML)."""
    if not file.filename.lower().endswith('.xml'):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um XML.")
    
    content = await file.read()
    try:
        qtd = MigracaoService.importar_produtos_xml(content, db)
        return {"message": f"Sucesso! {qtd} produtos importados ou atualizados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no parse do XML: {str(e)}")

@router.get("", response_model=List[ProdutoSchema])
def list_produtos(
    db: Session = Depends(get_db), 
    categoria: Optional[CategoriaEnum] = None,
    skip: int = 0, 
    limit: int = 100,
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos os produtos com filtro opcional de categoria."""
    query = db.query(ProdutoModel)
    if categoria:
        query = query.filter(ProdutoModel.categoria == categoria)
    return query.offset(skip).limit(limit).all()

@router.get("/{produto_id}", response_model=ProdutoSchema)
def get_produto(
    produto_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtém detalhes de um produto específico."""
    produto = db.query(ProdutoModel).filter(ProdutoModel.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@router.post("", response_model=ProdutoSchema, status_code=status.HTTP_201_CREATED)
def create_produto(
    produto_in: ProdutoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    """Cria um novo produto no cardápio."""
    new_produto = ProdutoModel(**produto_in.model_dump())
    db.add(new_produto)
    db.commit()
    db.refresh(new_produto)
    return new_produto

@router.put("/{produto_id}", response_model=ProdutoSchema)
def update_produto(
    produto_id: int, 
    produto_in: ProdutoUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    """Atualiza dados de um produto existente."""
    produto = db.query(ProdutoModel).filter(ProdutoModel.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Pega apenas os campos que o frontend REALMENTE enviou no JSON
    update_data = produto_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        # SEGURANÇA EXTRA: Só atualiza se o valor não for None
        # Isso evita que campos obrigatórios (como NCM) sejam sobrescritos por nulo
        if value is not None:
            setattr(produto, field, value)
        
    db.commit()
    db.refresh(produto)
    return produto

@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_produto(
    produto_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    """Remove um produto do cardápio."""
    produto = db.query(ProdutoModel).filter(ProdutoModel.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Excluir imagem se existir
    if produto.imagem_url:
        ImagemService.excluir_imagem(produto.imagem_url)
        
    db.delete(produto)
    db.commit()
    return None

@router.post("/{produto_id}/imagem", response_model=ProdutoSchema)
async def upload_produto_imagem(
    produto_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    """Faz o upload de uma imagem para um produto específico."""
    produto = db.query(ProdutoModel).filter(ProdutoModel.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # 1. Excluir imagem antiga se existir
    if produto.imagem_url:
        ImagemService.excluir_imagem(produto.imagem_url)
        
    # 2. Salvar nova imagem
    content = await file.read()
    path = ImagemService.salvar_imagem_produto(content, file.filename)
    
    # 3. Atualizar produto
    produto.imagem_url = path
    db.commit()
    db.refresh(produto)
    return produto
