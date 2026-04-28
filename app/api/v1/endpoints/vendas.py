import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from app.db.session import get_db
from app.models.venda import Venda as VendaModel, VendaItem as VendaItemModel, StatusVenda, FormaPagamento
from app.models.produto import Produto as ProdutoModel
from app.models.cliente import Cliente as ClienteModel
from app.schemas.venda import Venda as VendaSchema, VendaCreate, VendaUpdate, VendaItemCreate, MesaStatus

from app.models.usuario import Usuario
from app.api.v1.deps import get_current_gerente

router = APIRouter()

# --- Mapa de Mesas ---

@router.get("/mesas", response_model=List[MesaStatus])
def get_status_mesas(db: Session = Depends(get_db)):
    """Retorna o status de todas as mesas, priorizando a venda mais recente se houver duplicidade por erro."""
    vendas_ativas = db.query(VendaModel).filter(
        VendaModel.status.in_([StatusVenda.ABERTA, StatusVenda.AGUARDANDO_PAGAMENTO])
    ).order_by(VendaModel.id.asc()).all()
    
    # Ao usar o loop, o ID mais alto (mais recente) prevalece no dicionário
    mesas_ocupadas = {v.mesa: v for v in vendas_ativas}
    status_mesas = []
    for m in range(1, 13):
        if m in mesas_ocupadas:
            v = mesas_ocupadas[m]
            status_mesas.append(MesaStatus(
                mesa=m, 
                venda_id=v.id, 
                status=v.status, 
                total=v.total
            ))
        else:
            status_mesas.append(MesaStatus(mesa=m, status="LIVRE"))
    return status_mesas

@router.get("/lista", response_model=List[VendaSchema])
def get_vendas_lista(db: Session = Depends(get_db)):
    """Retorna o histórico das últimas 50 vendas com itens e cliente carregados."""
    try:
        return db.query(VendaModel).options(
            joinedload(VendaModel.itens),
            joinedload(VendaModel.cliente)
        ).order_by(VendaModel.data_abertura.desc()).limit(50).all()
    except Exception as e:
        print(f"ERRO LISTA VENDAS: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao carregar lista.")

# --- Gerenciamento de Vendas ---

@router.post("", response_model=VendaSchema)
def abrir_venda(venda_in: VendaCreate, db: Session = Depends(get_db)):
    """Abre uma nova mesa ou recupera a venda atual. Garante unicidade de venda ativa por mesa."""
    # 1. Tenta encontrar a venda existente
    venda_existente = db.query(VendaModel).options(
        joinedload(VendaModel.itens),
        joinedload(VendaModel.cliente)
    ).filter(
        VendaModel.mesa == venda_in.mesa,
        VendaModel.status.in_([StatusVenda.ABERTA, StatusVenda.AGUARDANDO_PAGAMENTO])
    ).order_by(VendaModel.id.desc()).first()
    
    if venda_existente:
        return venda_existente
        
    try:
        # 2. Tenta criar uma nova
        new_venda = VendaModel(mesa=venda_in.mesa)
        db.add(new_venda)
        db.commit()
        db.refresh(new_venda)
    except Exception:
        # 3. Se houver erro (ex: IntegrityError por clique duplo rápido), tenta buscar de novo
        db.rollback()
        venda_re_busca = db.query(VendaModel).options(
            joinedload(VendaModel.itens),
            joinedload(VendaModel.cliente)
        ).filter(
            VendaModel.mesa == venda_in.mesa,
            VendaModel.status.in_([StatusVenda.ABERTA, StatusVenda.AGUARDANDO_PAGAMENTO])
        ).order_by(VendaModel.id.desc()).first()
        
        if venda_re_busca:
            return venda_re_busca
        raise HTTPException(status_code=400, detail="Erro ao abrir mesa.")
    
    return db.query(VendaModel).options(
        joinedload(VendaModel.itens),
        joinedload(VendaModel.cliente)
    ).filter(VendaModel.id == new_venda.id).first()

