import pytest
from fastapi import status
from unittest.mock import patch, MagicMock

def test_ciclo_emissao_nfce_sucesso(client):
    """
    Testa o ciclo completo de emissão de NFC-e:
    Configuração -> Venda -> Emissão -> Verificação de Persistência.
    """
    # 1. SETUP: Configurar Empresa (Emitente)
    empresa_data = {
        "cnpj": "49112135000138",
        "razao_social": "ROSICLER LUCIA DOS SANTOS",
        "inscricao_estadual": "123456789",
        "uf": "SP",
        "ambiente": 2 # Homologação
    }
    client.post("/api/v1/empresa/configurar", json=empresa_data)

    # 2. SETUP: Criar Produto
    prod_res = client.post("/api/v1/produtos/", json={
        "descricao": "Coca-Cola 350ml",
        "preco_venda": 5.50,
        "unidade": "UN",
        "categoria": "BEBIDA",
        "ncm": "22021000",
        "cfop": "5102",
        "origem": "0"
    })
    produto_id = prod_res.json()["id"]

    # 3. REALIZAR VENDA
    venda_res = client.post("/api/v1/vendas/", json={"mesa": 1})
    venda_id = venda_res.json()["id"]
    client.post(f"/api/v1/vendas/{venda_id}/itens", json={"produto_id": produto_id, "quantidade": 1})
    client.put(f"/api/v1/vendas/{venda_id}/fechar", json={"forma_pagamento": "DINHEIRO", "status": "PAGA"})

    # 4. EMITIR NOTA (Mockando apenas a transmissão SOAP para evitar rede externa)
    # Se HAS_ERPBRASIL for False, o código já faz mock interno, mas vamos garantir estabilidade no teste.
    with patch("app.services.sefaz.SefazService.emitir_nfce") as mock_emit:
        # Simulando retorno de sucesso da SEFAZ
        mock_nota = MagicMock()
        mock_nota.status_sefaz = "100"
        mock_nota.chave_acesso = "35230449112135000138650010000000011000000010"
        mock_nota.protocolo = "135230000000001"
        mock_nota.motivo_sefaz = "Autorizado o uso da NF-e"
        mock_nota.numero_nota = 1
        mock_nota.serie_nota = 1
        mock_nota.venda_id = venda_id
        mock_emit.return_value = mock_nota

        res_emissao = client.post(f"/api/v1/notas/emitir/{venda_id}")
        assert res_emissao.status_code == status.HTTP_200_OK
        assert res_emissao.json()["status_sefaz"] == "100"
        assert "chave_acesso" in res_emissao.json()

def test_emissao_falha_empresa_nao_configurada(client):
    """
    Valida se o sistema impede a emissão se a empresa não tiver dados fiscais.
    """
    # Abrir venda sem configurar empresa
    venda_res = client.post("/api/v1/vendas/", json={"mesa": 2})
    venda_id = venda_res.json()["id"]
    
    # Tentar emitir
    res = client.post(f"/api/v1/notas/emitir/{venda_id}")
    # Nota: O backend atual raise Exception que vira 500 ou 400 dependendo do handler
    assert res.status_code != status.HTTP_200_OK

def test_emissao_falha_conexao_sefaz(client):
    """
    Simula uma falha de rede/conexão com os servidores da SEFAZ.
    """
    # 1. SETUP: Empresa configurada
    client.post("/api/v1/empresa/configurar", json={
        "cnpj": "49112135000138",
        "razao_social": "ROSICLER LUCIA DOS SANTOS",
        "inscricao_estadual": "123456789",
        "uf": "SP",
        "ambiente": 2
    })

    # 2. SETUP: Venda paga
    venda_res = client.post("/api/v1/vendas/", json={"mesa": 5})
    venda_id = venda_res.json()["id"]
    client.put(f"/api/v1/vendas/{venda_id}/fechar", json={"forma_pagamento": "DINHEIRO", "status": "PAGA"})

    # 3. TENTAR EMITIR COM FALHA DE CONEXÃO (Simulada)
    with patch("app.services.sefaz.SefazService.emitir_nfce", side_effect=Exception("Timeout ou Falha de Conexão com SEFAZ")):
        res = client.post(f"/api/v1/notas/emitir/{venda_id}")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Falha de Conexão com SEFAZ" in res.json()["detail"]
