import pytest
from fastapi import status
from decimal import Decimal
from app.models.venda import StatusVenda, FormaPagamento

def test_fluxo_venda_completo_pix(client):
    """
    Simula o fluxo completo de uma venda no PDV (US003):
    Abrir mesa -> Adicionar itens -> Fechar com PIX -> Confirmar Pagamento.
    """
    
    # 1. SETUP: Criar um produto para vender
    produto_data = {
        "descricao": "Hambúrguer de Teste",
        "preco_venda": 25.50,
        "categoria": "REFEICAO",
        "unidade": "UN",
        "ncm": "12345678",
        "cfop": "5102"
    }
    res_prod = client.post("/api/v1/produtos/", json=produto_data)
    assert res_prod.status_code == status.HTTP_201_CREATED
    produto_id = res_prod.json()["id"]

    # 2. SETUP: Configurar chave PIX na empresa
    empresa_data = {
        "cnpj": "12345678000199",
        "razao_social": "Restaurante de Teste LTDA",
        "inscricao_estadual": "ISENTO",
        "pix_chave": "teste@pix.com.br"
    }
    client.post("/api/v1/empresa/configurar", json=empresa_data)

    # 3. ABRIR MESA (Mesa 5)
    res_venda = client.post("/api/v1/vendas/", json={"mesa": 5})
    assert res_venda.status_code == status.HTTP_200_OK
    venda_id = res_venda.json()["id"]
    assert res_venda.json()["status"] == StatusVenda.ABERTA

    # 4. ADICIONAR ITENS (2 Hambúrgueres)
    item_data = {"produto_id": produto_id, "quantidade": 2}
    res_item = client.post(f"/api/v1/vendas/{venda_id}/itens", json=item_data)
    assert res_item.status_code == status.HTTP_200_OK
    assert Decimal(res_item.json()["total"]) == Decimal("51.00")
    assert len(res_item.json()["itens"]) == 1

    # 5. FECHAR COM PIX (Gerar payload)
    fechamento_data = {
        "forma_pagamento": FormaPagamento.PIX
    }
    res_fechar = client.put(f"/api/v1/vendas/{venda_id}/fechar", json=fechamento_data)
    assert res_fechar.status_code == status.HTTP_200_OK
    assert res_fechar.json()["status"] == StatusVenda.AGUARDANDO_PAGAMENTO
    assert "BR.GOV.BCB.PIX" in res_fechar.json()["pix_payload"]
    assert "51.00" in res_fechar.json()["pix_payload"]

    # 6. CONFIRMAR PAGAMENTO
    confirmacao_data = {
        "status": StatusVenda.PAGA
    }
    res_pago = client.put(f"/api/v1/vendas/{venda_id}/fechar", json=confirmacao_data)
    assert res_pago.status_code == status.HTTP_200_OK
    assert res_pago.json()["status"] == StatusVenda.PAGA
    assert res_pago.json()["data_fechamento"] is not None

    # 7. VERIFICAR MAPA DE MESAS (Mesa 5 deve estar LIVRE agora)
    res_mesas = client.get("/api/v1/vendas/mesas")
    mesa_5 = next(m for m in res_mesas.json() if m["mesa"] == 5)
    assert mesa_5["status"] == "LIVRE"
