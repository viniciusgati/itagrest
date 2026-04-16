import pytest
from decimal import Decimal
from app.services.migracao import MigracaoService
from app.models.produto import CategoriaEnum

def test_importar_xml_com_dados_invalidos(db_session):
    """
    TESTE DE FALHA: Simula um XML com campos faltantes ou formatos errados.
    Deve falhar ou ser tratado pelo serviço para não quebrar a transação.
    """
    xml_sujo = b"""<?xml version="1.0" standalone="yes"?>
    <Produtos>
      <Produto ProdutoID="999">
        <Codigo>99</Codigo>
        <Descritivo></Descritivo> 
        <PrecoUnitario>INVALIDO</PrecoUnitario>
        <Un>UN</Un>
        <CST>NCM_ERRADO;CST;PIS</CST>
      </Produto>
    </Produtos>
    """
    
    # Este teste deve falhar se o código não tratar ValueError de Decimal 
    # ou AttributeError de None.text
    try:
        count = MigracaoService.importar_produtos_xml(xml_sujo, db_session)
        assert count == 0, "Deveria ter pulado o produto inválido"
    except Exception as e:
        pytest.fail(f"O serviço quebrou em vez de tratar o erro: {str(e)}")
