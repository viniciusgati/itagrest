from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models.venda import Venda as VendaModel, VendaItem as VendaItemModel, StatusVenda
from app.models.produto import Produto as ProdutoModel


def _periodo_anterior(dias: int):
    fim_anterior = datetime.utcnow() - timedelta(days=dias)
    inicio_anterior = fim_anterior - timedelta(days=dias)
    return inicio_anterior, fim_anterior


def calcular_resumo(db: Session, dias: int):
    agora = datetime.utcnow()
    inicio_periodo = agora - timedelta(days=dias)
    inicio_anterior, fim_anterior = _periodo_anterior(dias)

    def _stats(inicio, fim):
        r = db.query(
            func.coalesce(func.sum(VendaModel.total), 0).label('total'),
            func.count(VendaModel.id).label('qtd')
        ).filter(
            VendaModel.data_abertura >= inicio,
            VendaModel.data_abertura < fim,
            VendaModel.status == StatusVenda.PAGA
        ).first()
        total = float(r.total)
        qtd = r.qtd
        ticket = total / qtd if qtd > 0 else 0
        return total, qtd, ticket

    total, qtd, ticket = _stats(inicio_periodo, agora)
    total_ant, qtd_ant, ticket_ant = _stats(inicio_anterior, fim_anterior)

    def variacao(atual, anterior):
        if anterior == 0:
            return 100.0 if atual > 0 else 0.0
        return round(((atual - anterior) / anterior) * 100, 1)

    return {
        "total_faturado": total,
        "qtd_vendas": qtd,
        "ticket_medio": ticket,
        "variacao_faturamento": variacao(total, total_ant),
        "variacao_qtd": variacao(qtd, qtd_ant),
        "variacao_ticket": variacao(ticket, ticket_ant),
    }


def calcular_faturamento_periodo(db: Session, dias: int):
    inicio = datetime.utcnow() - timedelta(days=dias)

    if dias > 30:
        res = db.query(
            func.strftime('%Y-%m', VendaModel.data_abertura).label('periodo'),
            func.sum(VendaModel.total).label('total')
        ).filter(
            VendaModel.data_abertura >= inicio,
            VendaModel.status == StatusVenda.PAGA
        ).group_by('periodo').order_by('periodo').all()
    else:
        res = db.query(
            func.date(VendaModel.data_abertura).label('periodo'),
            func.sum(VendaModel.total).label('total')
        ).filter(
            VendaModel.data_abertura >= inicio,
            VendaModel.status == StatusVenda.PAGA
        ).group_by('periodo').order_by('periodo').all()

    return [{"periodo": str(r.periodo), "total": float(r.total)} for r in res]


def calcular_top_produtos(db: Session, dias: int):
    inicio = datetime.utcnow() - timedelta(days=dias)
    res = db.query(
        VendaItemModel.descricao,
        func.sum(VendaItemModel.quantidade).label('qtd')
    ).join(VendaModel).filter(
        VendaModel.data_abertura >= inicio,
        VendaModel.status == StatusVenda.PAGA
    ).group_by(VendaItemModel.descricao).order_by(
        func.sum(VendaItemModel.quantidade).desc()
    ).limit(5).all()

    return [{"produto": r.descricao, "qtd": int(r.qtd)} for r in res]