@router.post("/{venda_id}/itens", response_model=VendaSchema)
def adicionar_item(venda_id: int, item_in: VendaItemCreate, db: Session = Depends(get_db)):
    """Adiciona um produto à comanda com suporte a preço customizado e snapshot completo."""
    venda = db.query(VendaModel).filter(VendaModel.id == venda_id).first()
    if not venda or venda.status != StatusVenda.ABERTA:
        raise HTTPException(status_code=400, detail="Comanda não permite alterações.")
    
    produto = db.query(ProdutoModel).filter(ProdutoModel.id == item_in.produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    # Define o preço unitário (prioriza o preço customizado enviado pelo usuário)
    preco_unitario = Decimal(item_in.preco_customizado) if item_in.preco_customizado is not None else Decimal(produto.preco_venda)
    subtotal = Decimal(item_in.quantidade) * preco_unitario
    
    new_item = VendaItemModel(
        venda_id=venda_id,
        produto_id=item_in.produto_id,
        quantidade=item_in.quantidade,
        preco_unitario=preco_unitario,
        subtotal=subtotal,
        # Snapshot completo para garantir histórico se o produto for deletado
        descricao=produto.descricao,
        unidade=produto.unidade,
        # Snapshot fiscal
        ncm=produto.ncm,
        cest=produto.cest,
        cfop=produto.cfop,
        origem=produto.origem,
        cst_icms=produto.cst_icms,
        cst_pis=produto.cst_pis,
        cst_cofins=produto.cst_cofins,
        aliquota_pis=produto.aliquota_pis,
        aliquota_cofins=produto.aliquota_cofins,
        aliquota_icms=produto.aliquota_icms
    )
    db.add(new_item)
    venda.total = Decimal(venda.total) + subtotal
    db.commit()
    
    return db.query(VendaModel).options(
        joinedload(VendaModel.itens),
        joinedload(VendaModel.cliente)
    ).filter(VendaModel.id == venda_id).first()

@router.put("/{venda_id}/fechar", response_model=VendaSchema)
def fechar_venda(venda_id: int, update_in: VendaUpdate, db: Session = Depends(get_db)):
    """Fecha a venda ou vincula um cliente."""
    venda = db.query(VendaModel).filter(VendaModel.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    # VALIDAÇÃO DE SEGURANÇA: Não permite pagar venda vazia
    if update_in.status == StatusVenda.PAGA:
        if not venda.itens or len(venda.itens) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Não é possível fechar uma venda sem produtos cadastrados."
            )
        if float(venda.total) <= 0:
            # Recalcula o total apenas para garantir
            total_real = sum(item.subtotal for item in venda.itens)
            if total_real <= 0:
                raise HTTPException(
                    status_code=400, 
                    detail="A venda possui produtos, mas o valor total é zero. Verifique os preços."
                )
            venda.total = total_real

    if update_in.forma_pagamento:
        venda.forma_pagamento = update_in.forma_pagamento
            
    if update_in.status:
        venda.status = update_in.status
        if update_in.status == StatusVenda.PAGA:
            venda.data_fechamento = datetime.utcnow()
    if update_in.cliente_id:
        venda.cliente_id = update_in.cliente_id

    db.commit()
    
    return db.query(VendaModel).options(
        joinedload(VendaModel.itens),
        joinedload(VendaModel.cliente)
    ).filter(VendaModel.id == venda_id).first()

@router.delete("/{venda_id}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_venda(venda_id: int, db: Session = Depends(get_db)):
    venda = db.query(VendaModel).filter(VendaModel.id == venda_id).first()
    if not venda or venda.status == StatusVenda.PAGA:
        raise HTTPException(status_code=400, detail="Não permitido.")
    db.delete(venda)
    db.commit()
    return None

@router.delete("/{venda_id}/itens/{item_id}", response_model=VendaSchema)
def cancelar_item(venda_id: int, item_id: int, db: Session = Depends(get_db)):
    venda = db.query(VendaModel).filter(VendaModel.id == venda_id).first()
    item = db.query(VendaItemModel).filter(VendaItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    venda.total = Decimal(venda.total) - Decimal(item.subtotal)
    db.delete(item)
    db.commit()
    return db.query(VendaModel).options(joinedload(VendaModel.itens), joinedload(VendaModel.cliente)).filter(VendaModel.id == venda_id).first()

@router.get("/stats/resumo")
def get_venda_resumo(
    dias: int = 7, 
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    # Data de início baseada no filtro
    inicio = datetime.utcnow() - timedelta(days=dias)
    vendas = db.query(VendaModel).filter(
        VendaModel.data_abertura >= inicio, 
        VendaModel.status == StatusVenda.PAGA
    ).all()
    
    total = sum(v.total for v in vendas)
    qtd = len(vendas)
    return {
        "total_faturado": total, 
        "qtd_vendas": qtd, 
        "ticket_medio": total/qtd if qtd > 0 else 0
    }

@router.get("/stats/faturamento-periodo")
def get_faturamento_periodo(
    dias: int = 7, 
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    """Retorna o faturamento agrupado por dia ou mês dependendo do período."""
    inicio = datetime.utcnow() - timedelta(days=dias)
    
    if dias > 30:
        # Agrupamento mensal para períodos longos (1 ano)
        # strftime ou date_trunc dependendo do banco. Para Postgres:
        res = db.query(
            func.to_char(VendaModel.data_abertura, 'YYYY-MM').label('periodo'), 
            func.sum(VendaModel.total).label('total')
        ).filter(
            VendaModel.data_abertura >= inicio, 
            VendaModel.status == StatusVenda.PAGA
        ).group_by('periodo').order_by('periodo').all()
    else:
        # Agrupamento diário
        res = db.query(
            func.date(VendaModel.data_abertura).label('periodo'), 
            func.sum(VendaModel.total).label('total')
        ).filter(
            VendaModel.data_abertura >= inicio, 
            VendaModel.status == StatusVenda.PAGA
        ).group_by('periodo').order_by('periodo').all()
        
    return [{"periodo": str(r.periodo), "total": float(r.total)} for r in res]

@router.get("/stats/top-produtos")
def get_top_produtos(
    dias: int = 7, 
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    inicio = datetime.utcnow() - timedelta(days=dias)
    res = db.query(
        ProdutoModel.descricao, 
        func.sum(VendaItemModel.quantidade).label('qtd')
    ).join(VendaItemModel).join(VendaModel).filter(
        VendaModel.data_abertura >= inicio,
        VendaModel.status == StatusVenda.PAGA
    ).group_by(ProdutoModel.id).order_by(func.sum(VendaItemModel.quantidade).desc()).limit(5).all()
    
    return [{"produto": r.descricao, "qtd": int(r.qtd)} for r in res]
