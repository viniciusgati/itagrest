
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.venda import StatusVenda

def test_duplicidade_venda_mesa(client):
    # 1. Abre mesa 1 pela primeira vez
    res1 = client.post("/api/v1/vendas/", json={"mesa": 1})
    assert res1.status_code == 200
    venda1_id = res1.json()["id"]

    # 2. Abre mesa 1 pela segunda vez
    res2 = client.post("/api/v1/vendas/", json={"mesa": 1})
    assert res2.status_code == 200
    venda2_id = res2.json()["id"]

    # Devem ser o mesmo ID
    assert venda1_id == venda2_id, f"IDs diferentes para a mesma mesa aberta: {venda1_id} != {venda2_id}"

def test_status_mesa_com_multiplas_vendas(client):
    # Simula o que encontramos no debug: duas vendas abertas para a mesma mesa
    # (Isso só aconteceria se houvesse falha no check acima, ou inserção direta)
    
    # Mas vamos testar o endpoint /mesas
    res_mesas = client.get("/api/v1/vendas/mesas")
    assert res_mesas.status_code == 200
