import pytest
from fastapi import status

def test_register_garcom_success(client):
    """
    Valida que um gerente pode criar um usuário garçom.
    """
    # 1. Criar admin primeiro
    admin_data = {
        "full_name": "Administrador",
        "username": "admin",
        "email": "admin@itagrest.com.br",
        "password": "senha_admin"
    }
    client.post("/api/v1/setup/setup-admin", json=admin_data)
    
    # 2. Login como admin para obter token
    login_response = client.post("/api/v1/auth/login", data={
        "username": "admin",
        "password": "senha_admin"
    })
    assert login_response.status_code == status.HTTP_200_OK
    token = login_response.json()["access_token"]
    
    # 3. Criar garçom com token de gerente
    garcom_data = {
        "full_name": "João Garçom",
        "username": "joao",
        "email": "joao@itagrest.com.br",
        "password": "senha_garcom"
    }
    response = client.post(
        "/api/v1/auth/register",
        json=garcom_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "joao"
    assert data["papel"] == "GARCOM"
    assert data["is_active"] == 1

def test_register_duplicate_username(client):
    """
    Valida que não é possível criar usuário com username duplicado.
    """
    # Login como admin do primeiro teste (ja existe no fixture module)
    login = client.post("/api/v1/auth/login", data={"username": "admin", "password": "senha_admin"})
    assert login.status_code == status.HTTP_200_OK
    token = login.json()["access_token"]
    
    # Criar primeiro garçom
    resp1 = client.post("/api/v1/auth/register", json={
        "full_name": "Garcom 1",
        "username": "garcom_dup",
        "email": "garcom_dup@test.com",
        "password": "senha1"
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == status.HTTP_200_OK
    
    # Tentar criar outro com mesmo username
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Garcom 2",
        "username": "garcom_dup",
        "email": "garcom2@test.com",
        "password": "senha2"
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "já cadastrado" in response.json()["detail"]

def test_register_unauthenticated(client):
    """
    Valida que um usuário não autenticado não pode criar garçons.
    """
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Garcom",
        "username": "garcom",
        "email": "garcom@test.com",
        "password": "senha"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
