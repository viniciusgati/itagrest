import pytest
from fastapi import status
from app.models.venda import StatusVenda

def test_persistencia_cliente_entre_sessoes(client):
    """
    TESTE DE REGRESSÃO: Garante que o vínculo do cliente persiste ao reabrir a comanda.
    Simula: Abrir mesa -> Vincular Cliente -> Fechar Tela -> Reabrir Mesa.
    """
    
    # 1. SETUP: Criar o cliente
    res_cli = client.post("/api/v1/clientes/", json={
        "nome": "Vinicius Gati",
        "documento": "99988877766",
        "email": "vinicius@teste.com"
    })
    cliente_id = res_cli.json()["id"]

    # 2. ABRIR COMANDA (Mesa 7)
    res_venda = client.post("/api/v1/vendas/", json={"mesa": 7})
    venda_id = res_venda.json()["id"]

    # 3. VINCULAR CLIENTE (PUT /fechar)
    res_vinculo = client.put(f"/api/v1/vendas/{venda_id}/fechar", json={"cliente_id": cliente_id})
    assert res_vinculo.status_code == status.HTTP_200_OK
    assert res_vinculo.json()["cliente"]["nome"] == "Vinicius Gati"

    # 4. SIMULAR REABERTURA (Como se o garçom tivesse voltado à mesa 7 depois)
    # O endpoint POST /vendas/ é o que o frontend usa para entrar na mesa
    res_reabertura = client.post("/api/v1/vendas/", json={"mesa": 7})
    assert res_reabertura.status_code == status.HTTP_200_OK
    
    # VERIFICAÇÃO CRÍTICA
    data = res_reabertura.json()
    assert data["cliente"] is not None, "ERRO: O cliente sumiu ao reabrir a comanda!"
    assert data["cliente"]["id"] == cliente_id
    assert data["cliente"]["nome"] == "Vinicius Gati"
