import pytest
import os
from app.services.certificado import CertificadoService

def test_validacao_pfx_senha_errada():
    """
    TESTE DE FALHA: Tenta validar um conteúdo que não é PFX ou com senha errada.
    """
    conteudo_falso = b"ISSO_NAO_E_UM_PFX"
    senha = "qualquer_senha"
    
    valido = CertificadoService.validar_pfx(conteudo_falso, senha)
    assert valido is False, "Não deveria validar um conteúdo falso"

def test_validacao_pfx_real_com_senha_errada():
    """
    TESTE DE FALHA: Usa o arquivo real mas com senha propositalmente errada.
    """
    caminho_real = "Cert Restaurante/ROSICLER LUCIA DOS SANTOS49112135000138 senha123456.pfx"
    
    if os.path.exists(caminho_real):
        with open(caminho_real, "rb") as f:
            content = f.read()
        
        valido = CertificadoService.validar_pfx(content, "SENHA_ERRADA_123")
        assert valido is False, "Deveria falhar com senha incorreta"
    else:
        pytest.skip("Arquivo de certificado real não encontrado para o teste")
