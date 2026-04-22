import os
import sys

# PRIMEIRO adiciona as libs ao path
sys.path.insert(0, os.path.abspath('temp_libs'))

import io
from lxml import etree
from datetime import datetime
import nfelib.v4_00.leiauteNFe as nfe

# --- MONKEY PATCH REFORÇADO ---
def apply_brutal_patch(module):
    def wrap_export(old_export):
        def new_export(self, outfile, level, namespace_='', name_=None, namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"', pretty_print=True):
            # 1. Exporta para um buffer temporário
            buf = io.StringIO()
            old_export(self, buf, level, namespace_='', name_=name_, namespacedef_=namespacedef_, pretty_print=pretty_print)
            content = buf.getvalue()
            # 2. Remove o prefixo editix: que a lib insiste em colocar
            content = content.replace('editix:', '')
            content = content.replace('xmlns:editix="http://www.portalfiscal.inf.br/nfe"', '')
            # 3. Escreve no outfile original
            outfile.write(content)
        return new_export

    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and hasattr(obj, 'export'):
            obj.export = wrap_export(obj.export)

apply_brutal_patch(nfe)

# --- MOCKS ---
class MockEmpresa:
    cnpj = "49112135000138"
    razao_social = "Rosicler Lúcia dos santos"
    inscricao_estadual = "124416138114"
    ambiente = 2
    uf = "SP"

class MockItem:
    id = 1
    origem = "0"
    ncm = "22021000"
    cfop = "5102"
    preco_unitario = 10.00
    quantidade = 1.0
    subtotal = 10.00
    class MockProduto:
        descricao = "PRODUTO TESTE"
        unidade = "UN"
    produto = MockProduto()

class MockVenda:
    id = 32
    total = 10.00
    forma_pagamento = "DINHEIRO"
    itens = [MockItem()]
    cliente = None

def simulate_montar_xml(empresa, venda, chave_acesso):
    ide = nfe.ideType(
        cUF='35', natOp="VENDA", mod='65', serie='1', nNF=str(venda.id),
        dhEmi=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S-03:00'),
        tpAmb=str(empresa.ambiente), tpImp='4', tpEmis='1', cDV=str(chave_acesso[-1]),
        cNF=str(venda.id).zfill(8), idDest='1', indFinal='1', indPres='1', 
        procEmi='0', verProc="1.0.0", tpNF='1', cMunFG='3550308'
    )
    emit = nfe.emitType(
        CNPJ=empresa.cnpj, xNome=empresa.razao_social, IE=empresa.inscricao_estadual, CRT='1',
        enderEmit=nfe.TEnderEmi(
            xLgr="AVENIDA PAULISTA", nro="1000", xBairro="BELA VISTA",
            cMun='3550308', xMun="SAO PAULO", UF=str(empresa.uf).upper(),
            CEP="01310100", cPais='1058', xPais="BRASIL"
        )
    )
    itens_det = []
    for i, item in enumerate(venda.itens):
        imposto = nfe.impostoType(
            ICMS=nfe.ICMSType(ICMSSN102=nfe.ICMSSN102Type(orig=str(item.origem or '0'), CSOSN='102')),
            PIS=nfe.PISType(PISNT=nfe.PISNTType(CST='07')),
            COFINS=nfe.COFINSType(COFINSNT=nfe.COFINSNTType(CST='07'))
        )
        det = nfe.detType(
            nItem=str(i+1),
            prod=nfe.prodType(
                cProd=str(item.id), cEAN="", xProd=item.produto.descricao,
                NCM=item.ncm or "00000000", CFOP=str(item.cfop or "5102"),
                uCom=item.produto.unidade, qCom=f"{item.quantidade:.4f}",
                vUnCom=f"{item.preco_unitario:.4f}", vProd=f"{item.subtotal:.2f}",
                cEANTrib="", uTrib=item.produto.unidade, qTrib=f"{item.quantidade:.4f}",
                vUnTrib=f"{item.preco_unitario:.4f}", indTot='1'
            ),
            imposto=imposto
        )
        itens_det.append(det)

    total = nfe.totalType(
        ICMSTot=nfe.ICMSTotType(
            vBC="0.00", vICMS="0.00", vICMSDeson="0.00", vFCP="0.00", vBCST="0.00",
            vST="0.00", vFCPST="0.00", vFCPSTRet="0.00", vProd=f"{venda.total:.2f}",
            vFrete="0.00", vSeg="0.00", vDesc="0.00", vII="0.00", vIPI="0.00",
            vIPIDevol="0.00", vPIS="0.00", vCOFINS="0.00", vOutro="0.00", vNF=f"{venda.total:.2f}"
        )
    )
    pag = nfe.pagType(detPag=[nfe.detPagType(tPag='01' if venda.forma_pagamento == "DINHEIRO" else '17', vPag=f"{venda.total:.2f}")])
    inf_nfe_data = nfe.infNFeType(Id=f"NFe{chave_acesso}", versao="4.00", ide=ide, emit=emit, dest=None, det=itens_det, total=total, pag=pag)
    return nfe.TNFe(infNFe=inf_nfe_data)

def test_validate_venda_32_xml():
    print("--- INICIANDO TESTE DE VALIDAÇÃO DE XML (VENDA 32) ---")
    empresa = MockEmpresa()
    venda = MockVenda()
    chave = "35260449112135000138650010000000321000000320"
    
    nfe_obj = simulate_montar_xml(empresa, venda, chave)
    
    output = io.StringIO()
    nfe_obj.export(output, 0, name_='TNFe', namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"')
    xml_content = output.getvalue()
    
    print("\nXML Gerado (Primeiros 200 chars):\n", xml_content[:200])
    
    # Validação do prefixo
    assert "editix" not in xml_content, "ERRO: O prefixo 'editix' ainda está presente no XML!"
    
    # Validação estrutural básica
    root = etree.fromstring(xml_content.encode('utf-8'))
    ns = "{http://www.portalfiscal.inf.br/nfe}"
    assert root.tag == f"{ns}TNFe", "Tag raiz deve ser TNFe"
    
    print("\n✅ SUCESSO: XML Validado e livre de erros de namespace!")

if __name__ == "__main__":
    test_validate_venda_32_xml()
