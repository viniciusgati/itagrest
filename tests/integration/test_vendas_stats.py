import pytest
from fastapi import status
from decimal import Decimal
from app.models.venda import StatusVenda, FormaPagamento

def test_estatisticas_pos_venda(client):
    """
    Valida se as estatísticas do Dashboard (BI) refletem as vendas realizadas (US003/US005).
    """
    
    # 1. SETUP: Criar 2 produtos
    p1 = client.post("/api/v1/produtos/", json={
        "descricao": "Produto A", "preco_venda": 10.00, "categoria": "BEBIDA", "unidade": "UN", "ncm": "12345678", "cfop": "5102"
    }).json()
    
    p2 = client.post("/api/v1/produtos/", json={
        "descricao": "Produto B", "preco_venda": 20.00, "categoria": "REFEICAO", "unidade": "UN", "ncm": "12345678", "cfop": "5102"
    }).json()

    # 2. REALIZAR UMA VENDA DE R$ 40.00 (2x P1 + 1x P2)
    res_venda = client.post("/api/v1/vendas/", json={"mesa": 1})
    v_id = res_venda.json()["id"]
    client.post(f"/api/v1/vendas/{v_id}/itens", json={"produto_id": p1["id"], "quantidade": 2})
    client.post(f"/api/v1/vendas/{v_id}/itens", json={"produto_id": p2["id"], "quantidade": 1})
    
    # Pagar a venda para entrar nas stats
    client.put(f"/api/v1/vendas/{v_id}/fechar", json={"forma_pagamento": "DINHEIRO", "status": "PAGA"})

    # 3. VALIDAR ENDPOINT: /stats/resumo
    res_resumo = client.get("/api/v1/vendas/stats/resumo")
    assert res_resumo.status_code == 200
    data = res_resumo.json()
    assert Decimal(str(data["total_faturado"])) == Decimal("40.00")
    assert data["qtd_vendas"] == 1
    assert Decimal(str(data["ticket_medio"])) == Decimal("40.00")

    # 4. VALIDAR ENDPOINT: /stats/top-produtos
    res_top = client.get("/api/v1/vendas/stats/top-produtos")
    assert res_top.status_code == 200
    top = res_top.json()
    assert top[0]["produto"] == "Produto A" # Mais vendido em quantidade (2)
    assert top[0]["qtd"] == 2
