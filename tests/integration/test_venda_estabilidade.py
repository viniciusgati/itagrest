import pytest
from fastapi import status
from app.models.venda import StatusVenda

def test_venda_identificacao_cliente_e_fechamento(client):
    """
    TESTE DE REGRESSÃO: Valida se o cliente permanece vinculado durante todo o fluxo.
    """
    
    # 1. Criar Cliente
    cliente_data = {
        "nome": "Cliente Teste Estabilidade",
        "documento": "12345678901",
        "email": "teste@estavel.com"
    }
    res_cli = client.post("/api/v1/clientes/", json=cliente_data)
    assert res_cli.status_code == status.HTTP_201_CREATED
    cliente_id = res_cli.json()["id"]

    # 2. Abrir Venda na Mesa 10
    res_venda = client.post("/api/v1/vendas/", json={"mesa": 10})
    assert res_venda.status_code == status.HTTP_200_OK
    venda_id = res_venda.json()["id"]

    # 3. Vincular Cliente à Venda (Via PUT /fechar que usamos para update)
    res_vinculo = client.put(f"/api/v1/vendas/{venda_id}/fechar", json={"cliente_id": cliente_id})
    assert res_vinculo.status_code == status.HTTP_200_OK
    
    # FALHA AQUI: O retorno deve conter o objeto 'cliente' para o Frontend atualizar
    venda_data = res_vinculo.json()
    assert venda_data["cliente"] is not None, "O retorno da API deve conter o objeto cliente após o vínculo"
    assert venda_data["cliente"]["nome"] == "Cliente Teste Estabilidade"

    # 4. Fechar Venda e garantir que o cliente persiste
    res_final = client.put(f"/api/v1/vendas/{venda_id}/fechar", json={"status": StatusVenda.PAGA, "forma_pagamento": "DINHEIRO"})
    assert res_final.status_code == status.HTTP_200_OK
    assert res_final.json()["cliente"]["id"] == cliente_id
