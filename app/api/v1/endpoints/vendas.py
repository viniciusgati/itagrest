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
from app.schemas.venda import Venda as VendaSchema, VendaCreate, VendaUpdate, VendaItemCreate, MesaStatus

router = APIRouter()

# --- Mapa de Mesas ---

@router.get("/mesas", response_model=List[MesaStatus])
def get_status_mesas(db: Session = Depends(get_db)):
    """Retorna o status de todas as mesas."""
    vendas_ativas = db.query(VendaModel).filter(
        VendaModel.status.in_([StatusVenda.ABERTA, StatusVenda.AGUARDANDO_PAGAMENTO])
    ).all()
    
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
    """Retorna o histórico das últimas 50 vendas com itens carregados de forma robusta."""
    try:
        vendas = db.query(VendaModel).options(
            joinedload(VendaModel.itens)
        ).order_by(VendaModel.data_abertura.desc()).limit(50).all()
        return vendas
    except Exception as e:
        print(f"ERRO CRÍTICO LISTA VENDAS: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao processar lista de vendas")

# --- Gerenciamento de Vendas ---

@router.post("/", response_model=VendaSchema)
def abrir_venda(venda_in: VendaCreate, db: Session = Depends(get_db)):
    """Abre uma nova mesa ou recupera a venda atual se já estiver aberta."""
    venda_existente = db.query(VendaModel).options(
        joinedload(VendaModel.itens),
        joinedload(VendaModel.cliente)
    ).filter(
        VendaModel.mesa == venda_in.mesa,
        VendaModel.status.in_([StatusVenda.ABERTA, StatusVenda.AGUARDANDO_PAGAMENTO])
    ).order_by(VendaModel.id.desc()).first()
    
    if venda_existente:
        return venda_existente
        
    new_venda = VendaModel(mesa=venda_in.mesa)
    db.add(new_venda)
    db.commit()
    db.refresh(new_venda)
    return new_venda

