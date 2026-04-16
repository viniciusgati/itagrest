import pytest
from fastapi import status

def test_empresa_status_carrega_dados_salvos(client):
    """
    TESTE DE FALHA: Verifica se os dados salvos no Passo 1 aparecem no GET /status.
    Isso garante que o Wizard consiga popular o formulário ao reabrir.
    """
    
    # 1. Salvar dados
    empresa_data = {
        "cnpj": "12345678000199",
        "razao_social": "Restaurante Original",
        "inscricao_estadual": "123.456.789"
    }
    client.post("/api/v1/empresa/configurar", json=empresa_data)
    
    # 2. Verificar se o GET /status traz a 'empresa' no payload
    # Muitos backends retornam apenas {"configurado": true}, falhando aqui.
    response = client.get("/api/v1/empresa/status")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert "empresa" in data, "O payload de status deve conter o objeto 'empresa'"
    assert data["empresa"]["cnpj"] == "12345678000199"
