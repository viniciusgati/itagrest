import os
import sys
import io
from datetime import datetime

# Adiciona pastas de libs
sys.path.insert(0, os.path.abspath('temp_libs'))
sys.path.insert(0, os.path.abspath('.'))

from nfelib.v4_00 import leiauteNFe as nfe
from app.services.sefaz import SefazService, DocumentoEletronico

# Mock de objetos mínimos para o teste
class MockEmpresa:
    cnpj = "49112135000138"
    razao_social = "ROSICLER LUCIA DOS SANTOS"
    inscricao_estadual = "124416138114"
    ambiente = 2
    uf = "SP"
    logradouro = "RUA INGLATERRA"
    numero = "921"
    bairro = "VILA NOSSA SENHORA DE FATIMA"
    municipio_ibge = "3549805"
    municipio_nome = "SAO JOSE DO RIO PRETO"
    cep = "15015510"
    csc_token = "8CBED289C3A71563DF4FAF8C6247329F7C527CEB"
    csc_id = "000002"

class MockItem:
    id = 40
    origem = 0
    cfop = "5102"
    ncm = "21069029"
    quantidade = 1.0
    preco_unitario = 10.0
    subtotal = 10.0
    class MockProd:
        descricao = "MARMITA MEDIA"
        unidade = "UN"
    produto = MockProd()

class MockVenda:
    id = 36
    total = 10.0
    forma_pagamento = "DINHEIRO"
    cliente = None
    itens = [MockItem()]

def test_gen():
    empresa = MockEmpresa()
    venda = MockVenda()
    chave = "35260449112135000138650010000000361000000360"
    
    print("Gerando XML...")
    # 1. Monta o objeto
    nfe_obj = SefazService._montar_xml_nfce(empresa, venda, chave)
    
    # 2. Gera a string (Usando nosso Patch Global)
    xml_string, _ = DocumentoEletronico()._generateds_to_string_etree(nfe_obj)
    
    print("\n--- XML RESULTANTE ---")
    print(xml_string)
    
    with open("venda_36_debug.xml", "w") as f:
        f.write(xml_string)
    print("\nArquivo salvo em venda_36_debug.xml")

if __name__ == "__main__":
    test_gen()