@router.post("/{venda_id}/itens", response_model=VendaSchema)
def adicionar_item(venda_id: int, item_in: VendaItemCreate, db: Session = Depends(get_db)):
    """Adiciona um produto à comanda aberta."""
    venda = db.query(VendaModel).filter(VendaModel.id == venda_id).first()
    if not venda or venda.status != StatusVenda.ABERTA:
        raise HTTPException(status_code=400, detail="Venda não encontrada ou finalizada")
    
    produto = db.query(ProdutoModel).filter(ProdutoModel.id == item_in.produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    subtotal = Decimal(item_in.quantidade) * produto.preco_venda
    new_item = VendaItemModel(
        venda_id=venda_id,
        produto_id=item_in.produto_id,
        quantidade=item_in.quantidade,
        preco_unitario=produto.preco_venda,
        subtotal=subtotal
    )
    db.add(new_item)
    venda.total = Decimal(venda.total) + subtotal
    
    db.commit()
    
    # Recarregar venda com relacionamentos para o retorno serializável
    return db.query(VendaModel).options(
        joinedload(VendaModel.itens),
        joinedload(VendaModel.cliente)
    ).filter(VendaModel.id == venda_id).first()

@router.put("/{venda_id}/fechar", response_model=VendaSchema)
def fechar_venda(venda_id: int, update_in: VendaUpdate, db: Session = Depends(get_db)):
    """Fecha a venda com a forma de pagamento."""
    venda = db.query(VendaModel).filter(VendaModel.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    if venda.status in [StatusVenda.PAGA, StatusVenda.AGUARDANDO_PAGAMENTO] and update_in.forma_pagamento:
        raise HTTPException(status_code=400, detail="Esta venda já está em processo de pagamento ou finalizada.")
    
    if update_in.forma_pagamento:
        venda.forma_pagamento = update_in.forma_pagamento
    if update_in.status:
        venda.status = update_in.status
        if update_in.status == StatusVenda.PAGA:
            venda.data_fechamento = datetime.utcnow()

    if venda.forma_pagamento == FormaPagamento.PIX and venda.status == StatusVenda.AGUARDANDO_PAGAMENTO:
        venda.pix_payload = f"00020101021226580014BR.GOV.BCB.PIX0136teste@pix.com.br520400005303986540{venda.total:.2f}5802BR5913ITAGREST_TEST6007SAO_PAULO62070503***6304"
        venda.pix_expiracao = datetime.utcnow() + timedelta(minutes=5)

    db.commit()
    db.refresh(venda)
    return venda

@router.get("/{venda_id}/log-xml")
def get_venda_xml(venda_id: int):
    """Retorna o arquivo XML de auditoria da venda."""
    path = f"storage/logs/xml_venda_{venda_id}.xml"
    if os.path.exists(path):
        return FileResponse(path, media_type='application/xml', filename=f"venda_{venda_id}.xml")
    raise HTTPException(status_code=404, detail="XML de auditoria não encontrado.")

@router.get("/{venda_id}/log-texto")
def get_venda_log_texto(venda_id: int, db: Session = Depends(get_db)):
    """Retorna resumo técnico da venda."""
    venda = db.query(VendaModel).filter(VendaModel.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada.")
    
    log = f"AUDITORIA VENDA #{venda.id}\nStatus: {venda.status}\nTotal: R$ {venda.total}\nPagamento: {venda.forma_pagamento}"
    return {"log": log}

@router.delete("/{venda_id}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_venda(venda_id: int, db: Session = Depends(get_db)):
    """Cancela uma venda aberta."""
    venda = db.query(VendaModel).filter(VendaModel.id == venda_id).first()
    if not venda or venda.status == StatusVenda.PAGA:
        raise HTTPException(status_code=400, detail="Não é possível cancelar.")
    db.delete(venda)
    db.commit()
    return None

@router.delete("/{venda_id}/itens/{item_id}", response_model=VendaSchema)
def cancelar_item(venda_id: int, item_id: int, db: Session = Depends(get_db)):
    """Remove um item da venda."""
    venda = db.query(VendaModel).filter(VendaModel.id == venda_id).first()
    item = db.query(VendaItemModel).filter(VendaItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    venda.total = Decimal(venda.total) - Decimal(item.subtotal)
    db.delete(item)
    db.commit()
    db.refresh(venda)
    return venda

@router.get("/stats/resumo")
def get_venda_resumo(db: Session = Depends(get_db)):
    """Resumo de faturamento hoje."""
    hoje = datetime.utcnow().date()
    vendas = db.query(VendaModel).filter(func.date(VendaModel.data_abertura) == hoje, VendaModel.status == StatusVenda.PAGA).all()
    total = sum(v.total for v in vendas)
    qtd = len(vendas)
    return {"total_faturado": total, "qtd_vendas": qtd, "ticket_medio": total/qtd if qtd > 0 else 0}

@router.get("/stats/faturamento-diario")
def get_faturamento_diario(db: Session = Depends(get_db)):
    """Faturamento dos últimos 7 dias."""
    sete_dias = datetime.utcnow() - timedelta(days=7)
    res = db.query(func.date(VendaModel.data_abertura).label('dia'), func.sum(VendaModel.total).label('total')).filter(VendaModel.data_abertura >= sete_dias, VendaModel.status == StatusVenda.PAGA).group_by(func.date(VendaModel.data_abertura)).all()
    return [{"dia": r.dia, "total": r.total} for r in res]

@router.get("/stats/top-produtos")
def get_top_produtos(db: Session = Depends(get_db)):
    """Top 5 produtos vendidos."""
    res = db.query(ProdutoModel.descricao, func.sum(VendaItemModel.quantidade).label('qtd')).join(VendaItemModel).join(VendaModel).filter(VendaModel.status == StatusVenda.PAGA).group_by(ProdutoModel.id).order_by(func.sum(VendaItemModel.quantidade).desc()).limit(5).all()
    return [{"produto": r.descricao, "qtd": r.qtd} for r in res]
