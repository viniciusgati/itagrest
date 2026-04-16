import pytest
from fastapi import status

def test_setup_flow_and_security(client):
    """
    Valida o fluxo completo de setup e o fechamento do bootstrap (US000).
    Cobre RISK-SEC-01 e os apontamentos do Quinn (QA).
    """
    
    # 1. Verificar se o setup é necessário inicialmente (DB vazio)
    response = client.get("/api/v1/setup/status")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["setup_needed"] is True
    
    # 2. Criar o administrador (Primeiro uso do bootstrap)
    admin_data = {
        "full_name": "Administrador do Sistema",
        "username": "admin",
        "email": "admin@itagrest.com.br",
        "password": "senha_segura_admin"
    }
    response = client.post("/api/v1/setup/setup-admin", json=admin_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "admin"
    assert "id" in response.json()
    
    # 3. Tentar criar outro administrador (Endpoint deve estar desativado)
    response = client.post("/api/v1/setup/setup-admin", json=admin_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Bootstrap desativado" in response.json()["detail"]
    
    # 4. Verificar se o status agora indica que o setup não é mais necessário
    response = client.get("/api/v1/setup/status")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["setup_needed"] is False
